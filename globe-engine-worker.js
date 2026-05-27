// GloBE Engine Worker — 분석을 메인 스레드에서 분리해 UI 블록 방지
// 사용: postMessage({entityList, edgeList, opts}) → postMessage({ok, result?, error?})

importScripts('./globe-engine.min.js');

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
