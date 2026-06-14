import os, re, subprocess
HERE=os.path.dirname(os.path.abspath(__file__))
CHROME=r"C:\Program Files\Google\Chrome\Application\chrome.exe"
t=open(os.path.join(HERE,"2026-06-12-bronte-chimborazo-routemap.html"),encoding="utf-8").read()
def grab(h):
    m=re.search(r'<svg viewBox="0 0 1600 '+str(h)+r'".*?</svg>', t, re.S)
    return m.group(0)
for name,h in (("panelB",720),("panelC",790)):
    svg=grab(h)
    html=f'<!doctype html><meta charset=utf-8><style>html,body{{margin:0;background:#fff}}svg{{width:1600px;height:auto;display:block}}</style>{svg}'
    hp=os.path.join(HERE,f"_{name}.html"); open(hp,"w",encoding="utf-8").write(html)
    png=os.path.join(HERE,f"_{name}.png")
    subprocess.run([CHROME,"--headless=new","--disable-gpu","--hide-scrollbars",
        f"--screenshot={png}",f"--window-size=1600,{h}","file:///"+hp.replace(os.sep,'/')],
        check=True,capture_output=True)
    print("rendered",png)
