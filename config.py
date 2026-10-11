import os
import re
import shutil

try:
    from qt.core import QApplication, QCheckBox, QLabel, QPlainTextEdit, QProgressDialog, QPushButton, QVBoxLayout, QWidget
except ImportError:
    from PyQt5.Qt import QApplication, QCheckBox, QLabel, QPlainTextEdit, QProgressDialog, QPushButton, QVBoxLayout, QWidget

from calibre.gui2 import error_dialog, info_dialog, question_dialog
from calibre.ptempfile import TemporaryDirectory

from calibre_plugins.string_remover.cleaner import FORMATS, build_pattern, clean_file, may_contain, prefs


class ConfigWidget(QWidget):

    def __init__(self):
        QWidget.__init__(self)
        layout = QVBoxLayout(self)

        label = QLabel('Strings to remove from the book text (one per line), e.g. the address '
                       'of a website. Links pointing to or showing such a string are removed '
                       'completely.')
        label.setWordWrap(True)
        layout.addWidget(label)
        self.strings = QPlainTextEdit(self)
        self.strings.setPlainText('\n'.join(prefs['strings']))
        layout.addWidget(self.strings)

        self.case_sensitive = QCheckBox('Case sensitive', self)
        self.case_sensitive.setChecked(prefs['case_sensitive'])
        layout.addWidget(self.case_sensitive)

        self.regex = QCheckBox('Treat lines as regular expressions', self)
        self.regex.setChecked(prefs['regex'])
        layout.addWidget(self.regex)

        self.clean_on_import = QCheckBox('Clean books automatically when they are added', self)
        self.clean_on_import.setChecked(prefs['clean_on_import'])
        layout.addWidget(self.clean_on_import)

        self.keep_original = QCheckBox('When cleaning the library, keep the unchanged file as ORIGINAL_EPUB / ORIGINAL_AZW3', self)
        self.keep_original.setChecked(prefs['keep_original'])
        layout.addWidget(self.keep_original)

        self.clean_button = QPushButton('Clean whole library now…', self)
        self.clean_button.clicked.connect(self.clean_library)
        layout.addWidget(self.clean_button)
        if self.gui() is None:
            self.clean_button.setEnabled(False)
            self.clean_button.setToolTip('Only available inside the calibre main program')

    def gui(self):
        from calibre.gui2.ui import get_gui
        return get_gui()

    def settings(self):
        return {
            'strings': [s.strip() for s in self.strings.toPlainText().splitlines() if s.strip()],
            'case_sensitive': self.case_sensitive.isChecked(),
            'regex': self.regex.isChecked(),
            'clean_on_import': self.clean_on_import.isChecked(),
            'keep_original': self.keep_original.isChecked(),
        }

    def validate(self):
        try:
            build_pattern(self.settings())
        except re.error as e:
            error_dialog(self, 'Invalid regular expression', str(e), show=True)
            return False
        return True

    def save_settings(self):
        for key, value in self.settings().items():
            prefs[key] = value

    def clean_library(self):
        if not self.validate():
            return
        settings = self.settings()
        pattern = build_pattern(settings)
        if pattern is None:
            return error_dialog(self, 'Nothing to do', 'Enter at least one string.', show=True)
        gui = self.gui()
        db = gui.current_db.new_api
        jobs = [(book_id, fmt) for book_id in db.all_book_ids() for fmt in db.formats(book_id) if fmt in FORMATS]

        with TemporaryDirectory('_string_remover') as tdir:
            # clean copies first, so nothing in the library is touched before the user confirms
            progress = QProgressDialog('Scanning books…', 'Cancel', 0, len(jobs), self)
            progress.setModal(True)
            progress.setMinimumDuration(0)
            found, errors = [], []
            for i, (book_id, fmt) in enumerate(jobs):
                progress.setValue(i)
                QApplication.processEvents()
                if progress.wasCanceled():
                    return
                title = db.field_for('title', book_id)
                try:
                    src = db.format_abspath(book_id, fmt)
                    if not src or not may_contain(src, pattern):
                        continue
                    copy = os.path.join(tdir, '%d.%s' % (book_id, fmt.lower()))
                    shutil.copyfile(src, copy)
                    count = clean_file(copy, pattern)
                except Exception as e:
                    errors.append('%s (%s): skipped, %s' % (title, fmt, e))
                    continue
                if count:
                    found.append((book_id, fmt, copy, '%s (%s): %d removed' % (title, fmt, count)))
            progress.setValue(len(jobs))

            if not found:
                return info_dialog(self, 'Nothing to do', 'No book in this library contains these strings.',
                                   det_msg='\n'.join(errors), show=True)
            if not question_dialog(self, 'Clean library',
                                   'This will rewrite %d book file(s). Continue?' % len(found),
                                   det_msg='\n'.join([f[3] for f in found] + errors)):
                return
            for book_id, fmt, copy, _ in found:
                if settings['keep_original'] and 'ORIGINAL_' + fmt not in db.formats(book_id):
                    db.save_original_format(book_id, fmt)
                db.add_format(book_id, fmt, copy, replace=True, run_hooks=False)
            gui.library_view.model().refresh_ids(list({f[0] for f in found}))
            info_dialog(self, 'Done', 'Cleaned %d book file(s).' % len(found),
                        det_msg='\n'.join(errors), show=True)
