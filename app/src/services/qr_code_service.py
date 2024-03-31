import qrcode
from io import BytesIO


def generate_qr_code(url: str):
    """
    generate_qr_code
    Generates QR Code for provided url
    Args:
        url (str): url to be added as qr code data

    Returns:
        IO[bytes]: An in-memory bytes buffer containing the QR code image in PNG format.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img_io = BytesIO()
    img.save(img_io, format="PNG")
    img_io.seek(0)

    return img_io
