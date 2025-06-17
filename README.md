# Revvity/Rigaku VOX to DICOM Converter

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](YOUR_STREAMLIT_APP_URL_HERE)

A web-based tool to convert proprietary `.VOX` micro-CT data files from Revvity (formerly Rigaku) scanners into a standard DICOM series, ready for use in medical imaging software like 3D Slicer or Horos.

## Live Application

The easiest way to use this converter is through the public web application, hosted for free on Streamlit Community Cloud.

**[>> Click here to access the live converter <<](YOUR_STREAMLIT_APP_URL_HERE)**

### How to Use the Web App
1.  **Open the Link:** Navigate to the live application URL provided above.
2.  **Upload File:** Click the "Browse files" button and select the `.VOX` file you wish to convert.
3.  **Convert:** Click the "Convert to DICOM" button to begin processing. The application will show you the metadata it found in the file header.
4.  **Download:** Once the conversion is complete, a "Download DICOM.zip" button will appear. Click it to save the archive containing your new DICOM files.

---

## About the VOX Format

This tool is specifically designed for the text-header-based `.VOX` file format used by Revvity/Rigaku micro-CT systems. It is not compatible with other formats that also use the `.vox` extension, such as the MagicaVoxel format.

The parser reads key metadata like `VolumeSize`, `VolumeScale`, and `BitsPerVoxel` directly from the VOX file header, so the associated `.VIF` file is not required for the conversion.

## Running the Application Locally (for Developers)

If you wish to run or modify the application on your local machine, follow these steps.

### Prerequisites
- Python 3.8+
- An IDE or text editor (e.g., VS Code)

### Setup
1.  **Clone the repository:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/vox-dicom-converter.git
    cd vox-dicom-converter
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows, use `venv\\Scripts\\activate`
    ```

3.  **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```

### Launch the App
Run the following command in your terminal. To support files larger than 200MB, you must include the `--server.maxUploadSize` flag.

```bash
streamlit run app.py --server.maxUploadSize 500
```

The application will open in your default web browser.

## For the Host (Person Running the App)

These are the one-time setup steps for the computer that will host the web application.

### 1. Initial Setup

- **Install Python:** If you don't have Python installed, download and install it from [python.org](https://www.python.org/downloads/).
- **Download App Files:** Make sure you have the `app.py` and `requirements.txt` files in a folder on your computer.
- **Install Dependencies:** Open a terminal, navigate to the folder containing the app files, and run the following command:
  ```bash
  pip install -r requirements.txt
  ```

### 2. Running the Web Application

To run the web server, open a terminal in the application's folder and use the following command.

**To support large files (e.g., up to 500MB), you must include the `--server.maxUploadSize` flag:**

```bash
streamlit run app.py --server.maxUploadSize 500
```

- After running the command, your terminal will display a "Network URL". It will look something like `http://192.168.1.10:8501`.
- You can share this URL with your colleagues.

## For the End User (Your Colleagues)

### How to Use the Converter

1.  **Open the Link:** Your colleague will provide you with a URL (e.g., `http://192.168.1.10:8501`). Open this link in your web browser.
2.  **Upload Your File:**
    - On the webpage, you will see an upload box.
    - Click "Browse files" and select the `.VOX` file you want to convert.
3.  **Convert:**
    - Once the file is uploaded, click the **"Convert to DICOM"** button.
    - The app will show the progress.
4.  **Download:**
    - After the conversion is complete, a **"Download DICOM.zip"** button will appear.
    - Click it to save the `.zip` archive containing your DICOM files.

That's it! There is no software to install.

## Initial Setup (One-time only)

1. **Install Python**
   - Open your web browser and go to: https://www.python.org/downloads/
   - Click the big yellow "Download Python" button
   - Once downloaded, double-click the installer package (it will be named something like "python-3.x.x-macos.pkg")
   - Follow the installation wizard, clicking "Continue" and "Install" when prompted
   - You may need to enter your computer's password

2. **Install Required Packages**
   - Open "Terminal" (you can find it by pressing Command+Space and typing "Terminal")
   - Copy and paste this command, then press Enter:
     ```bash
     python3 -m pip install pydicom numpy
     ```
   - Wait for the installation to complete (you'll see some text scrolling)

## Using the Converter

### Method 1: Using the GUI (Recommended)

1. **Start the Program**
   - Double-click the `run_converter.command` file
   - If you get a security warning, right-click the file and select "Open" instead
   - A window will appear with the converter interface

2. **Convert Your VOX File**
   - Click "Browse" next to "Input Folder" and select the folder containing your `.VOX` file
   - Click "Browse" next to "Output Folder" and select where you want to save the DICOM files
   - The converter will automatically read the voxel dimensions from your `.VOX` file
   - Click "Convert to DICOM"
   - Wait for the "Conversion completed successfully!" message

### Method 2: Using Terminal (Alternative)

If the GUI method doesn't work, you can use Terminal:

1. Open Terminal (Command+Space, type "Terminal")
2. Type these commands (replace the paths with your actual folder paths):
   ```bash
   cd /path/to/folder/containing/script
   python3 vox_to_dicom_converter.py /path/to/your/file.VOX /path/to/output/folder
   ```

## Troubleshooting

If you get any errors:

1. **"Command not found" error**
   - Make sure you completed the Python installation step
   - Try running the setup steps again

2. **Permission denied error**
   - Right-click the `run_converter.command` file
   - Select "Get Info"
   - At the bottom, check "Open using Terminal"
   - Close the Get Info window
   - Try running the program again

3. **Package installation errors**
   - Make sure you're connected to the internet
   - Try running the pip install command again

4. **VOX file not found or invalid**
   - Make sure your `.VOX` file is a valid Revvity/Rigaku micro-CT data file
   - Check that the file hasn't been corrupted
   - Ensure you have both the `.VOX` and `.VIF` files in the same directory

## Need Help?

If you encounter any issues:
1. Take a screenshot of any error messages
2. Note down what you were doing when the error occurred
3. Contact your IT support or the person who provided this tool

## Notes

- This converter is specifically designed for Revvity/Rigaku `.VOX` micro-CT data files
- The converter will automatically read the voxel dimensions and other metadata from your `.VOX` file
- The output will be a series of DICOM files that can be loaded into 3D Slicer or other medical imaging software
- Make sure both the `.VOX` and `.VIF` files are present in the same directory 