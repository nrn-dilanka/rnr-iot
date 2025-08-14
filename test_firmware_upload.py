import paho.mqtt.client as mqtt
import json
import time

def test_firmware_upload():
    """Test firmware upload functionality"""
    print("🧪 Testing Firmware Upload")
    print("=" * 40)
    
    try:
        import requests
        
        # Test GET firmware endpoint
        print("1. Testing GET /api/firmware endpoint...")
        response = requests.get("http://192.168.8.105:8000/api/firmware")
        if response.status_code == 200:
            print(f"✅ GET firmware endpoint works: {len(response.json())} firmware versions found")
            for fw in response.json():
                print(f"   - Version {fw['version']}: {fw['file_name']}")
        else:
            print(f"❌ GET firmware endpoint failed: {response.status_code}")
            return
        
        # Test file upload with a small test file
        print("\n2. Testing POST /api/firmware/upload endpoint...")
        
        # Create a small test firmware file
        test_content = b"FIRMWARE_TEST_DATA" + b"\x00" * 1000  # 1KB test file
        
        files = {
            'file': ('test_firmware_v2.0.0.bin', test_content, 'application/octet-stream')
        }
        data = {
            'version': '2.0.0'
        }
        
        upload_response = requests.post(
            "http://192.168.8.105:8000/api/firmware/upload",
            files=files,
            data=data
        )
        
        if upload_response.status_code == 201:
            print("✅ Firmware upload successful!")
            print(f"   Response: {upload_response.json()}")
        else:
            print(f"❌ Firmware upload failed: {upload_response.status_code}")
            print(f"   Error: {upload_response.text}")
        
    except ImportError:
        print("❌ requests library not available")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_firmware_upload()
