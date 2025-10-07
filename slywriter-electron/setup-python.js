const https = require('https')
const fs = require('fs')
const path = require('path')
const { spawn } = require('child_process')
const AdmZip = require('adm-zip')

// Python embeddable package URL (Windows x64)
const PYTHON_URL = 'https://www.python.org/ftp/python/3.11.7/python-3.11.7-embed-amd64.zip'

// Will be set by init() function
let PYTHON_DIR = null
let PYTHON_EXE = null

// Initialize Python paths with writable directory
function init(userDataPath) {
  PYTHON_DIR = path.join(userDataPath, 'python-embed')
  PYTHON_EXE = path.join(PYTHON_DIR, 'python.exe')
  console.log('[setup-python] Initialized with PYTHON_DIR:', PYTHON_DIR)
  console.log('[setup-python] PYTHON_EXE:', PYTHON_EXE)
}

async function downloadFile(url, dest, retries = 3) {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      console.log(`Downloading ${url} (attempt ${attempt}/${retries})...`)
      await new Promise((resolve, reject) => {
        const file = fs.createWriteStream(dest)

        const request = https.get(url, (response) => {
          // Handle redirects
          if (response.statusCode === 301 || response.statusCode === 302) {
            console.log(`Following redirect to: ${response.headers.location}`)
            https.get(response.headers.location, (redirectResponse) => {
              redirectResponse.pipe(file)
              file.on('finish', () => {
                file.close(resolve)
              })
            }).on('error', (err) => {
              fs.unlink(dest, () => {})
              reject(err)
            })
            return
          }

          if (response.statusCode !== 200) {
            fs.unlink(dest, () => {})
            reject(new Error(`HTTP ${response.statusCode}: ${response.statusMessage}`))
            return
          }

          response.pipe(file)
          file.on('finish', () => {
            file.close(resolve)
          })
        }).on('error', (err) => {
          fs.unlink(dest, () => {})
          reject(err)
        })

        // Timeout after 60 seconds
        request.setTimeout(60000, () => {
          request.abort()
          fs.unlink(dest, () => {})
          reject(new Error('Download timeout'))
        })
      })

      // Verify file exists and has content
      if (fs.existsSync(dest) && fs.statSync(dest).size > 0) {
        console.log(`✅ Downloaded successfully: ${path.basename(dest)}`)
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

async function setupPython(onProgress) {
  try {
    // Check if Python exists
    if (fs.existsSync(PYTHON_EXE)) {
      console.log('Python executable found, checking for missing packages...')

      // Required packages
      const requiredPackages = ['fastapi', 'clipboard', 'requests', 'pydantic', 'google-auth-oauthlib']
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
        if (onProgress) onProgress(`Installing ${missingPackages.length} missing packages...`, 50)

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
          'bcrypt'
        ]

        for (const pkg of allPackages) {
          try {
            console.log(`Installing ${pkg}...`)
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

    if (onProgress) onProgress('Installing dependencies...', 80)

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
      'bcrypt'
    ]

    const failedPackages = []
    for (const pkg of packages) {
      const pkgName = pkg.split('[')[0] // Handle uvicorn[standard]
      console.log(`Installing ${pkg}...`)

      try {
        await runCommand(PYTHON_EXE, ['-m', 'pip', 'install', '--no-cache-dir', pkg], PYTHON_DIR)

        // Verify it installed
        const verifyResult = await runCommand(PYTHON_EXE, ['-m', 'pip', 'show', pkgName], PYTHON_DIR)
        if (verifyResult.includes(`Name: ${pkgName}`)) {
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

module.exports = {
  init,
  setupPython,
  get PYTHON_EXE() { return PYTHON_EXE },
  get PYTHON_DIR() { return PYTHON_DIR }
}