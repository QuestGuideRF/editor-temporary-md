import sys
import os
import re
import json
import markdown
import datetime
import requests
import threading
from PyQt6 .QtWidgets import (
QApplication ,QMainWindow ,QSplitter ,QPlainTextEdit ,QTextEdit ,
QTextBrowser ,QVBoxLayout ,QWidget ,QToolBar ,QMenu ,
QMenuBar ,QStatusBar ,QFileDialog ,QMessageBox ,QDialog ,
QGridLayout ,QLabel ,QLineEdit ,QPushButton ,QCheckBox ,QGroupBox ,
QTreeView ,QDockWidget ,QInputDialog ,QHBoxLayout ,QComboBox ,
QListWidget ,QListWidgetItem ,QProgressDialog ,QScrollArea
)
from PyQt6 .QtCore import (
Qt ,QSize ,QTimer ,pyqtSignal as Signal ,pyqtSlot as Slot ,QSettings ,QRect ,QRegularExpression ,
QDir ,QFileInfo ,QModelIndex ,QItemSelectionModel ,QFile ,QTextStream ,QThread
)
from PyQt6 .QtGui import (
QAction ,QIcon ,QFont ,QColor ,QTextCharFormat ,QPainter ,
QTextCursor ,QSyntaxHighlighter ,QTextFormat ,QPalette ,QTextDocument ,
QFileSystemModel ,QStandardItemModel ,QStandardItem ,QKeySequence ,QPixmap ,QGuiApplication ,QImage ,QShortcut
)
try :
    from markdown_it import MarkdownIt
    from pygments import highlight
    from pygments .lexers import get_lexer_by_name
    from pygments .formatters import HtmlFormatter
    MARKDOWN_IT_AVAILABLE =True
except ImportError :
    MARKDOWN_IT_AVAILABLE =False
    print ("Внимание: уценка-it-py или пигменты не найдены. Использование базового рендеринга Markdown.")
try :
    import latex2mathml .converter
    LATEX_AVAILABLE =True
except ImportError :
    LATEX_AVAILABLE =False
    print ("Внимание: latex2mathml не найден. Поддержка LaTeX будет отключена.")
try :
    import cairosvg
    SVG_AVAILABLE =True
except ImportError :
    SVG_AVAILABLE =False
    print ("Внимание: cairosvg не найден. Рендеринг SVG будет ограничен.")
MERMAID_SUPPORT =True
class LineNumberArea (QWidget ):
    def __init__ (self ,editor ):
        super ().__init__ (editor )
        self .editor =editor
    def sizeHint (self ):
        return QSize (self .editor .line_number_area_width (),0 )
    def paintEvent (self ,event ):
        self .editor .line_number_area_paint_event (event )
class MarkdownHighlighter (QSyntaxHighlighter ):
    def __init__ (self ,parent =None ):
        super ().__init__ (parent )
        self .highlighting_rules =[]
        color_fg =QColor ("#D4D4D4")
        color_bg =QColor ("#1E1E1E")
        color_heading =QColor ("#569CD6")
        color_bold =QColor ("#D19A66")
        color_italic =QColor ("#B5CEA8")
        color_list =QColor ("#CE9178")
        color_link =QColor ("#4EC9B0")
        color_code =QColor ("#DCDCAA")
        color_quote =QColor ("#6A9955")
        color_math =QColor ("#C586C0")
        color_mermaid =QColor ("#4EC9B0")
        color_svg =QColor ("#CE9178")
        h1_format =QTextCharFormat ()
        h1_format .setFontWeight (QFont .Weight .Bold )
        h1_format .setFontPointSize (20 )
        h1_format .setForeground (color_heading )
        self .highlighting_rules .append ((QRegularExpression (r"^# .+$"),h1_format ))
        h2_format =QTextCharFormat ()
        h2_format .setFontWeight (QFont .Weight .Bold )
        h2_format .setFontPointSize (16 )
        h2_format .setForeground (color_heading )
        self .highlighting_rules .append ((QRegularExpression (r"^## .+$"),h2_format ))
        h3_format =QTextCharFormat ()
        h3_format .setFontWeight (QFont .Weight .Bold )
        h3_format .setFontPointSize (14 )
        h3_format .setForeground (color_heading )
        self .highlighting_rules .append ((QRegularExpression (r"^### .+$"),h3_format ))
        h4_format =QTextCharFormat ()
        h4_format .setFontWeight (QFont .Weight .Bold )
        h4_format .setFontPointSize (12 )
        h4_format .setForeground (color_heading )
        self .highlighting_rules .append ((QRegularExpression (r"^#### .+$"),h4_format ))
        bold_format =QTextCharFormat ()
        bold_format .setFontWeight (QFont .Weight .Bold )
        bold_format .setForeground (color_bold )
        self .highlighting_rules .append ((QRegularExpression (r"\*\*.+?\*\*"),bold_format ))
        self .highlighting_rules .append ((QRegularExpression (r"__.+?__"),bold_format ))
        italic_format =QTextCharFormat ()
        italic_format .setFontItalic (True )
        italic_format .setForeground (color_italic )
        self .highlighting_rules .append ((QRegularExpression (r"\*.+?\*"),italic_format ))
        self .highlighting_rules .append ((QRegularExpression (r"_.+?_"),italic_format ))
        list_format =QTextCharFormat ()
        list_format .setForeground (color_list )
        list_format .setFontWeight (QFont .Weight .Bold )
        self .highlighting_rules .append ((QRegularExpression (r"^[\*\-\+] "),list_format ))
        self .highlighting_rules .append ((QRegularExpression (r"^\d+\. "),list_format ))
        link_format =QTextCharFormat ()
        link_format .setForeground (color_link )
        link_format .setUnderlineStyle (QTextCharFormat .UnderlineStyle .SingleUnderline )
        self .highlighting_rules .append ((QRegularExpression (r"\[.+?\]\(.+?\)"),link_format ))
        code_format =QTextCharFormat ()
        code_format .setFontFamily ("Consolas")
        code_format .setBackground (QColor ("#262626"))
        code_format .setForeground (color_code )
        self .highlighting_rules .append ((QRegularExpression (r"`[^`]+`"),code_format ))
        code_block_format =QTextCharFormat ()
        code_block_format .setFontFamily ("Consolas")
        code_block_format .setBackground (QColor ("#23272E"))
        code_block_format .setForeground (color_code )
        self .code_block_pattern =QRegularExpression (r"```.*$")
        self .code_block_end_pattern =QRegularExpression (r"```$")
        self .code_block_format =code_block_format
        quote_format =QTextCharFormat ()
        quote_format .setForeground (color_quote )
        quote_format .setFontItalic (True )
        self .highlighting_rules .append ((QRegularExpression (r"^> .+$"),quote_format ))
        math_inline_format =QTextCharFormat ()
        math_inline_format .setForeground (color_math )
        math_inline_format .setFontFamily ("Consolas")
        self .highlighting_rules .append ((QRegularExpression (r"\$[^$\n]+\$"),math_inline_format ))
        math_block_format =QTextCharFormat ()
        math_block_format .setForeground (color_math )
        math_block_format .setFontFamily ("Consolas")
        self .highlighting_rules .append ((QRegularExpression (r"\$\$[^$]+\$\$"),math_block_format ))
        mermaid_format =QTextCharFormat ()
        mermaid_format .setForeground (color_mermaid )
        mermaid_format .setFontFamily ("Consolas")
        self .mermaid_block_pattern =QRegularExpression (r"```mermaid.*$")
        self .mermaid_format =mermaid_format
        svg_format =QTextCharFormat ()
        svg_format .setForeground (color_svg )
        svg_format .setFontFamily ("Consolas")
        self .svg_block_pattern =QRegularExpression (r"```svg.*$")
        self .svg_format =svg_format
    def highlightBlock (self ,text ):
        previous_block_state =self .previousBlockState ()
        if previous_block_state ==-1 :
            previous_block_state =0
        if previous_block_state ==1 :
            self .setFormat (0 ,len (text ),self .code_block_format )
            match =self .code_block_end_pattern .match (text )
            if match .hasMatch ():
                self .setCurrentBlockState (0 )
            else :
                self .setCurrentBlockState (1 )
            return
        elif previous_block_state ==2 :
            self .setFormat (0 ,len (text ),self .mermaid_format )
            match =self .code_block_end_pattern .match (text )
            if match .hasMatch ():
                self .setCurrentBlockState (0 )
            else :
                self .setCurrentBlockState (2 )
            return
        elif previous_block_state ==3 :
            self .setFormat (0 ,len (text ),self .svg_format )
            match =self .code_block_end_pattern .match (text )
            if match .hasMatch ():
                self .setCurrentBlockState (0 )
            else :
                self .setCurrentBlockState (3 )
            return
        match =self .code_block_pattern .match (text )
        if match .hasMatch ():
            self .setFormat (0 ,len (text ),self .code_block_format )
            self .setCurrentBlockState (1 )
            return
        match =self .mermaid_block_pattern .match (text )
        if match .hasMatch ():
            self .setFormat (0 ,len (text ),self .mermaid_format )
            self .setCurrentBlockState (2 )
            return
        match =self .svg_block_pattern .match (text )
        if match .hasMatch ():
            self .setFormat (0 ,len (text ),self .svg_format )
            self .setCurrentBlockState (3 )
            return
        for pattern ,format in self .highlighting_rules :
            match_iterator =pattern .globalMatch (text )
            while match_iterator .hasNext ():
                match =match_iterator .next ()
                self .setFormat (match .capturedStart (),match .capturedLength (),format )
class MarkdownRenderer :
    def __init__ (self ):
        self .md =None
        if MARKDOWN_IT_AVAILABLE :
            self .md =MarkdownIt ("commonmark",{"html":True ,"linkify":True ,"typographer":True })
            def highlight_code (code ,lang ,attrs ):
                if not lang :
                    return f'<pre><code>{code }</code></pre>'
                elif lang =="mermaid"and MERMAID_SUPPORT :
                    return f'<div class="mermaid">{code }</div>'
                elif lang =="svg"and SVG_AVAILABLE :
                    return f'<div class="svg-container">{code }</div>'
                try :
                    lexer =get_lexer_by_name (lang ,stripall =True )
                    formatter =HtmlFormatter (style ="default",noclasses =True )
                    return f'<div class="code-block">{highlight (code ,lexer ,formatter )}</div>'
                except :
                    return f'<pre><code>{code }</code></pre>'
            self .md .options .highlight =highlight_code
    def render (self ,text ):
        if LATEX_AVAILABLE :
            text =self ._process_latex_blocks (text )
            text =self ._process_latex_inline (text )
        if MARKDOWN_IT_AVAILABLE and self .md :
            html =self .md .render (text )
            return self ._wrap_html (html )
        else :
            html =self ._basic_render (text )
            return self ._wrap_html (html )
    def _process_latex_blocks (self ,text ):
        if not LATEX_AVAILABLE :
            return text
        def replace_latex_block (match ):
            latex_content =match .group (1 )
            try :
                mathml =latex2mathml .converter .convert (latex_content )
                return f'<div class="math-block">{mathml }</div>'
            except Exception as e :
                print (f"Error converting LaTeX block: {e }")
                return match .group (0 )
        return re .sub (r'\$\$(.*?)\$\$',replace_latex_block ,text ,flags =re .DOTALL )
    def _process_latex_inline (self ,text ):
        if not LATEX_AVAILABLE :
            return text
        def replace_latex_inline (match ):
            latex_content =match .group (1 )
            try :
                mathml =latex2mathml .converter .convert (latex_content )
                return f'<span class="math-inline">{mathml }</span>'
            except Exception as e :
                print (f"Error converting LaTeX inline: {e }")
                return match .group (0 )
        return re .sub (r'\$(.*?)\$',replace_latex_inline ,text )
    def _basic_render (self ,text ):
        text =re .sub (r'^# (.+)$',r'<h1>\1</h1>',text ,flags =re .MULTILINE )
        text =re .sub (r'^## (.+)$',r'<h2>\1</h2>',text ,flags =re .MULTILINE )
        text =re .sub (r'^### (.+)$',r'<h3>\1</h3>',text ,flags =re .MULTILINE )
        text =re .sub (r'^#### (.+)$',r'<h4>\1</h4>',text ,flags =re .MULTILINE )
        text =re .sub (r'\*\*(.+?)\*\*',r'<strong>\1</strong>',text )
        text =re .sub (r'__(.+?)__',r'<strong>\1</strong>',text )
        text =re .sub (r'\*(.+?)\*',r'<em>\1</em>',text )
        text =re .sub (r'_(.+?)_',r'<em>\1</em>',text )
        text =re .sub (r'^\* (.+)$',r'<ul><li>\1</li></ul>',text ,flags =re .MULTILINE )
        text =re .sub (r'^(- .+)$',r'<ul><li>\1</li></ul>',text ,flags =re .MULTILINE )
        text =re .sub (r'^(\d+)\. (.+)$',r'<ol><li>\2</li></ol>',text ,flags =re .MULTILINE )
        text =re .sub (r'\[(.+?)\]\((.+?)\)',r'<a href="\2">\1</a>',text )
        text =re .sub (r'`(.+?)`',r'<code>\1</code>',text )
        text =re .sub (r'```(.+?)```',r'<pre><code>\1</code></pre>',text ,flags =re .DOTALL )
        text =re .sub (r'^> (.+)$',r'<blockquote>\1</blockquote>',text ,flags =re .MULTILINE )
        paragraphs =[]
        for line in text .split ('\n'):
            if line .strip ()and not line .startswith ('<'):
                paragraphs .append (f'<p>{line }</p>')
            else :
                paragraphs .append (line )
        return '\n'.join (paragraphs )
    def _wrap_html (self ,html ):
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
                    line-height: 1.6;
                    padding: 20px;
                    max-width: 800px;
                    margin: 0 auto;
                }}
                h1, h2, h3, h4, h5, h6 {{
                    margin-top: 24px;
                    margin-bottom: 16px;
                    font-weight: 600;
                    color: #0366d6;
                }}
                h1 {{ font-size: 2em; padding-bottom: .3em; border-bottom: 1px solid #eaecef; }}
                h2 {{ font-size: 1.5em; padding-bottom: .3em; border-bottom: 1px solid #eaecef; }}
                h3 {{ font-size: 1.25em; }}
                h4 {{ font-size: 1em; }}
                p, blockquote, ul, ol, table {{
                    margin-bottom: 16px;
                }}
                code {{
                    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace;
                    padding: 0.2em 0.4em;
                    margin: 0;
                    font-size: 85%;
                    background-color: rgba(27, 31, 35, 0.05);
                    border-radius: 3px;
                }}
                pre {{
                    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace;
                    padding: 16px;
                    overflow: auto;
                    font-size: 85%;
                    line-height: 1.45;
                    background-color: #f6f8fa;
                    border-radius: 3px;
                }}
                pre code {{
                    background-color: transparent;
                    padding: 0;
                    margin: 0;
                    font-size: 100%;
                    word-break: normal;
                    white-space: pre;
                    border: 0;
                }}
                blockquote {{
                    padding: 0 1em;
                    color: #6a737d;
                    border-left: 0.25em solid #dfe2e5;
                }}
                ul, ol {{
                    padding-left: 2em;
                }}
                a {{
                    color: #0366d6;
                    text-decoration: none;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
                table {{
                    border-spacing: 0;
                    border-collapse: collapse;
                    width: 100%;
                    overflow: auto;
                }}
                table th, table td {{
                    padding: 6px 13px;
                    border: 1px solid #dfe2e5;
                }}
                table tr {{
                    background-color: #fff;
                    border-top: 1px solid #c6cbd1;
                }}
                table tr:nth-child(2n) {{
                    background-color: #f6f8fa;
                }}
                img {{
                    max-width: 100%;
                }}
                .code-block {{
                    margin-bottom: 16px;
                }}
                /* Стили для математических формул */
                .math-block {{
                    display: block;
                    margin: 1em 0;
                    text-align: center;
                    overflow-x: auto;
                }}
                .math-inline {{
                    display: inline-block;
                    vertical-align: middle;
                }}
                /* Стили для mermaid диаграмм */
                .mermaid {{
                    text-align: center;
                    margin: 1em 0;
                }}
                /* Стили для SVG */
                .svg-container {{
                    text-align: center;
                    margin: 1em 0;
                }}
                .svg-container svg {{
                    max-width: 100%;
                }}
            </style>
            <!-- Скрипт для рендеринга mermaid диаграмм -->
            <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
            <script>
                document.addEventListener('DOMContentLoaded', function() {{
                    mermaid.initialize({{
                        startOnLoad: true,
                        theme: 'default'
                    }});
                }});
            </script>
        </head>
        <body>
            {html }
        </body>
        </html>
        """
class FindReplaceDialog (QDialog ):
    def __init__ (self ,parent =None ):
        super ().__init__ (parent )
        self .parent =parent
        self .last_match =None
        self .setWindowIcon (QIcon ("Markdown_Editor.ico"))
        self .init_ui ()
    def init_ui (self ):
        self .setWindowTitle ("Поиск и замена")
        self .setMinimumWidth (400 )
        layout =QGridLayout ()
        layout .addWidget (QLabel ("Найти:"),0 ,0 )
        self .find_input =QLineEdit ()
        layout .addWidget (self .find_input ,0 ,1 )
        layout .addWidget (QLabel ("Заменить на:"),1 ,0 )
        self .replace_input =QLineEdit ()
        layout .addWidget (self .replace_input ,1 ,1 )
        options_group =QGroupBox ("Опции")
        options_layout =QVBoxLayout ()
        self .case_sensitive =QCheckBox ("Учитывать регистр")
        options_layout .addWidget (self .case_sensitive )
        self .whole_words =QCheckBox ("Только целые слова")
        options_layout .addWidget (self .whole_words )
        options_group .setLayout (options_layout )
        layout .addWidget (options_group ,2 ,0 ,1 ,2 )
        button_layout =QGridLayout ()
        find_button =QPushButton ("Найти")
        find_button .clicked .connect (self .find )
        button_layout .addWidget (find_button ,0 ,0 )
        find_next_button =QPushButton ("Найти далее")
        find_next_button .clicked .connect (self .find_next )
        button_layout .addWidget (find_next_button ,0 ,1 )
        replace_button =QPushButton ("Заменить")
        replace_button .clicked .connect (self .replace )
        button_layout .addWidget (replace_button ,1 ,0 )
        replace_all_button =QPushButton ("Заменить все")
        replace_all_button .clicked .connect (self .replace_all )
        button_layout .addWidget (replace_all_button ,1 ,1 )
        close_button =QPushButton ("Закрыть")
        close_button .clicked .connect (self .close )
        button_layout .addWidget (close_button ,2 ,0 ,1 ,2 )
        layout .addLayout (button_layout ,3 ,0 ,1 ,2 )
        self .setLayout (layout )
    def find (self ):
        editor =self .parent .editor
        text =self .find_input .text ()
        if not text :
            return
        flags =QTextDocument .FindFlag (0 )
        if self .case_sensitive .isChecked ():
            flags |=QTextDocument .FindFlag .FindCaseSensitively
        if self .whole_words .isChecked ():
            flags |=QTextDocument .FindFlag .FindWholeWords
        cursor =editor .textCursor ()
        if cursor .hasSelection ():
            cursor .setPosition (cursor .selectionStart ())
            editor .setTextCursor (cursor )
        found =editor .find (text ,flags )
        if not found :
            cursor .movePosition (QTextCursor .MoveOperation .Start )
            editor .setTextCursor (cursor )
            found =editor .find (text ,flags )
        if found :
            self .last_match =True
        else :
            self .last_match =False
            QMessageBox .information (self ,"Поиск",f"Текст '{text }' не найден")
    def find_next (self ):
        if self .last_match :
            self .find ()
        else :
            self .find ()
    def replace (self ):
        editor =self .parent .editor
        if editor .textCursor ().hasSelection ():
            editor .textCursor ().insertText (self .replace_input .text ())
            self .find ()
    def replace_all (self ):
        editor =self .parent .editor
        text =self .find_input .text ()
        replace_text =self .replace_input .text ()
        if not text :
            return
        cursor =editor .textCursor ()
        cursor_position =cursor .position ()
        cursor .movePosition (QTextCursor .MoveOperation .Start )
        editor .setTextCursor (cursor )
        flags =QTextDocument .FindFlag (0 )
        if self .case_sensitive .isChecked ():
            flags |=QTextDocument .FindFlag .FindCaseSensitively
        if self .whole_words .isChecked ():
            flags |=QTextDocument .FindFlag .FindWholeWords
        count =0
        while editor .find (text ,flags ):
            cursor =editor .textCursor ()
            cursor .insertText (replace_text )
            count +=1
        cursor .setPosition (cursor_position )
        editor .setTextCursor (cursor )
        QMessageBox .information (self ,"Замена",f"Заменено {count } вхождений")
class FileTreeView (QTreeView ):
    def __init__ (self ,parent =None ):
        super ().__init__ (parent )
        self .parent =parent
        self .init_ui ()
    def init_ui (self ):
        self .model =QFileSystemModel ()
        self .model .setReadOnly (False )
        self .model .setNameFilters (["*.md","*.текст","*.html","*.docx"])
        self .model .setNameFilterDisables (False )
        self .set_root_directory (os .path .expanduser ("~"))
        self .setModel (self .model )
        self .setAnimated (False )
        self .setIndentation (20 )
        self .setSortingEnabled (True )
        self .sortByColumn (0 ,Qt .SortOrder .AscendingOrder )
        for column in range (1 ,self .model .columnCount ()):
            self .hideColumn (column )
        self .doubleClicked .connect (self .on_double_click )
        self .setContextMenuPolicy (Qt .ContextMenuPolicy .CustomContextMenu )
        self .customContextMenuRequested .connect (self .show_context_menu )
    def set_root_directory (self ,path ):
        self .model .setRootPath (path )
        self .setRootIndex (self .model .index (path ))
    def on_double_click (self ,index ):
        path =self .model .filePath (index )
        if QFileInfo (path ).isFile ():
            self .parent .load_file (path )
    def show_context_menu (self ,position ):
        index =self .indexAt (position )
        if not index .isValid ():
            return
        path =self .model .filePath (index )
        info =QFileInfo (path )
        menu =QMenu ()
        if info .isFile ():
            open_action =QAction ("Открыть",self )
            open_action .triggered .connect (lambda :self .parent .load_file (path ))
            menu .addAction (open_action )
        if info .isDir ():
            new_file_action =QAction ("Новый файл",self )
            new_file_action .triggered .connect (lambda :self .create_new_file (path ))
            menu .addAction (new_file_action )
        menu .addSeparator ()
        rename_action =QAction ("Переименовать",self )
        rename_action .triggered .connect (lambda :self .rename_item (index ))
        menu .addAction (rename_action )
        delete_action =QAction ("Удалить",self )
        delete_action .triggered .connect (lambda :self .delete_item (index ))
        menu .addAction (delete_action )
        menu .exec_ (self .viewport ().mapToGlobal (position ))
    def create_new_file (self ,directory ):
        file_name ,ok =QInputDialog .getText (
        self ,"Новый файл","Имя файла:",text ="новый_файл.md"
        )
        if ok and file_name :
            file_path =os .path .join (directory ,file_name )
            try :
                with open (file_path ,'w',encoding ='utf-8')as f :
                    f .write ("")
                self .parent .load_file (file_path )
            except Exception as e :
                QMessageBox .warning (self ,"Ошибка",f"Не удалось создать файл: {str (e )}")
    def rename_item (self ,index ):
        path =self .model .filePath (index )
        info =QFileInfo (path )
        old_name =info .fileName ()
        new_name ,ok =QInputDialog .getText (
        self ,"Переименовать","Новое имя:",text =old_name
        )
        if ok and new_name and new_name !=old_name :
            new_path =os .path .join (os .path .dirname (path ),new_name )
            try :
                os .rename (path ,new_path )
                if self .parent .current_file ==path :
                    self .parent .current_file =new_path
                    self .parent .setWindowTitle (f"Markdown Editor - {new_name }")
            except Exception as e :
                QMessageBox .warning (self ,"Ошибка",f"Не удалось переименовать: {str (e )}")
    def delete_item (self ,index ):
        path =self .model .filePath (index )
        info =QFileInfo (path )
        name =info .fileName ()
        reply =QMessageBox .question (
        self ,"Удаление",
        f"Вы уверены, что хотите удалить {name }?",
        QMessageBox .StandardButton .Yes |QMessageBox .StandardButton .No
        )
        if reply ==QMessageBox .StandardButton .Yes :
            try :
                if info .isDir ():
                    import shutil
                    shutil .rmtree (path )
                else :
                    os .remove (path )
                    if self .parent .current_file ==path :
                        self .parent .new_file ()
            except Exception as e :
                QMessageBox .warning (self ,"Ошибка",f"Не удалось удалить: {str (e )}")
class MarkdownEditorWidget (QPlainTextEdit ):
    def __init__ (self ,parent =None ):
        super ().__init__ (parent )
        font =QFont ("Consolas",13 )
        self .setFont (font )
        self .setTabStopDistance (48 )
        self .line_number_area =LineNumberArea (self )
        self .highlighter =MarkdownHighlighter (self .document ())
        self .blockCountChanged .connect (self .update_line_number_area_width )
        self .updateRequest .connect (self .update_line_number_area )
        self .cursorPositionChanged .connect (self .highlight_current_line )
        self .cursorPositionChanged .connect (self .highlight_matching_bracket )
        self .update_line_number_area_width (0 )
        self .highlight_current_line ()
        self .setPlaceholderText ("Введите Markdown текст здесь...")
        self .setStyleSheet ("цвет фона: #1E1E1E; цвет: #D4D4D4; радиус границы: 10 пикселей; граница: нет;")
        QShortcut (QKeySequence ("Ctrl+Б"),self ,activated =self .shortcut_bold )
        QShortcut (QKeySequence ("Ctrl+I"),self ,activated =self .shortcut_italic )
        QShortcut (QKeySequence ("Ctrl+К"),self ,activated =self .shortcut_link )
        QShortcut (QKeySequence ("Ctrl+Shift+С"),self ,activated =self .shortcut_code )
        QShortcut (QKeySequence ("Ctrl+Shift+Л"),self ,activated =self .shortcut_list )
    def shortcut_bold (self ):
        self ._wrap_selection ("**","**")
    def shortcut_italic (self ):
        self ._wrap_selection ("*","*")
    def shortcut_link (self ):
        self ._wrap_selection ("[","](URL-адрес)")
    def shortcut_code (self ):
        self ._wrap_selection ("`","`")
    def shortcut_list (self ):
        cursor =self .textCursor ()
        cursor .movePosition (QTextCursor .MoveOperation .StartOfLine )
        cursor .insertText ("- ")
        self .setTextCursor (cursor )
    def _wrap_selection (self ,left ,right ):
        cursor =self .textCursor ()
        if cursor .hasSelection ():
            selected =cursor .selectedText ()
            cursor .insertText (f"{left }{selected }{right }")
        else :
            cursor .insertText (f"{left }{right }")
            cursor .movePosition (QTextCursor .MoveOperation .Left ,QTextCursor .MoveMode .MoveAnchor ,len (right ))
            self .setTextCursor (cursor )
    def highlight_matching_bracket (self ):
        extra =[]
        pairs ={'(':')','[':']','{':'}','"':'"',"'":"'",'`':'`','*':'*','_':'_'}
        cursor =self .textCursor ()
        pos =cursor .position ()
        doc =self .document ().toPlainText ()
        if pos >0 and pos <=len (doc ):
            char =doc [pos -1 ]
            if char in pairs :
                match =self ._find_matching (doc ,pos -1 ,char ,pairs [char ])
                if match is not None :
                    sel1 =QTextEdit .ExtraSelection ()
                    sel1 .cursor =self .textCursor ()
                    sel1 .cursor .setPosition (pos -1 )
                    sel1 .cursor .movePosition (QTextCursor .MoveOperation .Right ,QTextCursor .MoveMode .KeepAnchor ,1 )
                    sel1 .format .setBackground (QColor ("#39C5BB"))
                    sel2 =QTextEdit .ExtraSelection ()
                    sel2 .cursor =self .textCursor ()
                    sel2 .cursor .setPosition (match )
                    sel2 .cursor .movePosition (QTextCursor .MoveOperation .Right ,QTextCursor .MoveMode .KeepAnchor ,1 )
                    sel2 .format .setBackground (QColor ("#39C5BB"))
                    extra .extend ([sel1 ,sel2 ])
        self .setExtraSelections (self .extraSelections ()+extra )
    def _find_matching (self ,text ,pos ,left ,right ):
        if left ==right :
            for i in range (pos +1 ,len (text )):
                if text [i ]==right :
                    return i
            for i in range (pos -2 ,-1 ,-1 ):
                if text [i ]==left :
                    return i
            return None
        if left in '([{':
            depth =1
            for i in range (pos +1 ,len (text )):
                if text [i ]==left :
                    depth +=1
                elif text [i ]==right :
                    depth -=1
                    if depth ==0 :
                        return i
        if right in ')]}':
            depth =1
            for i in range (pos -2 ,-1 ,-1 ):
                if text [i ]==right :
                    depth +=1
                elif text [i ]==left :
                    depth -=1
                    if depth ==0 :
                        return i
        return None
    def line_number_area_width (self ):
        digits =1
        max_num =max (1 ,self .blockCount ())
        while max_num >=10 :
            max_num /=10
            digits +=1
        space =3 +self .fontMetrics ().horizontalAdvance ('9')*digits
        return space
    def update_line_number_area_width (self ,_ ):
        self .setViewportMargins (self .line_number_area_width (),0 ,0 ,0 )
    def update_line_number_area (self ,rect ,dy ):
        if dy :
            self .line_number_area .scroll (0 ,dy )
        else :
            self .line_number_area .update (0 ,rect .y (),self .line_number_area .width (),rect .height ())
        if rect .contains (self .viewport ().rect ()):
            self .update_line_number_area_width (0 )
    def resizeEvent (self ,event ):
        super ().resizeEvent (event )
        cr =self .contentsRect ()
        self .line_number_area .setGeometry (QRect (cr .left (),cr .top (),self .line_number_area_width (),cr .height ()))
    def line_number_area_paint_event (self ,event ):
        painter =QPainter (self .line_number_area )
        painter .fillRect (event .rect (),QColor ("#23272E"))
        block =self .firstVisibleBlock ()
        block_number =block .blockNumber ()
        top =self .blockBoundingGeometry (block ).translated (self .contentOffset ()).top ()
        bottom =top +self .blockBoundingRect (block ).height ()
        while block .isValid ()and top <=event .rect ().bottom ():
            if block .isVisible ()and bottom >=event .rect ().top ():
                number =str (block_number +1 )
                painter .setPen (QColor ("#444B53"))
                rect =QRect (0 ,int (top ),self .line_number_area .width (),self .fontMetrics ().height ())
                painter .drawText (rect ,Qt .AlignmentFlag .AlignRight ,number )
            block =block .next ()
            top =bottom
            bottom =top +self .blockBoundingRect (block ).height ()
            block_number +=1
    def highlight_current_line (self ):
        extra_selections =[]
        if not self .isReadOnly ():
            selection =QTextEdit .ExtraSelection ()
            line_color =QColor ("#23272E").lighter (120 )
            selection .format .setBackground (line_color )
            selection .format .setProperty (QTextFormat .Property .FullWidthSelection ,True )
            selection .cursor =self .textCursor ()
            selection .cursor .clearSelection ()
            extra_selections .append (selection )
        self .setExtraSelections (extra_selections )
class TranslatorThread (QThread ):
    progress_signal =Signal (int ,str )
    finished_signal =Signal (bool ,str )
    def __init__ (self ,translator ,md_content ,output_folder ,base_filename ,
    main_lang_code ,selected_langs ,parent =None ):
        super ().__init__ (parent )
        self .translator =translator
        self .md_content =md_content
        self .output_folder =output_folder
        self .base_filename =base_filename
        self .main_lang_code =main_lang_code
        self .selected_langs =selected_langs
        self .is_cancelled =False
        self .base_dir =os .path .dirname (output_folder )
    def run (self ):
        try :
            is_temp_file =False
            if self .translator .current_file :
                is_temp_file =(self .translator .current_file ==os .path .join (os .path .dirname (os .path .abspath (__file__ )),"temporary.md"))
            blocks =self .translator .parse_markdown (self .md_content )
            translated_files =[]
            progress_value =0
            total_langs =len (self .selected_langs )
            for lang_name ,lang_code in self .selected_langs .items ():
                if self .is_cancelled :
                    break
                self .progress_signal .emit (
                int (progress_value /total_langs *100 ),
                f"Перевод на {lang_name }..."
                )
                translated_blocks =self .translator .translate_blocks (blocks ,lang_code )
                translated_md =self .translator .reconstruct_markdown (translated_blocks )
                output_filename =f"README_{lang_code }.md"
                output_path =os .path .join (self .output_folder ,output_filename )
                with open (output_path ,'w',encoding ='utf-8')as file :
                    file .write (translated_md )
                translated_files .append ((lang_name ,output_filename ))
                progress_value +=1
            if not self .is_cancelled :
                main_output_path =os .path .join (self .base_dir ,"README.md")
                if is_temp_file or not self .translator .current_file :
                    content =self .md_content
                else :
                    try :
                        with open (self .translator .current_file ,'r',encoding ='utf-8')as src_file :
                            content =src_file .read ()
                    except :
                        content =self .md_content
                with open (main_output_path ,'w',encoding ='utf-8')as dest_file :
                    dest_file .write (content )
                with open (main_output_path ,'a',encoding ='utf-8')as file :
                    file .write ("\n\n## Переводы\n\n")
                    for lang_name ,filename in translated_files :
                        file .write (f"- [{lang_name }](./translations/{filename })\n")
            if self .is_cancelled :
                self .finished_signal .emit (False ,"Перевод был отменен")
            else :
                self .finished_signal .emit (True ,f"Перевод завершен. Главный файл сохранен как README.md, переводы в папке translations")
        except Exception as e :
            import traceback
            traceback_str =traceback .format_exc ()
            self .finished_signal .emit (False ,f"Ошибка при переводе: {str (e )}\n{traceback_str }")
    def cancel (self ):
        self .is_cancelled =True
class TranslatorDialog (QDialog ):
    def __init__ (self ,parent =None ):
        super ().__init__ (parent )
        self .parent =parent
        self .setWindowTitle ("Перевод Markdown")
        self .setWindowIcon (QIcon ("Markdown_Editor.ico"))
        self .setMinimumSize (500 ,400 )
        self .languages ={
        "Русский":"ru",
        "Английский":"en",
        "Испанский":"es",
        "Китайский":"zh",
        "Хинди":"hi",
        "Арабский":"ar",
        "Бенгальский":"bn",
        "Португальский":"pt",
        "Индонезийский":"id",
        "Французский":"fr",
        "Японский":"ja",
        "Немецкий":"de",
        "Урду":"ur",
        "Итальянский":"it",
        "Турецкий":"tr"
        }
        self .setup_ui ()
    def setup_ui (self ):
        main_layout =QVBoxLayout (self )
        title_label =QLabel ("Перевод Markdown-файла")
        title_label .setStyleSheet ("размер шрифта: 16pt; начертание шрифта: жирный; поле внизу: 10 пикселей;")
        main_layout .addWidget (title_label )
        description_label =QLabel (
        "Выберите основной язык файла и языки, на которые нужно перевести документ."
        )
        description_label .setWordWrap (True )
        main_layout .addWidget (description_label )
        lang_group =QGroupBox ("Настройки перевода")
        lang_group_layout =QVBoxLayout ()
        main_lang_layout =QHBoxLayout ()
        main_lang_layout .addWidget (QLabel ("Основной язык:"))
        self .main_language =QComboBox ()
        for lang in self .languages .keys ():
            self .main_language .addItem (lang )
        self .main_language .setCurrentText ("Русский")
        main_lang_layout .addWidget (self .main_language )
        main_lang_layout .addStretch ()
        lang_group_layout .addLayout (main_lang_layout )
        lang_group_layout .addWidget (QLabel ("Языки для перевода:"))
        scroll_area =QScrollArea ()
        scroll_area .setWidgetResizable (True )
        scroll_widget =QWidget ()
        scroll_layout =QVBoxLayout (scroll_widget )
        self .lang_list =QListWidget ()
        self .lang_list .setMinimumHeight (150 )
        for lang in self .languages .keys ():
            item =QCheckBox (lang )
            if lang =="Английский":
                item .setChecked (True )
            list_item =QListWidgetItem ()
            self .lang_list .addItem (list_item )
            self .lang_list .setItemWidget (list_item ,item )
        scroll_layout .addWidget (self .lang_list )
        scroll_area .setWidget (scroll_widget )
        lang_group_layout .addWidget (scroll_area )
        select_buttons_layout =QHBoxLayout ()
        select_all_button =QPushButton ("Выбрать все")
        select_all_button .clicked .connect (self .select_all_languages )
        select_none_button =QPushButton ("Снять выбор")
        select_none_button .clicked .connect (self .select_no_languages )
        select_buttons_layout .addWidget (select_all_button )
        select_buttons_layout .addWidget (select_none_button )
        lang_group_layout .addLayout (select_buttons_layout )
        lang_group .setLayout (lang_group_layout )
        main_layout .addWidget (lang_group )
        buttons_layout =QHBoxLayout ()
        self .translate_button =QPushButton ("Перевести")
        self .translate_button .setMinimumHeight (40 )
        self .translate_button .setStyleSheet ("начертание шрифта: жирный;")
        self .translate_button .clicked .connect (self .accept )
        cancel_button =QPushButton ("Отмена")
        cancel_button .clicked .connect (self .reject )
        buttons_layout .addWidget (cancel_button )
        buttons_layout .addWidget (self .translate_button )
        main_layout .addLayout (buttons_layout )
    def select_all_languages (self ):
        for i in range (self .lang_list .count ()):
            item =self .lang_list .item (i )
            checkbox =self .lang_list .itemWidget (item )
            checkbox .setChecked (True )
    def select_no_languages (self ):
        for i in range (self .lang_list .count ()):
            item =self .lang_list .item (i )
            checkbox =self .lang_list .itemWidget (item )
            checkbox .setChecked (False )
    def get_selected_languages (self ):
        selected_langs ={}
        for i in range (self .lang_list .count ()):
            item =self .lang_list .item (i )
            checkbox =self .lang_list .itemWidget (item )
            if checkbox .isChecked ():
                lang_name =checkbox .text ()
                lang_code =self .languages [lang_name ]
                selected_langs [lang_name ]=lang_code
        return selected_langs
    def get_main_language (self ):
        main_lang_name =self .main_language .currentText ()
        main_lang_code =self .languages [main_lang_name ]
        return main_lang_name ,main_lang_code
class MarkdownEditor (QMainWindow ):
    def __init__ (self ):
        super ().__init__ ()
        self .setWindowTitle ("Редактор уценки")
        self .setWindowIcon (QIcon ("Markdown_Editor.ico"))
        self .setMinimumSize (800 ,600 )
        self .current_file =None
        self .file_changed =False
        self .settings =QSettings ("MarkdownEditor","MarkdownEditor")
        self .central_widget =QWidget ()
        self .setCentralWidget (self .central_widget )
        self .main_layout =QHBoxLayout (self .central_widget )
        self .main_layout .setContentsMargins (0 ,0 ,0 ,0 )
        self .splitter =QSplitter (Qt .Orientation .Horizontal )
        self .editor =MarkdownEditorWidget ()
        self .preview =QTextBrowser ()
        self .preview .setOpenExternalLinks (True )
        self .markdown_renderer =MarkdownRenderer ()
        self .splitter .addWidget (self .editor )
        self .splitter .addWidget (self .preview )
        self .splitter .setSizes ([400 ,400 ])
        self .main_layout .addWidget (self .splitter )
        self .create_file_tree ()
        self .menu_bar =QMenuBar (self )
        self .setMenuBar (self .menu_bar )
        self .create_menu ()
        self .create_toolbar ()
        self .create_statusbar ()
        self .editor .textChanged .connect (self .update_preview )
        self .editor .textChanged .connect (self .handle_text_changed )
        self .autosave_timer =QTimer (self )
        self .autosave_timer .timeout .connect (self .autosave )
        self .autosave_timer .start (10000 )
        self .load_settings ()
        self .editor .setPlainText ("""# Добро пожаловать в Markdown Editor!
Это **простой** редактор Markdown с *превью* в реальном времени.
## Возможности:
- Разделенный экран
- Подсветка синтаксиса
- Экспорт в разные форматы
```python
def hello_world():
    print("Hello, Markdown!")
```
[Узнать больше о Markdown](https://www.markdownguide.org/)
""")
        self .update_preview ()
    def create_file_tree (self ):
        self .file_tree =FileTreeView (self )
        self .file_tree_dock =QDockWidget ("Файлы",self )
        self .file_tree_dock .setWidget (self .file_tree )
        self .file_tree_dock .setAllowedAreas (Qt .DockWidgetArea .LeftDockWidgetArea |Qt .DockWidgetArea .RightDockWidgetArea )
        self .addDockWidget (Qt .DockWidgetArea .LeftDockWidgetArea ,self .file_tree_dock )
    def create_menu (self ):
        file_menu =self .menu_bar .addMenu ("&Файл")
        new_action =QAction ("&Новый",self )
        new_action .setShortcut ("Ctrl+Н")
        new_action .triggered .connect (self .new_file )
        file_menu .addAction (new_action )
        open_action =QAction ("&Открыть...",self )
        open_action .setShortcut ("Ctrl+О")
        open_action .triggered .connect (self .open_file )
        file_menu .addAction (open_action )
        self .recent_files_menu =QMenu ("Недавние файлы",self )
        file_menu .addMenu (self .recent_files_menu )
        self .update_recent_files_menu ()
        file_menu .addSeparator ()
        save_action =QAction ("&Сохранить",self )
        save_action .setShortcut ("Ctrl+S")
        save_action .triggered .connect (self .save_file )
        file_menu .addAction (save_action )
        save_as_action =QAction ("Сохранить &как...",self )
        save_as_action .setShortcut ("Ctrl+Shift+S")
        save_as_action .triggered .connect (self .save_file_as )
        file_menu .addAction (save_as_action )
        file_menu .addSeparator ()
        translate_action =QAction ("&Перевести документ...",self )
        translate_action .setShortcut ("Ctrl+Т")
        translate_action .triggered .connect (self .translate_current_file )
        file_menu .addAction (translate_action )
        file_menu .addSeparator ()
        export_menu =QMenu ("&Экспорт",self )
        export_html_action =QAction ("Экспорт в &HTML...",self )
        export_html_action .triggered .connect (self .export_html )
        export_pdf_action =QAction ("Экспорт в &PDF...",self )
        export_pdf_action .triggered .connect (self .export_pdf )
        export_docx_action =QAction ("Экспорт в &DOCX...",self )
        export_docx_action .triggered .connect (self .export_docx )
        export_menu .addAction (export_html_action )
        export_menu .addAction (export_pdf_action )
        export_menu .addAction (export_docx_action )
        file_menu .addMenu (export_menu )
        file_menu .addSeparator ()
        exit_action =QAction ("&Выход",self )
        exit_action .setShortcut ("Ctrl+Q")
        exit_action .triggered .connect (self .close )
        file_menu .addAction (exit_action )
        edit_menu =self .menu_bar .addMenu ("&Правка")
        undo_action =QAction ("&Отменить",self )
        undo_action .setShortcut ("Ctrl+Z")
        undo_action .triggered .connect (self .editor .undo )
        edit_menu .addAction (undo_action )
        redo_action =QAction ("&Повторить",self )
        redo_action .setShortcut ("Ctrl+Shift+Z")
        redo_action .triggered .connect (self .editor .redo )
        edit_menu .addAction (redo_action )
        edit_menu .addSeparator ()
        cut_action =QAction ("&Вырезать",self )
        cut_action .setShortcut ("Ctrl+X")
        cut_action .triggered .connect (self .editor .cut )
        edit_menu .addAction (cut_action )
        copy_action =QAction ("&Копировать",self )
        copy_action .setShortcut ("Ctrl+С")
        copy_action .triggered .connect (self .editor .copy )
        edit_menu .addAction (copy_action )
        paste_action =QAction ("&Вставить",self )
        paste_action .setShortcut ("Ctrl+V")
        paste_action .triggered .connect (self .editor .paste )
        edit_menu .addAction (paste_action )
        edit_menu .addSeparator ()
        find_action =QAction ("&Найти...",self )
        find_action .setShortcut ("Ctrl+Ф")
        find_action .triggered .connect (self .show_find_dialog )
        edit_menu .addAction (find_action )
        replace_action =QAction ("&Заменить...",self )
        replace_action .setShortcut ("Ctrl+H")
        replace_action .triggered .connect (self .show_replace_dialog )
        edit_menu .addAction (replace_action )
        view_menu =self .menu_bar .addMenu ("&Вид")
        editor_only_action =QAction ("&Только редактор",self )
        editor_only_action .triggered .connect (self .show_editor_only )
        view_menu .addAction (editor_only_action )
        preview_only_action =QAction ("&Только превью",self )
        preview_only_action .triggered .connect (self .show_preview_only )
        view_menu .addAction (preview_only_action )
        split_view_action =QAction ("&Разделенный вид",self )
        split_view_action .triggered .connect (self .show_split_view )
        view_menu .addAction (split_view_action )
        view_menu .addSeparator ()
        file_tree_action =QAction ("Дерево файлов",self )
        file_tree_action .setCheckable (True )
        file_tree_action .setChecked (True )
        file_tree_action .triggered .connect (self .toggle_file_tree )
        view_menu .addAction (file_tree_action )
        project_menu =self .menu_bar .addMenu ("&Проект")
        open_dir_action =QAction ("Открыть директорию...",self )
        open_dir_action .triggered .connect (self .open_directory )
        project_menu .addAction (open_dir_action )
    def create_toolbar (self ):
        self .toolbar =QToolBar ("Панель инструментов")
        self .toolbar .setIconSize (QSize (18 ,18 ))
        self .toolbar .setStyleSheet ("QToolBar { spacing: 2px; padding: 2px 4px; }")
        self .addToolBar (self .toolbar )
        bold_action =QAction ("Ж",self )
        bold_action .setShortcut ("Ctrl+Б")
        bold_action .triggered .connect (lambda :self .insert_markdown_tag ("**","**"))
        self .toolbar .addAction (bold_action )
        italic_action =QAction ("К",self )
        italic_action .setShortcut ("Ctrl+I")
        italic_action .triggered .connect (lambda :self .insert_markdown_tag ("*","*"))
        self .toolbar .addAction (italic_action )
        h1_action =QAction ("H1",self )
        h1_action .triggered .connect (lambda :self .insert_heading (1 ))
        self .toolbar .addAction (h1_action )
        h2_action =QAction ("H2",self )
        h2_action .triggered .connect (lambda :self .insert_heading (2 ))
        self .toolbar .addAction (h2_action )
        h3_action =QAction ("H3",self )
        h3_action .triggered .connect (lambda :self .insert_heading (3 ))
        self .toolbar .addAction (h3_action )
        self .toolbar .addSeparator ()
        list_action =QAction ("•",self )
        list_action .triggered .connect (lambda :self .insert_list ())
        self .toolbar .addAction (list_action )
        numbered_list_action =QAction ("1.",self )
        numbered_list_action .triggered .connect (lambda :self .insert_numbered_list ())
        self .toolbar .addAction (numbered_list_action )
        self .toolbar .addSeparator ()
        link_action =QAction ("🔗",self )
        link_action .triggered .connect (lambda :self .insert_markdown_tag ("[","](URL-адрес)"))
        self .toolbar .addAction (link_action )
        image_action =QAction ("🖼",self )
        image_action .triggered .connect (lambda :self .insert_markdown_tag ("![","](URL-адрес)"))
        self .toolbar .addAction (image_action )
        code_action =QAction ("<>",self )
        code_action .triggered .connect (lambda :self .insert_markdown_tag ("`","`"))
        self .toolbar .addAction (code_action )
        code_block_action =QAction ("БК",self )
        code_block_action .triggered .connect (lambda :self .insert_code_block ())
        self .toolbar .addAction (code_block_action )
        self .toolbar .addSeparator ()
        quote_action =QAction ("❝",self )
        quote_action .triggered .connect (lambda :self .insert_quote ())
        self .toolbar .addAction (quote_action )
        hr_action =QAction ("—",self )
        hr_action .triggered .connect (lambda :self .insert_horizontal_rule ())
        self .toolbar .addAction (hr_action )
        self .toolbar .addSeparator ()
        latex_inline_action =QAction ("∑",self )
        latex_inline_action .setToolTip ("Вставить инлайн формулу LaTeX")
        latex_inline_action .triggered .connect (lambda :self .insert_markdown_tag ("$","$"))
        self .toolbar .addAction (latex_inline_action )
        latex_block_action =QAction ("∑∫",self )
        latex_block_action .setToolTip ("Вставить блок формул LaTeX")
        latex_block_action .triggered .connect (self .insert_latex_block )
        self .toolbar .addAction (latex_block_action )
        mermaid_action =QAction ("📊",self )
        mermaid_action .setToolTip ("Вставить диаграмму mermaid")
        mermaid_action .triggered .connect (self .insert_mermaid_diagram )
        self .toolbar .addAction (mermaid_action )
        svg_action =QAction ("SVG",self )
        svg_action .setToolTip ("Вставить SVG")
        svg_action .triggered .connect (self .insert_svg )
        self .toolbar .addAction (svg_action )
        self .toolbar .addSeparator ()
    def create_statusbar (self ):
        self .statusBar ().showMessage ("Готово")
    def update_preview (self ):
        markdown_text =self .editor .toPlainText ()
        html =self .markdown_renderer .render (markdown_text )
        self .preview .setHtml (html )
    def show_editor_only (self ):
        self .splitter .setSizes ([1 ,0 ])
    def show_preview_only (self ):
        self .splitter .setSizes ([0 ,1 ])
    def show_split_view (self ):
        self .splitter .setSizes ([1 ,1 ])
    def show_about (self ):
        msg =QMessageBox (self )
        msg .setWindowIcon (QIcon ("Markdown_Editor.ico"))
        msg .setIcon (QMessageBox .Icon .Information )
        msg .setWindowTitle ("О программе Markdown Editor")
        msg .setText ("Markdown Editor - простой редактор Markdown с превью в реальном времени.\n\nВерсия: 0.1\nАвтор: Your Name\nЛицензия: MIT")
        msg .exec ()
    def insert_markdown_tag (self ,start_tag ,end_tag ):
        cursor =self .editor .textCursor ()
        selected_text =cursor .selectedText ()
        if selected_text :
            cursor .insertText (f"{start_tag }{selected_text }{end_tag }")
        else :
            cursor .insertText (f"{start_tag }{end_tag }")
            cursor .movePosition (QTextCursor .MoveOperation .Left ,QTextCursor .MoveMode .MoveAnchor ,len (end_tag ))
            self .editor .setTextCursor (cursor )
        self .editor .setFocus ()
    def insert_heading (self ,level ):
        cursor =self .editor .textCursor ()
        cursor .movePosition (QTextCursor .MoveOperation .StartOfLine )
        line_text =cursor .block ().text ()
        if line_text .startswith ('#'):
            for i in range (len (line_text )):
                if line_text [i ]=='#':
                    cursor .deleteChar ()
                elif line_text [i ]==' ':
                    cursor .deleteChar ()
                    break
                else :
                    break
        cursor .insertText ('#'*level +' ')
        self .editor .setFocus ()
    def insert_list (self ):
        cursor =self .editor .textCursor ()
        cursor .movePosition (QTextCursor .MoveOperation .StartOfLine )
        cursor .insertText ("- ")
        self .editor .setFocus ()
    def insert_numbered_list (self ):
        cursor =self .editor .textCursor ()
        cursor .movePosition (QTextCursor .MoveOperation .StartOfLine )
        cursor .insertText ("1. ")
        self .editor .setFocus ()
    def insert_code_block (self ):
        cursor =self .editor .textCursor ()
        cursor .insertText ("```\n")
        cursor .insertText ("\n```")
        cursor .movePosition (QTextCursor .MoveOperation .Up )
        cursor .movePosition (QTextCursor .MoveOperation .EndOfLine )
        self .editor .setTextCursor (cursor )
        self .editor .setFocus ()
    def insert_quote (self ):
        cursor =self .editor .textCursor ()
        cursor .movePosition (QTextCursor .MoveOperation .StartOfLine )
        cursor .insertText ("> ")
        self .editor .setFocus ()
    def insert_horizontal_rule (self ):
        cursor =self .editor .textCursor ()
        cursor .insertText ("\n---\n")
        self .editor .setFocus ()
    def handle_text_changed (self ):
        self .file_changed =True
        if self .current_file :
            self .setWindowTitle (f"Markdown Editor - {os .path .basename (self .current_file )} *")
        else :
            self .setWindowTitle ("Редактор разметки *")
    def new_file (self ):
        if self .maybe_save ():
            self .editor .clear ()
            self .current_file =None
            self .file_changed =False
            self .setWindowTitle ("Редактор уценки")
    def open_file (self ):
        if self .maybe_save ():
            file_path ,_ =QFileDialog .getOpenFileName (
            self ,"Открыть файл","",
            "Файлы Markdown (*.md);;Текстовые файлы (*.txt);;Все файлы (*)"
            )
            if file_path :
                self .load_file (file_path )
    def load_file (self ,file_path ):
        try :
            with open (file_path ,'r',encoding ='utf-8')as file :
                self .editor .setPlainText (file .read ())
            self .current_file =file_path
            self .file_changed =False
            self .setWindowTitle (f"Markdown Editor - {os .path .basename (file_path )}")
            self .statusBar ().showMessage (f"Файл {os .path .basename (file_path )} загружен")
            recent_files =self .settings .value ("recentFiles",[])
            if file_path in recent_files :
                recent_files .remove (file_path )
            recent_files .insert (0 ,file_path )
            recent_files =recent_files [:10 ]
            self .settings .setValue ("recentFiles",recent_files )
            self .update_recent_files_menu ()
            return True
        except Exception as e :
            QMessageBox .warning (self ,"Ошибка",f"Не удалось открыть файл: {str (e )}")
            return False
    def save_file (self ):
        if not self .current_file :
            return self .save_file_as ()
        reply =QMessageBox .question (
        self ,"Перевод",
        "Желаете ли вы добавить перевод для этого файла?",
        QMessageBox .StandardButton .Yes |QMessageBox .StandardButton .No
        )
        if reply ==QMessageBox .StandardButton .Yes :
            return self .save_and_translate ()
        else :
            return self .save_to_file (self .current_file )
    def save_file_as (self ):
        reply =QMessageBox .question (
        self ,"Перевод",
        "Желаете ли вы добавить перевод для этого файла?",
        QMessageBox .StandardButton .Yes |QMessageBox .StandardButton .No
        )
        if reply ==QMessageBox .StandardButton .Yes :
            return self .save_and_translate ()
        else :
            file_path ,_ =QFileDialog .getSaveFileName (
            self ,"Сохранить файл","",
            "Файлы Markdown (*.md);;Текстовые файлы (*.txt);;Все файлы (*)"
            )
            if file_path :
                return self .save_to_file (file_path )
        return False
    def save_and_translate (self ):
        temp_dir =os .path .dirname (os .path .abspath (__file__ ))
        temp_file =os .path .join (temp_dir ,"temporary.md")
        try :
            with open (temp_file ,'w',encoding ='utf-8')as file :
                file .write (self .editor .toPlainText ())
            original_file =self .current_file
            self .current_file =temp_file
            self .translate_current_file ()
            self .current_file =original_file
            if os .path .exists (temp_file ):
                os .remove (temp_file )
            return True
        except Exception as e :
            QMessageBox .critical (self ,"Ошибка",f"Не удалось создать временный файл: {str (e )}")
            return False
    def save_to_file (self ,file_path ):
        try :
            with open (file_path ,'w',encoding ='utf-8')as file :
                file .write (self .editor .toPlainText ())
            self .current_file =file_path
            self .file_changed =False
            self .setWindowTitle (f"Markdown Editor - {os .path .basename (file_path )}")
            self .statusBar ().showMessage (f"Файл {os .path .basename (file_path )} сохранен")
            recent_files =self .settings .value ("recentFiles",[])
            if file_path in recent_files :
                recent_files .remove (file_path )
            recent_files .insert (0 ,file_path )
            recent_files =recent_files [:10 ]
            self .settings .setValue ("recentFiles",recent_files )
            self .update_recent_files_menu ()
            return True
        except Exception as e :
            QMessageBox .warning (self ,"Ошибка",f"Не удалось сохранить файл: {str (e )}")
            return False
    def autosave (self ):
        if self .file_changed and self .current_file :
            self .save_to_file (self .current_file )
            self .statusBar ().showMessage ("Автосохранение выполнено",2000 )
    def export_html (self ):
        file_path ,_ =QFileDialog .getSaveFileName (
        self ,"Экспорт в HTML","",
        "HTML-файлы (*.html);;Все файлы (*)"
        )
        if file_path :
            try :
                html =self .markdown_renderer .render (self .editor .toPlainText ())
                with open (file_path ,'w',encoding ='utf-8')as file :
                    file .write (html )
                self .statusBar ().showMessage (f"Экспорт в HTML выполнен: {os .path .basename (file_path )}")
            except Exception as e :
                QMessageBox .warning (self ,"Ошибка",f"Не удалось экспортировать в HTML: {str (e )}")
    def export_pdf (self ):
        file_path ,_ =QFileDialog .getSaveFileName (
        self ,"Экспорт в PDF","",
        "PDF-файлы (*.pdf);;Все файлы (*)"
        )
        if file_path :
            try :
                from PyQt6 .QtPrintSupport import QPrinter
                printer =QPrinter (QPrinter .PrinterMode .HighResolution )
                printer .setOutputFormat (QPrinter .OutputFormat .PdfFormat )
                printer .setOutputFileName (file_path )
                self .preview .document ().print_ (printer )
                self .statusBar ().showMessage (f"Экспорт в PDF выполнен: {os .path .basename (file_path )}")
            except Exception as e :
                QMessageBox .warning (self ,"Ошибка",f"Не удалось экспортировать в PDF: {str (e )}")
    def export_docx (self ):
        file_path ,_ =QFileDialog .getSaveFileName (
        self ,"Экспорт в DOCX","",
        "Файлы Word (*.docx);;Все файлы (*)"
        )
        if file_path :
            try :
                try :
                    import docx
                except ImportError :
                    QMessageBox .warning (
                    self ,"Ошибка",
                    "Для экспорта в DOCX требуется библиотека python-docx.\n"
                    "Установите ее командой: pip install python-docx"
                    )
                    return
                from docx import Document
                document =Document ()
                html_content =self .preview .toHtml ()
                document .add_heading ("Документ Markdown",0 )
                markdown_text =self .editor .toPlainText ()
                lines =markdown_text .split ('\n')
                for line in lines :
                    if line .startswith ('# '):
                        document .add_heading (line [2 :],level =1 )
                    elif line .startswith ('## '):
                        document .add_heading (line [3 :],level =2 )
                    elif line .startswith ('### '):
                        document .add_heading (line [4 :],level =3 )
                    elif line .startswith ('#### '):
                        document .add_heading (line [5 :],level =4 )
                    elif line .startswith ('- ')or line .startswith ('* '):
                        document .add_paragraph (line [2 :],style ='Список маркеров')
                    elif re .match (r'^\d+\.\s',line ):
                        document .add_paragraph (re .sub (r'^\d+\.\s','',line ),style ='Номер списка')
                    elif line .strip ():
                        line =re .sub (r'\*\*(.*?)\*\*',r'\1',line )
                        line =re .sub (r'\*(.*?)\*',r'\1',line )
                        line =re .sub (r'`(.*?)`',r'\1',line )
                        line =re .sub (r'\[(.*?)\]\(.*?\)',r'\1',line )
                        document .add_paragraph (line )
                    else :
                        document .add_paragraph ('')
                document .save (file_path )
                self .statusBar ().showMessage (f"Экспорт в DOCX выполнен: {os .path .basename (file_path )}")
            except Exception as e :
                QMessageBox .warning (self ,"Ошибка",f"Не удалось экспортировать в DOCX: {str (e )}")
    def maybe_save (self ):
        if not self .file_changed :
            return True
        reply =QMessageBox .question (
        self ,"Сохранение изменений",
        "Документ был изменен. Сохранить изменения?",
        QMessageBox .StandardButton .Save |QMessageBox .StandardButton .Discard |QMessageBox .StandardButton .Cancel
        )
        if reply ==QMessageBox .StandardButton .Save :
            return self .save_file ()
        elif reply ==QMessageBox .StandardButton .Cancel :
            return False
        return True
    def closeEvent (self ,event ):
        if self .maybe_save ():
            self .save_settings ()
            event .accept ()
        else :
            event .ignore ()
    def load_settings (self ):
        geometry =self .settings .value ("geometry")
        if geometry :
            self .restoreGeometry (geometry )
        splitter_sizes =self .settings .value ("splitterSizes")
        if splitter_sizes and isinstance (splitter_sizes ,list )and all (isinstance (size ,int )for size in splitter_sizes ):
            self .splitter .setSizes (splitter_sizes )
        last_directory =self .settings .value ("lastDirectory")
        if last_directory and isinstance (last_directory ,str )and os .path .exists (last_directory ):
            self .file_tree .set_root_directory (last_directory )
    def save_settings (self ):
        self .settings .setValue ("geometry",self .saveGeometry ())
        self .settings .setValue ("splitterSizes",self .splitter .sizes ())
        self .update_recent_files_menu ()
    def show_find_dialog (self ):
        dialog =FindReplaceDialog (self )
        dialog .setWindowIcon (QIcon ("Markdown_Editor.ico"))
        dialog .replace_input .hide ()
        dialog .layout ().itemAtPosition (1 ,0 ).widget ().hide ()
        dialog .exec ()
    def show_replace_dialog (self ):
        dialog =FindReplaceDialog (self )
        dialog .setWindowIcon (QIcon ("Markdown_Editor.ico"))
        dialog .exec ()
    def update_recent_files_menu (self ):
        self .recent_files_menu .clear ()
        recent_files =self .settings .value ("recentFiles",[])
        for file_path in recent_files :
            if os .path .exists (file_path ):
                action =QAction (os .path .basename (file_path ),self )
                action .setData (file_path )
                action .triggered .connect (self .open_recent_file )
                self .recent_files_menu .addAction (action )
    def open_recent_file (self ):
        action =self .sender ()
        if action :
            file_path =action .data ()
            if os .path .exists (file_path ):
                if self .maybe_save ():
                    self .load_file (file_path )
    def toggle_file_tree (self ):
        if self .file_tree_dock .isVisible ():
            self .file_tree_dock .hide ()
        else :
            self .file_tree_dock .show ()
    def open_directory (self ):
        directory =QFileDialog .getExistingDirectory (
        self ,"Открыть директорию","",QFileDialog .Option .ShowDirsOnly
        )
        if directory :
            self .file_tree .set_root_directory (directory )
            self .settings .setValue ("lastDirectory",directory )
    def parse_markdown (self ,md_content ):
        blocks =[]
        code_block_pattern =r'```(?:[^\n]*)\n(.*?)```'
        inline_code_pattern =r'`([^`]+)`'
        link_pattern =r'\[(.*?)\]\((.*?)\)'
        image_pattern =r'!\[(.*?)\]\((.*?)\)'
        header_pattern =r'^(#{1,6})\s+(.*?)$'
        html_tag_pattern =r'<([a-zA-Z][a-zA-Z0-9]*)[^>]*>.*?</\1>'
        hr_pattern =r'^([-*_])\s*\1\s*\1\s*[\1\s]*$'
        list_item_pattern =r'^(\s*)([*+-]|\d+\.)\s+(.*?)$'
        last_end =0
        for match in re .finditer (code_block_pattern ,md_content ,re .DOTALL ):
            start ,end =match .span ()
            if start >last_end :
                text_before =md_content [last_end :start ]
                if text_before .strip ():
                    blocks .append (('text',text_before ))
            blocks .append (('code',match .group (0 )))
            last_end =end
        if last_end <len (md_content ):
            blocks .append (('text',md_content [last_end :]))
        processed_blocks =[]
        for block_type ,content in blocks :
            if block_type =='code':
                processed_blocks .append ((block_type ,content ))
            else :
                lines =content .split ('\n')
                current_text =""
                for line in lines :
                    header_match =re .match (header_pattern ,line )
                    if header_match :
                        if current_text :
                            processed_blocks .append (('text',current_text ))
                            current_text =""
                        hashes =header_match .group (1 )
                        header_text =header_match .group (2 )
                        processed_blocks .append (('format',hashes +' '))
                        processed_blocks .append (('text',header_text ))
                        processed_blocks .append (('format','\n'))
                        continue
                    list_match =re .match (list_item_pattern ,line )
                    if list_match :
                        if current_text :
                            processed_blocks .append (('text',current_text ))
                            current_text =""
                        indent =list_match .group (1 )
                        marker =list_match .group (2 )
                        item_text =list_match .group (3 )
                        processed_blocks .append (('format',indent +marker +' '))
                        processed_blocks .append (('text',item_text ))
                        processed_blocks .append (('format','\n'))
                        continue
                    if re .match (hr_pattern ,line ):
                        if current_text :
                            processed_blocks .append (('text',current_text ))
                            current_text =""
                        processed_blocks .append (('format',line +'\n'))
                        continue
                    line_parts =[]
                    last_pos =0
                    def process_pattern (pattern ,line ,last_pos ,line_parts ,is_code =False ):
                        new_last_pos =last_pos
                        for match in re .finditer (pattern ,line ):
                            start ,end =match .span ()
                            if start >new_last_pos :
                                line_parts .append (('text',line [new_last_pos :start ]))
                            if is_code :
                                line_parts .append (('code',match .group (0 )))
                            elif pattern ==link_pattern :
                                link_text =match .group (1 )
                                url =match .group (2 )
                                line_parts .append (('format','['))
                                line_parts .append (('text',link_text ))
                                line_parts .append (('format',']('+url +')'))
                            elif pattern ==image_pattern :
                                alt_text =match .group (1 )
                                url =match .group (2 )
                                line_parts .append (('format','!['))
                                line_parts .append (('text',alt_text ))
                                line_parts .append (('format',']('+url +')'))
                            else :
                                line_parts .append (('format',match .group (0 )))
                            new_last_pos =end
                        return new_last_pos
                    last_pos =process_pattern (inline_code_pattern ,line ,last_pos ,line_parts ,is_code =True )
                    last_pos =process_pattern (image_pattern ,line ,last_pos ,line_parts )
                    last_pos =process_pattern (link_pattern ,line ,last_pos ,line_parts )
                    last_pos =process_pattern (html_tag_pattern ,line ,last_pos ,line_parts ,is_code =True )
                    if last_pos <len (line ):
                        line_parts .append (('text',line [last_pos :]))
                    if line_parts :
                        if current_text :
                            processed_blocks .append (('text',current_text ))
                            current_text =""
                        for part_type ,part_content in line_parts :
                            processed_blocks .append ((part_type ,part_content ))
                        processed_blocks .append (('format','\n'))
                    else :
                        current_text +=line +'\n'
                if current_text :
                    processed_blocks .append (('text',current_text ))
        return processed_blocks
    def translate_blocks (self ,blocks ,target_lang ):
        translated_blocks =[]
        for block_type ,content in blocks :
            if block_type =='text'and content .strip ():
                translated_content =self .translate_text (content ,target_lang )
                translated_blocks .append ((block_type ,translated_content ))
            else :
                translated_blocks .append ((block_type ,content ))
        return translated_blocks
    def translate_text (self ,text ,target_lang ):
        try :
            text =text .strip ()
            if not text :
                return text
            url ="https://translate.googleapis.com/translate_a/single"
            params ={
            "client":"gtx",
            "sl":"auto",
            "tl":target_lang ,
            "dt":"t",
            "q":text
            }
            headers ={
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, например Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response =requests .get (url ,params =params ,headers =headers )
            if response .status_code ==200 :
                result =response .json ()
                translated_text =""
                for part in result [0 ]:
                    if part [0 ]:
                        translated_text +=part [0 ]
                return translated_text
            else :
                print (f"Ошибка API: {response .status_code }")
                return text
        except Exception as e :
            print (f"Ошибка перевода: {str (e )}")
            return text
    def reconstruct_markdown (self ,blocks ):
        result =""
        for block_type ,content in blocks :
            result +=content
        result =re .sub (r'\n{3,}','\n\n',result )
        return result
    def translate_current_file (self ):
        is_temp_file =False
        if self .current_file :
            is_temp_file =(self .current_file ==os .path .join (os .path .dirname (os .path .abspath (__file__ )),"temporary.md"))
        if not is_temp_file and not self .current_file :
            reply =QMessageBox .question (
            self ,"Сохранение файла",
            "Для перевода документ должен быть сохранен. Сохранить сейчас?",
            QMessageBox .StandardButton .Yes |QMessageBox .StandardButton .No
            )
            if reply ==QMessageBox .StandardButton .Yes :
                if not self .save_file_as ():
                    return
            else :
                return
        translator_dialog =TranslatorDialog (self )
        if translator_dialog .exec ()!=QDialog .DialogCode .Accepted :
            return
        main_lang_name ,main_lang_code =translator_dialog .get_main_language ()
        selected_langs =translator_dialog .get_selected_languages ()
        if not selected_langs :
            QMessageBox .warning (self ,"Предупреждение","Выберите хотя бы один язык для перевода")
            return
        if is_temp_file or not self .current_file :
            base_dir =QFileDialog .getExistingDirectory (
            self ,"Выберите папку для сохранения переводов",""
            )
            if not base_dir :
                return
        else :
            base_dir =os .path .dirname (self .current_file )
        output_folder =os .path .join (base_dir ,"translations")
        try :
            if not os .path .exists (output_folder ):
                os .makedirs (output_folder )
        except Exception as e :
            QMessageBox .critical (self ,"Ошибка",f"Не удалось создать папку translations: {str (e )}")
            return
        md_content =self .editor .toPlainText ()
        if is_temp_file or not self .current_file :
            base_filename ="README"
        else :
            base_filename =os .path .splitext (os .path .basename (self .current_file ))[0 ]
        self .progress_dialog =QProgressDialog ("Подготовка к переводу...","Отмена",0 ,100 ,self )
        self .progress_dialog .setWindowTitle ("Прогресс перевода")
        self .progress_dialog .setWindowModality (Qt .WindowModality .WindowModal )
        self .progress_dialog .setMinimumDuration (0 )
        self .progress_dialog .setValue (0 )
        self .progress_dialog .show ()
        self .translator_thread =TranslatorThread (
        self ,md_content ,output_folder ,base_filename ,
        main_lang_code ,selected_langs
        )
        self .translator_thread .progress_signal .connect (self .update_translation_progress )
        self .translator_thread .finished_signal .connect (self .translation_finished )
        self .progress_dialog .canceled .connect (self .cancel_translation )
        self .translator_thread .start ()
    @Slot (int ,str )
    def update_translation_progress (self ,value ,message ):
        if self .progress_dialog :
            self .progress_dialog .setValue (value )
            self .progress_dialog .setLabelText (message )
    @Slot (bool ,str )
    def translation_finished (self ,success ,message ):
        if self .progress_dialog :
            self .progress_dialog .close ()
        if success :
            QMessageBox .information (self ,"Успех",message )
        else :
            QMessageBox .critical (self ,"Ошибка",message )
    def cancel_translation (self ):
        if hasattr (self ,'translator_thread')and self .translator_thread .isRunning ():
            self .translator_thread .cancel ()
            self .translator_thread .wait ()
    def insert_latex_block (self ):
        cursor =self .editor .textCursor ()
        cursor .insertText ("$$\n")
        cursor .insertText ("x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}\n")
        cursor .insertText ("$$")
        self .editor .setFocus ()
    def insert_mermaid_diagram (self ):
        cursor =self .editor .textCursor ()
        cursor .insertText ("```mermaid\n")
        cursor .insertText ("график ТД;\n")
        cursor .insertText ("    А-->Б;\n")
        cursor .insertText ("    А-->С;\n")
        cursor .insertText ("    Б-->Д;\n")
        cursor .insertText ("    C-->D;\n")
        cursor .insertText ("```")
        self .editor .setFocus ()
    def insert_svg (self ):
        cursor =self .editor .textCursor ()
        cursor .insertText ("```svg\n")
        cursor .insertText ('<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">\n')
        cursor .insertText ('  <circle cx="50" cy="50" r="40" штрих="черный" штрих-ширина="2" fill="красный" />\n')
        cursor .insertText ('</svg>\n')
        cursor .insertText ("```")
        self .editor .setFocus ()
def apply_modern_dark_theme (app ):
    app .setStyle ("Fusion")
    font =QFont ("Следуйте пользовательскому интерфейсу",12 )
    app .setFont (font )
    qss ="""    QВиджет {
            цвет фона: #181A1B;
            цвет: #E4E6EB;
            размер шрифта: 16 пикселей;
        }
        QMainWindow, QDialog, QMenuBar, QMenu, QStatusBar {
            цвет фона: #181A1B;
            цвет: #E4E6EB;
            граница: нет;
        }
        QMenuBar {
            размер шрифта: 18 пикселей;
            отступ: 0 8 пикселей;
            фон: #181A1B;
        }
        QMenuBar::item {
            фон: прозрачный;
            отступы: 6 пикселей 18 пикселей;
            поле: 0 2 пикселя;
            радиус границы: 8 пикселей;
            минимальная ширина: 32 пикселя;
            минимальная высота: 24 пикселей;
        }
        QMenuBar::item:selected {
            фон: #23272E;
            цвет: #7FDBFF;
        }
        QМеню {
            размер шрифта: 16 пикселей;
            отступы: 6 пикселей 12 пикселей;
            радиус границы: 8 пикселей;
        }
        QMenu::item {
            отступы: 6 пикселей 18 пикселей;
            радиус границы: 6 пикселей;
        }
        QMenu::item:selected {
            цвет фона: #31343B;
            цвет: #7FDBFF;
        }
        QToolBar {
            фон: #23272E;
            граница: нет;
            интервал: 4 пикселя;
            отступ: 6 пикселей 8 пикселей;
        }
        QToolButton {
            цвет фона: #23272E;
            цвет: #E4E6EB;
            радиус границы: 7 пикселей;
            отступы: 4 пикселя 10 пикселей;
            размер шрифта: 14 пикселей;
            минимальная ширина: 28 пикселей;
            минимальная высота: 28 пикселей;
            максимальная ширина: 32 пикселя;
            максимальная высота: 32 пикселей;
            граница: сплошная 1 пиксель #23272E;
        }
        QToolButton: наведите {
            цвет фона: #31343B;
            цвет: #7FDBFF;
        }
        QToolButton: нажал {
            цвет фона: #1A1D22;
            цвет: #39C5BB;
        }
        QPushButton {
            цвет фона: #23272E;
            цвет: #E4E6EB;
            радиус границы: 12 пикселей;
            отступ: 10 пикселей 20 пикселей;
            размер шрифта: 16 пикселей;
            граница: сплошная 1 пиксель #23272E;
        }
        QPushButton: наведите {
            цвет фона: #31343B;
            цвет: #7FDBFF;
        }
        QPushButton: нажал {
            цвет фона: #1A1D22;
            цвет: #39C5BB;
        }
        QLineEdit, QTextEdit, QPlainTextEdit, QTextBrowser {
            цвет фона: #23272E;
            цвет: #E4E6EB;
            радиус границы: 10 пикселей;
            граница: сплошная 1 пиксель #23272E;
            отступ: 8 пикселей;
            размер шрифта: 16 пикселей;
            цвет фона выбора: #31343B;
            цвет выделения: #7FDBFF;
        }
        QStatusBar {
            фон: #181A1B;
            цвет: #7FDBFF;
            граница: нет;
        }
        QGroupBox {
            граница: сплошная 1 пиксель #23272E;
            радиус границы: 10 пикселей;
            маржа сверху: 10 пикселей;
        }
        QGroupBox:title {
            subcontrol-origin: маржа;
            слева: 10 пикселей;
            отступ: 0 3px 0 3px;
        }
        QTreeView, QDockWidget {
            цвет фона: #181A1B;
            цвет: #E4E6EB;
            радиус границы: 10 пикселей;
        }
        QScrollBar: вертикальный, QScrollBar: горизонтальный {
            фон: #23272E;
            радиус границы: 8 пикселей;
            ширина: 14 пикселей;
            поле: 2 пикселя;
        }
        QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
            фон: #31343B;
            радиус границы: 8 пикселей;
            минимальная высота: 20 пикселей;
            минимальная ширина: 20 пикселей;
        }
        QScrollBar::handle:hover {
            фон: #7FDBFF;
        }
        QScrollBar::add-line, QScrollBar::sub-line {
            фон: нет;
            граница: нет;
        }
        QLabel {
            цвет: #E4E6EB;
            размер шрифта: 16 пикселей;
        }"""
    app .setStyleSheet (qss )
def main ():
    app =QApplication (sys .argv )
    apply_modern_dark_theme (app )
    window =MarkdownEditor ()
    window .show ()
    sys .exit (app .exec ())
if __name__ =="__main__":
    main ()