from calibre.customize import FileTypePlugin


class StringRemover(FileTypePlugin):
    name = 'String Remover'
    description = ('Removes configured strings and links (e.g. watermark links at the end '
                   'of each chapter) from the text of EPUB and AZW3 books, for newly '
                   'added books and for the whole library.')
    supported_platforms = ['windows', 'osx', 'linux']
    author = 'DerSchmachtin'
    version = (2, 0, 0)
    minimum_calibre_version = (5, 0, 0)

    file_types = {'epub', 'azw3'}
    on_import = True

    def run(self, path_to_ebook):
        import os
        import shutil
        import traceback

        from calibre_plugins.string_remover.cleaner import build_pattern, clean_file, may_contain, prefs
        if not prefs['clean_on_import']:
            return path_to_ebook
        try:
            pattern = build_pattern(prefs)
            if pattern is None or not may_contain(path_to_ebook, pattern):
                return path_to_ebook
            out = self.temporary_file(os.path.splitext(path_to_ebook)[1])
            out.close()
            shutil.copyfile(path_to_ebook, out.name)
            if clean_file(out.name, pattern):
                return out.name
        except Exception:
            # e.g. DRM or a damaged file: add the book unchanged
            traceback.print_exc()
        return path_to_ebook

    def is_customizable(self):
        return True

    def config_widget(self):
        from calibre_plugins.string_remover.config import ConfigWidget
        return ConfigWidget()

    def save_settings(self, config_widget):
        config_widget.save_settings()
