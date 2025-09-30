const https = require('https')
const fs = require('fs')
const path = require('path')
const { spawn } = require('child_process')
const AdmZip = require('adm-zip')

// Python embeddable package URL (Windows x64)
const PYTHON_URL = 'https://www.python.org/ftp/python/3.11.7/python-3.11.7-embed-amd64.zip'
const PYTHON_DIR = path.join(__dirname, 'python-embed')
const PYTHON_EXE = path.join(PYTHON_DIR, 'python.exe')

async function downloadFile(url, dest) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(dest)
    https.get(url, (response) => {
      response.pipe(file)
      file.on('finish', () => {
        file.close(resolve)
      })
    }).on('error', (err) => {
      fs.unlink(dest, () => {})
      reject(err)
    })
  })
}

async function setupPython(onProgress) {
  try {
    // Check if Python is already set up
    if (fs.existsSync(PYTHON_EXE)) {
      console.log('Python already installed')
      if (onProgress) onProgress('Python already installed', 100)
      return PYTHON_EXE
    }

    console.log('Setting up Python...')
    if (onProgress) onProgress('Downloading Python...', 10)

    // Create directory
    if (!fs.existsSync(PYTHON_DIR)) {
      fs.mkdirSync(PYTHON_DIR, { recursive: true })
    }

    // Download Python
    const zipPath = path.join(PYTHON_DIR, 'python.zip')
    if (!fs.existsSync(zipPath)) {
      await downloadFile(PYTHON_URL, zipPath)
    }
    if (onProgress) onProgress('Extracting Python...', 40)

    // Extract Python
    const zip = new AdmZip(zipPath)
    zip.extractAllTo(PYTHON_DIR, true)
    if (onProgress) onProgress('Python extracted', 60)

    // Download get-pip.py
    const getPipPath = path.join(PYTHON_DIR, 'get-pip.py')
    if (!fs.existsSync(getPipPath)) {
      await downloadFile('https://bootstrap.pypa.io/get-pip.py', getPipPath)
    }
    if (onProgress) onProgress('Installing pip...', 70)

    // Install pip
    await runCommand(PYTHON_EXE, [getPipPath], PYTHON_DIR)
    if (onProgress) onProgress('Installing dependencies...', 80)

    // Install required packages
    const packages = [
      'fastapi',
      'uvicorn[standard]',
      'python-multipart',
      'keyboard',
      'pyautogui',
      'openai',
      'python-dotenv',
      'pyperclip',
      'pillow'
    ]

    for (const pkg of packages) {
      try {
        await runCommand(PYTHON_EXE, ['-m', 'pip', 'install', pkg], PYTHON_DIR)
      } catch (e) {
        console.error(`Failed to install ${pkg}:`, e.message)
      }
    }

    if (onProgress) onProgress('Python setup complete!', 100)
    console.log('Python setup complete!')
    return PYTHON_EXE

  } catch (error) {
    console.error('Failed to setup Python:', error)
    throw error
  }
}

function runCommand(command, args, cwd) {
  return new Promise((resolve, reject) => {
    const proc = spawn(command, args, { cwd, stdio: 'pipe' })
    let output = ''

    proc.stdout.on('data', (data) => {
      output += data.toString()
    })

    proc.stderr.on('data', (data) => {
      output += data.toString()
    })

    proc.on('close', (code) => {
      if (code === 0) {
        resolve(output)
      } else {
        reject(new Error(`Command failed with code ${code}: ${output}`))
      }
    })
  })
}

module.exports = { setupPython, PYTHON_EXE, PYTHON_DIR }