# Annotating Legal References (Allegationes) in the Liber Extra's Ordinary Gloss

This is the repository for the code for the automatic annotation of legal references in the Liber Extra's Ordinary Gloss.

The input to the code are the [digital version of the Ordinary Gloss](https://www.digitaldecretals.com/) and a training set of annotations from an expert, made using [INCEpTION](https://inception-project.github.io/) and exported in UIMA CAS XMI (XML 1.0) format.

The training of the model uses Conditional Random Fields.

The output is the full annotation of the Ordinary Gloss, in UIMA CAS XMI format, which can be imported back to INCEpTION, or further processed to produce additional knowledge.

We produced an [automatically generate index of all the legal references in the Liber Extra](https://zenodo.org/records/14381710) which lists for any legal reference the external norm that is references and in the Liber Extra its position identified by the title, the chapter, and the specific glossed lemma.

## Acknowledgment

This activity is supported by the [ITSERR project](https://www.itserr.it/).

Finanziato dall'Unione europea - NextGenerationEU