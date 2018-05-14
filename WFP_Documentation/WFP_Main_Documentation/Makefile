DOC=documentation

all:
	pdflatex $(DOC)
	bibtex $(DOC)
	pdflatex $(DOC)
	pdflatex $(DOC)

clean:
	find -name '*~' -exec rm -f {} \;
	rm -rf *.tdo *.log *.ps *.toc *.lo* *.bbl *.blg *.dvi *.idx *.ind *.ist *.glo *.glg *.alg *.acn *.acr *.out *.ilg *.gls *.aux *.pdf chapters/*.aux pictures/*.aux
