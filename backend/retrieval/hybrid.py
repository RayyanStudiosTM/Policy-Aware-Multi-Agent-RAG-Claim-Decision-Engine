from __future__ import annotations
import json, math, re, pickle
from pathlib import Path
from collections import Counter
import numpy as np

TOKEN_RE=re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*")
def toks(s): return [x.lower() for x in TOKEN_RE.findall(s)]

class SimpleBM25:
    def __init__(self, docs, k1=1.5,b=0.75):
        self.docs=docs; self.k1=k1; self.b=b; self.tokens=[toks(d) for d in docs]
        self.df=Counter();
        for ts in self.tokens: self.df.update(set(ts))
        self.avgdl=sum(map(len,self.tokens))/max(1,len(self.tokens)); self.N=len(docs)
    def scores(self,q):
        qt=toks(q); out=[]
        for ts in self.tokens:
            tf=Counter(ts); dl=len(ts); s=0.0
            for term in qt:
                if term not in tf: continue
                df=self.df[term]; idf=math.log(1+(self.N-df+0.5)/(df+0.5))
                f=tf[term]; s += idf*(f*(self.k1+1))/(f+self.k1*(1-self.b+self.b*dl/max(1,self.avgdl)))
            out.append(s)
        return np.array(out)

class DenseIndex:
    def __init__(self, texts, model_name=None):
        self.backend='svd'
        self.model=None; self.matrix=None; self.vectorizer=None
        try:
            from sentence_transformers import SentenceTransformer
            self.model=SentenceTransformer(model_name or 'BAAI/bge-small-en-v1.5'); self.backend='sentence-transformers'
            self.matrix=self.model.encode(texts,normalize_embeddings=True,show_progress_bar=False)
        except Exception:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.decomposition import TruncatedSVD
            self.vectorizer=TfidfVectorizer(ngram_range=(1,2),min_df=1,max_features=12000,sublinear_tf=True)
            X=self.vectorizer.fit_transform(texts)
            ncomp=max(2,min(128,X.shape[1]-1 if X.shape[1]>2 else 2, X.shape[0]-1 if X.shape[0]>2 else 2))
            if X.shape[1] <= 2 or X.shape[0] <= 2:
                self.matrix=X.toarray(); self.svd=None
            else:
                from sklearn.preprocessing import normalize
                self.svd=TruncatedSVD(n_components=ncomp,random_state=42)
                self.matrix=normalize(self.svd.fit_transform(X))
    def encode(self,q):
        if self.backend=='sentence-transformers': return self.model.encode([q],normalize_embeddings=True)[0]
        from sklearn.preprocessing import normalize
        X=self.vectorizer.transform([q])
        if getattr(self,'svd',None) is not None: return normalize(self.svd.transform(X))[0]
        return X.toarray()[0]
    def scores(self,q): return np.asarray(self.matrix) @ self.encode(q)

class HybridRetriever:
    def __init__(self,chunks,index_dir='policy/processed'):
        self.chunks=chunks; self.texts=[c['text'] for c in chunks]; self.bm25=SimpleBM25(self.texts); self.dense=DenseIndex(self.texts)
    def search(self,q,k=8,rerank_k=12):
        ds=self.dense.scores(q); bs=self.bm25.scores(q)
        dr=np.argsort(-ds)[:rerank_k]; br=np.argsort(-bs)[:rerank_k]
        ranks={}
        for rank,i in enumerate(dr,1): ranks[i]=ranks.get(i,0)+1/(60+rank)
        for rank,i in enumerate(br,1): ranks[i]=ranks.get(i,0)+1/(60+rank)
        cand=sorted(ranks,key=ranks.get,reverse=True)[:rerank_k]
        # Lightweight cross-encoder fallback: query-term coverage + RRF. If available, use a real CrossEncoder.
        reranked=[]
        try:
            from sentence_transformers import CrossEncoder
            model=CrossEncoder('BAAI/bge-reranker-base')
            pairs=[(q,self.texts[i]) for i in cand]
            scores=model.predict(pairs)
            order=np.argsort(-np.asarray(scores))
            reranked=[(cand[j],float(scores[j]),'cross-encoder') for j in order[:k]]
        except Exception:
            qterms=set(toks(q))
            for i in cand:
                dt=set(toks(self.texts[i])); overlap=len(qterms&dt)/max(1,len(qterms));
                score=0.55*ranks[i]+0.45*overlap
                reranked.append((i,float(score),'lexical-rerank-fallback'))
            reranked.sort(key=lambda x:x[1],reverse=True); reranked=reranked[:k]
        return [{**self.chunks[i], 'dense_score':float(ds[i]), 'bm25_score':float(bs[i]), 'rrf_score':float(ranks[i]), 'rerank_score':s, 'reranker':method} for i,s,method in reranked]

def build_index(chunks_path='policy/processed/chunks.json'):
    # The retrieval index is intentionally rebuilt on startup; chunks are the source artifact.
    chunks=json.loads(Path(chunks_path).read_text(encoding='utf-8'))
    return HybridRetriever(chunks)
