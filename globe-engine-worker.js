// GloBE Engine Worker — 분석을 메인 스레드에서 분리해 UI 블록 방지
// 사용: postMessage({entityList, edgeList, opts}) → postMessage({ok, result?, error?})

// 절대 URL로 해석 — 일부 환경(인앱 브라우저/확장이 워커를 blob으로 재포장, base 재정의 등)에서
// 상대경로 './'가 'invalid URL'로 깨지는 것을 방지. self.location 기준 동일 디렉터리의 엔진을 로드.
importScripts(new URL('globe-engine.min.js', self.location.href).href);

self.onmessage = function(ev){
  const {entityList, edgeList, opts} = ev.data || {};
  try {
    const opts2 = Object.assign({}, opts || {}, {
      progressCb: function(pct){ self.postMessage({type: 'progress', pct}); }
    });
    const result = runGloBEEngine(entityList, edgeList, opts2);
    self.postMessage({ok: true, result});
  } catch(err){
    self.postMessage({ok: false, error: err && err.message ? err.message : String(err)});
  }
};
