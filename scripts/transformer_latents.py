"""Local MiniLM concept cosine and latent projections for the pinned corpus."""
import collections, hashlib, json, math, os, re, sys
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]/'working/text-primitives'
OUT=ROOT
MODEL=Path('/home/user0/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/1110a243fdf4706b3f48f1d95db1a4f5529b4d41')
STUDENT=Path('/home/user0/.local/state/turn-transport/philosophy-stream-v1/student')
STUDENT_CODE=Path('/home/user0/worktrees/research-laya-qwen-rg-ingestion-v1/corpusGraph/semantic_tower')
MULTI=Path('/home/user0/.local/state/turn-transport/philosophy-multitype-v1')
TOKEN=re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)?",re.UNICODE)
FAMILIES=['me','plato','parmenides','aristotle']
STOP=set('the a an and or of to in is are was were be been being for from with by on that this it as if then than not no can could would should which who what have has had do does did its their they them we our i you he she'.split())

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def readjsonl(path):return [json.loads(x) for x in Path(path).read_text().splitlines() if x]
def dump(path,value):Path(path).write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n')

def local_student_logits(texts):
    sys.path.insert(0,str(STUDENT_CODE))
    import torch
    from student_stream import Student,batch,LABELS
    torch.set_num_threads(2)
    output={}
    for which in ('incumbent','live'):
        path=STUDENT/(which+'.pt')
        checkpoint=torch.load(path,map_location='cpu',weights_only=True)
        model=Student().eval();model.load_state_dict(checkpoint['state_dict'])
        rows=[]
        with torch.no_grad():
            for start in range(0,len(texts),64):
                x,_=batch([{'text':t} for t in texts[start:start+64]])
                logits=model(x).cpu().numpy()
                rows.extend(logits.tolist())
        output[which]={'step':checkpoint['step'],'watermark':checkpoint['watermark'],'labels':LABELS,'logits':rows,
            'checkpoint_sha256':sha(path),'parameter_count':sum(p.numel() for p in model.parameters())}
    return output

def main():
    import torch
    from transformers import AutoModel,AutoTokenizer
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA
    torch.set_num_threads(4)
    docs=readjsonl(ROOT/'sources.jsonl');ids=[d['id'] for d in docs];texts=[d['text'] for d in docs]
    if not MODEL.exists() or not (MODEL/'model.safetensors').exists():raise FileNotFoundError('Cached MiniLM weights absent; offline run refused')
    tokenizer=AutoTokenizer.from_pretrained(str(MODEL),local_files_only=True)
    model=AutoModel.from_pretrained(str(MODEL),local_files_only=True).eval().to('cpu')
    vectors=[];truncated=0
    with torch.inference_mode():
        for start in range(0,len(texts),48):
            batch=tokenizer(texts[start:start+48],padding=True,truncation=True,max_length=256,return_tensors='pt')
            truncated+=sum(int(v>=256) for v in batch['attention_mask'].sum(1).tolist())
            hidden=model(**batch).last_hidden_state;mask=batch['attention_mask'].unsqueeze(-1)
            pooled=(hidden*mask).sum(1)/mask.sum(1).clamp(min=1)
            vectors.append(torch.nn.functional.normalize(pooled,p=2,dim=1).cpu().numpy())
    vectors=np.concatenate(vectors).astype('float32');assert vectors.shape==(len(docs),384)
    counts=collections.Counter()
    for d in docs:counts.update(t.casefold() for t in TOKEN.findall(d['text']))
    # Frequency-ranked concept inventory plus the logical/concept anchors used in the lexical pass.
    concepts=[t for t,c in counts.most_common() if c>=5 and t not in STOP and len(t)>2][:44]
    anchors=['truth','false','falseness','being','one','substance','form','all','things','not','and','or','implies','identity','negation','whole','part','cause','change','same','different']
    concepts=list(dict.fromkeys([*anchors,*concepts]))[:64]
    cv=[]
    with torch.inference_mode():
        for start in range(0,len(concepts),64):
            batch=tokenizer(concepts[start:start+64],padding=True,truncation=True,max_length=24,return_tensors='pt')
            hidden=model(**batch).last_hidden_state;mask=batch['attention_mask'].unsqueeze(-1)
            pooled=(hidden*mask).sum(1)/mask.sum(1).clamp(min=1)
            cv.append(torch.nn.functional.normalize(pooled,p=2,dim=1).cpu().numpy())
    cv=np.concatenate(cv).astype('float32');sims=cv@vectors.T
    # 32-dimensional PCA retains a compact auditable latent vector; 2D is a viewer projection only.
    pca=PCA(n_components=32,random_state=17);latent=pca.fit_transform(vectors).astype('float32')
    xy=PCA(n_components=2,random_state=17).fit_transform(vectors).astype('float32')
    clusters=KMeans(n_clusters=12,random_state=17,n_init=10).fit_predict(latent)
    # Exact cosine kNN over normalized 384D vectors. Float32 block multiply avoids GPU use.
    neighbors=[]
    for start in range(0,len(vectors),256):
        block=vectors[start:start+256]@vectors.T
        for j,row in enumerate(block):
            i=start+j;row[i]=-2;ix=np.argpartition(row,-6)[-6:];ix=ix[np.argsort(row[ix])[::-1]]
            neighbors.append([(ids[int(k)],round(float(row[k]),6)) for k in ix])
    # Cosine links between concept vectors, plus nearest corpus passages per concept.
    cm=cv@cv.T;concept_edges=[]
    for i,name in enumerate(concepts):
        js=[j for j in range(len(concepts)) if j!=i]
        for j in sorted(js,key=lambda q:float(cm[i,q]),reverse=True)[:3]:
            if i<j:concept_edges.append({'source':name,'target':concepts[j],'cosine':round(float(cm[i,j]),6)})
    # Deduplicate the top-neighbor graph and retain its edge weight/provenance.
    for edge in concept_edges:edge['kind']='MiniLM cosine; distributional similarity, not identity'
    rows=[];cluster_counts=collections.Counter()
    for i,d in enumerate(docs):
        family=d['family'];cluster_counts[(family,int(clusters[i]))]+=1
        top=np.argsort(sims[:,i])[-5:][::-1]
        rows.append({'source_id':d['id'],'family':family,'source_ref':d['source_ref'],
            'text_sha256':hashlib.sha256(d['text'].encode()).hexdigest(),'cluster':int(clusters[i]),
            'pca2':[round(float(x),6) for x in xy[i]],'latent32':[round(float(x),6) for x in latent[i]],
            'neighbors':[{'source_id':a,'cosine':b} for a,b in neighbors[i]],
            'keyword_cosines':[{'keyword':concepts[int(k)],'cosine':round(float(sims[k,i]),6)} for k in top]})
    # Family centroids compare author/corpus distributions, not historical semantic change.
    family_ix={f:[i for i,d in enumerate(docs) if d['family']==f] for f in FAMILIES}
    centroids={f:(vectors[ix].mean(0)/np.linalg.norm(vectors[ix].mean(0))).astype('float32') for f,ix in family_ix.items()}
    family_cosine={f:{g:round(float(centroids[f]@centroids[g]),6) for g in FAMILIES} for f in FAMILIES}
    per_concept={}
    for i,c in enumerate(concepts):
        per_concept[c]={f:[{'source_id':ids[int(k)],'cosine':round(float(sims[i,k]),6)} for k in np.argsort(sims[i,family_ix[f]])[-3:][::-1]] for f in FAMILIES}
    # Capture raw head outputs from the local CPU student, both live candidate and frozen incumbent.
    student=local_student_logits(texts)
    for i,row in enumerate(rows):
        row['student_logits']={which:{name:round(float(v),7) for name,v in zip(data['labels'],data['logits'][i])} for which,data in student.items()}
        row['student_model_steps']={which:data['step'] for which,data in student.items()}
    output={
      'schema':'PhilosopherTransformerLatentsV1','source_manifest_sha256':sha(ROOT/'manifest.json'),
      'model':{'name':'sentence-transformers/all-MiniLM-L6-v2','revision':'1110a243fdf4706b3f48f1d95db1a4f5529b4d41','weights_sha256':sha(MODEL/'model.safetensors'),'config_sha256':sha(MODEL/'config.json'),'pooling':'attention-mask mean, L2 normalized','device':'cpu','truncated_at_256_tokens':truncated},
      'shape':[len(docs),vectors.shape[1]],'latent_shape':[len(docs),latent.shape[1]],
      'pca32_explained_variance_ratio':pca.explained_variance_ratio_.tolist(),
      'cluster_count':12,'clusters_by_family':{f:{str(k):cluster_counts[(f,k)] for k in range(12)} for f in FAMILIES},
      'family_centroid_cosine':family_cosine,'concepts':concepts,'concept_cosine_edges':concept_edges,
      'concept_nearest_source_units':per_concept,
      'student_models':{k:{'step':v['step'],'watermark':v['watermark'],'labels':v['labels'],'checkpoint_sha256':v['checkpoint_sha256'],'parameters':v['parameter_count'],'training_data_unique_records':7,'validation_gated':'incumbent' if k=='incumbent' else 'live candidate'} for k,v in student.items()},
      'interpretation':'Cosine/PCA/clusters are model-space similarity, not logical identity, entailment, gold labels, or diachronic change.'}
    np.savez_compressed(OUT/'transformer-latents.npz',source_ids=np.array(ids),vectors=vectors,concepts=np.array(concepts),concept_vectors=cv,latent32=latent,pca2=xy,clusters=clusters)
    dump(OUT/'transformer-latent-index.json',output);dump(OUT/'transformer-latent-rows.json',rows)
    dump(OUT/'transformer-concept-network.json',{'nodes':[{'id':c,'count':counts[c]} for c in concepts],'edges':concept_edges})
    # Retain the prior local Laya probability distributions and Qwen raw feedback completions.
    src=json.loads((MULTI/'sources.json').read_text());results=json.loads((MULTI/'results.json').read_text());model_rows=[]
    for r in results:
        if r.get('provider')!='laya':continue
        base=MULTI/'laya'/r['id']/r['mode'];resp=json.loads((base/'response.json').read_text())
        raw_qwen=json.loads((base/'qwen.response.json').read_text()) if (base/'qwen.response.json').exists() else None
        srow=next(x for x in src if x['id']==r['id'])
        model_rows.append({'source_case_id':r['id'],'source_text':srow['source'],'source_ref':srow['source_ref'],
          'provider':'Laya','model':resp.get('model'),'mode':r['mode'],'answers':resp.get('answers'),
          'metric_snapshot':{k:r.get(k) for k in ['heads','correct','logloss','brier']},
          'raw_response_sha256':sha(base/'response.json'),'raw_qwen':raw_qwen,
          'qwen_raw_response_sha256':sha(base/'qwen.response.json') if raw_qwen is not None else None,
          'qwen_probability_status':'not returned; raw completion retained' if raw_qwen is not None else 'no Qwen call in this mode',
          'authority':'prior local model outputs; diagnostic reference labels were authored, not independent human gold'})
    dump(OUT/'local-model-observations.json',model_rows)
    print(json.dumps({'status':'complete','source_units':len(docs),'model':output['model']['name'],'embedding_shape':list(vectors.shape),'concepts':len(concepts),'concept_edges':len(concept_edges),'clusters':12,'student_logits_per_source':len(rows)*2,'prior_local_teacher_observations':len(model_rows),'device':'cpu','output':str(OUT)},indent=2))

if __name__=='__main__':main()
