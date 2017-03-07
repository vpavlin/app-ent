# -*- mode: python -*-

# Function in order to recursively add data directories to pyinstaller
def extra_datas(mydir):
    def rec_glob(p, files):
        import os
        import glob
        for d in glob.glob(p):
            if os.path.isfile(d):
                files.append(d)
            rec_glob("%s/*" % d, files)
    files = []
    rec_glob("%s/*" % mydir, files)
    extra_datas = []
    for f in files:
        extra_datas.append((f, f, 'DATA'))

    return extra_datas

block_cipher = None

# Due to the way that we dynamically load providers via import_module
# in atomicapp/plugin.py we have to specify explicitly the modules directly
# so pyinstaller can "see" them. This is indicated by 'hiddenimports'
a = Analysis(['atomicapp/cli/main.py'],
             pathex=['.'],
             binaries=None,
             datas=None,
             hiddenimports=[
               'atomicapp.providers.docker', 
               'atomicapp.providers.kubernetes',
               'atomicapp.providers.openshift',
               'atomicapp.providers.marathon'
             ],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

# Add external data (atomicapp init + provider external data)
a.datas += extra_datas('atomicapp/providers/external')
a.datas += extra_datas('atomicapp/nulecule/external')

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='atomicapp/cli/main',
          debug=False,
          strip=False,
          upx=True,
          console=True )
