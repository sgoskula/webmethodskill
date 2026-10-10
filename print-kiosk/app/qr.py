"""Generate the poster QR: python -m app.qr https://print.example.com/?k=lobby-1 kiosk-qr.png"""
import sys
import qrcode

if __name__ == "__main__":
    qrcode.make(sys.argv[1]).save(sys.argv[2])
    print("saved", sys.argv[2])
