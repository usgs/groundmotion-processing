---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: '0.8'
    jupytext_version: '1.4.1'
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---
# Title

some text


\```{python echo=TRUE}
import pandas as pd
series = pd.Series({'A':1, 'B':3, 'C':2})
pd.DataFrame({"Columne A": series})
\```

