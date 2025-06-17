import streamlit as st
import os
import pydicom
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.uid import generate_uid, ExplicitVRLittleEndian
import numpy as np
import datetime
import zipfile
import io
import re

# --- Core Logic (adapted from previous scripts) ---

CTImageStorage_UID = "1.2.840.10008.5.1.4.1.1.2"

def parse_revvity_vox_from_stream(vox_stream):
    """Parses a Revvity/Rigaku .VOX file from an in-memory stream."""
    header_info = {}
    header_lines_log = []  # For debugging
    MAX_HEADER_SIZE = 5 * 1024 * 1024  # 5 MB limit for header
    header_bytes_read = 0

    try:
        while header_bytes_read < MAX_HEADER_SIZE:
            line_bytes = vox_stream.readline()
            if not line_bytes:
                st.error("Error: End of file reached before finding the end-of-header marker (`##\\f`) within the first 5MB.")
                return None, None, header_lines_log
            
            # --- SAFETY CHECK ---
            # If a single "line" is huge, it's not a text header. Abort.
            if len(line_bytes) > 2048: # 2KB is a very generous limit for a header line
                st.error("Error: Detected a line of over 2KB, which indicates this is not a text-based header. The file is likely a binary format that is not supported, or it is corrupt.")
                header_lines_log.append(f"SAFETY_ABORT: Read a single line of {len(line_bytes)} bytes.")
                return None, None, header_lines_log

            header_bytes_read += len(line_bytes)

            try:
                line_text = line_bytes.decode('ascii').strip()
                header_lines_log.append(line_text)
            except UnicodeDecodeError:
                header_lines_log.append(f"UNICODE_DECODE_ERROR on bytes: {line_bytes[:200]!r}...") # Log truncated bytes
                if b'##\\x0c' in line_bytes: # Still check raw bytes for this edge case
                    line_text = line_bytes.split(b'##\\x0c', 1)[0].decode('ascii', 'ignore').strip()
                    if 'volume_size' in header_info and 'bits_per_voxel' in header_info:
                        break
                else:
                    # If we hit binary data, stop trying to read it as text.
                    st.error("Error: Detected what appears to be binary data before finding the end-of-header marker. The file header may be corrupt or the file is not a valid Revvity VOX file.")
                    header_lines_log.append(f"UNICODE_DECODE_ERROR on bytes: {line_bytes[:200]!r}...") # Log truncated bytes
                    return None, None, header_lines_log

            if line_text.startswith("Endian"):
                header_info['endian'] = line_text.split()[-1]
            elif line_text.startswith("VolumeSize"):
                parts = line_text.split()
                header_info['volume_size'] = [int(p) for p in parts[1:4]]
            elif line_text.startswith("VolumeScale"):
                header_info['volume_scale'] = " ".join(line_text.split()[1:])
            elif line_text.startswith("Field 0"):
                match = re.search(r"Size\s+(\d+)", line_text)
                if match:
                    header_info['bits_per_voxel'] = int(match.group(1))
                match_format = re.search(r"Format\s+([a-zA-Z]+)", line_text)
                if match_format:
                    header_info['format'] = match_format.group(1)

            # New, more robust end-of-header check.
            # It checks if the line text ends with ## OR if the raw bytes contain the form-feed marker.
            if line_text.endswith('##') or b'##\\x0c' in line_bytes:
                if 'volume_size' in header_info and 'bits_per_voxel' in header_info:
                    break
        
        if header_bytes_read >= MAX_HEADER_SIZE:
            st.error(f"Error: Header parsing stopped after reading {MAX_HEADER_SIZE/(1024*1024):.1f}MB without finding the end-of-header marker. The file may be corrupt or not a valid Revvity VOX file.")
            return None, None, header_lines_log

        dims = header_info['volume_size']
        bits_per_voxel = header_info['bits_per_voxel']
        bytes_per_voxel = bits_per_voxel // 8
        num_voxels = dims[0] * dims[1] * dims[2]
        expected_binary_data_size = num_voxels * bytes_per_voxel
        
        raw_data = vox_stream.read(expected_binary_data_size)

        if len(raw_data) != expected_binary_data_size:
            st.error(f"Error: Read {len(raw_data)} bytes of binary data, but expected {expected_binary_data_size}.")
            return None, header_info, header_lines_log

        dt = np.dtype(np.uint16).newbyteorder('<')
        voxel_array = np.frombuffer(raw_data, dtype=dt)
        voxel_array = voxel_array.reshape((dims[0], dims[1], dims[2]), order='F').transpose(2, 1, 0)
        
        return voxel_array, header_info, header_lines_log
    except Exception as e:
        st.error(f"An unexpected error occurred during VOX parsing: {e}")
        return None, None, header_lines_log

def create_dicom_zip(voxel_data, header_info):
    """Creates a zip archive of DICOM files in-memory."""
    num_slices, height, width = voxel_data.shape
    bits_stored = header_info.get('bits_per_voxel', 16)
    volume_scale_str = header_info.get('volume_scale', "1.0 1.0 1.0")
    scales = [float(s) for s in volume_scale_str.split()]
    pixel_spacing_xy = [scales[1], scales[0]]
    slice_thickness = scales[2]

    study_instance_uid = generate_uid()
    series_instance_uid = generate_uid()
    series_frame_of_ref_uid = generate_uid()

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for i in range(num_slices):
            slice_data = voxel_data[i, :, :].astype(np.uint16)
            
            file_meta = FileMetaDataset()
            file_meta.MediaStorageSOPClassUID = CTImageStorage_UID
            file_meta.MediaStorageSOPInstanceUID = generate_uid()
            file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
            file_meta.ImplementationClassUID = generate_uid(prefix="2.25.")

            ds = Dataset()
            ds.file_meta = file_meta
            ds.PatientName = "VOX_Converted"
            ds.PatientID = "12345"
            ds.StudyDate = datetime.datetime.now().strftime("%Y%m%d")
            ds.StudyTime = datetime.datetime.now().strftime("%H%M%S")
            ds.StudyInstanceUID = study_instance_uid
            ds.SeriesInstanceUID = series_instance_uid
            ds.Modality = "CT"
            ds.SeriesNumber = 1
            ds.InstanceNumber = i + 1
            ds.SOPClassUID = CTImageStorage_UID
            ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
            ds.SamplesPerPixel = 1
            ds.PhotometricInterpretation = "MONOCHROME2"
            ds.PixelRepresentation = 0
            ds.Rows = height
            ds.Columns = width
            ds.BitsAllocated = 16
            ds.BitsStored = bits_stored
            ds.HighBit = bits_stored - 1
            ds.RescaleIntercept = "0"
            ds.RescaleSlope = "1"
            ds.PixelSpacing = [str(pixel_spacing_xy[0]), str(pixel_spacing_xy[1])]
            ds.SliceThickness = str(slice_thickness)
            ds.ImagePositionPatient = ["0.0", "0.0", str(i * slice_thickness)]
            ds.ImageOrientationPatient = ["1.0", "0.0", "0.0", "0.0", "1.0", "0.0"]
            ds.FrameOfReferenceUID = series_frame_of_ref_uid
            ds.PixelData = slice_data.tobytes()
            ds.is_little_endian = True
            ds.is_implicit_VR = False

            # Save to an in-memory file
            dcm_buffer = io.BytesIO()
            pydicom.dcmwrite(dcm_buffer, ds, write_like_original=False)
            dcm_buffer.seek(0)
            
            # Add to zip
            zf.writestr(f"slice_{i+1:04d}.dcm", dcm_buffer.read())
            
    zip_buffer.seek(0)
    return zip_buffer

# --- Streamlit App UI ---

st.set_page_config(page_title="VOX to DICOM Converter", layout="centered")

st.title("VOX to DICOM Converter")
st.markdown("This web app converts a **zipped** Revvity/Rigaku `.VOX` file into a DICOM series, packaged as a new `.zip` file.")
st.warning("Please zip your `.VOX` file before uploading. This helps with large file transfers.")

st.header("1. Upload Zipped .VOX File")
uploaded_zip = st.file_uploader(
    "Choose a .ZIP file containing your .VOX data",
    type="zip",
    help="Upload a .zip archive containing the primary .VOX data file."
)

if uploaded_zip is not None:
    st.success(f"Successfully uploaded `{uploaded_zip.name}`.")
    
    st.header("2. Convert to DICOM")
    st.markdown("Click the button below to start the conversion process.")
    
    if st.button("Convert to DICOM", key="convert_button"):
        vox_stream = None
        original_vox_filename = None
        
        # --- Unzipping Logic ---
        with st.spinner("Analyzing ZIP file..."):
            try:
                with zipfile.ZipFile(uploaded_zip, 'r') as zf:
                    # Find the .vox file inside the zip, ignoring hidden macOS resource fork files
                    vox_files_in_zip = [
                        f for f in zf.namelist() 
                        if f.lower().endswith('.vox') and not os.path.basename(f).startswith('._')
                    ]
                    
                    if not vox_files_in_zip:
                        st.error("Error: No `.VOX` file found inside the uploaded ZIP archive.")
                    elif len(vox_files_in_zip) > 1:
                        st.error("Error: Multiple `.VOX` files found in the ZIP. Please ensure there is only one.")
                    else:
                        original_vox_filename = vox_files_in_zip[0]
                        st.info(f"Found `{original_vox_filename}` inside the ZIP file. Preparing to parse...")
                        vox_bytes = zf.read(original_vox_filename)
                        vox_stream = io.BytesIO(vox_bytes)

            except zipfile.BadZipFile:
                st.error("Error: The uploaded file is not a valid ZIP archive.")
            except Exception as e:
                st.error(f"An unexpected error occurred while reading the ZIP file: {e}")
        # --- End Unzipping ---

        if vox_stream:
            with st.spinner("Parsing VOX file... This may take a moment."):
                voxel_data, header_info, debug_header_lines = parse_revvity_vox_from_stream(vox_stream)

            if voxel_data is not None and header_info is not None:
                st.success("VOX file parsed successfully!")
                st.json(header_info)
                
                with st.spinner("Creating DICOM files and zipping them..."):
                    zip_buffer = create_dicom_zip(voxel_data, header_info)
                
                st.success("DICOM series created and zipped!")
                
                st.header("3. Download Results")
                st.markdown("Click the button below to download your DICOM files.")

                output_zip_name = f"{os.path.splitext(os.path.basename(original_vox_filename))[0]}_dicom.zip"
                
                st.download_button(
                    label="Download DICOM.zip",
                    data=zip_buffer,
                    file_name=output_zip_name,
                    mime="application/zip",
                )
            else:
                st.error("Failed to process the VOX file. Please check that it is a valid Revvity/Rigaku .VOX file and try again.")
                if debug_header_lines:
                    with st.expander("Show Debugging Information"):
                        st.warning("The parser could not find a valid header. The content it read from the file's header section is shown below. This can help diagnose if the file is corrupt or not in the expected format.")
                        log_display = '\\n'.join(debug_header_lines[:500])
                        if len(debug_header_lines) > 500:
                            log_display += "\\n... (log truncated for display)"
                        st.code(log_display, language='text')

st.markdown("---")
st.info("Note: This tool is specifically for Revvity/Rigaku .VOX files. The associated .VIF file is not needed for upload, as key metadata is read from the VOX header.") 