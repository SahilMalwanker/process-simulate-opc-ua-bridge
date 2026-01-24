"""
Certificate Generator for the OPC UA server (server/ folder)
Generates open62541-compatible certificates for new machines

Usage:
    python generate_cert.py <hostname> <ip_address>

Example:
    python generate_cert.py myserver 192.168.1.100
"""
import sys
from pathlib import Path
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from datetime import datetime, timedelta
import ipaddress


def generate_certificate(hostname, ip_address, output_dir="."):
    """Generate OPC UA server certificate matching open62541 format"""
    
    output_dir = Path(output_dir)
    
    # Generate private key (2048-bit RSA)
    print(f"Generating 2048-bit RSA key pair...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    # Certificate subject/issuer
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "DE"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "open62541"),
        x509.NameAttribute(NameOID.COMMON_NAME, "open62541 PS Server"),
    ])
    
    # Application URI
    app_uri = f"urn:{hostname}:open62541:ps"
    
    # Subject Alternative Names (critical for OPC UA)
    san = [
        x509.UniformResourceIdentifier(app_uri),
        x509.DNSName(hostname),
        x509.IPAddress(ipaddress.ip_address(ip_address)),
    ]
    
    # Build certificate
    print(f"Creating certificate...")
    print(f"  Application URI: {app_uri}")
    print(f"  DNS Name: {hostname}")
    print(f"  IP Address: {ip_address}")
    
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=3650))  # 10 years
        .add_extension(
            x509.SubjectAlternativeName(san),
            critical=False,
        )
        .add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=True,
                content_commitment=True,
                data_encipherment=True,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(
            x509.ExtendedKeyUsage([
                ExtendedKeyUsageOID.CLIENT_AUTH,
                ExtendedKeyUsageOID.SERVER_AUTH,
            ]),
            critical=True,
        )
        .sign(private_key, hashes.SHA256(), default_backend())
    )
    
    # Save certificate (DER format)
    cert_path = output_dir / "open62541_server_cert.der"
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.DER))
    print(f"\n✓ Certificate saved: {cert_path}")
    
    # Save private key (PEM format)
    key_path = output_dir / "open62541_server_key.pem"
    key_path.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    print(f"✓ Private key saved: {key_path}")
    
    return cert_path, key_path


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        print("\nError: Missing arguments")
        print(f"Usage: python {sys.argv[0]} <hostname> <ip_address>")
        sys.exit(1)
    
    hostname = sys.argv[1]
    ip_address = sys.argv[2]
    
    # Validate IP address
    try:
        ipaddress.ip_address(ip_address)
    except ValueError:
        print(f"Error: Invalid IP address: {ip_address}")
        sys.exit(1)
    
    print("=" * 60)
    print("OPC UA Certificate Generator for the PS server")
    print("=" * 60)
    print()
    
    try:
        generate_certificate(hostname, ip_address)
        print()
        print("=" * 60)
        print("Certificate generated successfully!")
        print()
        print("Next steps:")
        print(f"1. Update ps_server.json5:")
        print(f"   - Change applicationUri to: urn:{hostname}:open62541:ps")
        print(f"   - Change serverUrls to: opc.tcp://{ip_address}:4841")
        print(f"   - Change discoveryUrls to: opc.tcp://{ip_address}:4841")
        print("2. Copy these files to the server folder:")
        print("   - open62541_server_cert.der")
        print("   - open62541_server_key.pem")
        print("3. Run: .\\server_json_config.exe ps_server.json5")
        print("=" * 60)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
