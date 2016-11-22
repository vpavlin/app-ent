## System tests for atomicapp

### Usage
From root directory of ``atomicapp`` repo, do:

```
sudo NULECULE_LIB=<path to nulecule-library> py.test tests/system
```

To test individual provider, you can do the following:

```
sudo NULECULE_LIB=<path to nulecule-library> py.test tests/system/test_<provider name>_provider.py
```
