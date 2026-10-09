"""Admit the four-corpus lexical/transformer outputs as a new ResearchGraph."""
import hashlib,json,sys,time
from pathlib import Path
CAS_CODE=Path('/home/user0/worktrees/research-laya-qwen-rg-ingestion-v1/corpusGraph')
sys.path.insert(0,str(CAS_CODE))
from recursive_cas import RecursiveCASRepository,Transaction,cas_ref,blob_ref,new_object
from recursive_cas.research import (dataset,environment,experiment,experiment_run,hypothesis,method,model,
    observation,research_program,research_question,validate_research_root)

ROOT=Path(__file__).resolve().parents[1]/'working/text-primitives'
RUN=Path('/home/user0/.local/state/turn-transport/philosopher-text-structure-v1')
GRAPH=RUN/'research-graph';RUN.mkdir(parents=True,exist_ok=True)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def filehash(p):return sha(Path(p).read_bytes())
def readjson(p):return json.loads(Path(p).read_text())
def put(repo,obj):rev=repo.put_canonical(obj);return cas_ref(rev,obj['id'])
def edge(ref,relation='derived_from'):return {'relation':relation,'domain':'provenance','target':ref}

def main():
    assert not GRAPH.exists() or not any(GRAPH.iterdir()),'Refusing to replace an existing ResearchGraph'
    repo=RecursiveCASRepository(GRAPH);assert repo.head is None
    source_rows=[json.loads(x) for x in (ROOT/'sources.jsonl').read_text().splitlines() if x]
    latent_rows=readjson(ROOT/'transformer-latent-rows.json');latent_index=readjson(ROOT/'transformer-latent-index.json')
    local_rows=readjson(ROOT/'local-model-observations.json');text_manifest=readjson(ROOT/'manifest.json')
    artifact_refs={};artifact_objects=[]
    def artifact(path,*,source_system='four-corpus-experiment',capture='immutable source/output byte snapshot'):
        path=Path(path);raw=path.read_bytes();ident='artifact:philosopher-text:'+hashlib.sha256(str(path.resolve()).encode()).hexdigest()[:20]
        obj=new_object(ident,kind='artifact',schema='ArtifactV1',value={'name':path.name,'path_at_capture':str(path.resolve()),'sha256':sha(raw),'bytes':len(raw),'payload':blob_ref(repo.blobs.put(raw)),'source_system':source_system,'capture':capture},authority={'evidence_class':'source_evidence','review_state':'accepted'})
        ref=put(repo,obj);artifact_refs[str(path.resolve())]=ref;artifact_objects.append((obj,ref));return ref
    # Pin the source snapshot and every underlying file named by its origin reference.
    raw_inputs={}
    verified_source_hashes={}
    for row in source_rows:
        ref=row['source_ref'];path=Path(ref['path'])
        if path.is_file():
            key=path.resolve()
            if key not in verified_source_hashes:
                verified_source_hashes[key]=filehash(path)
            assert verified_source_hashes[key]==ref['sha256'],f"source digest changed: {path}"
            raw_inputs[key]=path
    for path in sorted(raw_inputs):artifact(path,source_system='source-corpus',capture='original corpus bytes; SHA verified against source manifest')
    manifest_inputs=[ROOT/n for n in ['sources.jsonl','manifest.json','extended-metrics.json','terms.jsonl','normalization.jsonl','ngrams-2.jsonl','ngrams-3.jsonl','association.jsonl','document-metrics.jsonl','dispersion.jsonl','dispersion-dp.jsonl','tfidf.jsonl','zipf.jsonl','keyword-network.json','count-surprisal.jsonl','lexical-specificity.jsonl','skipgrams.jsonl','cross-family-trigrams.jsonl','edit-variants.jsonl','transformer-latents.npz','transformer-latent-index.json','transformer-latent-rows.json','transformer-concept-network.json','local-model-observations.json','scripts/../manifest.json']]
    for path in manifest_inputs:
        if path.is_file() and str(path.resolve()) not in artifact_refs:artifact(path)
    for path in [Path(__file__),Path(__file__).with_name('text_primitives.py'),Path(__file__).with_name('extended_text_metrics.py'),Path(__file__).with_name('transformer_latents.py'),Path(__file__).with_name('keyword_view.py')]:artifact(path,source_system='analysis-code',capture='code snapshot at graph admission')
    multi=Path('/home/user0/.local/state/turn-transport/philosophy-multitype-v1')
    run_manifest=readjson(multi/'manifest.json')
    artifact(multi/'manifest.json',source_system='prior-local-model-run',capture='original run manifest; pins request and response files')
    for rel,digest in run_manifest['files'].items():
        path=multi/rel
        if not path.is_file():raise FileNotFoundError(path)
        assert filehash(path)==digest,f'prior local output hash mismatch: {path}'
        if str(path.resolve()) not in artifact_refs:artifact(path,source_system='prior-local-model-run',capture='hash verified against original run manifest')
    # Capture model weights/configs used for this run. Teacher Qwen/Laya weights were not available in the prior receipt.
    minilm=Path('/home/user0/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/1110a243fdf4706b3f48f1d95db1a4f5529b4d41')
    for name in ['model.safetensors','config.json','tokenizer.json','tokenizer_config.json','modules.json','sentence_bert_config.json']:
        p=minilm/name
        if p.exists() and str(p.resolve()) not in artifact_refs:artifact(p,source_system='local-transformer-model',capture='exact cached model component')
    student_dir=Path('/home/user0/.local/state/turn-transport/philosophy-stream-v1/student')
    for name in ['live.pt','incumbent.pt']:
        p=student_dir/name
        if p.exists() and str(p.resolve()) not in artifact_refs:artifact(p,source_system='local-student-model',capture='exact local checkpoint used for score extraction')
    def ref(path):return artifact_refs[str(Path(path).resolve())]
    def model_obj(ident,name,family,architecture,weights=None):
        obj=model(ident,name,family=family,architecture=architecture,weights_ref=weights)
        return obj,put(repo,obj)
    minilm_art=ref(minilm/'model.safetensors');live_art=ref(student_dir/'live.pt');inc_art=ref(student_dir/'incumbent.pt')
    models={}
    specs=[
      ('minilm','sentence-transformers/all-MiniLM-L6-v2','Transformer sentence embedder',{'revision':latent_index['model']['revision'],'pooling':latent_index['model']['pooling'],'weights_sha256':latent_index['model']['weights_sha256'],'device':'cpu'},minilm_art),
      ('student-incumbent','TinyStudentV1 incumbent','Small local transformer classifier',{'head_logits':'10 explicit operator presence heads','step':latent_index['student_models']['incumbent']['step'],'unique_training_records':7,'validation_gated':True},inc_art),
      ('student-live','TinyStudentV1 live candidate','Small local transformer classifier',{'head_logits':'10 explicit operator presence heads','step':latent_index['student_models']['live']['step'],'unique_training_records':7,'validation_gated':False},live_art),
      ('laya','laya-rl-agent','Local multi-type classifier',{'execution':'prior source-pinned run','native_output':'categorical probability distributions','checkpoint_sha256':'not recorded in original run'},None),
      ('qwen','Qwen3.5-9B-Q4_K_M','Local generative transformer',{'execution':'prior source-pinned run','native_output':'raw completion text; token logprobs not recorded','system_fingerprint':'retained in raw response artifacts','checkpoint_sha256':'not recorded in original run'},None)]
    for key,name,fam,arch,w in specs:models[key]=model_obj('model:philosopher-text:'+key,name,fam,arch,w)
    dataset_obj=dataset('dataset:philosopher-text-four-corpora','Essay, Plato, Parmenides, Aristotle source-unit corpus',task='source-grounded lexical statistics, transformer similarity and fallible operator observations',content_digest=filehash(ROOT/'sources.jsonl'),split_policy={'source_manifest_sha256':text_manifest['files']['sources'],'families':text_manifest['families'],'chronology':'not present','source_unit_boundaries':'preserved','truth_labels':'no gold labels; existing local model diagnostic references only'})
    ds_ref=put(repo,dataset_obj)
    methods=[]
    for ident,name,fam,params in [
      ('count-measures','Count-based lexical and graph measures','distributional-counts',{'window':5,'ngram_sizes':[1,2,3,4],'association':'PMI/PPMI/NPMI/lift/confidence/conviction/LogDice/LLR','source_boundaries':True}),
      ('transformer-latents','MiniLM embeddings and cosine neighborhood analysis','transformer-embedding',{'metric':'cosine','pca_dimensions':32,'viewer_projection_dimensions':2,'kmeans_clusters':12,'source_unit_count':len(source_rows)}),
      ('local-logits','Tiny student raw operator-head logits','local-transformer-classifier',{'classes':latent_index['student_models']['live']['labels'],'incumbent_step':latent_index['student_models']['incumbent']['step'],'live_step':latent_index['student_models']['live']['step'],'unique_training_records':7}),
      ('teacher-observations','Prior Laya probability and Qwen completion observations','local-model-observation',{'run_manifest_sha256':filehash(multi/'manifest.json'),'prompts_and_raw_outputs':'hash-verified artifacts','probability_calibration':'not established'})]:
        o=method('method:philosopher-text:'+ident,name,method_family=fam,parameters=params,version='v1');methods.append((o,put(repo,o)))
    env=new_object('environment:philosopher-text-local',kind='environment',schema='EnvironmentV1',value={'device':'CPU for MiniLM and student score extraction','source_root':str(ROOT),'model_server_outputs':'prior source-pinned local run','gpu_model_inference_added':False})
    env_ref=put(repo,env)
    qref_id='question:philosopher-text-structure-v1';hyp_id='hypothesis:philosopher-text-structure-v1';exp_id='experiment:philosopher-text-structure-v1';run_id='run:philosopher-text-structure-v1';program_id='program:philosopher-text-structure-v1'
    hyp=hypothesis(hyp_id,'Model-free measures and local transformer representations expose complementary structure in four philosophical corpora.',scope={'exploratory':True,'no_truth_verification':True,'no_gold_training':True});hyp_ref=put(repo,hyp)
    question=research_question(qref_id,'How do sequence, association, graph, transformer and local operator scores relate across the four pinned corpora?',hypotheses=[hyp]);question_ref=put(repo,question)
    observations=[];source_refs={}
    for row in source_rows:
        sid=row['id'];short=hashlib.sha256(sid.encode()).hexdigest()[:16];source_art=ref(ROOT/'sources.jsonl')
        obj=new_object('source-span:philosopher-text:'+short,kind='source_span',schema='SourceSpanV1',value={'source_id':sid,'family':row['family'],'text':row['text'],'text_sha256':sha(row['text'].encode()),'original_source_ref':row['source_ref'],'source_inventory_ref':source_art},links=[edge(source_art)],authority={'evidence_class':'source_evidence','review_state':'accepted'})
        source_refs[sid]=put(repo,obj)
    latent_art=ref(ROOT/'transformer-latent-rows.json')
    latent_matrix=ref(ROOT/'transformer-latents.npz')
    for family in ('me','plato','parmenides','aristotle'):
        family_rows=[r for r in latent_rows if r['family']==family]
        obs=observation('observation:philosopher-text:latent-logits:'+family,run_id,'transformer_embedding_cosines_and_student_raw_logits',{
          'family':family,'source_ids':[r['source_id'] for r in family_rows],
          'source_text_sha256':[r['text_sha256'] for r in family_rows],
          'transformer_model_ref':models['minilm'][1],
          'per_source_vectors_cosine_neighbors_keyword_cosines_and_raw_student_logits_artifact_ref':latent_art,
          'full_embedding_matrix_artifact_ref':latent_matrix,
          'student_model_steps':latent_index['student_models'],
          'score_authority':'per-source values are in the hash-pinned artifact; experimental, uncalibrated; seven unique training records; not gold or proof'},artifact_ref=latent_art)
        obs['links'].extend([edge(models['minilm'][1]),edge(models['student-incumbent'][1]),edge(models['student-live'][1]),edge(latent_matrix)])
        observations.append(obs)
    # Keep actual local teacher outputs separate from the fresh transformer pass and from reference judgments.
    for i,row in enumerate(local_rows):
        sid=row['source_case_id'];rid='local-model-observation:'+hashlib.sha256(f"{sid}:{row['mode']}:laya".encode()).hexdigest()[:18]
        src_obj=new_object('source-span:philosopher-text:teacher:'+hashlib.sha256(f"{sid}:{row['mode']}".encode()).hexdigest()[:18],kind='source_span',schema='SourceSpanV1',value={'source_id':'local-teacher:'+sid,'text':row['source_text'],'text_sha256':sha(row['source_text'].encode()),'original_source_ref':row['source_ref']},authority={'evidence_class':'source_evidence','review_state':'accepted'})
        src_ref=put(repo,src_obj);source_refs[f'local-teacher:{i}:{sid}:{row["mode"]}']=src_ref;resp_path=multi/'laya'/sid/row['mode']/'response.json';resp_ref=ref(resp_path)
        val={'case_id':sid,'source_text':row['source_text'],'source_ref':row['source_ref'],'mode':row['mode'],'answers':row['answers'],'metric_snapshot':row['metric_snapshot'],'native_score_kind':'categorical_probabilities','calibration':'not established','diagnostic_reference':'Codex-authored, not independent human gold','qwen_completion':row['raw_qwen']['choices'][0]['message']['content'] if row['raw_qwen'] else None,'qwen_score_kind':row['qwen_probability_status']}
        obs=observation('observation:philosopher-text:'+rid,run_id,'local_laya_probabilities_and_qwen_completion',val,artifact_ref=resp_ref)
        obs['links'].extend([edge(src_ref),edge(models['laya'][1]),edge(resp_ref),edge(ref(multi/'manifest.json'))])
        if row['raw_qwen']:
            qref=ref(multi/'laya'/sid/row['mode']/'qwen.response.json');obs['links'].extend([edge(models['qwen'][1]),edge(qref)])
        observations.append(obs)
    summary_art=ref(ROOT/'extended-metrics.json');latent_summary_art=ref(ROOT/'transformer-latent-index.json')
    summary=observation('observation:philosopher-text:corpus-measures',run_id,'four-corpus_measurement_summary',{'source_manifest_sha256':text_manifest['files']['sources'],'extended_metrics_sha256':filehash(ROOT/'extended-metrics.json'),'transformer_latent_summary_sha256':filehash(ROOT/'transformer-latent-index.json'),'counts':{'source_units':len(source_rows),'transformer_vectors':len(latent_rows),'local_teacher_rows':len(local_rows)},'scope':'all 7,723 source units; statistics are descriptive; no diachronic/sense annotations'},artifact_ref=summary_art)
    summary['links'].extend([edge(ds_ref),edge(summary_art),edge(latent_summary_art),edge(ref(ROOT/'association.jsonl')),edge(ref(ROOT/'keyword-network.json'))]);observations.append(summary)
    run_obj=experiment_run(run_id,exp_id,configuration={'source_manifest_sha256':text_manifest['files']['sources'],'transformer_revision':latent_index['model']['revision'],'transformer_device':'cpu','full_latent_archive':ref(ROOT/'transformer-latents.npz'),'local_teacher_run_manifest_sha256':filehash(multi/'manifest.json'),'score_types_separated':True,'diachronic_claims':False},observations=observations)
    run_ref=put(repo,run_obj)
    exp=experiment(exp_id,'Four-corpus lexical, transformer and local-model results graph',hyp_id,runs=[run_obj],dataset_pins=[ds_ref],model_pins=[x[1] for x in models.values()],environment_pins=[env_ref],method_pins=[x[1] for x in methods],source_pins=[ref(ROOT/'sources.jsonl'),ref(ROOT/'manifest.json')],design={'source_units':len(source_rows),'transformer_embeddings':len(latent_rows),'local_teacher_observations':len(local_rows),'student_logits':'incumbent and live raw ten-head outputs','gold_labels':False,'training':False,'temporal_slices':False},acceptance_criteria={'provenance':'all byte artifacts SHA checked on CAS readback','interpretation':'observations are not logical proofs'})
    exp_ref=put(repo,exp)
    program=research_program(program_id,'Philosopher corpus structure and local model evidence',description='Source-grounded distributional measures, MiniLM cosine/latent geometry, and distinct local-model score types.',questions=[question],experiments=[exp]);program_ref=put(repo,program)
    content={'research_programs':{program_id:program_ref},'datasets':{dataset_obj['id']:ds_ref},'models':{o['id']:r for o,r in models.values()},'methods':{o['id']:r for o,r in methods},'environments':{env['id']:env_ref},'sources':source_refs,'artifacts':{o['id']:r for o,r in artifact_objects}}
    root=new_object('research-universe:philosopher-text-structure-v1',kind='research_universe',schema='ResearchUniverseV1',value={'version':1,'title':'Essay · Plato · Parmenides · Aristotle'},content=content,authority={'evidence_class':'empirical_measurement','review_state':'candidate'})
    commit=repo.commit(None,Transaction(base_commit=None,root=root,metadata={'source':'four-corpus-transformer-latent-and-local-model-ingestion-v1','source_manifest_sha256':text_manifest['files']['sources']}))
    root_rev=repo.root_revision(commit);assert validate_research_root(repo,root_rev)
    for obj,refv in artifact_objects:
        actual=repo.get_revision(refv['$cas']);raw=repo.blobs.get(actual['value']['payload']['$blob']);assert sha(raw)==actual['value']['sha256']
    assert repo.head==commit
    receipt={'schema':'PhilosopherTextResearchGraphAdmissionV1','graph':str(GRAPH),'commit_id':commit,'root_revision':root_rev,'parent_commit':None,'source_units':len(source_rows),'source_spans':len(source_refs),'artifacts':len(artifact_objects),'observations':len(observations),'transformer_observations':4,'per_source_transformer_rows_in_artifact':len(latent_rows),'local_teacher_observations':len(local_rows),'byte_snapshots_verified':True,'native_research_root_validated':True,'score_types':'student raw logits; Laya probabilities; Qwen raw completions','diachrony':'not inferred','head_unchanged_after_commit':repo.head==commit}
    (RUN/'admission-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
