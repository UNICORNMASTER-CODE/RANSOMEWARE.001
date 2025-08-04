import socket
import threading
import time
import random
import ipaddress
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

class StealthNetworkScanner:
    def __init__(self, target_range=None, max_threads=20, timing_profile='normal'):
        # Auto-detect local network if not specified
        if target_range is None:
            self.target_range = self.get_local_network()
        else:
            self.target_range = target_range
        self.max_threads = max_threads
        self.open_hosts = []
        self.timing_profile = timing_profile
        self.setup_logging()
        self.setup_timing()
    
    def get_local_network(self):
        """Auto-detect local network range"""
        try:
            # Get local IP by connecting to external address
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
            
            # Convert to /24 network
            ip_parts = local_ip.split('.')
            network = '.'.join(ip_parts[:3]) + '.0/24'
            return network
        except:
            return "192.168.1.0/24"  # fallback

    def setup_logging(self):
        """Setup minimal logging to avoid detection"""
        logging.basicConfig(
            level=logging.WARNING,  # Reduced logging
            format='%(asctime)s - %(message)s',
            handlers=[logging.FileHandler('scan.log')]
        )
        self.logger = logging.getLogger(__name__)
   
    def setup_timing(self):
        """Configure timing profiles for evasion"""
        timing_configs = {
            'paranoid': {'min_delay': 5.0, 'max_delay': 10.0, 'timeout': 3.0, 'batch_delay': 30.0},
            'sneaky': {'min_delay': 1.0, 'max_delay': 3.0, 'timeout': 2.0, 'batch_delay': 10.0},
            'normal': {'min_delay': 0.1, 'max_delay': 0.5, 'timeout': 1.0, 'batch_delay': 2.0},
            'aggressive': {'min_delay': 0.01, 'max_delay': 0.1, 'timeout': 0.5, 'batch_delay': 0.5}
        }
        self.timing = timing_configs.get(self.timing_profile, timing_configs['normal'])
   
    def generate_targets(self):
        """Generate and randomize target list"""
        try:
            network = ipaddress.ip_network(self.target_range, strict=False)
            targets = [str(ip) for ip in network.hosts()]
        except ValueError:
            targets = [self.target_range]
       
        # Randomize target order to avoid sequential patterns
        random.shuffle(targets)
        return targets
   
    def randomize_ports(self, ports):
        """Randomize port scanning order"""
        port_list = list(ports)
        random.shuffle(port_list)
        return port_list
   
    def adaptive_delay(self):
        """Generate random delays to avoid pattern detection"""
        return random.uniform(self.timing['min_delay'], self.timing['max_delay'])
   
    def decoy_connection(self, host, port):
        """Create decoy connections to mask real scans"""
        decoy_ports = [80, 443, 53, 8080, 8443]
        decoy_port = random.choice([p for p in decoy_ports if p != port])
       
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as decoy_sock:
                decoy_sock.settimeout(0.5)
                decoy_sock.connect_ex((host, decoy_port))
        except:
            pass  # Decoy connection, ignore failures
   
    def check_port_stealth(self, host, port):
        """Enhanced port checking with evasion techniques"""
        try:
            # Random delay before each connection
            time.sleep(self.adaptive_delay())
           
            # Occasionally create decoy connections
            if random.random() < 0.3:  # 30% chance
                threading.Thread(target=self.decoy_connection, args=(host, port), daemon=True).start()
           
            # Use random source port to avoid detection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
           
            # Bind to random high port to vary source
            try:
                random_port = random.randint(32768, 65535)
                sock.bind(('', random_port))
            except:
                pass  # If binding fails, use system-assigned port
           
            sock.settimeout(self.timing['timeout'])
           
            # Connect with timeout
            result = sock.connect_ex((host, port))
           
            if result == 0:
                # Brief connection to avoid suspicion
                banner = self.grab_banner_stealth(sock)
                sock.close()
                return True, banner
            else:
                sock.close()
                return False, None
               
        except Exception as e:
            return False, None
   
    def grab_banner_stealth(self, sock):
        """Lightweight banner grabbing"""
        try:
            sock.settimeout(1.0)
            # Send minimal HTTP request
            sock.send(b'GET / HTTP/1.0\r\n\r\n')
            banner = sock.recv(256).decode('utf-8', errors='ignore').strip()
            return banner[:50]  # Limit banner length
        except:
            return "Service detected"
   
    def scan_host_batch(self, host, ports=[22, 80, 135, 139, 443, 445, 3389]):
        """Scan host with batch optimization and evasion"""
        open_ports = []
       
        # Quick host availability check
        if not self.quick_host_check(host):
            return
       
        # Randomize port order
        randomized_ports = self.randomize_ports(ports)
       
        # Scan ports with adaptive timing
        for i, port in enumerate(randomized_ports):
            is_open, banner = self.check_port_stealth(host, port)
           
            if is_open:
                open_ports.append({
                    'port': port,
                    'service': self.get_service_name(port),
                    'banner': banner
                })
           
            # Add extra delay between ports on same host
            if i < len(randomized_ports) - 1:
                time.sleep(random.uniform(0.1, 0.3))
       
        if open_ports:
            host_info = {
                'host': host,
                'ports': open_ports,
                'scan_time': datetime.now().isoformat()
            }
            self.open_hosts.append(host_info)
            self.logger.warning(f"Host {host}: {len(open_ports)} open ports")
   
    def quick_host_check(self, host):
        """Fast host availability check using common ports"""
        common_ports = [80, 443, 22]
       
        for port in common_ports:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.5)
                    if s.connect_ex((host, port)) == 0:
                        return True
            except:
                continue
        return True  # Assume host is up if we can't determine quickly
   
    def get_service_name(self, port):
        """Map port numbers to service names"""
        services = {
            22: 'SSH', 80: 'HTTP', 135: 'RPC-Endpoint', 139: 'NetBIOS-SSN',
            443: 'HTTPS', 445: 'SMB', 3389: 'RDP', 21: 'FTP', 23: 'Telnet',
            25: 'SMTP', 53: 'DNS', 110: 'POP3', 143: 'IMAP', 993: 'IMAPS',
            995: 'POP3S', 8080: 'HTTP-Alt', 8443: 'HTTPS-Alt'
        }
        return services.get(port, f'Unknown-{port}')
   
    def scan_network_stealth(self):
        """Main scanning function with stealth and performance optimizations"""
        targets = self.generate_targets()
        self.logger.warning(f"Starting stealth scan of {len(targets)} targets")
       
        # Process targets in smaller batches to avoid overwhelming the network
        batch_size = min(50, len(targets))
        total_batches = (len(targets) + batch_size - 1) // batch_size
       
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(targets))
            batch_targets = targets[start_idx:end_idx]
           
            # Process batch with limited threading
            with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
                futures = [executor.submit(self.scan_host_batch, host) for host in batch_targets]
               
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        self.logger.error(f"Scan error: {e}")
           
            # Delay between batches to avoid detection
            if batch_num < total_batches - 1:
                batch_delay = random.uniform(
                    self.timing['batch_delay'] * 0.5,
                    self.timing['batch_delay'] * 1.5
                )
                time.sleep(batch_delay)
       
        self.logger.warning(f"Stealth scan complete: {len(self.open_hosts)} responsive hosts")
        return self.open_hosts
   
    def generate_summary_report(self):
        """Generate a concise summary report"""
        if not self.open_hosts:
            return "No open ports discovered."
       
        report = f"\n{'='*60}\n"
        report += f"STEALTH SCAN SUMMARY - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"{'='*60}\n"
        report += f"Hosts scanned: {len(self.generate_targets())}\n"
        report += f"Responsive hosts: {len(self.open_hosts)}\n"
        report += f"Timing profile: {self.timing_profile}\n\n"
       
        for host_info in self.open_hosts:
            report += f"Host: {host_info['host']}\n"
            report += f"{'─' * 40}\n"
           
            for port_info in host_info['ports']:
                service = port_info['service']
                port = port_info['port']
                banner = port_info.get('banner', 'No banner')[:30]
                report += f"  {port:>5}/tcp  {service:<12} {banner}\n"
            report += "\n"
       
        return report

class ScanConfiguration:
    """Simple configuration class for scan parameters"""
    def __init__(self):
        self.target_range = None  # Auto-detect local network
        self.timing_profile = 'sneaky'
        self.max_threads = 15
        self.custom_ports = [22, 80, 135, 139, 443, 445, 3389, 8080, 8443]

def main():
    """Main execution function with error handling"""
    print("Stealth Network Scanner - Educational Use Only")
    print("=" * 50)
   
    config = ScanConfiguration()
   
    scanner = StealthNetworkScanner(
        target_range=config.target_range,
        max_threads=config.max_threads,
        timing_profile=config.timing_profile
    )
   
    try:
        print(f"Starting {config.timing_profile} scan of {scanner.target_range}")
        print("Press Ctrl+C to stop scan safely\n")
       
        start_time = time.time()
        results = scanner.scan_network_stealth()
        end_time = time.time()
       
        print(scanner.generate_summary_report())
        print(f"Scan completed in {end_time - start_time:.2f} seconds")
       
        if results:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            with open(f"scan_results_{timestamp}.log", 'w') as f:
                f.write(scanner.generate_summary_report())
            print(f"Detailed results saved to scan_results_{timestamp}.log")
       
    except KeyboardInterrupt:
        print("\nScan interrupted by user")
    except Exception as e:
        print(f"Scan error: {e}")

if __name__ == "__main__":
    main()

