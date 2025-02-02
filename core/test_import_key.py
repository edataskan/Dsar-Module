import gnupg

def test_import_private_key(private_key):
    gpg = gnupg.GPG()
    import_result = gpg.import_keys(private_key)
    print("Import result:", import_result.results)
    
    if not import_result.count:
        print("Error importing private key:", import_result.stderr)
        return False
    return True

# Replace 'your_private_key_here' with the actual private key you are trying to import.
private_key = """-----BEGIN PGP PRIVATE KEY BLOCK-----
Version: GnuPG v1

lIYEZrCu3xYJKwYBBAHaRw8BAQdAK54TFzEN67f8tqc4UXEVzBt3Qugm+0qw+Nrq
8wOSgJv+BwMC3mYOftrRZJ/Shnez97yITXdz3SXdSJi5P92RVphT3aoQhtDMN0S7
7b5+WxL25jnFAOeQOWIhpq9dg8aG9I+1DJZFsfgkovUBxAMI0YPBG7QbZHNhciA8
ZHNhcm1vZHVsZUBnbWFpbC5jb20+iJkEExYKAEEWIQTrdSjuy5zU7hFr4tVLwm67
bVL8TwUCZrCu3wIbAwUJBaOagAULCQgHAgIiAgYVCgkICwIEFgIDAQIeBwIXgAAK
CRBLwm67bVL8T30EAP93ISgRknUzfB25gci2YFtBnNLYhjoIv0yzFctxshcVdQD/
fvxl+8oVSt0okIqn7pAa3o9JXA2Q9cm6PUrM0I0V5AGciwRmsK7fEgorBgEEAZdV
AQUBAQdAV9/D1gk88mCEsesLxpXYFQnnm84e0Dn5TIgn9EkWhDsDAQgH/gcDAj1q
nvarO/Bv0iv8rzrTfzKQ+j6HKpMMtD83XKjEh62fWgAIkCblUM9ZUmC+oYRzXUal
1N71CyY6spIFk/IHX2qN9CzXFaqKweOrGjzvHRaIfgQYFgoAJhYhBOt1KO7LnNTu
EWvi1UvCbrttUvxPBQJmsK7fAhsMBQkFo5qAAAoJEEvCbrttUvxPRcMBAPo1ykB/
3zHneX2aFs9g+VjKlbTdZqpnUtQN0rIcbk0IAQDk4ft3nGPe2QWpqZr4LFsTnsTw
03UCfZv2g5M+BfNqAJSGBGawvjIWCSsGAQQB2kcPAQEHQMFwtJEDNR4YHV9R/mqn
/hveBhk4/nKJpy0fELGRWk10/gcDApMDU43c+hWN0r/hsRcjciMu7/p5ke318AQn
q8/pxLAhbLJsY8oVJzpgL7/xcwFUTxwDSVtaAxH9nOG5jZliv91VDEC0ciz2Jl9/
tBqL8iC0G2RzYXIgPGRzYXJtb2R1bGVAZ21haWwuY29tPoiZBBMWCgBBFiEE+Lw3
iAf7946191BxIBdXN77xno4FAmawvjICGwMFCQWjmoAFCwkIBwICIgIGFQoJCAsC
BBYCAwECHgcCF4AACgkQIBdXN77xno6MDgD/YjLSSO2wpzIEaHvRYxOtE3bmzUHO
OuO+aYu7sEhJ+TYBAO2FqbXhx99f38HVNEItEG3W0jq9b+9Nuk89Lop+GbYJnIsE
ZrC+MhIKKwYBBAGXVQEFAQEHQMjjEKISvYMsuk8axks+gyoml7ulyzeFOxlhwDIr
8fkKAwEIB/4HAwLAztfSS+tCQ9Kzq6ggw4WdWXexHvDPXqGmQ17/XEK3qgBh0V41
dsegxptb06jeQqOAQvRIYKHNl7PCXHgA+amRX7yIt7aH8pDjjkcsQLCIiH4EGBYK
ACYWIQT4vDeIB/v3jrX3UHEgF1c3vvGejgUCZrC+MgIbDAUJBaOagAAKCRAgF1c3
vvGejh2wAQDIrQJ8wyyo+MlhK78L/bQfF2765aeyH0R3ec2fAoNhDgD/QUfBsUs9
bVyGpLObqI+ZjQXBF/9sjf8fI1wY5bifKAY=
=7dpj
-----END PGP PRIVATE KEY BLOCK-----"""

if test_import_private_key(private_key):
    print("Private key imported successfully.")
else:
    print("Failed to import private key.")
