// Cookie-authenticated website requests only. Backend bearer requests run server-side.
(() => {
 const nativeFetch = window.fetch;
 window.fetch = function(input, init) {
  const target = new URL(input instanceof Request ? input.url : input, location.href);
  const method = (init?.method || (input instanceof Request ? input.method : 'GET')).toUpperCase();
  if (target.origin === location.origin && !['GET','HEAD','OPTIONS'].includes(method)) {
   init = {...init};
   const headers = new Headers(init.headers || (input instanceof Request ? input.headers : undefined));
   headers.set('X-CSRFToken', document.querySelector('meta[name="csrf-token"]').content);
   init.headers = headers;
  }
  return nativeFetch.call(this, input, init);
 };
})();
