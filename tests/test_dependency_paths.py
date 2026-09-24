"""Dependency boundaries must use filesystem identity on Windows aliases."""
from pathlib import Path
import ctypes,os,sys,tempfile,unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts import fetch_dependencies as fetcher


class DependencyPathsTests(unittest.TestCase):
    def test_missing_nested_destination(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(fetcher,'BASE',Path(folder).resolve()):
            expected=Path(folder).resolve()/'runtime-archives/windows-x64/python.tar.gz'
            self.assertEqual(fetcher.dependency_path('runtime-archives/windows-x64/python.tar.gz'),expected)
            self.assertFalse(expected.parent.exists())

    def test_outside_paths_rejected_before_creation(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(fetcher,'BASE',Path(folder).resolve()):
            for path in ('../escape/archive.zip',str(Path(folder).resolve().parent/'outside.zip')):
                with self.subTest(path=path),self.assertRaisesRegex(ValueError,'outside package'):
                    fetcher.dependency_path(path)

    @unittest.skipUnless(os.name=='nt','Windows extended-length paths')
    def test_windows_extended_root_alias(self):
        with tempfile.TemporaryDirectory(prefix='Logisim dependency paths ') as folder:
            canonical=Path(folder).resolve()
            alias=Path('\\\\?\\'+str(canonical))
            self.assertTrue(alias.samefile(canonical))
            with patch.object(fetcher,'BASE',alias):
                result=fetcher.dependency_path('runtime-archives/python.tar.gz')
            self.assertTrue(result.parent.parent.samefile(canonical))

    @unittest.skipUnless(os.name=='nt','Windows short filenames')
    def test_windows_short_root_alias(self):
        with tempfile.TemporaryDirectory(prefix='Logisim dependency paths ') as folder:
            canonical=Path(folder).resolve()
            fn=ctypes.WinDLL('kernel32',use_last_error=True).GetShortPathNameW
            fn.argtypes=[ctypes.c_wchar_p,ctypes.c_wchar_p,ctypes.c_uint32];fn.restype=ctypes.c_uint32
            buffer=ctypes.create_unicode_buffer(32768)
            self.assertTrue(fn(str(canonical),buffer,len(buffer)))
            alias=Path(buffer.value)
            if alias==canonical:self.skipTest('Volume does not provide short filenames')
            with patch.object(fetcher,'BASE',alias):
                result=fetcher.dependency_path('runtime-archives/python.tar.gz')
            self.assertTrue(result.parent.parent.samefile(canonical))

    def test_directory_link_cannot_escape(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'package';root.mkdir()
            outside=Path(folder)/'outside';outside.mkdir()
            try:(root/'escape').symlink_to(outside,target_is_directory=True)
            except OSError as error:self.skipTest('Directory symlinks unavailable: '+str(error))
            with patch.object(fetcher,'BASE',root.resolve()),self.assertRaisesRegex(ValueError,'outside package'):
                fetcher.dependency_path('escape/dependency.zip')


if __name__=='__main__':unittest.main()
