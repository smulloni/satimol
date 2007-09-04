DOCUTILS_HTML=/usr/bin/rst2html.py

manual.html:  manual.txt
	${DOCUTILS_HTML} -v -s --stylesheet=style.css manual.txt manual.html
clean: 
	-rm manual.html
