const https = require('https')
const fs = require('fs')
const path = require('path')
const { spawn, execSync } = require('child_process')
const AdmZip = require('adm-zip')
const os = require('os')

// Platform detection
const IS_WINDOWS = process.platform === 'win32'
const IS_MACOS = process.platform === 'darwin'
const IS_LINUX = process.platform === 'linux'

// Python URLs for different platforms
// Note: python-build-standalone repo was transferred from indygreg to astral-sh
const PYTHON_URLS = {
  win32: 'https://www.python.org/ftp/python/3.11.7/python-3.11.7-embed-amd64.zip',
  darwin_x64: 'https://github.com/astral-sh/python-build-standalone/releases/download/20231002/cpython-3.11.6%2B20231002-x86_64-apple-darwin-install_only.tar.gz',
  darwin_arm64: 'https://github.com/astral-sh/python-build-standalone/releases/download/20231002/cpython-3.11.6%2B20231002-aarch64-apple-darwin-install_only.tar.gz'
}

// Get platform-specific Python URL
function getPythonUrl() {
  if (IS_WINDOWS) {
    return PYTHON_URLS.win32
  } else if (IS_MACOS) {
    const arch = os.arch()
    return arch === 'arm64' ? PYTHON_URLS.darwin_arm64 : PYTHON_URLS.darwin_x64
  }
  throw new Error(`Unsupported platform: ${process.platform}`)
}

// Will be set by init() function
let PYTHON_DIR = null
let PYTHON_EXE = null

// Initialize Python paths with writable directory
function init(userDataPath) {
  PYTHON_DIR = path.join(userDataPath, 'python-embed')

  if (IS_WINDOWS) {
    PYTHON_EXE = path.join(PYTHON_DIR, 'python.exe')
  } else if (IS_MACOS) {
    PYTHON_EXE = path.join(PYTHON_DIR, 'python', 'bin', 'python3')
  }

  console.log('[setup-python] Platform:', process.platform, 'Arch:', os.arch())
  console.log('[setup-python] Initialized with PYTHON_DIR:', PYTHON_DIR)
  console.log('[setup-python] PYTHON_EXE:', PYTHON_EXE)
}

async function downloadFile(url, dest, retries = 3, redirectCount = 0) {
  const MAX_REDIRECTS = 5

  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      console.log(`Downloading ${url} (attempt ${attempt}/${retries})...`)
      await new Promise((resolve, reject) => {
        const file = fs.createWriteStream(dest)
        let fileOpened = true

        const request = https.get(url, (response) => {
          // Handle redirects
          if (response.statusCode === 301 || response.statusCode === 302) {
            if (redirectCount >= MAX_REDIRECTS) {
              file.close()
              fs.unlink(dest, () => {})
              reject(new Error('Too many redirects'))
              return
            }

            const redirectUrl = response.headers.location
            console.log(`Following redirect to: ${redirectUrl}`)
            file.close()
            fileOpened = false

            // Recursively call downloadFile with the redirect URL
            downloadFile(redirectUrl, dest, 1, redirectCount + 1).then(resolve).catch(reject)
            return
          }

          if (response.statusCode !== 200) {
            file.close()
            fs.unlink(dest, () => {})
            reject(new Error(`HTTP ${response.statusCode}: ${response.statusMessage}`))
            return
          }

          response.pipe(file)
          file.on('finish', () => {
            file.close(() => {
              fileOpened = false
              resolve()
            })
          })
          file.on('error', (err) => {
            if (fileOpened) {
              file.close()
              fileOpened = false
            }
            fs.unlink(dest, () => {})
            reject(err)
          })
        }).on('error', (err) => {
          if (fileOpened) {
            file.close()
            fileOpened = false
          }
          fs.unlink(dest, () => {})
          reject(err)
        })

        // Timeout after 120 seconds (larger files for macOS)
        request.setTimeout(120000, () => {
          request.abort()
          if (fileOpened) {
            file.close()
            fileOpened = false
          }
          fs.unlink(dest, () => {})
          reject(new Error('Download timeout'))
        })
      })

      // Verify file exists and has content
      if (fs.existsSync(dest) && fs.statSync(dest).size > 0) {
        console.log(`✅ Downloaded successfully: ${path.basename(dest)} (${fs.statSync(dest).size} bytes)`)
        return
      } else {
        throw new Error('Downloaded file is empty or missing')
      }
    } catch (err) {
      console.error(`❌ Download attempt ${attempt} failed:`, err.message)
      if (attempt === retries) {
        throw new Error(`Failed to download after ${retries} attempts: ${err.message}`)
      }
      await new Promise(resolve => setTimeout(resolve, 2000)) // Wait 2s before retry
    }
  }
}

function extractTarGz(archivePath, destDir) {
  return new Promise((resolve, reject) => {
    try {
      console.log(`Extracting ${archivePath} to ${destDir}...`)
      // Use system tar command on macOS
      execSync(`tar -xzf "${archivePath}" -C "${destDir}"`, {
        stdio: 'inherit',
        maxBuffer: 50 * 1024 * 1024 // 50MB buffer
      })
      console.log('✅ Extraction complete')
      resolve()
    } catch (err) {
      reject(new Error(`Failed to extract tar.gz: ${err.message}`))
    }
  })
}

async function setupPython(onProgress) {
  try {
    // Check if Python exists
    if (fs.existsSync(PYTHON_EXE)) {
      console.log('Python executable found at:', PYTHON_EXE)
      console.log('Checking for missing packages...')

      // Required packages - these must be present for the app to work
      const requiredPackages = ['fastapi', 'clipboard', 'requests', 'pydantic', 'google-auth-oauthlib', 'keyboard', 'pyautogui', 'uvicorn']
      const missingPackages = []

      // Check each required package
      for (const pkg of requiredPackages) {
        try {
          const result = await runCommand(PYTHON_EXE, ['-m', 'pip', 'show', pkg], path.dirname(PYTHON_EXE))
          if (!result.includes(`Name: ${pkg}`)) {
            missingPackages.push(pkg)
          }
        } catch (e) {
          missingPackages.push(pkg)
        }
      }

      // Install missing packages
      if (missingPackages.length > 0) {
        console.log(`Installing missing packages: ${missingPackages.join(', ')}`)

        const allPackages = [
          'fastapi',
          'uvicorn[standard]',
          'python-multipart',
          'keyboard',
          'pyautogui',
          'openai',
          'python-dotenv',
          'pyperclip',
          'clipboard',
          'requests',
          'pillow',
          'pydantic',
          'google-auth-oauthlib',
          'google-auth',
          'google-api-python-client',
          'PyJWT',
          'bcrypt',
          'ttkbootstrap'
        ]

        const tips = [
          'Updating packages...',
          'This should take 2-5 minutes...',
          'Installing core dependencies...',
          'Setting up authentication...',
          'Almost done...'
        ]

        for (let i = 0; i < allPackages.length; i++) {
          const pkg = allPackages[i]
          const progress = 50 + Math.floor((i / allPackages.length) * 50) // 50-100%
          const tipIndex = Math.floor((i / allPackages.length) * tips.length)
          const tip = tips[tipIndex] || 'Installing packages...'

          if (onProgress) onProgress(`${tip} (${i + 1}/${allPackages.length})`, progress)

          try {
            console.log(`Installing ${pkg}... (${i + 1}/${allPackages.length})`)
            await runCommand(PYTHON_EXE, ['-m', 'pip', 'install', '--no-cache-dir', pkg], PYTHON_DIR)
          } catch (e) {
            console.error(`Failed to install ${pkg}:`, e.message)
          }
        }

        if (onProgress) onProgress('All packages installed', 100)
      } else {
        console.log('All required packages already installed')
        if (onProgress) onProgress('Python already installed', 100)
      }

      return PYTHON_EXE
    }

    console.log('Setting up Python...')
    if (onProgress) onProgress('Downloading Python...', 10)

    // Create directory
    if (!fs.existsSync(PYTHON_DIR)) {
      fs.mkdirSync(PYTHON_DIR, { recursive: true })
    }

    // Get platform-specific Python URL
    const pythonUrl = getPythonUrl()
    console.log('Python URL:', pythonUrl)

    // Download Python
    const isZip = pythonUrl.endsWith('.zip')
    const archivePath = path.join(PYTHON_DIR, isZip ? 'python.zip' : 'python.tar.gz')

    if (!fs.existsSync(archivePath)) {
      await downloadFile(pythonUrl, archivePath)
    }
    if (onProgress) onProgress('Extracting Python...', 40)

    // Extract Python based on platform
    if (IS_WINDOWS) {
      console.log('Extracting ZIP archive...')
      const zip = new AdmZip(archivePath)
      zip.extractAllTo(PYTHON_DIR, true)
    } else if (IS_MACOS) {
      console.log('Extracting TAR.GZ archive...')
      await extractTarGz(archivePath, PYTHON_DIR)
    }

    if (onProgress) onProgress('Python extracted', 60)

    // Platform-specific post-extraction setup
    if (IS_WINDOWS) {
      // Fix python._pth to allow pip to work in embedded Python
      const pthFile = path.join(PYTHON_DIR, 'python311._pth')
      if (fs.existsSync(pthFile)) {
        let content = fs.readFileSync(pthFile, 'utf8')
        // Uncomment "import site" line to enable pip
        content = content.replace('#import site', 'import site')
        // Add Scripts directory to path
        content += '\nScripts\n'
        fs.writeFileSync(pthFile, content)
      }

      // Download get-pip.py
      const getPipPath = path.join(PYTHON_DIR, 'get-pip.py')
      if (!fs.existsSync(getPipPath)) {
        await downloadFile('https://bootstrap.pypa.io/get-pip.py', getPipPath)
      }
      if (onProgress) onProgress('Installing pip...', 70)

      // Install pip with retries
      let pipInstalled = false
      for (let attempt = 1; attempt <= 3; attempt++) {
        try {
          console.log(`Installing pip (attempt ${attempt}/3)...`)
          await runCommand(PYTHON_EXE, [getPipPath], PYTHON_DIR)
          pipInstalled = true
          console.log('✅ Pip installed successfully')
          break
        } catch (e) {
          console.error(`❌ Pip installation attempt ${attempt} failed:`, e.message)
          if (attempt === 3) {
            throw new Error('Failed to install pip after 3 attempts. Please check your internet connection.')
          }
          await new Promise(resolve => setTimeout(resolve, 2000)) // Wait 2s before retry
        }
      }

      if (!pipInstalled) {
        throw new Error('Could not install pip - aborting setup')
      }
    } else if (IS_MACOS) {
      // python-build-standalone already includes pip
      console.log('✅ Python standalone build includes pip')
      if (onProgress) onProgress('Verifying pip...', 70)

      // Verify pip works
      try {
        await runCommand(PYTHON_EXE, ['-m', 'pip', '--version'], PYTHON_DIR)
        console.log('✅ Pip is working')
      } catch (e) {
        throw new Error('Pip verification failed: ' + e.message)
      }
    }

    // Install required packages with verification
    const packages = [
      'fastapi',
      'uvicorn[standard]',
      'python-multipart',
      'keyboard',
      'pyautogui',
      'openai',
      'python-dotenv',
      'pyperclip',
      'clipboard',
      'requests',
      'pillow',
      'pydantic',
      'google-auth-oauthlib',
      'google-auth',
      'google-api-python-client',
      'PyJWT',
      'bcrypt',
      'ttkbootstrap'
    ]

    // Installation tips to show progress
    const tips = [
      'Setting up your workspace...',
      'Installing core dependencies...',
      'Almost there! This may take 2-5 minutes...',
      'Configuring authentication modules...',
      'Setting up the typing engine...',
      'Installing UI components...',
      'Just a few more packages...',
      'Finalizing setup...'
    ]

    const failedPackages = []
    for (let i = 0; i < packages.length; i++) {
      const pkg = packages[i]
      const pkgName = pkg.split('[')[0] // Handle uvicorn[standard]
      const progress = 80 + Math.floor((i / packages.length) * 15) // 80-95%

      // Show current package with progress
      const tipIndex = Math.floor((i / packages.length) * tips.length)
      const tip = tips[tipIndex] || 'Installing dependencies...'
      if (onProgress) onProgress(`${tip} (${i + 1}/${packages.length})`, progress)

      console.log(`Installing ${pkg}... (${i + 1}/${packages.length})`)

      try {
        await runCommand(PYTHON_EXE, ['-m', 'pip', 'install', '--no-cache-dir', pkg], PYTHON_DIR)

        // Verify it installed (case-insensitive check for package names like PyAutoGUI)
        const verifyResult = await runCommand(PYTHON_EXE, ['-m', 'pip', 'show', pkgName], PYTHON_DIR)
        if (verifyResult.toLowerCase().includes(`name: ${pkgName.toLowerCase()}`)) {
          console.log(`✅ ${pkg} installed successfully`)
        } else {
          console.error(`❌ ${pkg} installation verification failed`)
          failedPackages.push(pkg)
        }
      } catch (e) {
        console.error(`❌ Failed to install ${pkg}:`, e.message)
        failedPackages.push(pkg)
      }
    }

    // Check critical packages
    const criticalPackages = ['fastapi', 'uvicorn', 'google-auth-oauthlib']
    const missingCritical = criticalPackages.filter(p => failedPackages.some(f => f.startsWith(p)))

    if (missingCritical.length > 0) {
      throw new Error(`Critical packages failed to install: ${missingCritical.join(', ')}. The app will not work without these.`)
    }

    if (failedPackages.length > 0) {
      console.warn(`⚠️ Some packages failed to install: ${failedPackages.join(', ')}`)
      console.warn('The app may have limited functionality')
    }

    if (onProgress) onProgress('Python setup complete!', 100)
    console.log('✅ Python setup complete!')
    console.log('✅ Python executable:', PYTHON_EXE)
    return PYTHON_EXE

  } catch (error) {
    console.error('❌ Failed to setup Python:', error)
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

module.exports = {
  init,
  setupPython,
  get PYTHON_EXE() { return PYTHON_EXE },
  get PYTHON_DIR() { return PYTHON_DIR }
}
