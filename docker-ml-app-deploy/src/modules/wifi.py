""" ProtonNG Wifi Commands
"""
import re
import logging
import time
from fastapi import HTTPException
from modules import common as cm

# Configure logging
logger = logging.getLogger(__name__)

def proton_wifi_connect(ssid, password):
    """
    Connect to a WiFi network using multiple methods.
    Works from Docker containers with fallback methods.
    """
    try:
        # Method 1: Try nmcli (NetworkManager approach)
        try:
            logger.info(f"Attempting to connect to {ssid} using nmcli")
            
            # Delete existing connection with the same SSID if it exists
            delete_cmd = f"nmcli connection delete '{ssid}' 2>/dev/null || true"
            cm.run_command(delete_cmd)
            
            # Scan first to make sure the network is available
            scan_cmd = f"nmcli device wifi rescan"
            cm.run_command(scan_cmd)
            
            # Wait a moment for scan to complete
            time.sleep(2)
            
            # Connect to the network
            if password and password.strip():
                connect_cmd = f"nmcli device wifi connect '{ssid}' password '{password}'"
            else:
                connect_cmd = f"nmcli device wifi connect '{ssid}'"
                
            cm.run_command(connect_cmd)
            
            # Verify connection
            verify_cmd = f"nmcli connection show --active | grep '{ssid}'"
            cm.run_command(verify_cmd)
            
            logger.info(f"Successfully connected to {ssid} using nmcli")
            return {"status": "success", "message": f"Connected to {ssid} using nmcli", "method": "nmcli"}
            
        except Exception as nmcli_error:
            logger.warning(f"nmcli connection failed: {str(nmcli_error)}")
        
        # Method 2: Try wpa_supplicant approach
        try:
            logger.info(f"Attempting to connect to {ssid} using wpa_supplicant")
            
            # Get wireless interface
            interfaces_cmd = "iw dev | grep Interface | awk '{print $2}' | head -1"
            interface = cm.run_command(interfaces_cmd).strip()
            
            if not interface:
                raise Exception("No wireless interface found")
            
            # Kill existing wpa_supplicant processes
            kill_cmd = "pkill wpa_supplicant || true"
            cm.run_command(kill_cmd)
            
            # Create temporary wpa_supplicant config
            if password and password.strip():
                wpa_config = f"""
network={{
    ssid="{ssid}"
    psk="{password}"
    key_mgmt=WPA-PSK
}}
"""
            else:
                wpa_config = f"""
network={{
    ssid="{ssid}"
    key_mgmt=NONE
}}
"""
            
            # Write config to temporary file
            config_file = "/tmp/wpa_supplicant_temp.conf"
            with open(config_file, 'w') as f:
                f.write(wpa_config)
            
            # Start wpa_supplicant
            wpa_cmd = f"wpa_supplicant -B -i {interface} -c {config_file}"
            cm.run_command(wpa_cmd)
            
            # Wait for connection
            time.sleep(5)
            
            # Get IP address via DHCP
            dhcp_cmd = f"dhclient {interface}"
            cm.run_command(dhcp_cmd)
            
            # Verify connection by checking if we got an IP
            ip_cmd = f"ip addr show {interface} | grep 'inet ' | awk '{{print $2}}'"
            ip_result = cm.run_command(ip_cmd).strip()
            
            if ip_result:
                logger.info(f"Successfully connected to {ssid} using wpa_supplicant")
                return {"status": "success", "message": f"Connected to {ssid} using wpa_supplicant", "method": "wpa_supplicant", "ip": ip_result}
            else:
                raise Exception("No IP address obtained")
                
        except Exception as wpa_error:
            logger.warning(f"wpa_supplicant connection failed: {str(wpa_error)}")
        
        # Method 3: Try iwconfig approach (for older systems or open networks)
        try:
            if not password or not password.strip():  # Only for open networks
                logger.info(f"Attempting to connect to open network {ssid} using iwconfig")
                
                # Get wireless interface
                interfaces_cmd = "cat /proc/net/wireless | tail -n +3 | cut -d: -f1 | tr -d ' ' | head -1"
                interface = cm.run_command(interfaces_cmd).strip()
                
                if not interface:
                    raise Exception("No wireless interface found")
                
                # Set interface up
                up_cmd = f"ip link set {interface} up"
                cm.run_command(up_cmd)
                
                # Connect to ESSID
                essid_cmd = f"iwconfig {interface} essid '{ssid}'"
                cm.run_command(essid_cmd)
                
                # Wait a moment
                time.sleep(3)
                
                # Get IP via DHCP
                dhcp_cmd = f"dhclient {interface}"
                cm.run_command(dhcp_cmd)
                
                # Verify connection
                ip_cmd = f"ip addr show {interface} | grep 'inet ' | awk '{{print $2}}'"
                ip_result = cm.run_command(ip_cmd).strip()
                
                if ip_result:
                    logger.info(f"Successfully connected to {ssid} using iwconfig")
                    return {"status": "success", "message": f"Connected to {ssid} using iwconfig", "method": "iwconfig", "ip": ip_result}
                else:
                    raise Exception("No IP address obtained")
                    
        except Exception as iwconfig_error:
            logger.warning(f"iwconfig connection failed: {str(iwconfig_error)}")
        
        # If all methods failed
        return {
            "status": "error", 
            "message": f"Failed to connect to {ssid}. All connection methods failed. Make sure the container has proper network privileges and the network credentials are correct."
        }
        
    except HTTPException as e:
        return {"status": "error", "message": str(e.detail)}
    except Exception as e:
        return {"status": "error", "message": f"WiFi connection failed: {str(e)}"}

def proton_wifi_status():
    try:
        # Try nmcli first
        try:
            connections_cmd = "nmcli -t -f NAME,TYPE,DEVICE connection show --active"
            connections_output = cm.run_command(connections_cmd)
            
            for line in connections_output.split('\n'):
                if line.strip():
                    parts = line.split(':')
                    if len(parts) >= 3 and ('wifi' in parts[1].lower() or '802-11-wireless' in parts[1].lower()):
                        ssid = parts[0]
                        device = parts[2]
                        
                        ip_cmd = f"nmcli -t -f IP4.ADDRESS connection show '{ssid}'"
                        try:
                            ip_output = cm.run_command(ip_cmd)
                            ip_address = None
                            for ip_line in ip_output.split('\n'):
                                if ip_line.strip() and 'IP4.ADDRESS' in ip_line:
                                    ip_parts = ip_line.split(':')
                                    if len(ip_parts) > 1:
                                        ip_address = ip_parts[1].strip().split('/')[0]
                                        break
                        except:
                            ip_address = None
                        
                        return {
                            'connected': True,
                            'ssid': ssid,
                            'ip_address': ip_address
                        }
        except:
            # Fallback to basic network info if nmcli fails
            pass
        
        # Fallback: Try to get basic network info
        try:
            # Get IP address from hostname
            ip_cmd = "hostname -I | awk '{print $1}'"
            ip_address = cm.run_command(ip_cmd).strip()
            
            # Try to get SSID from iwconfig (if available)
            ssid = "Unknown"
            try:
                iwconfig_cmd = "iwgetid -r"
                ssid = cm.run_command(iwconfig_cmd).strip() or "Unknown"
            except:
                pass
                
            return {
                'connected': bool(ip_address),
                'ssid': ssid,
                'ip_address': ip_address if ip_address else None
            }
        except Exception as e:
            return {
                'connected': False,
                'ssid': None,
                'ip_address': None,
                'message': f"Fallback method failed: {str(e)}"
            }
            
    except HTTPException as e:
        return {"status": "error", "message": str(e.detail)}
    except Exception as e:
        return {"status": "error", "message": f"WiFi status check failed: {str(e)}"}

def proton_wifi_scan():
    """
    Scan for available WiFi networks.
    Works from Docker containers by trying multiple methods including host network access.
    """
    try:
        networks = []
        
        # Method 1: Try nmcli (works if container has access to host network)
        try:
            scan_cmd = "nmcli -t -f SSID,SIGNAL,SECURITY device wifi list"
            scan_output = cm.run_command(scan_cmd)
            
            for line in scan_output.split('\n'):
                if line.strip():
                    parts = line.split(':')
                    if len(parts) >= 3:
                        ssid = parts[0].strip()
                        signal = parts[1].strip()
                        security = parts[2].strip()
                        
                        # Filter out empty SSIDs and duplicates
                        if ssid and not any(net['ssid'] == ssid for net in networks):
                            networks.append({
                                'ssid': ssid,
                                'signal': signal,
                                'security': security,
                                'method': 'nmcli'
                            })
            
            if networks:
                return {"status": "success", "networks": networks, "method": "nmcli"}
                
        except Exception as nmcli_error:
            logger.warning(f"nmcli method failed: {str(nmcli_error)}")
        
        # Method 2: Try iwlist scan (alternative WiFi scanning tool)
        try:
            # First get wireless interfaces
            interfaces_cmd = "cat /proc/net/wireless | tail -n +3 | cut -d: -f1 | tr -d ' '"
            interfaces_output = cm.run_command(interfaces_cmd)
            
            for interface in interfaces_output.split('\n'):
                if interface.strip():
                    interface = interface.strip()
                    try:
                        # Scan with iwlist
                        scan_cmd = f"iwlist {interface} scan"
                        scan_output = cm.run_command(scan_cmd)
                        
                        # Parse iwlist output
                        current_network = {}
                        for line in scan_output.split('\n'):
                            line = line.strip()
                            
                            if 'ESSID:' in line:
                                ssid_match = re.search(r'ESSID:"([^"]*)"', line)
                                if ssid_match and ssid_match.group(1):
                                    current_network['ssid'] = ssid_match.group(1)
                            
                            elif 'Signal level=' in line:
                                signal_match = re.search(r'Signal level=(-?\d+)', line)
                                if signal_match:
                                    current_network['signal'] = signal_match.group(1)
                            
                            elif 'Encryption key:' in line:
                                if 'on' in line.lower():
                                    current_network['security'] = 'WPA/WEP'
                                else:
                                    current_network['security'] = 'Open'
                            
                            elif line.startswith('Cell') and current_network.get('ssid'):
                                # Save previous network and start new one
                                if not any(net['ssid'] == current_network['ssid'] for net in networks):
                                    networks.append({
                                        'ssid': current_network['ssid'],
                                        'signal': current_network.get('signal', 'Unknown'),
                                        'security': current_network.get('security', 'Unknown'),
                                        'method': 'iwlist'
                                    })
                                current_network = {}
                        
                        # Add last network if exists
                        if current_network.get('ssid') and not any(net['ssid'] == current_network['ssid'] for net in networks):
                            networks.append({
                                'ssid': current_network['ssid'],
                                'signal': current_network.get('signal', 'Unknown'),
                                'security': current_network.get('security', 'Unknown'),
                                'method': 'iwlist'
                            })
                            
                    except Exception as iface_error:
                        logger.warning(f"iwlist scan failed for interface {interface}: {str(iface_error)}")
                        continue
            
            if networks:
                return {"status": "success", "networks": networks, "method": "iwlist"}
                
        except Exception as iwlist_error:
            logger.warning(f"iwlist method failed: {str(iwlist_error)}")
        
        # Method 3: Try iw scan (modern WiFi scanning tool)
        try:
            # Get wireless interfaces using iw
            interfaces_cmd = "iw dev | grep Interface | awk '{print $2}'"
            interfaces_output = cm.run_command(interfaces_cmd)
            
            for interface in interfaces_output.split('\n'):
                if interface.strip():
                    interface = interface.strip()
                    try:
                        scan_cmd = f"iw {interface} scan | grep -E 'SSID|signal|capability'"
                        scan_output = cm.run_command(scan_cmd)
                        
                        lines = scan_output.split('\n')
                        current_network = {}
                        
                        for line in lines:
                            line = line.strip()
                            
                            if 'SSID:' in line:
                                ssid = line.split('SSID:')[1].strip()
                                if ssid and ssid != '--':
                                    current_network['ssid'] = ssid
                            
                            elif 'signal:' in line:
                                signal_match = re.search(r'signal:\s*(-?\d+\.?\d*)', line)
                                if signal_match:
                                    current_network['signal'] = signal_match.group(1)
                            
                            elif 'capability:' in line:
                                if 'Privacy' in line:
                                    current_network['security'] = 'WPA/WEP'
                                else:
                                    current_network['security'] = 'Open'
                                
                                # End of network entry, save it
                                if current_network.get('ssid') and not any(net['ssid'] == current_network['ssid'] for net in networks):
                                    networks.append({
                                        'ssid': current_network['ssid'],
                                        'signal': current_network.get('signal', 'Unknown'),
                                        'security': current_network.get('security', 'Unknown'),
                                        'method': 'iw'
                                    })
                                current_network = {}
                                
                    except Exception as iface_error:
                        logger.warning(f"iw scan failed for interface {interface}: {str(iface_error)}")
                        continue
            
            if networks:
                return {"status": "success", "networks": networks, "method": "iw"}
                
        except Exception as iw_error:
            logger.warning(f"iw method failed: {str(iw_error)}")
        
        # If no networks found, return empty list with warning
        if not networks:
            return {
                "status": "warning", 
                "networks": [], 
                "message": "No WiFi networks found. This might be due to Docker container limitations or missing wireless interfaces."
            }
        
        return {"status": "success", "networks": networks}
        
    except HTTPException as e:
        return {"status": "error", "message": str(e.detail)}
    except Exception as e:
        return {"status": "error", "message": f"WiFi scan failed: {str(e)}"}