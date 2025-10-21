# 🔄 Demo Data Switching Guide for volLite

This guide explains how to switch between different demo data scenarios in your volLite application.

## 📊 Available Demo Scenarios

### 1. 🟢 Low Risk Demo (Default)
- **Risk Level**: Minimal (0-20)
- **Description**: Normal system behavior
- **Features**: 
  - Standard Windows processes
  - Normal network connections
  - No suspicious activity
  - Clean registry and files

### 2. 🟡 Medium Risk Demo
- **Risk Level**: Medium (40-60)
- **Description**: Some suspicious activity detected
- **Features**:
  - PowerShell execution
  - LOLBin usage (certutil.exe)
  - Suspicious network connections
  - Registry persistence attempts

### 3. 🔴 High Risk Demo
- **Risk Level**: High (60-80)
- **Description**: APT compromise simulation
- **Features**:
  - Encoded PowerShell commands
  - Multiple LOLBin abuse
  - C2 server connections
  - Advanced persistence mechanisms

## 🎯 Method 1: Quick Switch Script (Recommended)

Use the automated script to switch demo data:

```bash
python switch_demo_data.py
```

**Steps:**
1. Run the script
2. Choose your scenario (1-4)
3. Restart your Flask app
4. Test with "Use Demo Data" button

## 🎯 Method 2: Manual Modification

### Step 1: Locate Demo Data in app.py

Find these sections in your `app.py` file:
- `demo_processes = [...]` (around line 34)
- `demo_network = [...]` (around line 61)
- `demo_system_info = {...}` (around line 72)

### Step 2: Replace Demo Data

Replace the demo data with your chosen scenario:

#### Low Risk Example:
```python
demo_processes = [
    {
        'pid': 4,
        'name': 'System',
        'ppid': 0,
        'path': 'C:\\Windows\\System32\\ntoskrnl.exe',
        'cmdline': 'System',
        'signature_status': 'signed'
    },
    {
        'pid': 1000,
        'name': 'explorer.exe',
        'ppid': 4,
        'path': 'C:\\Windows\\explorer.exe',
        'cmdline': 'explorer.exe',
        'signature_status': 'signed'
    }
]

demo_network = [
    {
        'remote': '8.8.8.8:53',
        'protocol': 'UDP'
    },
    {
        'remote': 'google.com:443',
        'protocol': 'TCP'
    }
]

demo_system_info = {
    'registry': [],
    'files': []
}
```

#### High Risk Example:
```python
demo_processes = [
    {
        'pid': 4,
        'name': 'System',
        'ppid': 0,
        'path': 'C:\\Windows\\System32\\ntoskrnl.exe',
        'cmdline': 'System',
        'signature_status': 'signed'
    },
    {
        'pid': 1234,
        'name': 'powershell.exe',
        'ppid': 1000,
        'path': 'C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe',
        'cmdline': 'powershell.exe -enc UwB0AGEAcgB0AC0AUwBsAGUAZQBwACAAMQAwAA== -WindowStyle Hidden',
        'signature_status': 'unsigned'
    },
    {
        'pid': 2345,
        'name': 'rundll32.exe',
        'ppid': 1234,
        'path': 'C:\\Windows\\System32\\rundll32.exe',
        'cmdline': 'rundll32.exe javascript:"\\..\\mshtml,RunHTMLApplication"',
        'signature_status': 'signed'
    }
]

demo_network = [
    {
        'remote': '8.8.8.8:53',
        'protocol': 'UDP'
    },
    {
        'remote': '203.0.113.1:4444',
        'protocol': 'TCP'
    },
    {
        'remote': 'malicious-server.com:8080',
        'protocol': 'TCP'
    }
]

demo_system_info = {
    'registry': [
        {
            'key': 'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run',
            'value': 'suspicious.exe',
            'data': 'C:\\Users\\Public\\suspicious.exe'
        }
    ],
    'files': [
        {
            'path': 'C:\\Users\\Public\\suspicious.exe',
            'executable': True
        }
    ]
}
```

## 🎯 Method 3: Using Test Data Files

### Step 1: Use Existing Test Files

Your application has pre-built test data files:
- `test_memory_dumps/high_risk_memory_dump.json`
- `test_memory_dumps/medium_risk_memory_dump.json`

### Step 2: Upload Test Files

1. Go to your dashboard
2. Upload one of the test JSON files
3. The system will analyze it automatically
4. You'll see the corresponding risk level

### Step 3: Use Integration Script

Run the integration script to use high-risk data:

```bash
python integrate_high_risk_demo.py
```

## 🎯 Method 4: Custom Demo Data

### Step 1: Create Custom Data

Create a JSON file with your custom scenario:

```json
{
  "processes": [
    {
      "pid": 1234,
      "name": "custom_process.exe",
      "ppid": 1000,
      "path": "C:\\Custom\\custom_process.exe",
      "cmdline": "custom_process.exe --suspicious-flag",
      "signature_status": "unsigned"
    }
  ],
  "network_connections": [
    {
      "remote": "custom-server.com:9999",
      "protocol": "TCP"
    }
  ],
  "system_info": {
    "registry": [
      {
        "key": "HKEY_CURRENT_USER\\Software\\Custom",
        "value": "suspicious_value",
        "data": "suspicious_data"
      }
    ],
    "files": [
      {
        "path": "C:\\Custom\\suspicious_file.exe",
        "executable": true
      }
    ]
  }
}
```

### Step 2: Load Custom Data

Use the demo data switcher:

```python
from demo_data_switcher import DemoDataSwitcher

switcher = DemoDataSwitcher()
switcher.load_custom_scenario('path/to/your/custom_data.json')
```

## 🔧 Testing Your Changes

### Step 1: Restart Application
```bash
python app.py
```

### Step 2: Test Demo Mode
1. Go to your dashboard
2. Click "Use Demo Data" button
3. Check the risk score and alerts
4. Verify the process tree and findings

### Step 3: Check Performance
Visit `/api/performance/stats` to see:
- Analysis timing
- Cache statistics
- Optimization status

## 📈 Expected Results

| Scenario | Risk Score | Alerts | Key Indicators |
|----------|------------|--------|----------------|
| Low Risk | 0-20 | 0-1 | Normal processes only |
| Medium Risk | 40-60 | 2-3 | PowerShell, LOLBin usage |
| High Risk | 60-80 | 4-5 | Encoded commands, C2 connections |

## 🚨 Troubleshooting

### Issue: Demo data not changing
**Solution**: 
1. Restart Flask application
2. Clear browser cache
3. Check console for errors

### Issue: Risk score not updating
**Solution**:
1. Verify demo data format
2. Check RiskAnalyzer logs
3. Test with known working data

### Issue: Performance issues
**Solution**:
1. Check `/api/performance/stats`
2. Clear analysis cache
3. Reduce data size for testing

## 💡 Tips

1. **Always backup** your app.py before making changes
2. **Test incrementally** - start with low risk, then medium, then high
3. **Use the quick switch script** for easy testing
4. **Monitor performance** with the new performance endpoints
5. **Check logs** for any analysis errors

## 🎯 Quick Commands

```bash
# Switch to high risk scenario
python switch_demo_data.py

# Use high-risk test data
python integrate_high_risk_demo.py

# Check performance stats
curl http://localhost:5000/api/performance/stats

# Test with demo data
# Go to dashboard and click "Use Demo Data"
```

---

**Happy Testing! 🚀**

Your volLite application now supports multiple demo scenarios with optimized performance monitoring!
