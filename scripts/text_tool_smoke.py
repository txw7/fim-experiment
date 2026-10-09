"""Exercise acquired extraction tools on one pinned passage from each family."""
import collections,csv,hashlib,importlib,json,os,random,sys
from pathlib import Path
import morfessor,spacy
from rakun2 import RakunKeyphraseDetector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'working/text-primitives'

def main():
    sources=[json.loads(s) for s in (OUT/'sources.jsonl').open()]
    chosen={}
    for d in sources:chosen.setdefault(d['family'],d)
    nlp=spacy.load('en_core_web_sm');detector=RakunKeyphraseDetector(dict(num_keywords=10,merge_threshold=1.1,alpha=.3,token_prune_len=3))
    rows=[]
    for family,d in chosen.items():
        parsed=nlp(d['text']);deps=[abs(t.i-t.head.i) for t in parsed if not t.is_punct and t.head!=t]
        rows.append(dict(family=family,source_id=d['id'],source_ref=d['source_ref'],
            source_text_sha256=hashlib.sha256(d['text'].encode()).hexdigest(),
            keywords=detector.find_keywords(d['text'],input_type='string'),
            parser_model='en_core_web_sm 3.8.0',dependency_distance_mean=sum(deps)/len(deps) if deps else None,
            dependency_edges=[dict(token=t.text,lemma=t.lemma_,head=t.head.text,relation=t.dep_,start=t.idx,end=t.idx+len(t)) for t in parsed]))
    (OUT/'tool-smoke.json').write_text(json.dumps(rows,indent=2,default=float))
    terms=[json.loads(s) for s in (OUT/'terms.jsonl').open()];random.seed(0)
    model=morfessor.BaselineModel();model.load_data((r['count'],r['term']) for r in terms);epochs,cost=model.train_batch(max_epochs=5)
    morfessor.MorfessorIO().write_binary_model_file(str(OUT/'morfessor.bin'),model)
    with (OUT/'morphemes.jsonl').open('w') as f:
        for r in terms:
            pieces,score=model.viterbi_segment(r['term']);f.write(json.dumps(dict(term=r['term'],segments=pieces,score=score))+'\n')
    (OUT/'morphology-receipt.json').write_text(json.dumps(dict(algorithm='Morfessor Baseline 2.0.6',epochs=epochs,cost=cost,seed=0,vocabulary=len(terms),authority='unsupervised morphological segmentation, not symbolic identity'),indent=2))
    taaco=ROOT/'deps/text-tools/TAACO';inputs=OUT/'taaco-input';inputs.mkdir(exist_ok=True)
    for family,d in chosen.items():(inputs/(family+'.txt')).write_text(d['text'])
    keys=['sourceKeyOverlap','sourceLSA','sourceLDA','sourceWord2vec','wordsAll','wordsContent','wordsFunction','wordsNoun','wordsPronoun','wordsArgument','wordsVerb','wordsAdjective','wordsAdverb','overlapSentence','overlapParagraph','overlapAdjacent','overlapAdjacent2','otherTTR','otherConnectives','otherGivenness','overlapLSA','overlapLDA','overlapWord2vec','overlapSynonym','overlapNgrams','outputTagged','outputDiagnostic']
    opts={k:k in {'wordsAll','wordsContent','overlapSentence','overlapAdjacent','otherTTR','otherConnectives','otherGivenness','outputDiagnostic'} for k in keys}
    sys.path.insert(0,str(taaco));cwd=Path.cwd()
    try:
        os.chdir(taaco);importlib.import_module('TAACOnoGUI').runTAACO(str(inputs)+'/',str(OUT/'taaco-smoke.csv'),opts)
    finally:os.chdir(cwd)
    with (OUT/'taaco-smoke.csv').open() as f:receipts=list(csv.DictReader(f))
    assert len(receipts)==len(chosen),(len(receipts),len(chosen))
    print(json.dumps(dict(status='tool runs passed',families=list(chosen),morfessor_epochs=epochs,taaco_rows=len(receipts))))
if __name__=='__main__':main()
