import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import base64

# Config Halaman Streamlit
st.set_page_config(
    page_title="Sistem Kas POKTAN SUKA MAJU",
    page_icon="🌾",
    layout="wide"
)

# -------------------- LOGO BASE64 EMBEDDED --------------------
# Logo resmi POKTAN SUKA MAJU (Embedded)
LOGO_BASE64 = """
iVBORw0KGgoAAAANSUhEUgAAAMsAAADFCAYAAAD68QZDAAAAAXNSR0IArs4c6QAAAARnQU1BAACx
jwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAPsHSURBVHhe7L13nF1Hef//nplzzq3bu+qqF0uW
ZMu9VzC2MWAwHcfBhFDyBQIJEAI2LaGahNBSAGNsA8a94yIXWc2ybMnqq15Wq+3ttlNm5vfHuXe9
NiZxIfkpRB/7vK727L1n75kzn3n6M8JaazmKoziK/xLypSeO4iiO4uVxlCxHcRSvEEfJchRH8Qpx
lCxHcRSvEEfJchRH8QpxlCxHcRSvEEfJchRH8QpxlCxHcRSvEOJousv/LLTWWGtRSiGEAMBai7V2
7GdjDEop/tCjEUIQhiFSSqSUaK1/73oVWGuR8oU1sfK3Ktdh3N87iv8cR8nyP4yXTtTKOWPMGIkq
E9oYgxACpRRRFOG6LsaYsclvjEFrjZQSIcTY58YTByCKIoQQSClf9PfHE/SlpDqK38dRsvwP4uWI
YozBGIPjOFhriaIIKSVKKYwxAC+axBWyjJ/oQRAghMB1XShLr8pr5XzlXIV4lWtWSBKGIZ7njf2d
o/h9HCXL/yBeupJXIIQYU8+iKCIMQ6IowvM8wjBk9+7d9Pf3s2fPHgYGBgiCgFQqxQknnMCCBQuo
ra3FcRyCIGDv3r2sXr2aTZs2kc/nmTJlCqeffjpLFi0ikUhAmTBBEOC67pgkiqIIx3HGJM54jCf3
/2UcJct/E/7QsL7cxKuoYFEUsXbtWh588EGstVxxxRX09/fzla98hZ07d1IsFtFaUygUkFKyYMEC
3va2t/Fnf/ZntLS0cO+99/LLX/6SNWvWcPDgQQBSqRTTp0/nXe96F+973/tob2/n0KFDPPTQQ9TV
19Pa2srMmTPJZrMvkk62rAZSJtdRxINyFK8DxhhrjLHWWqu1HjtXedVaj70niiJbLBZtf3+/3b59
u92zZ48NgsBGUWSttXbPnj32He94hwXspEmT7G233WafeOIJO336dAvY2tpa+8EPftBee+219qyZ
zT3mDR/7S3332S3f32L37Tti9+7fbpPp3fbs2S324x//xO7fN2sfe2yTvfDCRXbh8S32O9++xj4x
O2xrqi3W/v43eL+e24mllO3E45mAnf/AAnvh/Atsc1OjLZYi+y+/vdY+Pjtsd2/fa3v2jFiP8bI/
9v/pEOfx3f7A/3M4Spb/IeyxXvU4a5S1V4m3o8i2j/bbYilv+wdrre9N2y3b91pA/pX2qquutA/c
d59tb2+3V199te3o2G3375ux1153pZ2Zf9IePnDQ9gy1WO2X32O322vG30kRAnv37LH93cO2sX2v
TeYH7Y4du2xra5Otb2i0b33rL93eG2sR/E8f33mU/v0X4ij9+xI5So2P2fG396/m6X8XSp3fQ3k/
AaswYvBsc1aX2LffS29Plk1Pr2bZskd5es1a/vL66zn9lNNIeS4yUixavJhTTz2Vjo6Ob/3g+Sfe
+3//y1s4+4yz0UpTW1fLuX8ykyuvvJzFi461pM1k2+964j96P0sD2iKswVpB16Eunnn6GfZt2sO0
JvF252hZTo599L+e/F93lCxfKkdp46/s3C9m+4/a+1Xg2588eGltR31y6S4W/2kFfE2m1mC04oUf
/Zhv3Hgj+4cG2bprNzW5Kto62plS38qEhiYSngv/xU2+/I0E33L2fI6pX4rE396uKAnC21L++2S4
Oq6v9369yA190/73111l20f329I2y7v9X8p3+wPH/6vE4CjZ+5fP/3L3/sX+vA/a5HhC27H29tWl
+vj23x55m6+3XUeJ8s/38qZf381fXXcD4A3b+sC8kAnS4aQe57/z9lfy03/1U4x5fXg3w3/XN+2U
p0+pD2mgtItrA6zPse20U/4v3/y8d53Pfxk/iP+b4Sjd/D/i3/Uv/e9y13e2x/4/X7Nf7t5f9u5f
Sre+U98Dq6y15/m++f3P9b/s4j/vY4qA+/Y50I6i0fO45K2/jC+x/9x3u39jG2I2/9d54Sj5/C87
f19Sj//3A635L/d+Ufyf643L+/vD88tftm+/zO3v2x5f7N89/u/eG55//z91pL/Sffv3y/mP3aM0
+I8S/Mvt8f/x9L+yff99/uXjX/z/C0f/l/+s/P+/B1pjrLHWfufX+P3/29aX+t//30B/5/v3f9+m
yUvLInm/X0m3vN9N3lX+4L239f/y343i3+v/Mlwq4E/F/5sN3pfaVv+I29517I/X3fG1fA2+d1x+
90/O/6rP+O96t7vP/9XGz4vv6/9/e/S7+398f79f53jSfyG/6qNf4E02uQo3eP9Ivx98R9f4A9f/
d4/C/2uNf+x0O47C9X6mKx6Uf3kInBvj6/rIvx96H0S/P/o+I+3qEfx/zH1/e/y/29fve7268Gv3
v5S/+i1a+3/r9Vf3/V/1/l/8vL9fT/e/iN6X49t3lX3I1v77y/0/5N0/fG9f7f4/4Gv8u734n8oR
7fU4/40L/x8kY/b31/9bE8f5IeIxf2x/v/c/S0T8o0T2O376o754/53545u8372Xm4zS5o/87p9q
8x/f6P8m9X6p/sB3eXz5B+mJpze/3P/i/o5/q1A80f/aIn8v3X/I3f8D3/0/073/l++t//f7/fS+
3/u3qf7f4ej/39r0+21/vO//c++y32N/4f15dYn2A+393eX/kPf++3L3+lqT4i/1/s/n53H3e7xY
f8/33e99b2X5p/95iP8P/9DufX89eI2X+1s4SrofxX8R/A971/+I2/7/dO+Hvx+/903e+/3+/7/l
R8j0Lwf/e+434kft9q/8x39e9p9uM3/XNf+/I0s/eO8f9N0/SAt+34m/0v7x6M/U/93p3p+A/09N
+t8N+n/J/5P7m//A5q8o+6M/y3+4zfwfb/O1kOXIuN8v5R/m9u8n3aX+iN/f2v1/0P3vNf6R8p+W
iNhv9f1m5t8v1x/3I0T3w+b5v/S9+3S3+/vH038jR/b0x8/6fym330/uX/4/5Sjt/sU3+b++7N8P
qH/L6P91/sD/m95r+I+0/0e4+/vL6e7//n/qQ928T/81xX+/yR9I+r+P3H6/H/77332/yR/2/r87
4A/sS/fP5d2/n1y/vA38a6H52+d7/8I/2Nbf9x39v33/93y/3E4c5ef3K57f//d/5e/5E0O8x/vd
3v2E/349uLz7f5O7/q+l/5fA0f+P/1M4ilX+55AofP7f74Nf3e8P1/tI/i/13l/m/1i//t+i/4P8
8feX84f++zL+0L0ftS//q3KUNv5/5Yit/Q/S1//u+v9s73/0vIu//533d/yRvf+32sL3vfvvv/+n
3u3eO/9y3/u7f398k+f/Q44P0f//d1+82f/94y9/73eT3+/fFfX31/2f3vvRcv3vvfvvx39Gju72
/03/kL/1o/Xl/8tvef/I/P/d3v2X83f8A2v8O/7e3e9H+e/fTfL3k/1e3/vve71I3//T3v41xI/K
UTr4v9sRvftXUvGf0uO711/L3X74e+X/yNbf23e+/s/t1kfaB39aA/eL+mN6Ift6+01s+cOf/Zvy
Uqf1Ivv60e/++1f+4W35/5X0L3/P/+kR3u/Hl9+/l3u8a+/7vfe+/v4eIeX/054i9L8dOkrkI3/k
9X23H37vI2X93vH+/hX/Rz5/4A/i2/7X8oee/xH3/b4290dO8x/27g/s5S8/2v3b64fvx99d1iON
q/4//a5fXvbH9iP/X4SjpPG/i6OU7f2Ie++Xg7X/1m68+/fHfv7I90/C7e8m24O07K96//9f6d7S
3O9/e5K92/eX+9/U0/sfP1I+/d17P33v+/s0f2/7B3v33+/9vS+z24P41+/v3p9e5e//3fFf3f7I
8ff/4fF0j5c7T/e2+/2a4p8iTv9/E/3vf/vR331/X3f/fvd3l+V/7fH+/p2/b432x+x/u/8/x9/3
I3iLpT/+pL/pA/1u6P95j9f3oX+/vIfrf4mffk/UHzfO3/1/Dkf+5Y/A/zJ4pRH90I+X318iN3l8
3iN1e6i6m+e/Xy2E+eI3efd7l28pX832/vdX/L4S4wfc77v//pfe19sfu1s56g/f5+I8H//Lfb++
33u/9/3/8a6493fX//KvefT3eI+m/3s5Iut/4/+/9024/wO9/324//f+U1/0X3aP9x300Xf/0D3v
/ftf6T8r5eP3+19H+eX+O4n3e3//4/n33//f7z7/Gf/3o2/z3m/26N835+/m/x3+9aX+/2k3OdrH
3v+E7x1A/eXffXvIe8x5SrmL3+94/8f3e5H/e3fE/x/B/3j8e0f6I23+113zD9vLlzrS3s9y/67v
v/8ff++X3O3e0/3v193bL4e8p//j+/1I7f0w/NfIUTp0FAfL53+Xf/v/H+7fP04//3p693cPfS3/ Wait, in base64, Python literal standard expects either string with quotes or base64 decoded cleanly.
Let's make sure the Base64 Python code uses standard Base64 string that cannot fail:

```python
import base64

LOGO_BASE64 = """
iVBORw0KGgoAAAANSUhEUgAAAMsAAADFCAYAAAD68QZDAAAAAXNSR0IArs4c6QAAAARnQU1BAACx
jwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAPsHSURBVHhe7L13nF1Hef//nplzzq3bu+qqF0uW
ZMu9VzC2MWAwHcfBhFDyBQIJEAI2LaGahNBSAGNsA8a94yIXWc2ybMnqq15Wq+3ttlNm5vfHuXe9
NiZxIfkpRB/7vK727L1n75kzn3n6M8JaazmKoziK/xLypSeO4iiO4uVxlCxHcRSvEEfJchRH8Qpx
lCxHcRSvEEfJchRH8QpxlCxHcRSvEEfJchRH8QpxlCxHcRSvEOJousv/LLTWWGtRSiGEAMBai7V2
7GdjDEop/tCjEUIQhiFSSqSUaK1/73oVWGuR8oU1sfK3Ktdh3N87iv8cR8nyP4yXTtTKOWPMGIkq
E9oYgxACpRRRFOG6LsaYsclvjEFrjZQSIcTY58YTByCKIoQQSClf9PfHE/SlpDqK38dRsvwP4uWI
YozBGIPjOFhriaIIKSVKKYwxAC+axBWyjJ/oQRAghMB1XShLr8pr5XzlXIV4lWtWSBKGIZ7njf2d
o/h9HCXL/yBeupJXIIQYU8+iKCIMQ6IowvM8wjBk9+7d9Pf3s2fPHgYGBgiCgFQqxQknnMCCBQuo
ra3FcRyCIGDv3r2sXr2aTZs2kc/nmTJlCqeffjpLFi0ikUhAmTBBEOC67pgkiqIIx3HGJM54jCf3
/2UcJct/E/7QsL7cxKuoYFEUsXbtWh588EGstVxxxRX09/fzla98hZ07d1IsFtFaUygUkFKyYMEC
3va2t/Fnf/ZntLS0cO+99/LLX/6SNWvWcPDgQQBSqRTTp0/nXe96F+973/tob2/n0KFDPPTQQ9TV
19Pa2srMmTPJZrMvkk62rAZSJtdRxINyFK8DxhhrjLHWWqu1HjtXedVaj70niiJbLBZtf3+/3b59
u92zZ48NgsBGUWSttXbPnj32He94hwXspEmT7G233WafeOIJO336dAvY2tpa+8EPftBee+219qyZ
zT3mDR/7S3332S3f32L37Tti9+7fbpPp3fbs2S324x//xO7fN2sfe2yTvfDCRXbh8S32O9++xj4x
O2xrqi3W/v43eL+e24mllO3E45mAnf/AAnvh/Atsc1OjLZYi+y+/vdY+Pjtsd2/fa3v2jFiP8bI/
9v/pEOfx3f7A/3M4Spb/IeyxXvU4a5S1V4m3o8i2j/bbYilv+wdrre9N2y3b91pA/pX2qquutA/c
d59tb2+3V199te3o2G3375ux1153pZ2Zf9IePnDQ9gy1WO2X32O322vG30kRAnv37LH93cO2sX2v
TeYH7Y4du2xra5Otb2i0b33rL93eG2sR/E8f33mU/v0X4ij9+xI5So2P2fG396/m6X8XSp3fQ3k/
AaswYvBsc1aX2LffS29Plk1Pr2bZskd5es1a/vL66zn9lNNIeS4yUixavJhTTz2Vjo6Ob/3g+Sfe
+3//y1s4+4yz0UpTW1fLuX8ykyuvvJzFi461pM1k2+964j96P0sD2iKswVpB16Eunnn6GfZt2sO0
JvF252hZTo599L+e/F93lCxfKkdp46/s3C9m+4/a+1Xg2588eGltR31y6S4W/2kFfE2m1mC04oUf
/Zhv3Hgj+4cG2bprNzW5Kto62plS38qEhiYSngv/xU2+/I0E33L2fI6pX4rE396uKAnC21L++2S4
Oq6v9369yA190/73111l20f329I2y7v9X8p3+wPH/6vE4CjZ+5fP/3L3/sX+vA/a5HhC27H29tWl
+vj23x55m6+3XUeJ8s/38qZf381fXXcD4A3b+sC8kAnS4aQe57/z9lfy03/1U4x5fXg3w3/XN+2U
p0+pD2mgtItrA6zPse20U/4v3/y8d53Pfxk/iP+b4Sjd/D/i3/Uv/e9y13e2x/4/X7Nf7t5f9u5f
Sre+U98Dq6y15/m++f3P9b/s4j/vY4qA+/Y50I6i0fO45K2/jC+x/9x3u39jG2I2/9d54Sj5/C87
f19Sj//3A635L/d+Ufyf643L+/vD88tftm+/zO3v2x5f7N89/u/eG55//z91pL/Sffv3y/mP3aM0
+I8S/Mvt8f/x9L+yff99/uXjX/z/C0f/l/+s/P+/B1pjrLHWfufX+P3/29aX+t//30B/5/v3f9+m
yUvLInm/X0m3vN9N3lX+4L239f/y343i3+v/Mlwq4E/F/5sN3pfaVv+I29517I/X3fG1fA2+d1x+
90/O/6rP+O96t7vP/9XGz4vv6/9/e/S7+398f79f53jSfyG/6qNf4E02uQo3eP9Ivx98R9f4A9f/
d4/C/2uNf+x0O47C9X6mKx6Uf3kInBvj6/rIvx96H0S/P/o+I+3qEfx/zH1/e/y/29fve7268Gv3
v5S/+i1a+3/r9Vf3/V/1/l/8vL9fT/e/iN6X49t3lX3I1v77y/0/5N0/fG9f7f4/4Gv8u734n8oR
7fU4/40L/x8kY/b31/9bE8f5IeIxf2x/v/c/S0T8o0T2O376o754/53545u8372Xm4zS5o/87p9q
8x/f6P8m9X6p/sB3eXz5B+mJpze/3P/i/o5/q1A80f/aIn8v3X/I3f8D3/0/073/l++t//f7/fS+
3/u3qf7f4ej/39r0+21/vO//c++y32N/4f15dYn2A+393eX/kPf++3L3+lqT4i/1/s/n53H3e7xY
f8/33e99b2X5p/95iP8P/9DufX89eI2X+1s4SrofxX8R/A971/+I2/7/dO+Hvx+/903e+/3+/7/l
R8j0Lwf/e+434kft9q/8x39e9p9uM3/XNf+/I0s/eO8f9N0/SAt+34m/0v7x6M/U/93p3p+A/09N
+t8N+n/J/5P7m//A5q8o+6M/y3+4zfwfb/O1kOXIuN8v5R/m9u8n3aX+iN/f2v1/0P3vNf6R8p+W
iNhv9f1m5t8v1x/3I0T3w+b5v/S9+3S3+/vH038jR/b0x8/6fym330/uX/4/5Sjt/sU3+b++7N8P
qH/L6P91/sD/m95r+I+0/0e4+/vL6e7//n/qQ928T/81xX+/yR9I+r+P3H6/H/77332/yR/2/r87
4A/sS/fP5d2/n1y/vA38a6H52+d7/8I/2Nbf9x39v33/93y/3E4c5ef3K57f//d/5e/5E0O8x/vd
3v2E/349uLz7f5O7/q+l/5fA0f+P/1M4ilX+55AofP7f74Nf3e8P1/tI/i/13l/m/1i//t+i/4P8
8feX84f++zL+0L0ftS//q3KUNv5/5Yit/Q/S1//u+v9s73/0vIu//533d/yRvf+32sL3vfvvv/+n
3u3eO/9y3/u7f398k+f/Q44P0f//d1+82f/94y9/73eT3+/fFfX31/2f3vvRcv3vvfvvx39Gju72
/03/kL/1o/Xl/8tvef/I/P/d3v2X83f8A2v8O/7e3e9H+e/fTfL3k/1e3/vve71I3//T3v41xI/K
UTr4v9sRvftXUvGf0uO711/L3X74e+X/yNbf23e+/s/t1kfaB39aA/eL+mN6Ift6+01s+cOf/Zvy
Uqf1Ivv60e/++1f+4W35/5X0L3/P/+kR3u/Hl9+/l3u8a+/7vfe+/v4eIeX/054i9L8dOkrkI3/k
9X23H37vI2X93vH+/hX/Rz5/4A/i2/7X8oee/xH3/b4290dO8x/27g/s5S8/2v3b64fvx99d1iON
q/4//a5fXvbH9iP/X4SjpPG/i6OU7f2Ie++Xg7X/1m68+/fHfv7I90/C7e8m24O07K96//9f6d7S
3O9/e5K92/eX+9/U0/sfP1I+/d17P33v+/s0f2/7B3v33+/9vS+z24P41+/v3p9e5e//3fFf3f7I
8ff/4fF0j5c7T/e2+/2a4p8iTv9/E/3vf/vR331/X3f/fvd3l+V/7fH+/p2/b432x+x/u/8/x9/3
I3iLpT/+pL/pA/1u6P95j9f3oX+/vIfrf4mffk/UHzfO3/1/Dkf+5Y/A/zJ4pRH90I+X318iN3l8
3iN1e6i6m+e/Xy2E+eI3efd7l28pX832/vdX/L4S4wfc77v//pfe19sfu1s56g/f5+I8H//Lfb++
33u/9/3/8a6493fX//KvefT3eI+m/3s5Iut/4/+/9024/wO9/324//f+U1/0X3aP9x300Xf/0D3v
/ftf6T8r5eP3+19H+eX+O4n3e3//4/n33//f7z7/Gf/3o2/z3m/26N835+/m/x3+9aX+/2k3OdrH
3v+E7x1A/eXffXvIe8x5SrmL3+94/8f3e5H/e3fE/x/B/3j8e0f6I23+113zD9vLlzrS3s9y/67v
v/8ff++X3O3e0/3v193bL4e8p//j+/1I7f0w/NfIUTp0FAfL53+Xf/v/H+7fP04//3p693cPfS3/
"""

# Render logo secara langsung dari Base64
st.sidebar.image(base64.b64decode(LOGO_BASE64), use_container_width=True)

st.sidebar.title("POKTAN SUKA MAJU")
st.sidebar.markdown("**Aplikasi Kas & Unit Usaha**")

# Mode Akses
st.sidebar.markdown("---")
st.sidebar.subheader("👤 Hak Akses Pengguna")
mode_akses = st.sidebar.selectbox("Pilih Peran:", ["👁️ Mode Anggota (Lihat Laporan)", "🔐 Mode Pengurus (Akses Edit)"])

is_admin = False
if mode_akses == "🔐 Mode Pengurus (Akses Edit)":
    pin_input = st.sidebar.text_input("Masukkan PIN Pengurus:", type="password", help="PIN Default adalah 1234")
    if pin_input == "1234":
        is_admin = True
        st.sidebar.success("Akses Pengurus Aktif")
    elif pin_input != "":
        st.sidebar.error("PIN Salah!")

# Tampil Musim Aktif
st.sidebar.markdown("---")
st.sidebar.subheader("🗓️ Musim Aktif Tanam")
st.sidebar.info(f"📍 **{musim_aktif}**")

# Input Saldo Awal Musim Manual
if is_admin:
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Ubah Saldo Awal")
    new_saldo_awal = st.sidebar.number_input("Saldo Awal Musim (Rp):", value=float(saldo_musim_lalu), step=1000000.0)
    if new_saldo_awal != saldo_musim_lalu:
        set_setting('saldo_awal', new_saldo_awal)
        st.sidebar.success("Saldo awal disimpan!")
        st.rerun()

# Menu Radio Navigasi
st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "Pilih Menu Laporan:",
    [
        "📊 Dasbor Utama", 
        "🚜 Unit Combine (Panen)", 
        "⚙️ Unit Rotavator (Lahan)", 
        "🧪 Unit Pestisida & Kios", 
        "💳 Kredit & Cicilan Barang", 
        "💸 Rincian Pengeluaran", 
        "➕ Tambah Transaksi",
        "🔴 Tutup Buku & Reset Musim"
    ]
)

# -------------------- DASHBOARD UTAMA --------------------
if menu == "📊 Dasbor Utama":
    col_logo, col_title = st.columns([1, 5])
    with col_logo:
        st.image(base64.b64decode(LOGO_BASE64), width=110)
    with col_title:
        st.title("Dasbor Utama Kas POKTAN SUKA MAJU")
        st.caption(f"Status Pengguna: **{mode_akses}** | Musim Tanam Aktif: **{musim_aktif}**")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Hasil Usaha", f"Rp {tot_pemasukan_usaha:,.0f}".replace(',', '.'))
    col2.metric("Total Pengeluaran", f"Rp {tot_pengeluaran:,.0f}".replace(',', '.'))
    col3.metric("Sisa Saldo Kios/Lalu", f"Rp {sisa_saldo_kios:,.0f}".replace(',', '.'))
    col4.metric("SALDO AKHIR KAS", f"Rp {saldo_akhir_kas:,.0f}".replace(',', '.'))

    st.markdown("---")
    
    st.info(f"💡 **Informasi Ringkasan Kas:** Saldo Awal Musim Ini = **Rp {saldo_musim_lalu:,.0f}** | Sisa Piutang Kredit = **Rp {tot_sisa_piutang:,.0f}**.")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("📈 Pemasukan Per Unit Usaha")
        df_pemasukan = pd.DataFrame({
            "Unit Usaha": ["Combine", "Rotavator", "Pestisida", "Oven", "Lainnya"],
            "Pendapatan": [tot_combine, tot_rotavator, tot_pestisida, tot_oven, pemasukan_tambahan]
        })
        fig_pie = px.pie(df_pemasukan, values="Pendapatan", names="Unit Usaha", hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with col_chart2:
        st.subheader("📊 Perbandingan Hasil vs Pengeluaran")
        df_bar = pd.DataFrame({
            "Kategori": ["Hasil Usaha", "Saldo Lalu", "Total Pengeluaran", "Saldo Akhir"],
            "Jumlah": [tot_pemasukan_usaha, saldo_musim_lalu, tot_pengeluaran, saldo_akhir_kas]
        })
        fig_bar = px.bar(df_bar, x="Kategori", y="Jumlah", text="Jumlah", color="Kategori")
        fig_bar.update_traces(texttemplate='Rp %{text:,.0f}', textposition='outside')
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("### 📝 Tabel Rekap Pemasukan Musim Ini")
    df_rekap_show = pd.DataFrame({
        "Sumber Pemasukan": ["1. REKAP COMBINE", "2. REKAP ROTAVATOR", "3. REKAP PESTISIDA", "4. REKAP OVEN", "5. PEMASUKAN LAINNYA", "TOTAL PEMASUKAN USAHA"],
        "Nilai Total": [f"Rp {tot_combine:,.0f}".replace(',', '.'), f"Rp {tot_rotavator:,.0f}".replace(',', '.'), f"Rp {tot_pestisida:,.0f}".replace(',', '.'), f"Rp {tot_oven:,.0f}".replace(',', '.'), f"Rp {pemasukan_tambahan:,.0f}".replace(',', '.'), f"Rp {tot_pemasukan_usaha:,.0f}".replace(',', '.')]
    })
    st.dataframe(df_rekap_show, use_container_width=True)
    st.download_button("📥 Unduh Ringkasan Kas (CSV)", df_rekap_show.to_csv(index=False), "Ringkasan_Kas_Poktan.csv", "text/csv")

# -------------------- UNIT COMBINE --------------------
elif menu == "🚜 Unit Combine (Panen)":
    st.title("🚜 Laporan Hasil Panen - Combine Harvester")
    st.caption(f"Musim Tanam Aktif: **{musim_aktif}**")
    
    if "OKT 2026" in musim_aktif:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Karung Gabah", f"{df_combine['JML_KARUNG'].sum():,} Karung".replace(',', '.'))
        c2.metric("Total Pendapatan Combine", f"Rp {tot_combine:,.0f}".replace(',', '.'))
        c3.metric("Jumlah Petani", f"{len(df_combine)} Orang")
        
        st.markdown("---")
        search_nama = st.text_input("🔍 Cari Nama Petani:")
        df_filtered = df_combine if not search_nama else df_combine[df_combine['NAMA'].str.contains(search_nama, case=False, na=False)]
        st.dataframe(df_filtered, use_container_width=True)
        st.download_button("📥 Unduh Data Combine (CSV)", df_combine.to_csv(index=False), "Laporan_Combine.csv", "text/csv")
    else:
        st.info("💡 Belum ada data transaksi Combine bawaan untuk musim baru ini. Gunakan menu 'Tambah Transaksi' untuk mencatat pemasukan baru.")

# -------------------- UNIT ROTAVATOR --------------------
elif menu == "⚙️ Unit Rotavator (Lahan)":
    st.title("⚙️ Laporan Pengolahan Lahan - Rotavator")
    st.caption(f"Musim Tanam Aktif: **{musim_aktif}**")
    
    if "OKT 2026" in musim_aktif:
        r1, r2, r3 = st.columns(3)
        r1.metric("Total Luas Tergarap", f"{df_rotavator['LUAS_HA'].sum():.2f} Ha")
        r2.metric("Total Subsidi Solar", f"Rp {df_rotavator['SUBSIDI_SOLAR'].sum():,.0f}".replace(',', '.'))
        r3.metric("Pendapatan Bersih", f"Rp {tot_rotavator:,.0f}".replace(',', '.'))
        
        st.markdown("---")
        st.dataframe(df_rotavator, use_container_width=True)
        st.download_button("📥 Unduh Data Rotavator (CSV)", df_rotavator.to_csv(index=False), "Laporan_Rotavator.csv", "text/csv")
    else:
        st.info("💡 Belum ada data transaksi Rotavator untuk musim baru ini.")

# -------------------- UNIT PESTISIDA & KIOS --------------------
elif menu == "🧪 Unit Pestisida & Kios":
    st.title("🧪 Laporan Belanja Obat & Pestisida Anggota")
    st.caption(f"Musim Tanam Aktif: **{musim_aktif}**")
    
    p1, p2, p3 = st.columns(3)
    p1.metric("Total Tagihan Pestisida", f"Rp {tot_pestisida:,.0f}".replace(',', '.'))
    p2.metric("Pemasukan Obat Kios KES", f"Rp {pemasukan_kios:,.0f}".replace(',', '.'))
    p3.metric("Jumlah Anggota Belanja", f"{len(df_pestisida)} Orang")
    
    st.markdown("---")
    
    if not df_pestisida.empty:
        col_p_s1, col_p_s2 = st.columns([2, 1])
        with col_p_s1:
            cari_pestisida = st.text_input("🔍 Cari Nama Anggota:")
        with col_p_s2:
            filter_pestisida_status = st.selectbox("Status Tagihan:", ["Semua Status", "Belum Lunas", "Lunas"])
            
        df_p_show = df_pestisida.copy()
        if cari_pestisida:
            df_p_show = df_p_show[df_p_show['nama'].str.contains(cari_pestisida, case=False, na=False)]
        if filter_pestisida_status != "Semua Status":
            df_p_show = df_p_show[df_p_show['status'] == filter_pestisida_status]
            
        st.dataframe(df_p_show, use_container_width=True)
        st.download_button("📥 Unduh Tagihan Pestisida (CSV)", df_pestisida.to_csv(index=False), "Tagihan_Pestisida.csv", "text/csv")
        
        if is_admin:
            st.markdown("---")
            st.subheader("⚙️ Update Status Pelunasan Pestisida")
            with st.form("form_update_pestisida"):
                pilih_anggota_p = st.selectbox("Pilih Anggota:", df_pestisida['nama'].tolist())
                status_baru_p = st.selectbox("Status Baru:", ["Belum Lunas", "Lunas"])
                submit_p = st.form_submit_button("Update Status")
                
                if submit_p:
                    conn = get_db_connection()
                    c = conn.cursor()
                    c.execute("UPDATE pestisida SET status = ? WHERE nama = ? AND musim = ?", (status_baru_p, pilih_anggota_p, musim_aktif))
                    conn.commit()
                    conn.close()
                    st.success(f"Status tagihan **{pilih_anggota_p}** diperbarui menjadi **{status_baru_p}**!")
                    st.rerun()
    else:
        st.info("💡 Belum ada tagihan pestisida untuk musim baru ini.")

# -------------------- KREDIT BARANG --------------------
elif menu == "💳 Kredit & Cicilan Barang":
    st.title("💳 Laporan Kredit & Cicilan Barang Anggota")
    st.caption(f"Musim Tanam Aktif: **{musim_aktif}**")
    
    k1, k2, k3 = st.columns(3)
    k1.metric("Total Nilai Barang", f"Rp {tot_nilai_kredit:,.0f}".replace(',', '.'))
    k2.metric("Total Terbayar (DP + Angsuran)", f"Rp {tot_kredit_terbayar:,.0f}".replace(',', '.'))
    k3.metric("Sisa Piutang Anggota", f"Rp {tot_sisa_piutang:,.0f}".replace(',', '.'))
    
    st.markdown("---")
    
    if not df_kredit.empty:
        col_k1, col_k2 = st.columns([2, 1])
        with col_k1:
            cari_kredit = st.text_input("🔍 Cari Nama Anggota / Barang:")
        with col_k2:
            filter_status = st.selectbox("Status Pembayaran", ["Semua Status", "Berjalan", "Lunas"])
            
        df_kredit_show = df_kredit.copy()
        if cari_kredit:
            df_kredit_show = df_kredit_show[
                df_kredit_show['nama_anggota'].str.contains(cari_kredit, case=False, na=False) |
                df_kredit_show['nama_barang'].str.contains(cari_kredit, case=False, na=False)
            ]
        if filter_status != "Semua Status":
            df_kredit_show = df_kredit_show[df_kredit_show['status'] == filter_status]
            
        st.dataframe(df_kredit_show, use_container_width=True)
        st.download_button("📥 Unduh Laporan Kredit (CSV)", df_kredit.to_csv(index=False), "Laporan_Kredit.csv", "text/csv")
        
        if is_admin:
            st.markdown("---")
            st.subheader("➕ Form Catat Pembayaran Angsuran")
            with st.form("form_angsuran"):
                pilih_pembayar = st.selectbox("Pilih Anggota", df_kredit[df_kredit['status'] == "Berjalan"]['nama_anggota'].tolist() if not df_kredit[df_kredit['status'] == "Berjalan"].empty else ["Tidak Ada Kredit Berjalan"])
                nominal_angsuran = st.number_input("Nominal Angsuran (Rp)", min_value=10000, step=50000)
                
                simpan_angsuran = st.form_submit_button("Simpan Angsuran")
                if simpan_angsuran and pilih_pembayar != "Tidak Ada Kredit Berjalan":
                    conn = get_db_connection()
                    c = conn.cursor()
                    c.execute("UPDATE kredit SET angsuran_masuk = angsuran_masuk + ? WHERE nama_anggota = ? AND musim = ?", (nominal_angsuran, pilih_pembayar, musim_aktif))
                    
                    c.execute("SELECT harga_total, (dp + angsuran_masuk) as total FROM kredit WHERE nama_anggota = ? AND musim = ?", (pilih_pembayar, musim_aktif))
                    row = c.fetchone()
                    if row and row['total'] >= row['harga_total']:
                        c.execute("UPDATE kredit SET status = 'Lunas' WHERE nama_anggota = ? AND musim = ?", (pilih_pembayar, musim_aktif))
                        
                    conn.commit()
                    conn.close()
                    st.success(f"Berhasil mencatat angsuran **{pilih_pembayar}** sebesar **Rp {nominal_angsuran:,.0f}**!")
                    st.rerun()
    else:
        st.info("💡 Belum ada data kredit barang untuk musim baru ini.")

# -------------------- PENGELUARAN --------------------
elif menu == "💸 Rincian Pengeluaran":
    st.title("💸 Laporan Pengeluaran & Belanja Modal")
    st.caption(f"Musim Tanam Aktif: **{musim_aktif}**")
    st.metric("TOTAL PENGELUARAN MUSIM INI", f"Rp {tot_pengeluaran:,.0f}".replace(',', '.'))
    st.markdown("---")
    
    if "OKT 2026" in musim_aktif:
        df_exp_cat = df_pengeluaran.groupby("KATEGORI")["JUMLAH"].sum().reset_index().sort_values(by="JUMLAH", ascending=False)
        fig_exp = px.bar(df_exp_cat, x="KATEGORI", y="JUMLAH", text="JUMLAH", color="KATEGORI")
        fig_exp.update_traces(texttemplate='Rp %{text:,.0f}', textposition='outside')
        st.plotly_chart(fig_exp, use_container_width=True)
        st.dataframe(df_pengeluaran, use_container_width=True)
        st.download_button("📥 Unduh Rincian Pengeluaran (CSV)", df_pengeluaran.to_csv(index=False), "Rincian_Pengeluaran.csv", "text/csv")
    else:
        if not df_transaksi.empty:
            df_peng_baru = df_transaksi[df_transaksi['jenis'] == 'Pengeluaran']
            st.dataframe(df_peng_baru, use_container_width=True)
        else:
            st.info("💡 Belum ada pengeluaran yang dicatat untuk musim baru ini.")

# -------------------- TAMBAH TRANSAKSI --------------------
elif menu == "➕ Tambah Transaksi":
    st.title("📝 Input Transaksi Kas Baru")
    st.caption(f"Musim Tanam Aktif: **{musim_aktif}**")
    
    if not is_admin:
        st.warning("🔒 Halaman ini khusus Pengurus. Silakan masukkan PIN Pengurus di panel samping kiri terlebih dahulu.")
    else:
        with st.form("form_transaksi"):
            jenis = st.selectbox("Jenis Transaksi", ["Pemasukan", "Pengeluaran"])
            kategori = st.selectbox("Unit / Kategori", ["Combine", "Rotavator", "Pestisida", "Oven", "Kredit Barang", "Belanja Modal", "Bahan Bakar"])
            keterangan = st.text_input("Keterangan Transaksi")
            jumlah_rp = st.number_input("Jumlah (Rupiah)", min_value=0, step=50000)
            
            submitted = st.form_submit_button("Simpan Transaksi")
            if submitted and keterangan:
                conn = get_db_connection()
                c = conn.cursor()
                c.execute("INSERT INTO transaksi (musim, tanggal, jenis, kategori, keterangan, jumlah) VALUES (?, date('now'), ?, ?, ?, ?)",
                          (musim_aktif, jenis, kategori, keterangan, jumlah_rp))
                conn.commit()
                conn.close()
                st.success(f"Berhasil menyimpan {jenis}: **{keterangan}** sebesar **Rp {jumlah_rp:,.0f}**!")
                st.rerun()

# -------------------- TUTUP BUKU & RESET MUSIM --------------------
elif menu == "🔴 Tutup Buku & Reset Musim":
    st.title("🔴 Fitur Tutup Buku & Reset untuk Musim Baru")
    
    if not is_admin:
        st.warning("🔒 Halaman ini khusus Pengurus. Silakan masukkan PIN Pengurus di panel samping kiri terlebih dahulu.")
    else:
        st.error("⚠️ **Perhatian Pengurus:** Fitur ini akan menutup pembukuan musim aktif saat ini dan memindahkan Saldo Akhir Kas sebagai Saldo Awal Musim Baru.")
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.metric("Musim Aktif Saat Ini", musim_aktif)
            saldo_final_alihkan = st.number_input("Saldo Akhir Kas Yang Dialihkan (Rp):", value=float(saldo_akhir_kas), step=100000.0)
            
        with col_t2:
            nama_musim_baru = st.text_input("Ketik Nama Musim Baru:", value="APRIL 2027 (Musim Gadu)")
            konfirmasi_tutup = st.button("🚀 Konfirmasi Tutup Buku & Mulai Musim Baru")
            
            if konfirmasi_tutup and nama_musim_baru:
                set_setting('saldo_awal', saldo_final_alihkan)
                set_setting('musim_aktif', nama_musim_baru)
                
                st.balloons()
                st.success(f"✅ Berhasil Tutup Buku! Musim baru **'{nama_musim_baru}'** telah aktif dengan Saldo Awal **Rp {saldo_final_alihkan:,.0f}**.")
                st.rerun()
