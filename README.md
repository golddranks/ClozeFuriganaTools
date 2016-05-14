# ClozeFuriganaTools
Anki addon: Cloze Furigana Tools. Also available here: https://ankiweb.net/shared/info/1263365841

##Description

Cloze deletion compatible furigana support & mass editing tools for Japanese.
By Pyry Kontio (https://twitter.com/golddranks)

You SHOULD study with clozes – and not just any random words, but whole sentences or passages of text! This tool makes it easy!

Note: This is a re-uploaded version – the original got deleted because my AnkiWeb account was deleted due to inactivity.

‣ NEW! What You See Is What You Get!
‣ NEW! The cards work even on AnkiWeb and ‣ AnkiDroid! (And most likely on AnkiMobile too...?)
‣ Furigana viewing with standard Anki 2.0 clozes
‣ Automatic mass reading generation in editing window
‣ Furigana mass clozing tool
‣ "Hidden ruby/base" for massive context kanji reading or writing exercise. Clozed furigana appear only for the word that is being asked currently.

This plugin intended to work well with cloze deletions, so you can easily cloze off any part of the base word or the ruby—or the whole word.




To demonstrate, this code...

これは {{c1::例}}[れい]で 御座[{{c2::ござ}}]います。 {{c3::今日[きょう]}}はいい {{c4::天}}気[てんき]ですね。

...transforms to all of these cards:





Following image demonstrates the "hidden ruby" feature. Note that furigana appears only when being asked! (Btw. you can peek hidden furigana—they appear as mouseover tooltips.)

ふりがなは 時[!{{c5::とき}}]にはありがたいが、 見[!{{c1::み}}]えっぱなしで 目障[!{{c2::めざわ}}]りだから「 隠[!{{c3::かく}}]れルビ」という 工夫[!{{c4::くふう}}]をくわえた。




NOTE: The "code" mode won't work in the Anki Mobile, Ankidroid or Anki Online due to technical limitations. Please convert everything to WYSIWG to enjoy clozed furigana on mobile platforms! Furthermore, the "code" mode won't work if tag "furigana" isn't tagged to the card. (The editor tags automatically it for convinience.)


Update history:

1.00 (2013-08-06) Initial version
1.50 (2013-08-08) A lot of work with furigana editor.
1.60 (2013-08-10) Furigana editing tools are quite stable now.
1.61 (2013-08-10) Editor adds "Furigana" tag automatically when Furigana editing tools are used.
2.00 (2013-08-13) WYSIWYG editing. AnkiWeb & AnkiDroid support. (Chrome and even Firefox after lots of hacking. IE? No way in hell.) Yet to be tested on AnkiMobile.
2.01 (2013-08-14) Fair amount of bug fixes.
2.10 (2013-08-15) Code cleanup and bug fixes.
2.13 (2013-08-15) Fixed a bug with multi-line reading generation.
2.14 (2013-08-17) A bug fix.
2.15 (2013-08-20) A bug fix.
2.16 (2013-08-20) A bug fix.
2.30 (2013-08-21) A slight change in how hidden ruby works. Now it shows hidden ruby if clozed kanji is being asked and the other way around.
2.32 (2013-08-22) Error logging did not seem to work on Windows, so it was disabled.
2.40 (2013-08-26) Some bug fixes.
2.50 (2013-08-27) More bug fixes.
2.51 (2013-10-06) A bug fix.
2.53 (2013-10-25) Small fixes.
2.60 (2013-11-18) Fixed the multi-paragraph support and made hidden rubytexts not to take vertical space.

Written by Pyry Kontio, an ambitious and passionate Japanese teacher from Finland. If you happen to love this little piece of code, have bug reports, feature suggestions or whatever, drop me a line!

E-mail: pyry.kontio@drasa.eu
Twitter: https://twitter.com/golddranks

Licenced with GPL 3
