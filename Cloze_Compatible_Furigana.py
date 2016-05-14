# -*- coding: utf-8 -*-

# ANKI 2 ADD-ON.
# CLOZE DELETION COMPATIBLE FURIGANA FOR JAPANESE + tools for editing furigana easily.
# Version 2.60, released 2013-11-18
# By Pyry Kontio.
# E-mail: pyry.kontio@drasa.eu
# Licenced with GPL 3.
# Thanks a bunch for Jake Probst whose Simple furigana plugin inspired this work!

########################################################################################
# Furigana display
########################################################################################

tagsToEnable = [
# Any of the tags in this list the card will enable this plugin. You can modify this list yourself.
    'furigana',
]

japaneseSupportCode = '3918629684'

cssfixercode = 'CFT.260.00'
oldcodes = ['CFT2.0120130813', 'CFT.200.00', 'CFT.200.01', 'CFT.200.02', 'CFT.202.00', 'CFT.210.00', 'CFT.210.01', 'CFT.212.00', 'CFT.220.00', 'CFT.220.01']


import re
import sys
from anki.hooks import wrap as wrapHook, runHook, addHook
from anki.lang import _
from anki.utils import json, isWin, isMac

from aqt.utils import showInfo, askUser, tooltip
import aqt.editor 	# This is needed since the aqt.editor._html property is modified later in the code.
from aqt.editor import Editor
from aqt.qt import QHBoxLayout, QSpacerItem, QSizePolicy, QWebPage, QLabel


TYPEIN_PATTERN = ur"\[\[type:.*?\]\]"
SOUND_PATTERN = ur"\[sound:.*?\]"
CLOZEDELETION_PATTERN_HTML = ur'<span class="?cloze"?>(.*?)</span>'
CLOZEDELETION_PATTERN_BRACES = ur'{{c\d+::(.*?)}}'
HTMLTAG = ur'<[^>]*>'
LINEBREAK = ur'<br ?/?>|<div>|</div>'
FURIGANA_BRACKETS = ur"[^\S\n]?(?P<base_part>(?P<base>[^\s。、？！!?：]+?)(?P<base_hide>!?))(?P<ruby_part>\[(?P<ruby_hide>!?)(?P<ruby>[^\]]*?)\])"

FURIGANA_HTML = ur'<ruby( title="(?P<title>[^"]*)")?([^>]*?)><rb(?P<base_hide>[^>]*?)>(?P<base>.*?)</rb><rt(?P<ruby_hide>[^>]*?)>(?P<ruby>.*?)</rt></ruby>'

#import logging
#logging.basicConfig(filename='cloze_compatible_furigana.log',level=logging.DEBUG,format='\n\n-------------------------------------------\n\n\n\n%(asctime)s %(message)s')

def stripHtml(text):
	text = re.sub(HTMLTAG, ur'',text)
	return text

def stripClozes(text, r=None):
	text = re.sub(CLOZEDELETION_PATTERN_BRACES, ur'\1',text)
	return text
	
class Replacer:
	def __init__(self):
		self.substitutes = []
		self.substitutes_dict = {}
		self.index = 0
	
	def sub(self, html, pattern, type='SUBSTITUTE', processing=lambda x: x.group(0)):
		html = re.sub(pattern, lambda match: self.subOne(match, type, processing), html, flags=re.UNICODE)
		return html
		
	def subOne(self, match, type, processing):
		sub = u"2304985732409587{0}".format(self.index)+type
		self.index += 1
		original = processing(match)
		self.substitutes.append((sub, original))
		self.substitutes_dict[sub] = original
		return sub

	def restore(self, html):
		for sub, original in reversed(self.substitutes):
			html = html.replace(sub, original)
			sub = sub.strip()
			html = html.replace(sub, original)
		return html

	def subEach(self, match, different_r):
		return self.subOne(match, type='SUBSTITUTE', processing=lambda x: x.group(0))

def subForBrackets(html, cloze_processor):
	r = Replacer()
	html = r.sub(html, TYPEIN_PATTERN, 'TYPEIN')
	html = r.sub(html, SOUND_PATTERN, 'SOUND')
	html = r.sub(html, CLOZEDELETION_PATTERN_HTML, 'CLOZE', cloze_processor)
	html = r.sub(html, CLOZEDELETION_PATTERN_BRACES, 'CLOZE_BRACES', cloze_processor)
	html = r.sub(html, LINEBREAK, 'LINEBREAK\n')
	html = r.sub(html, HTMLTAG, 'HTMLTAG')
	return html, r

def inside_cloze(match, callback):
	"makes furigana work even inside clozes"
	inside = match.group(1)
	r = Replacer()
	furigana = re.sub(FURIGANA_BRACKETS, lambda match: callback(match, r, insideCloze=True), inside, flags=re.UNICODE)
	return match.group(0).replace(inside, furigana)

def catchFuriganaBrackets(html, callback):
	html, r = subForBrackets(html, lambda match: inside_cloze(match, callback))
	html, number = re.subn(FURIGANA_BRACKETS, lambda match: callback(match, r), html, flags=re.UNICODE)
	html = r.restore(html)
	return html, number
	
def htmlRuby(base, ruby, base_hide, ruby_hide, base_cloze, ruby_cloze, insideCloze):
	if ruby_hide:
		ruby_hide = ' class="hidden"'
	else:
		ruby_hide = ''
	if base_hide:
		base_hide = ' class="hidden"'
	else:
		base_hide = ''
	title = stripHtml(base+'('+ruby+')')
	title = stripClozes(title)
	html = u'''<ruby title="{4}"><rb{0}>{1}</rb><rt{2}>{3}</rt></ruby>'''.format( base_hide, base, ruby_hide, ruby, title)
	return html

def baseMaruer(match):
	base = match.group('base')
	ruby = match.group('ruby')
	base_hide = match.group('base_hide')
	ruby_hide = match.group('ruby_hide')
	if 'hidden' in base_hide and not re.search(CLOZEDELETION_PATTERN_HTML, base) and 'hidden' in ruby_hide:
		return ''
	if 'hidden' in base_hide and not re.search(CLOZEDELETION_PATTERN_HTML, base):
		base = u'◯'*len(stripHtml(base))
	return u'<ruby><rb>{0}</rb><rt{1}>{2}</rt></ruby>'.format(base, ruby_hide, ruby)

def htmlToHtml(match):
	base = match.group('base')
	ruby = match.group('ruby')
	base_hide = 'hidden' in match.group('base_hide')
	ruby_hide = 'hidden' in match.group('ruby_hide')
	base_cloze = re.search(CLOZEDELETION_PATTERN_HTML, base)
	ruby_cloze = re.search(CLOZEDELETION_PATTERN_HTML, ruby)
	return htmlRuby(base, ruby, base_hide, ruby_hide, base_cloze, ruby_cloze, False)

def renderFurigana(html, renderRealtime=False):
#	logging.debug('\n\n\n\nRender furigana! '+unicode(renderRealtime)+unicode(html))
	html, number = catchFuriganaBrackets(html, bracketsToHtml)
 	if renderRealtime: html = re.sub(FURIGANA_HTML, baseMaruer, html, flags=re.UNICODE)
	return html


def mungeFurigana(html, type, fields, model, data, col):
    "Makes furigana work by replacing [ and ] characters with ruby html element."
    tagstring = data[5]
    if not any([tag in tagstring.lower() for tag in tagsToEnable]):
        return html
    
    html = html.replace('&nbsp;', u'\u00A0')
    html = renderFurigana(html, renderRealtime=True)
    return html

addHook("mungeQA", mungeFurigana)



##########################################################################################
# FURIGANA EDITING BUTTONS FOR JAPANESE. (Utilizes Reading generator of Japanene support plugin)
##########################################################################################


# Monkey patching the reading method of MecabController to fix some annoyances (mainly unknown words ridden with spaces)

def reading(self, expr):
	self.ensureOpen()
#	showInfo(expr.replace('<', '&lt;').replace('\n', '\\n'))
	self.mecab.stdin.write(expr.replace(' ', '_BSP_').replace(u'\u00a0', '_NBSP_').encode("euc-jp", "ignore")+'\n')
	self.mecab.stdin.flush()
	expr = unicode(self.mecab.stdout.readline().rstrip('\r\n'), "euc-jp").replace('_NBSP_', u'\u00a0').replace('_BSP_', ' ')
#	showInfo(expr.replace('<', '&lt;').replace(' ', '_').replace('\n', '\\n'))
	out = []
	inNode = False
	for node in re.split(ur"( [^ ]+?\[.*?\])", expr):
		if not inNode:
			out.append(node)
			inNode = True
			continue
		else:
#			showInfo(node.replace('<', '&lt;'))
#			showInfo(str(inNode))
			(kanji, reading) = re.match(ur" (.+?)\[(.*?)\]", node, flags=re.UNICODE).groups()
			inNode = False
		# hiragana, punctuation, not japanese, or lacking a reading
		if kanji == reading or not reading:
			out.append(kanji)
			continue
		# katakana
		if kanji == japanese.reading.kakasi.reading(reading):
			out.append(kanji)
			continue
		# convert to hiragana
		reading = japanese.reading.kakasi.reading(reading)
		# ended up the same
		if reading == kanji:
			out.append(kanji)
			continue
		# don't add readings of numbers
		if kanji in u"一二三四五六七八九十０１２３４５６７８９":
			out.append(kanji)
			continue
		# strip matching characters and beginning and end of reading and kanji
		# reading should always be at least as long as the kanji
		placeL = 0
		placeR = 0
#		showInfo(unicode([kanji, reading]))
		for i in range(1,len(kanji)):
			if kanji[-i] != reading[-i]:
				break
			placeR = i
		for i in range(0,len(kanji)-1):
			if kanji[i] != reading[i]:
				break
			placeL = i+1
		if placeL == 0:
			if placeR == 0:
				out.append(" %s[%s]" % (kanji, reading))
			else:
				out.append(" %s[%s]%s" % (
					kanji[:-placeR], reading[:-placeR], reading[-placeR:]))
		else:
			if placeR == 0:
				out.append("%s %s[%s]" % (
					reading[:placeL], kanji[placeL:], reading[placeL:]))
			else:
				out.append("%s %s[%s]%s" % (
					reading[:placeL], kanji[placeL:-placeR],
					reading[placeL:-placeR], reading[-placeR:]))
	fin = u""
#	for c, s in enumerate(out):
#		if c < len(out) - 1 and re.match("^[A-Za-z0-9]+$", out[c+1]):
#			s += " "
#		fin += s
#	showInfo(unicode(out))
	fin = ''.join(out)
	return fin


try:
    import japanese.reading
    japanese.reading.mecabArgs = ['--node-format= %m[%f[7]]', '--eos-format=\n', '--unk-format=%m']
    japanese.reading.MecabController.reading = reading
    mecab = japanese.reading.MecabController()
except ImportError:
    mecab = None

# Monkey patching the editor style sheet to display hidden furigana as grey, ruby with bounding boxes and clozes with blue background.

aqt.editor._html = aqt.editor._html.replace("<style>\n", """<style>\n
	rt.hidden,rb.hidden {visibility: visible !important; opacity:0.35;}
	ruby{border: 1px dashed #ccc; padding-top: 0.6em; margin-right: 2px; margin-top: 2px;}
	div{line-height: 2em; padding-top:3px;}
	.clozewrapper{background-color: #E8E8FF;}
	rb.hidden .clozewrapper{background-color: #D0D0FF;}.""")


# Patching the toolbar into editor

def senseiButtons(editor):

    editor.upperIcondsBox = editor.iconsBox
    editor.iconsBox = QHBoxLayout()
    if not isMac:
        editor.iconsBox.setMargin(6)
    else:
        editor.iconsBox.setMargin(0)
    editor.iconsBox.setSpacing(0)
    editor.outerLayout.addLayout(editor.iconsBox)
    editor._addButton("generateRuby", lambda: doIt(editor, generateRuby), key=_("Ctrl+F"), tip=_(u"Automatically generate furigana (Ctrl+F)"), text=_(u"Generate readings"), size=False)
    editor._addButton("deleteRuby", lambda: doIt(editor, deleteRuby), tip=_(u"Mass delete furigana"), text=_(u"Delete readings"), size=False)
    editor._addButton("preRender", lambda: doIt(editor, preRender), tip=_(u"Show furigana or markup"), text=_(u"Visual/Code"), size=False)
    editor._addButton("extractKanji", lambda: extract(editor), tip=_(u"Strip everything but base-clozed kanji"), text=_(u"Extract clozed kanji"), size=False)

    runHook("senseiButtons", editor)
    editor.iconsBox.addItem(QSpacerItem(20,1, QSizePolicy.Expanding))
    editor.iconsBox.addWidget(QLabel('Furigana '))
    editor._addButton("clozeRuby", lambda: doIt(editor, clozeRuby), key=_("Ctrl+H"), tip=_(u"Create a reading excercise (Ctrl+H)"),
                    text=_(u"Cloze/Uncloze"), size=False)
    editor._addButton("hideRuby", lambda: doIt(editor, hideRuby), tip=_(u"Make ruby texts hidden so they show only up when being asked."), text=_(u"Hide/Show"), size=False)
    editor.iconsBox.addItem(QSpacerItem(20,1, QSizePolicy.Expanding))
    editor.iconsBox.addWidget(QLabel('Kanji '))
    editor._addButton("clozeKanji", lambda: doIt(editor, clozeKanji), key=_("Ctrl+J"), tip=_(u"Create a writing excercise (Ctrl+J)"),
                    text=_(u"Cloze/Uncloze"), size=False)
    editor._addButton("hideBase", lambda: doIt(editor, hideBase), tip=_(u"Make base texts hidden so they are replaced with ◯ signs unless asked."),
                    text=_(u"Hide/Show"), size=False)

Editor.setupButtons = wrapHook(Editor.setupButtons, senseiButtons)


class Selection:

	def __init__(self, window):
		self.window = window
		js_get_html = u"""
			sel = window.getSelection();
			range = sel.getRangeAt(0);
			if ( range.collapsed) {
				html = ""; htmlAfter = ""; htmlBefore = "";
			} else {
				ancestorStart = $(range.startContainer).closest("ruby").get(0);
				ancestorEnd = $(range.endContainer).closest("ruby").get(0);
				if ( ancestorStart ) {
					range.setStartBefore( ancestorStart );
				}
				if ( ancestorEnd ) {
					range.setEndAfter( ancestorEnd );
				}
				afterRange = range.cloneRange();
				afterRange.collapse(false);
				endPoint = $(range.endContainer).closest("div").get(0).lastChild;
				if (endPoint === null) {endPoint = $(range.endContainer).closest("div").get(0).parentNode.lastChild}
				afterRange.setEndAfter(endPoint);
				docFragmentAfter = afterRange.cloneContents();
				div = document.createElement('div');
				div.appendChild(docFragmentAfter);
				htmlAfter = div.innerHTML;
				div = null;
				
				beforeRange = range.cloneRange();
				beforeRange.collapse(true);
				startPoint = $(range.startContainer).closest("div").get(0).firstChild;
				if (startPoint === null) {startPoint = $(range.startContainer).closest("div").get(0).parentNode.firstChild}
				beforeRange.setStartBefore(startPoint);
				docFragmentBefore = beforeRange.cloneContents();
				div = document.createElement('div');
				div.appendChild(docFragmentBefore);
				htmlBefore = div.innerHTML;
				div = null;
				
				sel.removeAllRanges();
				sel.addRange(range);
				
				docFragment = range.cloneContents();
				div = document.createElement('div');
				div.appendChild(docFragment);
				html = div.innerHTML;
				div = null;
				
				range.detach();
				afterRange.detach();
				beforeRange.detach();
			}
			[htmlBefore, html, htmlAfter]
			"""
		self.before, self.selected, self.after = window.web.page().mainFrame().evaluateJavaScript(js_get_html)
		if self.selected.strip() == '':
			self.window.web.eval("setFormat('selectAll', '');")
			self.before, self.selected, self.after = window.web.page().mainFrame().evaluateJavaScript(js_get_html)
		self.selected = self.selected.replace('&nbsp;', u'\u00a0')
		self.before = self.before.replace('&nbsp;', u'\u00a0')
		self.after = self.after.replace('&nbsp;', u'\u00a0')

	def length(self, text = None):
		html = text if text else self.selected
		# Btw. inserthtml doesn't have inserted html selected, so we must select it by ourselves:
		textRows = []
		for row in html.split("<div>"):
			js_get_text = u"""
			div = document.createElement('div');
			div.innerHTML = {0};
			text = div.textContent;
			div = null;
			text
			""".format(json.dumps(row))
			textRows.append(self.window.web.page().mainFrame().evaluateJavaScript(js_get_text))
		if textRows[0] == '': textRows = textRows[1:]
		selectedText = '\n'.join(textRows).replace('&nbsp;', u'\u00a0')
		selectedText = re.sub(ur'( +)', ' ', selectedText)
		selectionLength = len(selectedText)
		selectionLength += len(re.findall(ur'<rt[^>]*>', html)) + html.count('</rt>')
		return selectionLength

	def modify(self, html, selectionLength = None, insert=False, spaceAtLeft=0, spaceAtRight=0):
		html = html.replace( u'\u00a0', '&nbsp;')
		if not html.endswith("</ruby>") and not self.selected.endswith("</ruby>") and not self.after.startswith('<ruby') and not self.after.startswith('<div') and self.after != '' and self.before != '' and not self.before.endswith('</div>') :
			if insert:
				html = self.selected + html
				selectionLength = self.length(html)-self.length()
			else:
				selectionLength = self.length(html)
	# if the selection contains ruby element on its end border, QWebView can't handle it without creating mess.
			self.window.web.eval("setFormat('inserthtml', %s);" % json.dumps(html))
			for _ in range(spaceAtRight):
				self.window.web.triggerPageAction(QWebPage.MoveToPreviousChar)
			for _ in range(selectionLength-spaceAtLeft):
				self.window.web.triggerPageAction(QWebPage.SelectPreviousChar)
		else: # So, we must implement our own replacement code - unfortunately this doesn't have undo functionality.
			js_replace_selection = u"""
			sel = window.getSelection();
			range = sel.getRangeAt(0);
			frag = document.createDocumentFragment();
			div = document.createElement('div');
			div.innerHTML = {0};
			while (child = div.firstChild) {{
				frag.appendChild(child);
			}}
			div = null;
			ancestorStart = $(range.startContainer).closest("ruby").get(0);
			ancestorEnd = $(range.endContainer).closest("ruby").get(0);
				if ( ancestorStart ) {{
					range.setStartBefore( ancestorStart );
				}}
				if ( ancestorEnd ) {{
					range.setEndAfter( ancestorEnd );
				}}
			if ({1}) {{
				range.collapse(false);
			}} else {{
				range.deleteContents();
			}}
			range.insertNode(frag);
			sel.removeAllRanges();
			sel.addRange(range);
			range.toString(); 
			""".format(json.dumps(html), ('false' if not insert else 'true'))
			selectedText = self.window.web.page().mainFrame().evaluateJavaScript(js_replace_selection)


def debug(*args):
	for arg in args:
		sys.stdout.write("'"+(unicode(arg)+"', ").encode('utf-8'))
	sys.stdout.write("\n")

def cardCSS(editor):
	css = editor.note.model()['css']
	question = editor.note.model()['tmpls'][0]['qfmt']
	answer = editor.note.model()['tmpls'][0]['afmt']
	
	cssExplanation = '/* This line is Added by Cloze Furigana Tools to make its various features work. {0}*/'.format(cssfixercode)
	# VERSION CFT.220.01: clozeShowCss = u'''.hidden {visibility: hidden;}               .hidden .cloze, .cloze .hidden {visibility: visible; background-color: white;                  } @-moz-document url-prefix() {ruby {position: relative;display: inline-block;} ruby rt {position: absolute;display: block;font-size: 0.5em;left: -50%;bottom: 115%;width: 210%;padding: 0;text-align: center;line-height:1em}} .hidden .basemaru {position:relative;} .hidden .basemaru:after {content: "◯"; visibility: visible; position:absolute; left:0;} .hidden .cloze .basemaru:after, .cloze .hidden .basemaru:after {visibility: hidden;} div{line-height: 2em;} .cloze_container .hidden {visibility: visible; background-color: white;}'''
	clozeShowCss                       = u'''.hidden {visibility: hidden; font-size: 0;} .hidden .cloze, .cloze .hidden {visibility: visible; background-color: white;font-size: 0.8rem;} @-moz-document url-prefix() {ruby {position: relative;display: inline-block;} ruby rt {position: absolute;display: block;font-size: 0.5em;left: -50%;bottom: 115%;width: 210%;padding: 0;text-align: center;line-height:1em}} .hidden .basemaru {position:relative;} .hidden .basemaru:after {content: "◯"; visibility: visible; position:absolute; left:0;} .hidden .cloze .basemaru:after, .cloze .hidden .basemaru:after {visibility: hidden;} div{line-height: 2em;} .cloze_container .hidden {visibility: visible; background-color: white;}'''
	cssFix = cssExplanation + clozeShowCss

	jsExplanation = '<!-- This line is Added by Cloze Furigana Tools to make its various features work. {0} -->'.format(cssfixercode)
	clozeShowJS = u'''<script>var rubys = document.getElementsByTagName('ruby'); var spans = document.getElementsByTagName('span'); for (var i=0; i < rubys.length; i++) { for (var s=0; s < spans.length; s++) { if ( spans[s].className === "cloze" && rubys[i].contains(spans[s])) { rubys[i].className = "cloze_container"; break; }}} </script>'''
	jsFix = jsExplanation + clozeShowJS

	csslined = css.split('\n')
	css = ''
	for line in csslined:
		if not any([(code in line) for code in oldcodes]):
			css += line+'\n'
		else: # OLD CSS DETECTED
			css += cssFix
	questionlined = question.split('\n')
	question = ''
	for line in questionlined:
		if not any([(code in line) for code in oldcodes]):
			question += line+'\n'
		else: # OLD JS DETECTED
			question += jsFix
	answerlined = answer.split('\n')
	answer = ''
	for line in answerlined:
		if not any([(code in line) for code in oldcodes]):
			answer += line+'\n'
		else: # OLD JS DETECTED
			answer += jsFix
	if cssfixercode not in css: # If there isn't any old CSS/JS, append to end.
		css += '\n\n' + cssFix
	if cssfixercode not in question:
		question += '\n\n' + jsFix
	if cssfixercode not in answer:
		answer += '\n\n' + jsFix
	editor.note.model()['css'] = css.strip()
	editor.note.model()['tmpls'][0]['qfmt'] = question.strip()
	editor.note.model()['tmpls'][0]['afmt'] = answer.strip()

def performToEveryFurigana(html, action):
	html, number_brackets = catchFuriganaBrackets(html, action)
	html = preRender(html)
	html, number_html = catchFuriganaBrackets(html, action)
	html = preRender(html)
	if number_brackets + number_html == 0:
		tooltip(_("No furigana text found! Create some first with 'Generate readings.'"))
	return html

def clozer(pattern, matchgroup, r):
	focus = pattern.group(matchgroup).replace("&nbsp;", u'\u00a0').strip()
	focus = r.restore(focus)
	fullmatch = pattern.group(0).replace("&nbsp;", u'\u00a0')
	fullmatch = r.restore(fullmatch)
	clozed_content = re.search(CLOZEDELETION_PATTERN_BRACES, focus, flags=re.UNICODE)
	if clozed_content:
		fullmatch = fullmatch.replace(clozed_content.group(0), clozed_content.group(1)) # remove cloze
	elif '{{c' in focus or '}}' in focus: # if there happens to be a partial cloze, don't do anything.
		return fullmatch
	else:
		fullmatch = fullmatch.replace(focus, u"{{{{c{0}::{1}}}}}".format(clozer.highest, focus))
	clozer.highest += 1
	return fullmatch


def doIt(editor, action):
	s = Selection(editor)
#	logging.debug('\n\n\n\nDo it!'+unicode(action)+unicode(s.selected))
	html = s.selected
	if action == generateRuby:
		if not japaneseSupportExists(editor):
			return
		html = preRender(html)
		html = generateRuby(html)
		html = preRender(html)
		if html == s.selected:
			tooltip(_("Nothing to generate!"))
			return
	elif action == preRender:
		html = preRender(html)
		if html == s.selected:
			tooltip(_("No furigana text found! Create some first with 'Generate readings.'"))
			return
	else:
		clozer.highest = checkCloze(editor)
		html = performToEveryFurigana(html, action)
	html, spaces = rubySanitizer(html, s.after, s.before)
	s.modify(html, spaceAtLeft=spaces[0], spaceAtRight=spaces[1])
	editor.saveTags()
	editor.note.addTag("Furigana")
	editor.tags.setText(editor.note.stringTags().strip())
	cardCSS(editor)

def japaneseSupportExists(editor):
    if not mecab:
        if askUser(_('Ruby generator needs "Japanese Support" add-on to work. Install it now?')):
        	from aqt.downloader import download
        	ret = download(editor.mw, japaneseSupportCode)
        	if not ret:
        		return False
        	data, fname = ret
        	editor.mw.addonManager.install(data, fname)
        	editor.mw.progress.finish()
        	showInfo(_("Download successful. Please restart Anki."))
        return False
    else:
    	return True

def generateRuby(html):
	r1 = Replacer()
	html = r1.sub(html, FURIGANA_HTML)
	
	html, r2 = subForBrackets(html, lambda x: x.group(0).replace( x.group(1), generateRuby(x.group(1)) ) )
	
	r3 = Replacer()
	html = r3.sub(html, FURIGANA_BRACKETS)
	html = html.replace('\n', '')
	html = mecab.reading(html)
    
	html = r3.restore(html)
	html = r2.restore(html)
	html = r1.restore(html)
	return html

def deleteRuby(match, r, insideCloze=False):
	return match.group('base')

def checkCloze(editor):
	# check that the model is set up for cloze deletion
	if '{{cloze:' not in editor.note.model()['tmpls'][0]['qfmt']:
		if editor.addMode:
			tooltip(_("Warning, cloze deletions will not work until "
			"you switch the type at the top to Cloze."))
		else:
			showInfo(_("""\
To make a cloze deletion on an existing note, you need to change it \
to a cloze type first, via Edit>Change Note Type."""))
	# find the highest existing cloze
	highest = 0
	for name, val in editor.note.items():
		m = re.findall(ur"\{\{c(\d+)::", val)
		if m:
			highest = max(highest, sorted([int(x) for x in m])[-1])
	highest += 1
	# must start at 1
	highest = max(1, highest)
	return highest
	

def clozeRuby(match, r, insideCloze=False):
	if insideCloze: return match.group(0)
	return clozer(match, 'ruby', r)
    
def clozeKanji(match, r, insideCloze=False):
	if insideCloze: return match.group(0)
	return clozer(match, 'base', r)

def hideRuby(match, r, insideCloze=False):
    if match.group('ruby_hide') == '!':
        return u'\u00a0{0}[{1}]'.format(match.group('base_part'),match.group('ruby'))
    else:
        return u'\u00a0{0}[!{1}]'.format(match.group('base_part'), match.group('ruby'))
    
def hideBase(match, r, insideCloze=False):
	if match.group('base_hide') == '!':
		return u'\u00a0{0}{1}'.format(match.group('base'), match.group('ruby_part'))
	else:
		return u'\u00a0{0}!{1}'.format(match.group('base'), match.group('ruby_part'))

def bracketsToHtml(match, r, insideCloze=False):
	base = r.restore(match.group('base'))
	ruby = r.restore(match.group('ruby'))
	base_hide = ( match.group('base_hide') == '!' )
	ruby_hide = ( match.group('ruby_hide') == '!' )
	base_cloze = re.search(CLOZEDELETION_PATTERN_HTML, base)
	ruby_cloze = re.search(CLOZEDELETION_PATTERN_HTML, ruby)
	return htmlRuby(base, ruby, base_hide, ruby_hide, base_cloze, ruby_cloze, insideCloze)

def rubySanitizer(html, after, before):

	def clozecleaner(m):
		inside = m.group(1)
		inside = inside.replace('</span>', '')
		whole = re.sub(ur'<span class="clozewrapper"( style="[^"]*")>', '<span class="clozewrapper">', m.group(0))
		return whole.replace(m.group(1), inside)
		

	def cleaner(html, insideRuby=False, insideBase=False):
		if insideRuby: html = re.sub(ur'<br ?/?>', '', html)
		if insideRuby: html = re.sub(ur'<div[^>]*>', '', html)
		if insideRuby: html = html.replace('</div>', '')
		html = re.sub('<ruby[^>]*>', '', html)
		html = re.sub('<rb[^>]*>', '', html)
		html = re.sub('<rt[^>]*>', '', html)
		html = html.replace('</ruby>', '')
		html = html.replace('</rb>', '')
		html = html.replace('</rt>', '')
	
		html = re.sub(ur'<span class="basemaru"[^>]*>', '', html)
		html = re.sub(ur'<!-- end_basemaru_l -->[^!]*?<!-- end_basemaru_r -->', '', html)
		html = html.replace('<span class="cjk_char">', '')
		html = html.replace('<!-- end_cjkl --></span><!-- end_cjkr -->', '')
		if insideRuby: html = html.replace('</span>', '')
	
		html = re.sub(ur'<span class="clozewrapper"[^>]*>(.*?)<!-- clozewr -->[^!]*?<!-- apper -->', clozecleaner, html)
		html = re.sub(ur'<span class="clozewrapper"[^>]*>', '', html)
		html = re.sub(ur'<!-- clozewr -->[^!]*?<!-- apper -->', '', html)
		html = html.replace('<div></div>', '')
		html = html.replace('<div><br /></div>', '<br>')
		html = re.sub(CLOZEDELETION_PATTERN_BRACES, lambda m: wrapCloze(m, insideRuby, insideBase), html)
		return html
	
	def wrapCloze(match, insideRuby, insideBase):
		text = match.group(0)
		if not 'clozewrapper' in text:
			if insideRuby and insideBase: text = ''.join(('<span class="basemaru">'+c+'<!-- end_basemaru_l --></span><!-- end_basemaru_r -->') if re.match(ur'[\u3041-\u3096\u30A0-\u30FF\u3400-\u4DB5\u4E00-\u9FCB\uF900-\uFA6A]',c) else c for c in text) # if hiragana katakana or kanji
			return '<span class="clozewrapper">'+text+'<!-- clozewr --></span><!-- apper -->'
		
		else:
			return match.group(0)

	def brokenRubycleaner(match):
		original = match.group(0)
		match = re.match(FURIGANA_HTML, original)
		if match:
			ruby_cleaned = cleaner(match.group('ruby'), insideRuby=True)
			base_cleaned = cleaner(match.group('base'), insideRuby=True, insideBase=True)
			if ruby_cleaned.strip() != '':
				original = original.replace('>'+match.group('base')+'<', '>'+base_cleaned+'<') # < ja > ettei replaceis title="BASE" -argumenttii samalla
				original = original.replace('>'+match.group('ruby')+'<', '>'+ruby_cleaned+'<')
			else:
				original = base_cleaned
		else:
			match = re.match(ur'<ruby[^>]*><rb[^>]*>(.*?)</rb></ruby>', original)
			if match:
				original = cleaner(match.group(1), insideRuby=True)
			else:
				match = re.match(ur'<ruby[^>]*><rt[^>]*>(.*?)</rt></ruby>', original)
				if match:
					original = cleaner(match.group(1), insideRuby=True)
				else:
					original = ''
		return original
	
	original_html = html
	r = Replacer()
	html = r.sub(html, ur'<ruby[^>]*>(.*?)</ruby>', 'RUBY_SANITIZE', brokenRubycleaner)
	html = cleaner(html)
	html = r.restore(html)
	
	html = html.replace("</ruby><", u"</ruby>\u00a0<")
	html = html.replace("><ruby", u">\u00a0<ruby")
#	html = html.replace("<!-- apper --><", u"<!-- apper -->\u00a0<")
#	html = html.replace("""><span class="clozewrapper">""", u""">\u00a0<span class="clozewrapper">""")
	spaceAtLeft = 0
	spaceAtRight = 0
	if html.endswith('</ruby>') and (after == '' or after[0] == '<'):
		html = html + u'\u00a0'
		spaceAtLeft = 1
	if html.startswith('<ruby') and (before == '' or before[-1] == '>'):
		html = u'\u00a0'+ html
		spaceAtRight = -1
	return html, [spaceAtLeft, spaceAtRight]

def htmlRubyUpdate(html):
	return re.sub(FURIGANA_HTML, htmlToHtml, html)

def sanitizeField(modifiedOrNot, note, currentField):
	original = note.fields[currentField]
	html, spaceatborder = rubySanitizer(original, '', '')
	html = htmlRubyUpdate(html)
	if original == html:
		return modifiedOrNot
	else:
#		logging.debug('sanitize on focuslost! \n\nORIGINAL '+unicode(original)+"\n\n\nSANITIZED"+unicode(html))
		note.fields[currentField] = html
		return True

addHook("editFocusLost", sanitizeField)

def preRender(html):

	def htmlToBrackets(match):
		original = match.group(0)
		if 'hidden' in match.group('base_hide'):
			bracket_base = u"\u00a0{0}!"
		else:
			bracket_base = u"\u00a0{0}"
		if 'hidden' in match.group('ruby_hide'):
			bracket_ruby = u"[!{1}]"
		else:
			bracket_ruby = u"[{1}]"
		base_cleaned, r = subForBrackets(match.group('base'), lambda x: x.group(0))
		base_cleaned = base_cleaned.replace(ur'\u00a0', '').replace(ur' ', '')
		bracket_pattern = bracket_base + bracket_ruby
		furigana_repl = bracket_pattern.format(base_cleaned, match.group('ruby'))
		furigana_repl = r.restore(furigana_repl)
		return furigana_repl

	r = Replacer()
	html = r.sub(html, FURIGANA_HTML, 'HTML_TO_BRACKETS', processing=htmlToBrackets)
	html = renderFurigana(html)
	html = r.restore(html)
	return html

def extract(editor):
	s = Selection(editor)
	original = html = s.selected
	kanjis = []
	def kanjifier(match, r, insideCloze=False):
		base = r.restore(match.group('base'))
		ruby = r.restore(match.group('ruby'))
		if re.search(CLOZEDELETION_PATTERN_BRACES, base):
			kanjis.append(u'{0}![!{1}]'.format(base, ruby))
	html, number_brackets = catchFuriganaBrackets(html, kanjifier)
	html = preRender(html)
	html, number_html = catchFuriganaBrackets(html, kanjifier)
	if len(kanjis) == 0:
		tooltip(_(u"No clozed basetexts found!"))
		return
	writeOrders = u'\u00a0'.join(kanjis).replace('&nbsp;', u'\u00a0')
	writeOrders = preRender(writeOrders)
	writeOrders, spaceatborder = rubySanitizer(writeOrders, s.after, s.before)
	s.modify(writeOrders, insert=True)