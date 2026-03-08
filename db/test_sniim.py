import requests

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.economia-sniim.gob.mx/SNIIM-Pecuarios-Nacionales/e_Hue.asp",
    "Cookie": "_ga=GA1.3.1595028401.1769446871; _ga_N4181LDPL7=GS2.3.s1772490517$o5$g0$t1772490517$j60$l0$h0; ASPSESSIONIDQAABRRTB=MGCGOMABLNMCPILNHEIPCMBI; ASPSESSIONIDSADAQQTA=CPNBAEOAKLGJCBCFBFHGACHF",
}

url = "https://www.economia-sniim.gob.mx/SNIIM-Pecuarios-Nacionales/e_Hue.asp"
params = {"prod":"0","destino":"100","sem":"1","mes":"03","anio":"2026","RegPag":"100"}

r = requests.get(url, params=params, headers=headers, timeout=15)
r.encoding = "latin-1"
print("Status:", r.status_code)
print("Primeros 2000 caracteres:")
print(r.text[:2000])
import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.economia-sniim.gob.mx/SNIIM-Pecuarios-Nacionales/e_Hue.asp",
    "Cookie": "_ga=GA1.3.1595028401.1769446871; _ga_N4181LDPL7=GS2.3.s1772490517$o5$g0$t1772490517$j60$l0$h0; ASPSESSIONIDQAABRRTB=MGCGOMABLNMCPILNHEIPCMBI; ASPSESSIONIDSADAQQTA=CPNBAEOAKLGJCBCFBFHGACHF",
}

url = "https://www.economia-sniim.gob.mx/SNIIM-Pecuarios-Nacionales/e_Hue.asp"
params = {"prod":"0","destino":"100","sem":"1","mes":"03","anio":"2026","RegPag":"100"}

r = requests.get(url, params=params, headers=headers, timeout=15)
r.encoding = "latin-1"
soup = BeautifulSoup(r.text, "html.parser")

for tr in soup.find_all("tr"):
    celdas = tr.find_all("td", class_="Datos")
    if len(celdas) >= 5:
        print([c.get_text(strip=True) for c in celdas])
        