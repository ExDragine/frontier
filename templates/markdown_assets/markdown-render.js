(function(){var e=Object.create,t=Object.defineProperty,n=Object.getOwnPropertyDescriptor,r=Object.getOwnPropertyNames,i=Object.getPrototypeOf,a=Object.prototype.hasOwnProperty,o=(e,t,n)=>()=>{if(n)throw n[0];try{return e&&(t=e(e=0)),t}catch(e){throw n=[e],e}},s=(e,t)=>()=>(t||(e((t={exports:{}}).exports,t),e=null),t.exports),l=(e,n)=>{let r={};for(var i in e)t(r,i,{get:e[i],enumerable:!0});return n||t(r,Symbol.toStringTag,{value:`Module`}),r},u=(e,i,o,s)=>{if(i&&typeof i==`object`||typeof i==`function`)for(var l=r(i),u=0,d=l.length,f;u<d;u++)f=l[u],!a.call(e,f)&&f!==o&&t(e,f,{get:(e=>i[e]).bind(null,f),enumerable:!(s=n(i,f))||s.enumerable});return e},d=(n,r,a)=>(a=n==null?{}:e(i(n)),u(r||!n||!n.__esModule?t(a,`default`,{value:n,enumerable:!0}):a,n)),f=function(e,t){return f=Object.setPrototypeOf||{__proto__:[]}instanceof Array&&function(e,t){e.__proto__=t}||function(e,t){for(var n in t)Object.prototype.hasOwnProperty.call(t,n)&&(e[n]=t[n])},f(e,t)};function p(e,t){if(typeof t!=`function`&&t!==null)throw TypeError(`Class extends value `+String(t)+` is not a constructor or null`);f(e,t);function n(){this.constructor=e}e.prototype=t===null?Object.create(t):(n.prototype=t.prototype,new n)}var m=`12px sans-serif`,h=20,g=100,_=`007LLmW'55;N0500LLLLLLLLLL00NNNLzWW\\\\WQb\\0FWLg\\bWb\\WQ\\WrWWQ000CL5LLFLL0LL**F*gLLLL5F0LF\\FFF5.5N`;function v(e){var t={};if(typeof JSON>`u`)return t;for(var n=0;n<e.length;n++){var r=String.fromCharCode(n+32);t[r]=(e.charCodeAt(n)-h)/g}return t}var y=v(_),b={createCanvas:function(){return typeof document<`u`&&document.createElement(`canvas`)},measureText:(function(){var e,t;return function(n,r){if(!e){var i=b.createCanvas();e=i&&i.getContext(`2d`)}if(e)return t!==r&&(t=e.font=r||`12px sans-serif`),e.measureText(n);n||=``,r||=`12px sans-serif`;var a=/((?:\d+)?\.?\d*)px/.exec(r),o=a&&+a[1]||12,s=0;if(r.indexOf(`mono`)>=0)s=o*n.length;else for(var l=0;l<n.length;l++){var u=y[n[l]];s+=u==null?o:u*o}return{width:s}}})(),loadImage:function(e,t,n){var r=new Image;return r.onload=t,r.onerror=n,r.src=e,r},getTime:function(){return Date.now?Date.now():+new Date}},x=se([`Function`,`RegExp`,`Date`,`Error`,`CanvasGradient`,`CanvasPattern`,`Image`,`Canvas`],function(e,t){return e[`[object `+t+`]`]=!0,e},{}),S=se([`Int8`,`Uint8`,`Uint8Clamped`,`Int16`,`Uint16`,`Int32`,`Uint32`,`Float32`,`Float64`],function(e,t){return e[`[object `+t+`Array]`]=!0,e},{}),C=Object.prototype.toString,w=Array.prototype,T=w.forEach,E=w.filter,D=w.slice,O=w.map,k=function(){}.constructor,A=k?k.prototype:null,j=`__proto__`,M=2311,N=2**53-1;function P(){return M>=N&&(M=0),M++}function F(){for(var e=[],t=0;t<arguments.length;t++)e[t]=arguments[t];typeof console<`u`&&console.error.apply(console,e)}function I(e){if(typeof e!=`object`||!e)return e;var t=e,n=C.call(e);if(n===`[object Array]`){if(!Pe(e)){t=[];for(var r=0,i=e.length;r<i;r++)t[r]=I(e[r])}}else if(S[n]){if(!Pe(e)){var a=e.constructor;if(a.from)t=a.from(e);else{t=new a(e.length);for(var r=0,i=e.length;r<i;r++)t[r]=e[r]}}}else if(!x[n]&&!Pe(e)&&!Se(e))for(var o in t={},e)e.hasOwnProperty(o)&&o!==j&&(t[o]=I(e[o]));return t}function L(e,t,n){if(!ye(t)||!ye(e))return n?I(t):e;for(var r in t)if(t.hasOwnProperty(r)&&r!==j){var i=e[r],a=t[r];ye(a)&&ye(i)&&!me(a)&&!me(i)&&!Se(a)&&!Se(i)&&!be(a)&&!be(i)&&!Pe(a)&&!Pe(i)?L(i,a,n):(n||!(r in e))&&(e[r]=I(t[r]))}return e}function R(e,t){if(Object.assign)Object.assign(e,t);else for(var n in t)t.hasOwnProperty(n)&&n!==j&&(e[n]=t[n]);return e}function ee(e,t,n){e||={};for(var r=0;r<n.length;r++){var i=n[r];e[i]=t[i]}return e}function te(e,t,n){for(var r=ue(t),i=0,a=r.length;i<a;i++){var o=r[i];(n?t[o]!=null:e[o]==null)&&(e[o]=t[o])}return e}b.createCanvas;function ne(e,t){if(e){if(e.indexOf)return e.indexOf(t);for(var n=0,r=e.length;n<r;n++)if(e[n]===t)return n}return-1}function re(e,t){var n=e.prototype;function r(){}for(var i in r.prototype=t.prototype,e.prototype=new r,n)n.hasOwnProperty(i)&&(e.prototype[i]=n[i]);e.prototype.constructor=e,e.superClass=t}function ie(e,t,n){if(e=`prototype`in e?e.prototype:e,t=`prototype`in t?t.prototype:t,Object.getOwnPropertyNames)for(var r=Object.getOwnPropertyNames(t),i=0;i<r.length;i++){var a=r[i];a!==`constructor`&&(n?t[a]!=null:e[a]==null)&&(e[a]=t[a])}else te(e,t,n)}function ae(e){return!e||typeof e==`string`?!1:typeof e.length==`number`}function z(e,t,n){if(e&&t)if(e.forEach&&e.forEach===T)e.forEach(t,n);else if(e.length===+e.length)for(var r=0,i=e.length;r<i;r++)t.call(n,e[r],r,e);else for(var a in e)e.hasOwnProperty(a)&&t.call(n,e[a],a,e)}function oe(e,t,n){if(!e)return[];if(!t)return Oe(e);if(e.map&&e.map===O)return e.map(t,n);for(var r=[],i=0,a=e.length;i<a;i++)r.push(t.call(n,e[i],i,e));return r}function se(e,t,n,r){if(e&&t){for(var i=0,a=e.length;i<a;i++)n=t.call(r,n,e[i],i,e);return n}}function ce(e,t,n){if(!e)return[];if(!t)return Oe(e);if(e.filter&&e.filter===E)return e.filter(t,n);for(var r=[],i=0,a=e.length;i<a;i++)t.call(n,e[i],i,e)&&r.push(e[i]);return r}function le(e,t,n){if(e&&t){for(var r=0,i=e.length;r<i;r++)if(t.call(n,e[r],r,e))return e[r]}}function ue(e){if(!e)return[];if(Object.keys)return Object.keys(e);var t=[];for(var n in e)e.hasOwnProperty(n)&&t.push(n);return t}function de(e,t){for(var n=[],r=2;r<arguments.length;r++)n[r-2]=arguments[r];return function(){return e.apply(t,n.concat(D.call(arguments)))}}var fe=A&&he(A.bind)?A.call.bind(A.bind):de;function pe(e){for(var t=[],n=1;n<arguments.length;n++)t[n-1]=arguments[n];return function(){return e.apply(this,t.concat(D.call(arguments)))}}function me(e){return Array.isArray?Array.isArray(e):C.call(e)===`[object Array]`}function he(e){return typeof e==`function`}function ge(e){return typeof e==`string`}function _e(e){return C.call(e)===`[object String]`}function ve(e){return typeof e==`number`}function ye(e){var t=typeof e;return t===`function`||!!e&&t===`object`}function be(e){return!!x[C.call(e)]}function xe(e){return!!S[C.call(e)]}function Se(e){return typeof e==`object`&&typeof e.nodeType==`number`&&typeof e.ownerDocument==`object`}function Ce(e){return e.colorStops!=null}function we(e){return e!==e}function Te(){for(var e=[],t=0;t<arguments.length;t++)e[t]=arguments[t];for(var n=0,r=e.length;n<r;n++)if(e[n]!=null)return e[n]}function Ee(e,t){return e??t}function De(e,t,n){return e??t??n}function Oe(e){for(var t=[],n=1;n<arguments.length;n++)t[n-1]=arguments[n];return D.apply(e,t)}function ke(e){if(typeof e==`number`)return[e,e,e,e];var t=e.length;return t===2?[e[0],e[1],e[0],e[1]]:t===3?[e[0],e[1],e[2],e[1]]:e}function Ae(e,t){if(!e)throw Error(t)}function je(e){return e==null?null:typeof e.trim==`function`?e.trim():e.replace(/^[\s\uFEFF\xA0]+|[\s\uFEFF\xA0]+$/g,``)}var Me=`__ec_primitive__`;function Ne(e){e[Me]=!0}function Pe(e){return e[Me]}var Fe=function(){function e(){this.data={}}return e.prototype.delete=function(e){var t=this.has(e);return t&&delete this.data[e],t},e.prototype.has=function(e){return this.data.hasOwnProperty(e)},e.prototype.get=function(e){return this.data[e]},e.prototype.set=function(e,t){return this.data[e]=t,this},e.prototype.keys=function(){return ue(this.data)},e.prototype.forEach=function(e){var t=this.data;for(var n in t)t.hasOwnProperty(n)&&e(t[n],n)},e}(),Ie=typeof Map==`function`;function Le(){return Ie?new Map:new Fe}var Re=function(){function e(t){var n=me(t);this.data=Le();var r=this;t instanceof e?t.each(i):t&&z(t,i);function i(e,t){n?r.set(e,t):r.set(t,e)}}return e.prototype.hasKey=function(e){return this.data.has(e)},e.prototype.get=function(e){return this.data.get(e)},e.prototype.set=function(e,t){return this.data.set(e,t),t},e.prototype.each=function(e,t){this.data.forEach(function(n,r){e.call(t,n,r)})},e.prototype.keys=function(){var e=this.data.keys();return Ie?Array.from(e):e},e.prototype.removeKey=function(e){this.data.delete(e)},e}();function ze(e){return new Re(e)}function Be(e,t){for(var n=new e.constructor(e.length+t.length),r=0;r<e.length;r++)n[r]=e[r];for(var i=e.length,r=0;r<t.length;r++)n[r+i]=t[r];return n}function Ve(e,t){var n;if(Object.create)n=Object.create(e);else{var r=function(){};r.prototype=e,n=new r}return t&&R(n,t),n}function He(e,t){return e.hasOwnProperty(t)}function Ue(){}var We=180/Math.PI,Ge=function(){function e(){this.firefox=!1,this.ie=!1,this.edge=!1,this.newEdge=!1,this.weChat=!1}return e}(),Ke=new(function(){function e(){this.browser=new Ge,this.node=!1,this.wxa=!1,this.worker=!1,this.svgSupported=!1,this.touchEventsSupported=!1,this.pointerEventsSupported=!1,this.domSupported=!1,this.transformSupported=!1,this.transform3dSupported=!1,this.hasGlobalWindow=typeof window<`u`}return e}());typeof wx==`object`&&typeof wx.getSystemInfoSync==`function`?(Ke.wxa=!0,Ke.touchEventsSupported=!0):typeof document>`u`&&typeof self<`u`?Ke.worker=!0:!Ke.hasGlobalWindow||`Deno`in window||typeof navigator<`u`&&typeof navigator.userAgent==`string`&&navigator.userAgent.indexOf(`Node.js`)>-1?(Ke.node=!0,Ke.svgSupported=!0):qe(navigator.userAgent,Ke);function qe(e,t){var n=t.browser,r=e.match(/Firefox\/([\d.]+)/),i=e.match(/MSIE\s([\d.]+)/)||e.match(/Trident\/.+?rv:(([\d.]+))/),a=e.match(/Edge?\/([\d.]+)/),o=/micromessenger/i.test(e);if(r&&(n.firefox=!0,n.version=r[1]),i&&(n.ie=!0,n.version=i[1]),a&&(n.edge=!0,n.version=a[1],n.newEdge=+a[1].split(`.`)[0]>18),o&&(n.weChat=!0),t.svgSupported=typeof SVGRect<`u`,t.touchEventsSupported=`ontouchstart`in window&&!n.ie&&!n.edge,t.pointerEventsSupported=`onpointerdown`in window&&(n.edge||n.ie&&+n.version>=11),t.domSupported=typeof document<`u`){var s=document.documentElement.style;t.transform3dSupported=(n.ie&&`transition`in s||n.edge||`WebKitCSSMatrix`in window&&`m11`in new WebKitCSSMatrix||`MozPerspective`in s)&&!(`OTransition`in s),t.transformSupported=t.transform3dSupported||n.ie&&+n.version>=9}}var Je=`.`,Ye=`___EC__COMPONENT__CONTAINER___`,Xe=`___EC__EXTENDED_CLASS___`;function Ze(e){var t={main:``,sub:``};if(e){var n=e.split(Je);t.main=n[0]||``,t.sub=n[1]||``}return t}function Qe(e){Ae(/^[a-zA-Z0-9_]+([.][a-zA-Z0-9_]+)?$/.test(e),`componentType "`+e+`" illegal`)}function $e(e){return!!(e&&e[Xe])}function et(e,t){e.$constructor=e,e.extend=function(e){var t=this,n;return tt(t)?n=function(e){p(t,e);function t(){return e.apply(this,arguments)||this}return t}(t):(n=function(){(e.$constructor||t).apply(this,arguments)},re(n,this)),R(n.prototype,e),n[Xe]=!0,n.extend=this.extend,n.superCall=at,n.superApply=ot,n.superClass=t,n}}function tt(e){return he(e)&&/^class\s/.test(Function.prototype.toString.call(e))}function nt(e,t){e.extend=t.extend}var rt=Math.round(Math.random()*10);function it(e){var t=[`__\0is_clz`,rt++].join(`_`);e.prototype[t]=!0,e.isInstance=function(e){return!!(e&&e[t])}}function at(e,t){for(var n=[],r=2;r<arguments.length;r++)n[r-2]=arguments[r];return this.superClass.prototype[t].apply(e,n)}function ot(e,t,n){return this.superClass.prototype[t].apply(e,n)}function st(e){var t={};e.registerClass=function(e){var r=e.type||e.prototype.type;if(r){Qe(r),e.prototype.type=r;var i=Ze(r);if(!i.sub)t[i.main]=e;else if(i.sub!==Ye){var a=n(i);a[i.sub]=e}}return e},e.getClass=function(e,n,r){var i=t[e];if(i&&i[Ye]&&(i=n?i[n]:null),r&&!i)throw Error(n?`Component `+e+`.`+(n||``)+` is used but not imported.`:e+`.type should be specified.`);return i},e.getClassesByMainType=function(e){var n=Ze(e),r=[],i=t[n.main];return i&&i[Ye]?z(i,function(e,t){t!==Ye&&r.push(e)}):r.push(i),r},e.hasClass=function(e){return!!t[Ze(e).main]},e.getAllClassMainTypes=function(){var e=[];return z(t,function(t,n){e.push(n)}),e},e.hasSubTypes=function(e){var n=t[Ze(e).main];return n&&n[Ye]};function n(e){var n=t[e.main];return(!n||!n[Ye])&&(n=t[e.main]={},n[Ye]=!0),n}}function ct(e,t){for(var n=0;n<e.length;n++)e[n][1]||(e[n][1]=e[n][0]);return t||=!1,function(n,r,i){for(var a={},o=0;o<e.length;o++){var s=e[o][1];if(!(r&&ne(r,s)>=0||i&&ne(i,s)<0)){var l=n.getShallow(s,t);l!=null&&(a[e[o][0]]=l)}}return a}}var lt=ct([[`fill`,`color`],[`shadowBlur`],[`shadowOffsetX`],[`shadowOffsetY`],[`opacity`],[`shadowColor`]]),ut=function(){function e(){}return e.prototype.getAreaStyle=function(e,t){return lt(this,e,t)},e}(),dt=function(){function e(e){this.value=e}return e}(),ft=function(){function e(){this._len=0}return e.prototype.insert=function(e){var t=new dt(e);return this.insertEntry(t),t},e.prototype.insertEntry=function(e){this.head?(this.tail.next=e,e.prev=this.tail,e.next=null,this.tail=e):this.head=this.tail=e,this._len++},e.prototype.remove=function(e){var t=e.prev,n=e.next;t?t.next=n:this.head=n,n?n.prev=t:this.tail=t,e.next=e.prev=null,this._len--},e.prototype.len=function(){return this._len},e.prototype.clear=function(){this.head=this.tail=null,this._len=0},e}(),pt=function(){function e(e){this._list=new ft,this._maxSize=10,this._map={},this._maxSize=e}return e.prototype.put=function(e,t){var n=this._list,r=this._map,i=null;if(r[e]==null){var a=n.len(),o=this._lastRemovedEntry;if(a>=this._maxSize&&a>0){var s=n.head;n.remove(s),delete r[s.key],i=s.value,this._lastRemovedEntry=s}o?o.value=t:o=new dt(t),o.key=e,n.insertEntry(o),r[e]=o}return i},e.prototype.get=function(e){var t=this._map[e],n=this._list;if(t!=null)return t!==n.tail&&(n.remove(t),n.insertEntry(t)),t.value},e.prototype.clear=function(){this._list.clear(),this._map={}},e.prototype.len=function(){return this._list.len()},e}(),mt=new pt(50);function ht(e){if(typeof e==`string`){var t=mt.get(e);return t&&t.image}else return e}function gt(e,t,n,r,i){if(!e)return t;if(typeof e==`string`){if(t&&t.__zrImageSrc===e||!n)return t;var a=mt.get(e),o={hostEl:n,cb:r,cbPayload:i};return a?(t=a.image,!vt(t)&&a.pending.push(o)):(t=b.loadImage(e,_t,_t),t.__zrImageSrc=e,mt.put(e,t.__cachedImgObj={image:t,pending:[o]})),t}else return e}function _t(){var e=this.__cachedImgObj;this.onload=this.onerror=this.__cachedImgObj=null;for(var t=0;t<e.pending.length;t++){var n=e.pending[t],r=n.cb;r&&r(this,n.cbPayload),n.hostEl.dirty()}e.pending.length=0}function vt(e){return e&&e.width&&e.height}function yt(){return[1,0,0,1,0,0]}function bt(e){return e[0]=1,e[1]=0,e[2]=0,e[3]=1,e[4]=0,e[5]=0,e}function xt(e,t){return e[0]=t[0],e[1]=t[1],e[2]=t[2],e[3]=t[3],e[4]=t[4],e[5]=t[5],e}function St(e,t,n){var r=t[0]*n[0]+t[2]*n[1],i=t[1]*n[0]+t[3]*n[1],a=t[0]*n[2]+t[2]*n[3],o=t[1]*n[2]+t[3]*n[3],s=t[0]*n[4]+t[2]*n[5]+t[4],l=t[1]*n[4]+t[3]*n[5]+t[5];return e[0]=r,e[1]=i,e[2]=a,e[3]=o,e[4]=s,e[5]=l,e}function Ct(e,t,n){return e[0]=t[0],e[1]=t[1],e[2]=t[2],e[3]=t[3],e[4]=t[4]+n[0],e[5]=t[5]+n[1],e}function wt(e,t,n,r){r===void 0&&(r=[0,0]);var i=t[0],a=t[2],o=t[4],s=t[1],l=t[3],u=t[5],d=Math.sin(n),f=Math.cos(n);return e[0]=i*f+s*d,e[1]=-i*d+s*f,e[2]=a*f+l*d,e[3]=-a*d+f*l,e[4]=f*(o-r[0])+d*(u-r[1])+r[0],e[5]=f*(u-r[1])-d*(o-r[0])+r[1],e}function Tt(e,t,n){var r=n[0],i=n[1];return e[0]=t[0]*r,e[1]=t[1]*i,e[2]=t[2]*r,e[3]=t[3]*i,e[4]=t[4]*r,e[5]=t[5]*i,e}function Et(e,t){var n=t[0],r=t[2],i=t[4],a=t[1],o=t[3],s=t[5],l=n*o-a*r;return l?(l=1/l,e[0]=o*l,e[1]=-a*l,e[2]=-r*l,e[3]=n*l,e[4]=(r*s-o*i)*l,e[5]=(a*i-n*s)*l,e):null}function Dt(e,t){return e??=0,t??=0,[e,t]}function Ot(e){return[e[0],e[1]]}function kt(e,t,n){return e[0]=t,e[1]=n,e}function At(e,t,n){return e[0]=t[0]+n[0],e[1]=t[1]+n[1],e}function jt(e,t,n){return e[0]=t[0]-n[0],e[1]=t[1]-n[1],e}function Mt(e){return Math.sqrt(Nt(e))}function Nt(e){return e[0]*e[0]+e[1]*e[1]}function Pt(e,t,n){return e[0]=t[0]*n,e[1]=t[1]*n,e}function Ft(e,t){var n=Mt(t);return n===0?(e[0]=0,e[1]=0):(e[0]=t[0]/n,e[1]=t[1]/n),e}function It(e,t){return Math.sqrt((e[0]-t[0])*(e[0]-t[0])+(e[1]-t[1])*(e[1]-t[1]))}var Lt=It;function Rt(e,t){return(e[0]-t[0])*(e[0]-t[0])+(e[1]-t[1])*(e[1]-t[1])}var zt=Rt;function Bt(e,t,n,r){return e[0]=t[0]+r*(n[0]-t[0]),e[1]=t[1]+r*(n[1]-t[1]),e}function Vt(e,t,n){var r=t[0],i=t[1];return e[0]=n[0]*r+n[2]*i+n[4],e[1]=n[1]*r+n[3]*i+n[5],e}function Ht(e,t,n){return e[0]=Math.min(t[0],n[0]),e[1]=Math.min(t[1],n[1]),e}function Ut(e,t,n){return e[0]=Math.max(t[0],n[0]),e[1]=Math.max(t[1],n[1]),e}var Wt=function(){function e(e,t){this.x=e||0,this.y=t||0}return e.prototype.copy=function(e){return this.x=e.x,this.y=e.y,this},e.prototype.clone=function(){return new e(this.x,this.y)},e.prototype.set=function(e,t){return this.x=e,this.y=t,this},e.prototype.equal=function(e){return e.x===this.x&&e.y===this.y},e.prototype.add=function(e){return this.x+=e.x,this.y+=e.y,this},e.prototype.scale=function(e){this.x*=e,this.y*=e},e.prototype.scaleAndAdd=function(e,t){this.x+=e.x*t,this.y+=e.y*t},e.prototype.sub=function(e){return this.x-=e.x,this.y-=e.y,this},e.prototype.dot=function(e){return this.x*e.x+this.y*e.y},e.prototype.len=function(){return Math.sqrt(this.x*this.x+this.y*this.y)},e.prototype.lenSquare=function(){return this.x*this.x+this.y*this.y},e.prototype.normalize=function(){var e=this.len();return this.x/=e,this.y/=e,this},e.prototype.distance=function(e){var t=this.x-e.x,n=this.y-e.y;return Math.sqrt(t*t+n*n)},e.prototype.distanceSquare=function(e){var t=this.x-e.x,n=this.y-e.y;return t*t+n*n},e.prototype.negate=function(){return this.x=-this.x,this.y=-this.y,this},e.prototype.transform=function(e){if(e){var t=this.x,n=this.y;return this.x=e[0]*t+e[2]*n+e[4],this.y=e[1]*t+e[3]*n+e[5],this}},e.prototype.toArray=function(e){return e[0]=this.x,e[1]=this.y,e},e.prototype.fromArray=function(e){this.x=e[0],this.y=e[1]},e.set=function(e,t,n){e.x=t,e.y=n},e.copy=function(e,t){e.x=t.x,e.y=t.y},e.len=function(e){return Math.sqrt(e.x*e.x+e.y*e.y)},e.lenSquare=function(e){return e.x*e.x+e.y*e.y},e.dot=function(e,t){return e.x*t.x+e.y*t.y},e.add=function(e,t,n){e.x=t.x+n.x,e.y=t.y+n.y},e.sub=function(e,t,n){e.x=t.x-n.x,e.y=t.y-n.y},e.scale=function(e,t,n){e.x=t.x*n,e.y=t.y*n},e.scaleAndAdd=function(e,t,n,r){e.x=t.x+n.x*r,e.y=t.y+n.y*r},e.lerp=function(e,t,n,r){var i=1-r;e.x=i*t.x+r*n.x,e.y=i*t.y+r*n.y},e}(),Gt=Math.min,Kt=Math.max,qt=Math.abs,Jt=[`x`,`y`],Yt=[`width`,`height`],Xt=new Wt,Zt=new Wt,Qt=new Wt,$t=new Wt,en=dn(),tn=en.minTv,nn=en.maxTv,rn=[0,0],an=function(){function e(e,t,n,r){on(this,e,t,n,r)}return e.set=function(e,t,n,r,i){return r<0&&(t+=r,r=-r),i<0&&(n+=i,i=-i),e.x=t,e.y=n,e.width=r,e.height=i,e},e.prototype.union=function(e){var t=Gt(e.x,this.x),n=Gt(e.y,this.y);isFinite(this.x)&&isFinite(this.width)?this.width=Kt(e.x+e.width,this.x+this.width)-t:this.width=e.width,isFinite(this.y)&&isFinite(this.height)?this.height=Kt(e.y+e.height,this.y+this.height)-n:this.height=e.height,this.x=t,this.y=n},e.prototype.applyTransform=function(t){e.applyTransform(this,this,t)},e.prototype.calculateTransform=function(e){return cn(yt(),this,e)},e.prototype.intersect=function(t,n,r){return e.intersect(this,t,n,r)},e.intersect=function(t,n,r,i){r&&Wt.set(r,0,0);var a=i&&i.outIntersectRect||null,o=i&&i.clamp;if(a&&(a.x=a.y=a.width=a.height=NaN),!t||!n)return!1;t instanceof e||(t=on(eee,t.x,t.y,t.width,t.height)),n instanceof e||(n=on(tee,n.x,n.y,n.width,n.height));var s=!!r;en.reset(i,s);var l=en.touchThreshold,u=t.x+l,d=t.x+t.width-l,f=t.y+l,p=t.y+t.height-l,m=n.x+l,h=n.x+n.width-l,g=n.y+l,_=n.y+n.height-l;if(u>d||f>p||m>h||g>_)return!1;var v=!(d<m||h<u||p<g||_<f);return(s||a)&&(rn[0]=1/0,rn[1]=0,un(u,d,m,h,0,s,a,o),un(f,p,g,_,1,s,a,o),s&&Wt.copy(r,v?en.useDir?en.dirMinTv:tn:nn)),v},e.contain=function(e,t,n){return t>=e.x&&t<=e.x+e.width&&n>=e.y&&n<=e.y+e.height},e.prototype.contain=function(t,n){return e.contain(this,t,n)},e.prototype.clone=function(){return new e(this.x,this.y,this.width,this.height)},e.prototype.copy=function(e){sn(this,e)},e.prototype.plain=function(){return{x:this.x,y:this.y,width:this.width,height:this.height}},e.prototype.isFinite=function(){return isFinite(this.x)&&isFinite(this.y)&&isFinite(this.width)&&isFinite(this.height)},e.prototype.isZero=function(){return this.width===0||this.height===0},e.create=function(t){return new e(t?t.x:0,t?t.y:0,t?t.width:0,t?t.height:0)},e.copy=function(e,t){return e.x=t.x,e.y=t.y,e.width=t.width,e.height=t.height,e},e.applyTransform=function(e,t,n){if(!n){e!==t&&sn(e,t);return}if(n[1]<1e-5&&n[1]>-1e-5&&n[2]<1e-5&&n[2]>-1e-5){var r=n[0],i=n[3],a=n[4],o=n[5];e.x=t.x*r+a,e.y=t.y*i+o,e.width=t.width*r,e.height=t.height*i,e.width<0&&(e.x+=e.width,e.width=-e.width),e.height<0&&(e.y+=e.height,e.height=-e.height);return}Xt.x=Qt.x=t.x,Xt.y=$t.y=t.y,Zt.x=$t.x=t.x+t.width,Zt.y=Qt.y=t.y+t.height,Xt.transform(n),$t.transform(n),Zt.transform(n),Qt.transform(n),e.x=Gt(Xt.x,Zt.x,Qt.x,$t.x),e.y=Gt(Xt.y,Zt.y,Qt.y,$t.y);var s=Kt(Xt.x,Zt.x,Qt.x,$t.x),l=Kt(Xt.y,Zt.y,Qt.y,$t.y);e.width=s-e.x,e.height=l-e.y},e.calculateTransform=function(e,t,n){var r=n.width/t.width,i=n.height/t.height;return e=bt(e||[]),Ct(e,e,kt(ln,-t.x,-t.y)),Tt(e,e,kt(ln,r,i)),Ct(e,e,kt(ln,n.x,n.y)),e},e}();an.create;var on=an.set,sn=an.copy,cn=an.calculateTransform;an.applyTransform,an.contain;var eee=new an(0,0,0,0),tee=new an(0,0,0,0),ln=[];function un(e,t,n,r,i,a,o,s){var l=qt(t-n),u=qt(r-e),d=Gt(l,u),f=Jt[i],p=Jt[1-i],m=Yt[i];t<n||r<e?l<u?(a&&(nn[f]=-l),s&&(o[f]=t,o[m]=0)):(a&&(nn[f]=u),s&&(o[f]=e,o[m]=0)):(o&&(o[f]=Kt(e,n),o[m]=Gt(t,r)-o[f]),a&&(d<rn[0]||en.useDir)&&(rn[0]=Gt(d,rn[0]),(l<u||!en.bidirectional)&&(tn[f]=l,tn[p]=0,en.useDir&&en.calcDirMTV()),(l>=u||!en.bidirectional)&&(tn[f]=-u,tn[p]=0,en.useDir&&en.calcDirMTV())))}function dn(){var e=0,t=new Wt,n=new Wt,r={minTv:new Wt,maxTv:new Wt,useDir:!1,dirMinTv:new Wt,touchThreshold:0,bidirectional:!0,negativeSize:!1,reset:function(i,a){r.touchThreshold=0,i&&i.touchThreshold!=null&&(r.touchThreshold=Kt(0,i.touchThreshold)),r.negativeSize=!1,a&&(r.minTv.set(1/0,1/0),r.maxTv.set(0,0),r.useDir=!1,i&&i.direction!=null&&(r.useDir=!0,r.dirMinTv.copy(r.minTv),n.copy(r.minTv),e=i.direction,r.bidirectional=i.bidirectional==null||!!i.bidirectional,r.bidirectional||t.set(Math.cos(e),Math.sin(e))))},calcDirMTV:function(){var a=r.minTv,o=r.dirMinTv,s=a.y*a.y+a.x*a.x,l=Math.sin(e),u=Math.cos(e),d=l*a.y+u*a.x;if(i(d)){i(a.x)&&i(a.y)&&o.set(0,0);return}if(n.x=s*u/d,n.y=s*l/d,i(n.x)&&i(n.y)){o.set(0,0);return}(r.bidirectional||t.dot(n)>0)&&n.len()<o.len()&&o.copy(n)}};function i(e){return qt(e)<1e-10}return r}function fn(e){pn||=new pt(100),e||=`12px sans-serif`;var t=pn.get(e);return t||(t={font:e,strWidthCache:new pt(500),asciiWidthMap:null,asciiWidthMapTried:!1,stWideCharWidth:b.measureText(`å›½`,e).width,asciiCharWidth:b.measureText(`a`,e).width},pn.put(e,t)),t}var pn;function mn(e){if(!(hn>=gn)){e||=`12px sans-serif`;for(var t=[],n=+new Date,r=0;r<=127;r++)t[r]=b.measureText(String.fromCharCode(r),e).width;var i=+new Date-n;return i>16?hn=gn:i>2&&hn++,t}}var hn=0,gn=5;function _n(e,t){return e.asciiWidthMapTried||=(e.asciiWidthMap=mn(e.font),!0),0<=t&&t<=127?e.asciiWidthMap==null?e.asciiCharWidth:e.asciiWidthMap[t]:e.stWideCharWidth}function vn(e,t){var n=e.strWidthCache,r=n.get(t);return r??(r=b.measureText(t,e.font).width,n.put(t,r)),r}function yn(e,t,n,r){var i=vn(fn(t),e),a=Cn(t);return new an(xn(0,i,n),Sn(0,a,r),i,a)}function bn(e,t,n,r){var i=((e||``)+``).split(`
`);if(i.length===1)return yn(i[0],t,n,r);for(var a=new an(0,0,0,0),o=0;o<i.length;o++){var s=yn(i[o],t,n,r);o===0?a.copy(s):a.union(s)}return a}function xn(e,t,n,r){return n===`right`?r?e+=t:e-=t:n===`center`&&(r?e+=t/2:e-=t/2),e}function Sn(e,t,n,r){return n===`middle`?r?e+=t/2:e-=t/2:n===`bottom`&&(r?e+=t:e-=t),e}function Cn(e){return fn(e).stWideCharWidth}function wn(e,t){return typeof e==`string`?e.lastIndexOf(`%`)>=0?parseFloat(e)/100*t:parseFloat(e):e}function Tn(e,t,n){var r=t.position||`inside`,i=t.distance==null?5:t.distance,a=n.height,o=n.width,s=a/2,l=n.x,u=n.y,d=`left`,f=`top`;if(r instanceof Array)l+=wn(r[0],n.width),u+=wn(r[1],n.height),d=null,f=null;else switch(r){case`left`:l-=i,u+=s,d=`right`,f=`middle`;break;case`right`:l+=i+o,u+=s,f=`middle`;break;case`top`:l+=o/2,u-=i,d=`center`,f=`bottom`;break;case`bottom`:l+=o/2,u+=a+i,d=`center`;break;case`inside`:l+=o/2,u+=s,d=`center`,f=`middle`;break;case`insideLeft`:l+=i,u+=s,f=`middle`;break;case`insideRight`:l+=o-i,u+=s,d=`right`,f=`middle`;break;case`insideTop`:l+=o/2,u+=i,d=`center`;break;case`insideBottom`:l+=o/2,u+=a-i,d=`center`,f=`bottom`;break;case`insideTopLeft`:l+=i,u+=i;break;case`insideTopRight`:l+=o-i,u+=i,d=`right`;break;case`insideBottomLeft`:l+=i,u+=a-i,f=`bottom`;break;case`insideBottomRight`:l+=o-i,u+=a-i,d=`right`,f=`bottom`;break}return e||={},e.x=l,e.y=u,e.align=d,e.verticalAlign=f,e}var En=/\{([a-zA-Z0-9_]+)\|([^}]*)\}/g;function Dn(e,t,n,r,i,a){if(!n){e.text=``,e.isTruncated=!1;return}var o=(t+``).split(`
`);a=On(n,r,i,a);for(var s=!1,l={},u=0,d=o.length;u<d;u++)kn(l,o[u],a),o[u]=l.textLine,s||=l.isTruncated;e.text=o.join(`
`),e.isTruncated=s}function On(e,t,n,r){r||={};var i=R({},r);n=Ee(n,`...`),i.maxIterations=Ee(r.maxIterations,2);var a=i.minChar=Ee(r.minChar,0),o=i.fontMeasureInfo=fn(t),s=o.asciiCharWidth;i.placeholder=Ee(r.placeholder,``);for(var l=e=Math.max(0,e-1),u=0;u<a&&l>=s;u++)l-=s;var d=vn(o,n);return d>l&&(n=``,d=0),l=e-d,i.ellipsis=n,i.ellipsisWidth=d,i.contentWidth=l,i.containerWidth=e,i}function kn(e,t,n){var r=n.containerWidth,i=n.contentWidth,a=n.fontMeasureInfo;if(!r){e.textLine=``,e.isTruncated=!1;return}var o=vn(a,t);if(o<=r){e.textLine=t,e.isTruncated=!1;return}for(var s=0;;s++){if(o<=i||s>=n.maxIterations){t+=n.ellipsis;break}var l=s===0?An(t,i,a):o>0?Math.floor(t.length*i/o):0;t=t.substr(0,l),o=vn(a,t)}t===``&&(t=n.placeholder),e.textLine=t,e.isTruncated=!0}function An(e,t,n){for(var r=0,i=0,a=e.length;i<a&&r<t;i++)r+=_n(n,e.charCodeAt(i));return i}function jn(e,t,n,r){var i=Vn(e),a=t.overflow,o=t.padding,s=o?o[1]+o[3]:0,l=o?o[0]+o[2]:0,u=t.font,d=a===`truncate`,f=Cn(u),p=Ee(t.lineHeight,f),m=t.lineOverflow===`truncate`,h=!1,g=t.width;g==null&&n!=null&&(g=n-s);var _=t.height;_==null&&r!=null&&(_=r-l);var v=g!=null&&(a===`break`||a===`breakAll`)?i?Rn(i,t.font,g,a===`breakAll`,0).lines:[]:i?i.split(`
`):[],y=v.length*p;if(_??=y,y>_&&m){var b=Math.floor(_/p);h||=v.length>b,v=v.slice(0,b),y=v.length*p}if(i&&d&&g!=null)for(var x=On(g,u,t.ellipsis,{minChar:t.truncateMinChar,placeholder:t.placeholder}),S={},C=0;C<v.length;C++)kn(S,v[C],x),v[C]=S.textLine,h||=S.isTruncated;for(var w=_,T=0,E=fn(u),C=0;C<v.length;C++)T=Math.max(vn(E,v[C]),T);g??=T;var D=g;return w+=l,D+=s,{lines:v,height:_,outerWidth:D,outerHeight:w,lineHeight:p,calculatedLineHeight:f,contentWidth:T,contentHeight:y,width:g,isTruncated:h}}var nee=function(){function e(){}return e}(),Mn=function(){function e(e){this.tokens=[],e&&(this.tokens=e)}return e}(),Nn=function(){function e(){this.width=0,this.height=0,this.contentWidth=0,this.contentHeight=0,this.outerWidth=0,this.outerHeight=0,this.lines=[],this.isTruncated=!1}return e}();function Pn(e,t,n,r,i){var a=new Nn,o=Vn(e);if(!o)return a;var s=t.padding,l=s?s[1]+s[3]:0,u=s?s[0]+s[2]:0,d=t.width;d==null&&n!=null&&(d=n-l);var f=t.height;f==null&&r!=null&&(f=r-u);for(var p=t.overflow,m=(p===`break`||p===`breakAll`)&&d!=null?{width:d,accumWidth:0,breakAll:p===`breakAll`}:null,h=En.lastIndex=0,g;(g=En.exec(o))!=null;){var _=g.index;_>h&&Fn(a,o.substring(h,_),t,m),Fn(a,g[2],t,m,g[1]),h=En.lastIndex}h<o.length&&Fn(a,o.substring(h,o.length),t,m);var v=[],y=0,b=0,x=p===`truncate`,S=t.lineOverflow===`truncate`,C={};function w(e,t,n){e.width=t,e.lineHeight=n,y+=n,b=Math.max(b,t)}outer:for(var T=0;T<a.lines.length;T++){for(var E=a.lines[T],D=0,O=0,k=0;k<E.tokens.length;k++){var A=E.tokens[k],j=A.styleName&&t.rich[A.styleName]||{},M=A.textPadding=j.padding,N=M?M[1]+M[3]:0,P=A.font=j.font||t.font;A.contentHeight=Cn(P);var F=Ee(j.height,A.contentHeight);if(A.innerHeight=F,M&&(F+=M[0]+M[2]),A.height=F,A.lineHeight=De(j.lineHeight,t.lineHeight,F),A.align=j&&j.align||i,A.verticalAlign=j&&j.verticalAlign||`middle`,S&&f!=null&&y+A.lineHeight>f){var I=a.lines.length;k>0?(E.tokens=E.tokens.slice(0,k),w(E,O,D),a.lines=a.lines.slice(0,T+1)):a.lines=a.lines.slice(0,T),a.isTruncated=a.isTruncated||a.lines.length<I;break outer}var L=j.width,R=L==null||L===`auto`;if(typeof L==`string`&&L.charAt(L.length-1)===`%`)A.percentWidth=L,v.push(A),A.contentWidth=vn(fn(P),A.text);else{if(R){var ee=j.backgroundColor,te=ee&&ee.image;te&&(te=ht(te),vt(te)&&(A.width=Math.max(A.width,te.width*F/te.height)))}var ne=x&&d!=null?d-O:null;ne!=null&&ne<A.width?!R||ne<N?(A.text=``,A.width=A.contentWidth=0):(Dn(C,A.text,ne-N,P,t.ellipsis,{minChar:t.truncateMinChar}),A.text=C.text,a.isTruncated=a.isTruncated||C.isTruncated,A.width=A.contentWidth=vn(fn(P),A.text)):A.contentWidth=vn(fn(P),A.text)}A.width+=N,O+=A.width,j&&(D=Math.max(D,A.lineHeight))}w(E,O,D)}a.outerWidth=a.width=Ee(d,b),a.outerHeight=a.height=Ee(f,y),a.contentHeight=y,a.contentWidth=b,a.outerWidth+=l,a.outerHeight+=u;for(var T=0;T<v.length;T++){var A=v[T],re=A.percentWidth;A.width=parseInt(re,10)/100*a.width}return a}function Fn(e,t,n,r,i){var a=t===``,o=i&&n.rich[i]||{},s=e.lines,l=o.font||n.font,u=!1,d,f;if(r){var p=o.padding,m=p?p[1]+p[3]:0;if(o.width!=null&&o.width!==`auto`){var h=wn(o.width,r.width)+m;s.length>0&&h+r.accumWidth>r.width&&(d=t.split(`
`),u=!0),r.accumWidth=h}else{var g=Rn(t,l,r.width,r.breakAll,r.accumWidth);r.accumWidth=g.accumWidth+m,f=g.linesWidths,d=g.lines}}d||=t.split(`
`);for(var _=fn(l),v=0;v<d.length;v++){var y=d[v],b=new nee;if(b.styleName=i,b.text=y,b.isLineHolder=!y&&!a,typeof o.width==`number`?b.width=o.width:b.width=f?f[v]:vn(_,y),!v&&!u){var x=(s[s.length-1]||(s[0]=new Mn)).tokens,S=x.length;S===1&&x[0].isLineHolder?x[0]=b:(y||!S||a)&&x.push(b)}else s.push(new Mn([b]))}}function ree(e){var t=e.charCodeAt(0);return t>=32&&t<=591||t>=880&&t<=4351||t>=4608&&t<=5119||t>=7680&&t<=8303}var In=se(`,&?/;] `.split(``),function(e,t){return e[t]=!0,e},{});function Ln(e){return!ree(e)||!!In[e]}function Rn(e,t,n,r,i){for(var a=[],o=[],s=``,l=``,u=0,d=0,f=fn(t),p=0;p<e.length;p++){var m=e.charAt(p);if(m===`
`){l&&(s+=l,d+=u),a.push(s),o.push(d),s=``,l=``,u=0,d=0;continue}var h=_n(f,m.charCodeAt(0)),g=!r&&!Ln(m);if(a.length?d+h>n:i+d+h>n){d?(s||l)&&(g?(s||(s=l,l=``,u=0,d=u),a.push(s),o.push(d-u),l+=m,u+=h,s=``,d=u):(l&&(s+=l,l=``,u=0),a.push(s),o.push(d),s=m,d=h)):g?(a.push(l),o.push(u),l=m,u=h):(a.push(m),o.push(h));continue}d+=h,g?(l+=m,u+=h):(l&&(s+=l,l=``,u=0),s+=m)}return l&&(s+=l),s&&(a.push(s),o.push(d)),a.length===1&&(d+=i),{accumWidth:d,lines:a,linesWidths:o}}function zn(e,t,n,r,i,a){if(e.baseX=n,e.baseY=r,e.outerWidth=e.outerHeight=null,t){var o=t.width*2,s=t.height*2;an.set(Bn,xn(n,o,i),Sn(r,s,a),o,s),an.intersect(t,Bn,null,iee);var l=iee.outIntersectRect;e.outerWidth=l.width,e.outerHeight=l.height,e.baseX=xn(l.x,l.width,i,!0),e.baseY=Sn(l.y,l.height,a,!0)}}var Bn=new an(0,0,0,0),iee={outIntersectRect:{},clamp:!0};function Vn(e){return e==null?e=``:e+=``}function aee(e){var t=Vn(e.text),n=e.font;return Hn(e,vn(fn(n),t),Cn(n),null)}function Hn(e,t,n,r){var i=new an(xn(e.x||0,t,e.textAlign),Sn(e.y||0,n,e.textBaseline),t,n),a=r??(Un(e)?e.lineWidth:0);return a>0&&(i.x-=a/2,i.y-=a/2,i.width+=a,i.height+=a),i}function Un(e){var t=e.stroke;return t!=null&&t!==`none`&&e.lineWidth>0}var Wn=bt,oee=5e-5;function Gn(e){return e>oee||e<-oee}var Kn=[],qn=[],Jn=yt(),Yn=Math.abs,Xn=function(){function e(){}return e.prototype.getLocalTransform=function(e){return see(this,e)},e.prototype.setPosition=function(e){this.x=e[0],this.y=e[1]},e.prototype.setScale=function(e){this.scaleX=e[0],this.scaleY=e[1]},e.prototype.setSkew=function(e){this.skewX=e[0],this.skewY=e[1]},e.prototype.setOrigin=function(e){this.originX=e[0],this.originY=e[1]},e.prototype.needLocalTransform=function(){return Gn(this.rotation)||Gn(this.x)||Gn(this.y)||Gn(this.scaleX-1)||Gn(this.scaleY-1)||Gn(this.skewX)||Gn(this.skewY)},e.prototype.updateTransform=function(){var e=this.parent&&this.parent.transform,t=this.needLocalTransform(),n=this.transform;if(!(t||e)){n&&(Wn(n),this.invTransform=null);return}n||=yt(),t?this.getLocalTransform(n):Wn(n),e&&(t?St(n,e,n):xt(n,e)),this.transform=n,this._resolveGlobalScaleRatio(n),this.invTransform=this.invTransform||yt(),Et(this.invTransform,n)},e.prototype._resolveGlobalScaleRatio=function(e){var t=this.globalScaleRatio;if(t!=null&&t!==1){this.getGlobalScale(Kn);var n=Kn[0]<0?-1:1,r=Kn[1]<0?-1:1,i=((Kn[0]-n)*t+n)/Kn[0]||0,a=((Kn[1]-r)*t+r)/Kn[1]||0;e[0]*=i,e[1]*=i,e[2]*=a,e[3]*=a}},e.prototype.getComputedTransform=function(){for(var e=this,t=[];e;)t.push(e),e=e.parent;for(;e=t.pop();)e.updateTransform();return this.transform},e.prototype.setLocalTransform=function(e){if(e){var t=e[0]*e[0]+e[1]*e[1],n=e[2]*e[2]+e[3]*e[3],r=Math.atan2(e[1],e[0]),i=Math.PI/2+r-Math.atan2(e[3],e[2]);n=Math.sqrt(n)*Math.cos(i),t=Math.sqrt(t),this.skewX=i,this.skewY=0,this.rotation=-r,this.x=+e[4],this.y=+e[5],this.scaleX=t,this.scaleY=n,this.originX=0,this.originY=0}},e.prototype.decomposeTransform=function(){if(this.transform){var e=this.parent,t=this.transform;e&&e.transform&&(e.invTransform=e.invTransform||yt(),St(qn,e.invTransform,t),t=qn);var n=this.originX,r=this.originY;(n||r)&&(Jn[4]=n,Jn[5]=r,St(qn,t,Jn),qn[4]-=n,qn[5]-=r,t=qn),this.setLocalTransform(t)}},e.prototype.getGlobalScale=function(e){var t=this.transform;return e||=[],t?(e[0]=Math.sqrt(t[0]*t[0]+t[1]*t[1]),e[1]=Math.sqrt(t[2]*t[2]+t[3]*t[3]),t[0]<0&&(e[0]=-e[0]),t[3]<0&&(e[1]=-e[1]),e):(e[0]=1,e[1]=1,e)},e.prototype.transformCoordToLocal=function(e,t){var n=[e,t],r=this.invTransform;return r&&Vt(n,n,r),n},e.prototype.transformCoordToGlobal=function(e,t){var n=[e,t],r=this.transform;return r&&Vt(n,n,r),n},e.prototype.getLineScale=function(){var e=this.transform;return e&&Yn(e[0]-1)>1e-10&&Yn(e[3]-1)>1e-10?Math.sqrt(Yn(e[0]*e[3]-e[2]*e[1])):1},e.prototype.copyTransform=function(e){Qn(this,e)},e.getLocalTransform=function(e,t){t||=[];var n=e.originX||0,r=e.originY||0,i=e.scaleX,a=e.scaleY,o=e.anchorX,s=e.anchorY,l=e.rotation||0,u=e.x,d=e.y,f=e.skewX?Math.tan(e.skewX):0,p=e.skewY?Math.tan(-e.skewY):0;if(n||r||o||s){var m=n+o,h=r+s;t[4]=-m*i-f*h*a,t[5]=-h*a-p*m*i}else t[4]=t[5]=0;return t[0]=i,t[3]=a,t[1]=p*i,t[2]=f*a,l&&wt(t,t,l),t[4]+=n+u,t[5]+=r+d,t},e.initDefaultProps=(function(){var t=e.prototype;t.scaleX=t.scaleY=t.globalScaleRatio=1,t.x=t.y=t.originX=t.originY=t.skewX=t.skewY=t.rotation=t.anchorX=t.anchorY=0})(),e}(),see=Xn.getLocalTransform,Zn=[`x`,`y`,`originX`,`originY`,`anchorX`,`anchorY`,`rotation`,`scaleX`,`scaleY`,`skewX`,`skewY`];function Qn(e,t){return ee(e,t,Zn)}var $n={linear:function(e){return e},quadraticIn:function(e){return e*e},quadraticOut:function(e){return e*(2-e)},quadraticInOut:function(e){return(e*=2)<1?.5*e*e:-.5*(--e*(e-2)-1)},cubicIn:function(e){return e*e*e},cubicOut:function(e){return--e*e*e+1},cubicInOut:function(e){return(e*=2)<1?.5*e*e*e:.5*((e-=2)*e*e+2)},quarticIn:function(e){return e*e*e*e},quarticOut:function(e){return 1- --e*e*e*e},quarticInOut:function(e){return(e*=2)<1?.5*e*e*e*e:-.5*((e-=2)*e*e*e-2)},quinticIn:function(e){return e*e*e*e*e},quinticOut:function(e){return--e*e*e*e*e+1},quinticInOut:function(e){return(e*=2)<1?.5*e*e*e*e*e:.5*((e-=2)*e*e*e*e+2)},sinusoidalIn:function(e){return 1-Math.cos(e*Math.PI/2)},sinusoidalOut:function(e){return Math.sin(e*Math.PI/2)},sinusoidalInOut:function(e){return .5*(1-Math.cos(Math.PI*e))},exponentialIn:function(e){return e===0?0:1024**(e-1)},exponentialOut:function(e){return e===1?1:1-2**(-10*e)},exponentialInOut:function(e){return e===0?0:e===1?1:(e*=2)<1?.5*1024**(e-1):.5*(-(2**(-10*(e-1)))+2)},circularIn:function(e){return 1-Math.sqrt(1-e*e)},circularOut:function(e){return Math.sqrt(1- --e*e)},circularInOut:function(e){return(e*=2)<1?-.5*(Math.sqrt(1-e*e)-1):.5*(Math.sqrt(1-(e-=2)*e)+1)},elasticIn:function(e){var t,n=.1,r=.4;return e===0?0:e===1?1:(!n||n<1?(n=1,t=r/4):t=r*Math.asin(1/n)/(2*Math.PI),-(n*2**(10*--e)*Math.sin((e-t)*(2*Math.PI)/r)))},elasticOut:function(e){var t,n=.1,r=.4;return e===0?0:e===1?1:(!n||n<1?(n=1,t=r/4):t=r*Math.asin(1/n)/(2*Math.PI),n*2**(-10*e)*Math.sin((e-t)*(2*Math.PI)/r)+1)},elasticInOut:function(e){var t,n=.1,r=.4;return e===0?0:e===1?1:(!n||n<1?(n=1,t=r/4):t=r*Math.asin(1/n)/(2*Math.PI),(e*=2)<1?-.5*(n*2**(10*--e)*Math.sin((e-t)*(2*Math.PI)/r)):n*2**(-10*--e)*Math.sin((e-t)*(2*Math.PI)/r)*.5+1)},backIn:function(e){var t=1.70158;return e*e*((t+1)*e-t)},backOut:function(e){var t=1.70158;return--e*e*((t+1)*e+t)+1},backInOut:function(e){var t=1.70158*1.525;return(e*=2)<1?.5*(e*e*((t+1)*e-t)):.5*((e-=2)*e*((t+1)*e+t)+2)},bounceIn:function(e){return 1-$n.bounceOut(1-e)},bounceOut:function(e){return e<1/2.75?7.5625*e*e:e<2/2.75?7.5625*(e-=1.5/2.75)*e+.75:e<2.5/2.75?7.5625*(e-=2.25/2.75)*e+.9375:7.5625*(e-=2.625/2.75)*e+.984375},bounceInOut:function(e){return e<.5?$n.bounceIn(e*2)*.5:$n.bounceOut(e*2-1)*.5+.5}},er=Math.pow,tr=Math.sqrt,nr=1e-8,cee=1e-4,rr=tr(3),ir=1/3,ar=Dt(),or=Dt(),sr=Dt();function cr(e){return e>-nr&&e<nr}function lr(e){return e>nr||e<-nr}function ur(e,t,n,r,i){var a=1-i;return a*a*(a*e+3*i*t)+i*i*(i*r+3*a*n)}function dr(e,t,n,r,i){var a=1-i;return 3*(((t-e)*a+2*(n-t)*i)*a+(r-n)*i*i)}function fr(e,t,n,r,i,a){var o=r+3*(t-n)-e,s=3*(n-t*2+e),l=3*(t-e),u=e-i,d=s*s-3*o*l,f=s*l-9*o*u,p=l*l-3*s*u,m=0;if(cr(d)&&cr(f))if(cr(s))a[0]=0;else{var h=-l/s;h>=0&&h<=1&&(a[m++]=h)}else{var g=f*f-4*d*p;if(cr(g)){var _=f/d,h=-s/o+_,v=-_/2;h>=0&&h<=1&&(a[m++]=h),v>=0&&v<=1&&(a[m++]=v)}else if(g>0){var y=tr(g),b=d*s+1.5*o*(-f+y),x=d*s+1.5*o*(-f-y);b=b<0?-er(-b,ir):er(b,ir),x=x<0?-er(-x,ir):er(x,ir);var h=(-s-(b+x))/(3*o);h>=0&&h<=1&&(a[m++]=h)}else{var S=(2*d*s-3*o*f)/(2*tr(d*d*d)),C=Math.acos(S)/3,w=tr(d),T=Math.cos(C),h=(-s-2*w*T)/(3*o),v=(-s+w*(T+rr*Math.sin(C)))/(3*o),E=(-s+w*(T-rr*Math.sin(C)))/(3*o);h>=0&&h<=1&&(a[m++]=h),v>=0&&v<=1&&(a[m++]=v),E>=0&&E<=1&&(a[m++]=E)}}return m}function pr(e,t,n,r,i){var a=6*n-12*t+6*e,o=9*t+3*r-3*e-9*n,s=3*t-3*e,l=0;if(cr(o)){if(lr(a)){var u=-s/a;u>=0&&u<=1&&(i[l++]=u)}}else{var d=a*a-4*o*s;if(cr(d))i[0]=-a/(2*o);else if(d>0){var f=tr(d),u=(-a+f)/(2*o),p=(-a-f)/(2*o);u>=0&&u<=1&&(i[l++]=u),p>=0&&p<=1&&(i[l++]=p)}}return l}function mr(e,t,n,r,i,a){var o=(t-e)*i+e,s=(n-t)*i+t,l=(r-n)*i+n,u=(s-o)*i+o,d=(l-s)*i+s,f=(d-u)*i+u;a[0]=e,a[1]=o,a[2]=u,a[3]=f,a[4]=f,a[5]=d,a[6]=l,a[7]=r}function hr(e,t,n,r,i,a,o,s,l,u,d){var f,p=.005,m=1/0,h,g,_,v;ar[0]=l,ar[1]=u;for(var y=0;y<1;y+=.05)or[0]=ur(e,n,i,o,y),or[1]=ur(t,r,a,s,y),_=zt(ar,or),_<m&&(f=y,m=_);m=1/0;for(var b=0;b<32&&!(p<cee);b++)h=f-p,g=f+p,or[0]=ur(e,n,i,o,h),or[1]=ur(t,r,a,s,h),_=zt(or,ar),h>=0&&_<m?(f=h,m=_):(sr[0]=ur(e,n,i,o,g),sr[1]=ur(t,r,a,s,g),v=zt(sr,ar),g<=1&&v<m?(f=g,m=v):p*=.5);return d&&(d[0]=ur(e,n,i,o,f),d[1]=ur(t,r,a,s,f)),tr(m)}function lee(e,t,n,r,i,a,o,s,l){for(var u=e,d=t,f=0,p=1/l,m=1;m<=l;m++){var h=m*p,g=ur(e,n,i,o,h),_=ur(t,r,a,s,h),v=g-u,y=_-d;f+=Math.sqrt(v*v+y*y),u=g,d=_}return f}function gr(e,t,n,r){var i=1-r;return i*(i*e+2*r*t)+r*r*n}function _r(e,t,n,r){return 2*((1-r)*(t-e)+r*(n-t))}function uee(e,t,n,r,i){var a=e-2*t+n,o=2*(t-e),s=e-r,l=0;if(cr(a)){if(lr(o)){var u=-s/o;u>=0&&u<=1&&(i[l++]=u)}}else{var d=o*o-4*a*s;if(cr(d)){var u=-o/(2*a);u>=0&&u<=1&&(i[l++]=u)}else if(d>0){var f=tr(d),u=(-o+f)/(2*a),p=(-o-f)/(2*a);u>=0&&u<=1&&(i[l++]=u),p>=0&&p<=1&&(i[l++]=p)}}return l}function vr(e,t,n){var r=e+n-2*t;return r===0?.5:(e-t)/r}function yr(e,t,n,r,i){var a=(t-e)*r+e,o=(n-t)*r+t,s=(o-a)*r+a;i[0]=e,i[1]=a,i[2]=s,i[3]=s,i[4]=o,i[5]=n}function dee(e,t,n,r,i,a,o,s,l){var u,d=.005,f=1/0;ar[0]=o,ar[1]=s;for(var p=0;p<1;p+=.05){or[0]=gr(e,n,i,p),or[1]=gr(t,r,a,p);var m=zt(ar,or);m<f&&(u=p,f=m)}f=1/0;for(var h=0;h<32&&!(d<cee);h++){var g=u-d,_=u+d;or[0]=gr(e,n,i,g),or[1]=gr(t,r,a,g);var m=zt(or,ar);if(g>=0&&m<f)u=g,f=m;else{sr[0]=gr(e,n,i,_),sr[1]=gr(t,r,a,_);var v=zt(sr,ar);_<=1&&v<f?(u=_,f=v):d*=.5}}return l&&(l[0]=gr(e,n,i,u),l[1]=gr(t,r,a,u)),tr(f)}function fee(e,t,n,r,i,a,o){for(var s=e,l=t,u=0,d=1/o,f=1;f<=o;f++){var p=f*d,m=gr(e,n,i,p),h=gr(t,r,a,p),g=m-s,_=h-l;u+=Math.sqrt(g*g+_*_),s=m,l=h}return u}var br=/cubic-bezier\(([0-9,\.e ]+)\)/;function xr(e){var t=e&&br.exec(e);if(t){var n=t[1].split(`,`),r=+je(n[0]),i=+je(n[1]),a=+je(n[2]),o=+je(n[3]);if(isNaN(r+i+a+o))return;var s=[];return function(e){return e<=0?0:e>=1?1:fr(0,r,a,1,e,s)&&ur(0,i,o,1,s[0])}}}var pee=function(){function e(e){this._inited=!1,this._startTime=0,this._pausedTime=0,this._paused=!1,this._life=e.life||1e3,this._delay=e.delay||0,this.loop=e.loop||!1,this.onframe=e.onframe||Ue,this.ondestroy=e.ondestroy||Ue,this.onrestart=e.onrestart||Ue,e.easing&&this.setEasing(e.easing)}return e.prototype.step=function(e,t){if(this._inited||=(this._startTime=e+this._delay,!0),this._paused){this._pausedTime+=t;return}var n=this._life,r=e-this._startTime-this._pausedTime,i=r/n;i<0&&(i=0),i=Math.min(i,1);var a=this.easingFunc,o=a?a(i):i;if(this.onframe(o),i===1)if(this.loop){var s=r%n;this._startTime=e-s,this._pausedTime=0,this.onrestart()}else return!0;return!1},e.prototype.pause=function(){this._paused=!0},e.prototype.resume=function(){this._paused=!1},e.prototype.setEasing=function(e){this.easing=e,this.easingFunc=he(e)?e:$n[e]||xr(e)},e}(),Sr={transparent:[0,0,0,0],aliceblue:[240,248,255,1],antiquewhite:[250,235,215,1],aqua:[0,255,255,1],aquamarine:[127,255,212,1],azure:[240,255,255,1],beige:[245,245,220,1],bisque:[255,228,196,1],black:[0,0,0,1],blanchedalmond:[255,235,205,1],blue:[0,0,255,1],blueviolet:[138,43,226,1],brown:[165,42,42,1],burlywood:[222,184,135,1],cadetblue:[95,158,160,1],chartreuse:[127,255,0,1],chocolate:[210,105,30,1],coral:[255,127,80,1],cornflowerblue:[100,149,237,1],cornsilk:[255,248,220,1],crimson:[220,20,60,1],cyan:[0,255,255,1],darkblue:[0,0,139,1],darkcyan:[0,139,139,1],darkgoldenrod:[184,134,11,1],darkgray:[169,169,169,1],darkgreen:[0,100,0,1],darkgrey:[169,169,169,1],darkkhaki:[189,183,107,1],darkmagenta:[139,0,139,1],darkolivegreen:[85,107,47,1],darkorange:[255,140,0,1],darkorchid:[153,50,204,1],darkred:[139,0,0,1],darksalmon:[233,150,122,1],darkseagreen:[143,188,143,1],darkslateblue:[72,61,139,1],darkslategray:[47,79,79,1],darkslategrey:[47,79,79,1],darkturquoise:[0,206,209,1],darkviolet:[148,0,211,1],deeppink:[255,20,147,1],deepskyblue:[0,191,255,1],dimgray:[105,105,105,1],dimgrey:[105,105,105,1],dodgerblue:[30,144,255,1],firebrick:[178,34,34,1],floralwhite:[255,250,240,1],forestgreen:[34,139,34,1],fuchsia:[255,0,255,1],gainsboro:[220,220,220,1],ghostwhite:[248,248,255,1],gold:[255,215,0,1],goldenrod:[218,165,32,1],gray:[128,128,128,1],green:[0,128,0,1],greenyellow:[173,255,47,1],grey:[128,128,128,1],honeydew:[240,255,240,1],hotpink:[255,105,180,1],indianred:[205,92,92,1],indigo:[75,0,130,1],ivory:[255,255,240,1],khaki:[240,230,140,1],lavender:[230,230,250,1],lavenderblush:[255,240,245,1],lawngreen:[124,252,0,1],lemonchiffon:[255,250,205,1],lightblue:[173,216,230,1],lightcoral:[240,128,128,1],lightcyan:[224,255,255,1],lightgoldenrodyellow:[250,250,210,1],lightgray:[211,211,211,1],lightgreen:[144,238,144,1],lightgrey:[211,211,211,1],lightpink:[255,182,193,1],lightsalmon:[255,160,122,1],lightseagreen:[32,178,170,1],lightskyblue:[135,206,250,1],lightslategray:[119,136,153,1],lightslategrey:[119,136,153,1],lightsteelblue:[176,196,222,1],lightyellow:[255,255,224,1],lime:[0,255,0,1],limegreen:[50,205,50,1],linen:[250,240,230,1],magenta:[255,0,255,1],maroon:[128,0,0,1],mediumaquamarine:[102,205,170,1],mediumblue:[0,0,205,1],mediumorchid:[186,85,211,1],mediumpurple:[147,112,219,1],mediumseagreen:[60,179,113,1],mediumslateblue:[123,104,238,1],mediumspringgreen:[0,250,154,1],mediumturquoise:[72,209,204,1],mediumvioletred:[199,21,133,1],midnightblue:[25,25,112,1],mintcream:[245,255,250,1],mistyrose:[255,228,225,1],moccasin:[255,228,181,1],navajowhite:[255,222,173,1],navy:[0,0,128,1],oldlace:[253,245,230,1],olive:[128,128,0,1],olivedrab:[107,142,35,1],orange:[255,165,0,1],orangered:[255,69,0,1],orchid:[218,112,214,1],palegoldenrod:[238,232,170,1],palegreen:[152,251,152,1],paleturquoise:[175,238,238,1],palevioletred:[219,112,147,1],papayawhip:[255,239,213,1],peachpuff:[255,218,185,1],peru:[205,133,63,1],pink:[255,192,203,1],plum:[221,160,221,1],powderblue:[176,224,230,1],purple:[128,0,128,1],red:[255,0,0,1],rosybrown:[188,143,143,1],royalblue:[65,105,225,1],saddlebrown:[139,69,19,1],salmon:[250,128,114,1],sandybrown:[244,164,96,1],seagreen:[46,139,87,1],seashell:[255,245,238,1],sienna:[160,82,45,1],silver:[192,192,192,1],skyblue:[135,206,235,1],slateblue:[106,90,205,1],slategray:[112,128,144,1],slategrey:[112,128,144,1],snow:[255,250,250,1],springgreen:[0,255,127,1],steelblue:[70,130,180,1],tan:[210,180,140,1],teal:[0,128,128,1],thistle:[216,191,216,1],tomato:[255,99,71,1],turquoise:[64,224,208,1],violet:[238,130,238,1],wheat:[245,222,179,1],white:[255,255,255,1],whitesmoke:[245,245,245,1],yellow:[255,255,0,1],yellowgreen:[154,205,50,1]};function Cr(e){return e=Math.round(e),e<0?0:e>255?255:e}function mee(e){return e=Math.round(e),e<0?0:e>360?360:e}function wr(e){return e<0?0:e>1?1:e}function Tr(e){var t=e;return t.length&&t.charAt(t.length-1)===`%`?Cr(parseFloat(t)/100*255):Cr(parseInt(t,10))}function Er(e){var t=e;return t.length&&t.charAt(t.length-1)===`%`?wr(parseFloat(t)/100):wr(parseFloat(t))}function Dr(e,t,n){return n<0?n+=1:n>1&&--n,n*6<1?e+(t-e)*n*6:n*2<1?t:n*3<2?e+(t-e)*(2/3-n)*6:e}function Or(e,t,n){return e+(t-e)*n}function kr(e,t,n,r,i){return e[0]=t,e[1]=n,e[2]=r,e[3]=i,e}function Ar(e,t){return e[0]=t[0],e[1]=t[1],e[2]=t[2],e[3]=t[3],e}var jr=new pt(20),Mr=null;function Nr(e,t){Mr&&Ar(Mr,t),Mr=jr.put(e,Mr||t.slice())}function Pr(e,t){if(e){t||=[];var n=jr.get(e);if(n)return Ar(t,n);e+=``;var r=e.replace(/ /g,``).toLowerCase();if(r in Sr)return Ar(t,Sr[r]),Nr(e,t),t;var i=r.length;if(r.charAt(0)===`#`){if(i===4||i===5){var a=parseInt(r.slice(1,4),16);if(!(a>=0&&a<=4095)){kr(t,0,0,0,1);return}return kr(t,(a&3840)>>4|(a&3840)>>8,a&240|(a&240)>>4,a&15|(a&15)<<4,i===5?parseInt(r.slice(4),16)/15:1),Nr(e,t),t}else if(i===7||i===9){var a=parseInt(r.slice(1,7),16);if(!(a>=0&&a<=16777215)){kr(t,0,0,0,1);return}return kr(t,(a&16711680)>>16,(a&65280)>>8,a&255,i===9?parseInt(r.slice(7),16)/255:1),Nr(e,t),t}return}var o=r.indexOf(`(`),s=r.indexOf(`)`);if(o!==-1&&s+1===i){var l=r.substr(0,o),u=r.substr(o+1,s-(o+1)).split(`,`),d=1;switch(l){case`rgba`:if(u.length!==4)return u.length===3?kr(t,+u[0],+u[1],+u[2],1):kr(t,0,0,0,1);d=Er(u.pop());case`rgb`:if(u.length>=3)return kr(t,Tr(u[0]),Tr(u[1]),Tr(u[2]),u.length===3?d:Er(u[3])),Nr(e,t),t;kr(t,0,0,0,1);return;case`hsla`:if(u.length!==4){kr(t,0,0,0,1);return}return u[3]=Er(u[3]),Fr(u,t),Nr(e,t),t;case`hsl`:if(u.length!==3){kr(t,0,0,0,1);return}return Fr(u,t),Nr(e,t),t;default:return}}kr(t,0,0,0,1)}}function Fr(e,t){var n=(parseFloat(e[0])%360+360)%360/360,r=Er(e[1]),i=Er(e[2]),a=i<=.5?i*(r+1):i+r-i*r,o=i*2-a;return t||=[],kr(t,Cr(Dr(o,a,n+1/3)*255),Cr(Dr(o,a,n)*255),Cr(Dr(o,a,n-1/3)*255),1),e.length===4&&(t[3]=e[3]),t}function Ir(e){if(e){var t=e[0]/255,n=e[1]/255,r=e[2]/255,i=Math.min(t,n,r),a=Math.max(t,n,r),o=a-i,s=(a+i)/2,l,u;if(o===0)l=0,u=0;else{u=s<.5?o/(a+i):o/(2-a-i);var d=((a-t)/6+o/2)/o,f=((a-n)/6+o/2)/o,p=((a-r)/6+o/2)/o;t===a?l=p-f:n===a?l=1/3+d-p:r===a&&(l=2/3+f-d),l<0&&(l+=1),l>1&&--l}var m=[l*360,u,s];return e[3]!=null&&m.push(e[3]),m}}function Lr(e,t){var n=Pr(e);if(n){for(var r=0;r<3;r++)t<0?n[r]=n[r]*(1-t)|0:n[r]=(255-n[r])*t+n[r]|0,n[r]>255?n[r]=255:n[r]<0&&(n[r]=0);return Br(n,n.length===4?`rgba`:`rgb`)}}function Rr(e,t,n){if(!(!(t&&t.length)||!(e>=0&&e<=1))){var r=e*(t.length-1),i=Math.floor(r),a=Math.ceil(r),o=Pr(t[i]),s=Pr(t[a]),l=r-i,u=Br([Cr(Or(o[0],s[0],l)),Cr(Or(o[1],s[1],l)),Cr(Or(o[2],s[2],l)),wr(Or(o[3],s[3],l))],`rgba`);return n?{color:u,leftIndex:i,rightIndex:a,value:r}:u}}function zr(e,t,n,r){var i=Pr(e);if(e)return i=Ir(i),t!=null&&(i[0]=mee(he(t)?t(i[0]):t)),n!=null&&(i[1]=Er(he(n)?n(i[1]):n)),r!=null&&(i[2]=Er(he(r)?r(i[2]):r)),Br(Fr(i),`rgba`)}function Br(e,t){if(!(!e||!e.length)){var n=e[0]+`,`+e[1]+`,`+e[2];return(t===`rgba`||t===`hsva`||t===`hsla`)&&(n+=`,`+e[3]),t+`(`+n+`)`}}function Vr(e,t){var n=Pr(e);return n?(.299*n[0]+.587*n[1]+.114*n[2])*n[3]/255+(1-n[3])*t:0}var Hr=new pt(100);function Ur(e){if(ge(e)){var t=Hr.get(e);return t||(t=Lr(e,-.1),Hr.put(e,t)),t}else if(Ce(e)){var n=R({},e);return n.colorStops=oe(e.colorStops,function(e){return{offset:e.offset,color:Lr(e.color,-.1)}}),n}return e}var Wr=Math.round;function Gr(e){var t;if(!e||e===`transparent`)e=`none`;else if(typeof e==`string`&&e.indexOf(`rgba`)>-1){var n=Pr(e);n&&(e=`rgb(`+n[0]+`,`+n[1]+`,`+n[2]+`)`,t=n[3])}return{color:e,opacity:t??1}}var hee=1e-4;function Kr(e){return e<hee&&e>-hee}function qr(e){return Wr(e*1e3)/1e3}function Jr(e){return Wr(e*1e4)/1e4}function gee(e){return`matrix(`+qr(e[0])+`,`+qr(e[1])+`,`+qr(e[2])+`,`+qr(e[3])+`,`+Jr(e[4])+`,`+Jr(e[5])+`)`}var Yr={left:`start`,right:`end`,center:`middle`,middle:`middle`};function Xr(e,t,n){return n===`top`?e+=t/2:n===`bottom`&&(e-=t/2),e}function _ee(e){return e&&(e.shadowBlur||e.shadowOffsetX||e.shadowOffsetY)}function Zr(e){var t=e.style,n=e.getGlobalScale();return[t.shadowColor,(t.shadowBlur||0).toFixed(2),(t.shadowOffsetX||0).toFixed(2),(t.shadowOffsetY||0).toFixed(2),n[0],n[1]].join(`,`)}function Qr(e){return e&&!!e.image}function $r(e){return e&&!!e.svgElement}function ei(e){return Qr(e)||$r(e)}function ti(e){return e.type===`linear`}function ni(e){return e.type===`radial`}function ri(e){return e&&(e.type===`linear`||e.type===`radial`)}function ii(e){return`url(#`+e+`)`}function ai(e){var t=e.getGlobalScale(),n=Math.max(t[0],t[1]);return Math.max(Math.ceil(Math.log(n)/Math.log(10)),1)}function oi(e){var t=e.x||0,n=e.y||0,r=(e.rotation||0)*We,i=Ee(e.scaleX,1),a=Ee(e.scaleY,1),o=e.skewX||0,s=e.skewY||0,l=[];return(t||n)&&l.push(`translate(`+t+`px,`+n+`px)`),r&&l.push(`rotate(`+r+`)`),(i!==1||a!==1)&&l.push(`scale(`+i+`,`+a+`)`),(o||s)&&l.push(`skew(`+Wr(o*We)+`deg, `+Wr(s*We)+`deg)`),l.join(` `)}var si=(function(){return typeof Buffer<`u`&&typeof Buffer.from==`function`?function(e){return Buffer.from(e).toString(`base64`)}:typeof btoa==`function`&&typeof unescape==`function`&&typeof encodeURIComponent==`function`?function(e){return btoa(unescape(encodeURIComponent(e)))}:function(e){return null}})(),ci=Array.prototype.slice;function li(e,t,n){return(t-e)*n+e}function ui(e,t,n,r){for(var i=t.length,a=0;a<i;a++)e[a]=li(t[a],n[a],r);return e}function vee(e,t,n,r){for(var i=t.length,a=i&&t[0].length,o=0;o<i;o++){e[o]||(e[o]=[]);for(var s=0;s<a;s++)e[o][s]=li(t[o][s],n[o][s],r)}return e}function di(e,t,n,r){for(var i=t.length,a=0;a<i;a++)e[a]=t[a]+n[a]*r;return e}function fi(e,t,n,r){for(var i=t.length,a=i&&t[0].length,o=0;o<i;o++){e[o]||(e[o]=[]);for(var s=0;s<a;s++)e[o][s]=t[o][s]+n[o][s]*r}return e}function pi(e,t){for(var n=e.length,r=t.length,i=n>r?t:e,a=Math.min(n,r),o=i[a-1]||{color:[0,0,0,0],offset:0},s=a;s<Math.max(n,r);s++)i.push({offset:o.offset,color:o.color.slice()})}function yee(e,t,n){var r=e,i=t;if(!(!r.push||!i.push)){var a=r.length,o=i.length;if(a!==o)if(a>o)r.length=o;else for(var s=a;s<o;s++)r.push(n===1?i[s]:ci.call(i[s]));for(var l=r[0]&&r[0].length,s=0;s<r.length;s++)if(n===1)isNaN(r[s])&&(r[s]=i[s]);else for(var u=0;u<l;u++)isNaN(r[s][u])&&(r[s][u]=i[s][u])}}function mi(e){if(ae(e)){var t=e.length;if(ae(e[0])){for(var n=[],r=0;r<t;r++)n.push(ci.call(e[r]));return n}return ci.call(e)}return e}function hi(e){return e[0]=Math.floor(e[0])||0,e[1]=Math.floor(e[1])||0,e[2]=Math.floor(e[2])||0,e[3]=e[3]==null?1:e[3],`rgba(`+e.join(`,`)+`)`}function gi(e){return ae(e&&e[0])?2:1}var _i=0,vi=1,yi=2,bi=3,xi=4,Si=5,Ci=6;function wi(e){return e===xi||e===Si}function Ti(e){return e===vi||e===yi}var Ei=[0,0,0,0],Di=function(){function e(e){this.keyframes=[],this.discrete=!1,this._invalid=!1,this._needsSort=!1,this._lastFr=0,this._lastFrP=0,this.propName=e}return e.prototype.isFinished=function(){return this._finished},e.prototype.setFinished=function(){this._finished=!0,this._additiveTrack&&this._additiveTrack.setFinished()},e.prototype.needsAnimate=function(){return this.keyframes.length>=1},e.prototype.getAdditiveTrack=function(){return this._additiveTrack},e.prototype.addKeyframe=function(e,t,n){this._needsSort=!0;var r=this.keyframes,i=r.length,a=!1,o=Ci,s=t;if(ae(t)){var l=gi(t);o=l,(l===1&&!ve(t[0])||l===2&&!ve(t[0][0]))&&(a=!0)}else if(ve(t)&&!we(t))o=_i;else if(ge(t))if(!isNaN(+t))o=_i;else{var u=Pr(t);u&&(s=u,o=bi)}else if(Ce(t)){var d=R({},s);d.colorStops=oe(t.colorStops,function(e){return{offset:e.offset,color:Pr(e.color)}}),ti(t)?o=xi:ni(t)&&(o=Si),s=d}i===0?this.valType=o:(o!==this.valType||o===Ci)&&(a=!0),this.discrete=this.discrete||a;var f={time:e,value:s,rawValue:t,percent:0};return n&&(f.easing=n,f.easingFunc=he(n)?n:$n[n]||xr(n)),r.push(f),f},e.prototype.prepare=function(e,t){var n=this.keyframes;this._needsSort&&n.sort(function(e,t){return e.time-t.time});for(var r=this.valType,i=n.length,a=n[i-1],o=this.discrete,s=Ti(r),l=wi(r),u=0;u<i;u++){var d=n[u],f=d.value,p=a.value;d.percent=d.time/e,o||(s&&u!==i-1?yee(f,p,r):l&&pi(f.colorStops,p.colorStops))}if(!o&&r!==Si&&t&&this.needsAnimate()&&t.needsAnimate()&&r===t.valType&&!t._finished){this._additiveTrack=t;for(var m=n[0].value,u=0;u<i;u++)r===_i?n[u].additiveValue=n[u].value-m:r===bi?n[u].additiveValue=di([],n[u].value,m,-1):Ti(r)&&(n[u].additiveValue=r===vi?di([],n[u].value,m,-1):fi([],n[u].value,m,-1))}},e.prototype.step=function(e,t){if(!this._finished){this._additiveTrack&&this._additiveTrack._finished&&(this._additiveTrack=null);var n=this._additiveTrack!=null,r=n?`additiveValue`:`value`,i=this.valType,a=this.keyframes,o=a.length,s=this.propName,l=i===bi,u,d=this._lastFr,f=Math.min,p,m;if(o===1)p=m=a[0];else{if(t<0)u=0;else if(t<this._lastFrP){for(u=f(d+1,o-1);u>=0&&!(a[u].percent<=t);u--);u=f(u,o-2)}else{for(u=d;u<o&&!(a[u].percent>t);u++);u=f(u-1,o-2)}m=a[u+1],p=a[u]}if(p&&m){this._lastFr=u,this._lastFrP=t;var h=m.percent-p.percent,g=h===0?1:f((t-p.percent)/h,1);m.easingFunc&&(g=m.easingFunc(g));var _=n?this._additiveValue:l?Ei:e[s];if((Ti(i)||l)&&!_&&(_=this._additiveValue=[]),this.discrete)e[s]=g<1?p.rawValue:m.rawValue;else if(Ti(i))i===vi?ui(_,p[r],m[r],g):vee(_,p[r],m[r],g);else if(wi(i)){var v=p[r],y=m[r],b=i===xi;e[s]={type:b?`linear`:`radial`,x:li(v.x,y.x,g),y:li(v.y,y.y,g),colorStops:oe(v.colorStops,function(e,t){var n=y.colorStops[t];return{offset:li(e.offset,n.offset,g),color:hi(ui([],e.color,n.color,g))}}),global:y.global},b?(e[s].x2=li(v.x2,y.x2,g),e[s].y2=li(v.y2,y.y2,g)):e[s].r=li(v.r,y.r,g)}else if(l)ui(_,p[r],m[r],g),n||(e[s]=hi(_));else{var x=li(p[r],m[r],g);n?this._additiveValue=x:e[s]=x}n&&this._addToTarget(e)}}},e.prototype._addToTarget=function(e){var t=this.valType,n=this.propName,r=this._additiveValue;t===_i?e[n]=e[n]+r:t===bi?(Pr(e[n],Ei),di(Ei,Ei,r,1),e[n]=hi(Ei)):t===vi?di(e[n],e[n],r,1):t===yi&&fi(e[n],e[n],r,1)},e}(),Oi=function(){function e(e,t,n,r){if(this._tracks={},this._trackKeys=[],this._maxTime=0,this._started=0,this._clip=null,this._target=e,this._loop=t,t&&r){F(`Can' use additive animation on looped animation.`);return}this._additiveAnimators=r,this._allowDiscrete=n}return e.prototype.getMaxTime=function(){return this._maxTime},e.prototype.getDelay=function(){return this._delay},e.prototype.getLoop=function(){return this._loop},e.prototype.getTarget=function(){return this._target},e.prototype.changeTarget=function(e){this._target=e},e.prototype.when=function(e,t,n){return this.whenWithKeys(e,t,ue(t),n)},e.prototype.whenWithKeys=function(e,t,n,r){for(var i=this._tracks,a=0;a<n.length;a++){var o=n[a],s=i[o];if(!s){s=i[o]=new Di(o);var l=void 0,u=this._getAdditiveTrack(o);if(u){var d=u.keyframes,f=d[d.length-1];l=f&&f.value,u.valType===bi&&l&&(l=hi(l))}else l=this._target[o];if(l==null)continue;e>0&&s.addKeyframe(0,mi(l),r),this._trackKeys.push(o)}s.addKeyframe(e,mi(t[o]),r)}return this._maxTime=Math.max(this._maxTime,e),this},e.prototype.pause=function(){this._clip.pause(),this._paused=!0},e.prototype.resume=function(){this._clip.resume(),this._paused=!1},e.prototype.isPaused=function(){return!!this._paused},e.prototype.duration=function(e){return this._maxTime=e,this._force=!0,this},e.prototype._doneCallback=function(){this._setTracksFinished(),this._clip=null;var e=this._doneCbs;if(e)for(var t=e.length,n=0;n<t;n++)e[n].call(this)},e.prototype._abortedCallback=function(){this._setTracksFinished();var e=this.animation,t=this._abortedCbs;if(e&&e.removeClip(this._clip),this._clip=null,t)for(var n=0;n<t.length;n++)t[n].call(this)},e.prototype._setTracksFinished=function(){for(var e=this._tracks,t=this._trackKeys,n=0;n<t.length;n++)e[t[n]].setFinished()},e.prototype._getAdditiveTrack=function(e){var t,n=this._additiveAnimators;if(n)for(var r=0;r<n.length;r++){var i=n[r].getTrack(e);i&&(t=i)}return t},e.prototype.start=function(e){if(!(this._started>0)){this._started=1;for(var t=this,n=[],r=this._maxTime||0,i=0;i<this._trackKeys.length;i++){var a=this._trackKeys[i],o=this._tracks[a],s=this._getAdditiveTrack(a),l=o.keyframes,u=l.length;if(o.prepare(r,s),o.needsAnimate())if(!this._allowDiscrete&&o.discrete){var d=l[u-1];d&&(t._target[o.propName]=d.rawValue),o.setFinished()}else n.push(o)}if(n.length||this._force){var f=new pee({life:r,loop:this._loop,delay:this._delay||0,onframe:function(e){t._started=2;var r=t._additiveAnimators;if(r){for(var i=!1,a=0;a<r.length;a++)if(r[a]._clip){i=!0;break}i||(t._additiveAnimators=null)}for(var a=0;a<n.length;a++)n[a].step(t._target,e);var o=t._onframeCbs;if(o)for(var a=0;a<o.length;a++)o[a](t._target,e)},ondestroy:function(){t._doneCallback()}});this._clip=f,this.animation&&this.animation.addClip(f),e&&f.setEasing(e)}else this._doneCallback();return this}},e.prototype.stop=function(e){if(this._clip){var t=this._clip;e&&t.onframe(1),this._abortedCallback()}},e.prototype.delay=function(e){return this._delay=e,this},e.prototype.during=function(e){return e&&(this._onframeCbs||=[],this._onframeCbs.push(e)),this},e.prototype.done=function(e){return e&&(this._doneCbs||=[],this._doneCbs.push(e)),this},e.prototype.aborted=function(e){return e&&(this._abortedCbs||=[],this._abortedCbs.push(e)),this},e.prototype.getClip=function(){return this._clip},e.prototype.getTrack=function(e){return this._tracks[e]},e.prototype.getTracks=function(){var e=this;return oe(this._trackKeys,function(t){return e._tracks[t]})},e.prototype.stopTracks=function(e,t){if(!e.length||!this._clip)return!0;for(var n=this._tracks,r=this._trackKeys,i=0;i<e.length;i++){var a=n[e[i]];a&&!a.isFinished()&&(t?a.step(this._target,1):this._started===1&&a.step(this._target,0),a.setFinished())}for(var o=!0,i=0;i<r.length;i++)if(!n[r[i]].isFinished()){o=!1;break}return o&&this._abortedCallback(),o},e.prototype.saveTo=function(e,t,n){if(e){t||=this._trackKeys;for(var r=0;r<t.length;r++){var i=t[r],a=this._tracks[i];if(!(!a||a.isFinished())){var o=a.keyframes,s=o[n?0:o.length-1];s&&(e[i]=mi(s.rawValue))}}}},e.prototype.__changeFinalValue=function(e,t){t||=ue(e);for(var n=0;n<t.length;n++){var r=t[n],i=this._tracks[r];if(i){var a=i.keyframes;if(a.length>1){var o=a.pop();i.addKeyframe(o.time,e[r]),i.prepare(this._maxTime,i.getAdditiveTrack())}}}},e}(),ki=function(){function e(e){e&&(this._$eventProcessor=e)}return e.prototype.on=function(e,t,n,r){this._$handlers||={};var i=this._$handlers;if(typeof t==`function`&&(r=n,n=t,t=null),!n||!e)return this;var a=this._$eventProcessor;t!=null&&a&&a.normalizeQuery&&(t=a.normalizeQuery(t)),i[e]||(i[e]=[]);for(var o=0;o<i[e].length;o++)if(i[e][o].h===n)return this;var s={h:n,query:t,ctx:r||this,callAtLast:n.zrEventfulCallAtLast},l=i[e].length-1,u=i[e][l];return u&&u.callAtLast?i[e].splice(l,0,s):i[e].push(s),this},e.prototype.isSilent=function(e){var t=this._$handlers;return!t||!t[e]||!t[e].length},e.prototype.off=function(e,t){var n=this._$handlers;if(!n)return this;if(!e)return this._$handlers={},this;if(t){if(n[e]){for(var r=[],i=0,a=n[e].length;i<a;i++)n[e][i].h!==t&&r.push(n[e][i]);n[e]=r}n[e]&&n[e].length===0&&delete n[e]}else delete n[e];return this},e.prototype.trigger=function(e){for(var t=[],n=1;n<arguments.length;n++)t[n-1]=arguments[n];if(!this._$handlers)return this;var r=this._$handlers[e],i=this._$eventProcessor;if(r)for(var a=t.length,o=r.length,s=0;s<o;s++){var l=r[s];if(!(i&&i.filter&&l.query!=null&&!i.filter(e,l.query)))switch(a){case 0:l.h.call(l.ctx);break;case 1:l.h.call(l.ctx,t[0]);break;case 2:l.h.call(l.ctx,t[0],t[1]);break;default:l.h.apply(l.ctx,t);break}}return i&&i.afterTrigger&&i.afterTrigger(e),this},e.prototype.triggerWithContext=function(e){for(var t=[],n=1;n<arguments.length;n++)t[n-1]=arguments[n];if(!this._$handlers)return this;var r=this._$handlers[e],i=this._$eventProcessor;if(r)for(var a=t.length,o=t[a-1],s=r.length,l=0;l<s;l++){var u=r[l];if(!(i&&i.filter&&u.query!=null&&!i.filter(e,u.query)))switch(a){case 0:u.h.call(o);break;case 1:u.h.call(o,t[0]);break;case 2:u.h.call(o,t[0],t[1]);break;default:u.h.apply(o,t.slice(1,a-1));break}}return i&&i.afterTrigger&&i.afterTrigger(e),this},e}(),Ai=1;Ke.hasGlobalWindow&&(Ai=Math.max(window.devicePixelRatio||window.screen&&window.screen.deviceXDPI/window.screen.logicalXDPI||1,1));var ji=Ai,Mi=.4,Ni=`#333`,Pi=`#ccc`,Fi=`#eee`,Ii=`__zr_normal__`,Li=Zn.concat([`ignore`]),Ri=se(Zn,function(e,t){return e[t]=!0,e},{ignore:!1}),zi={},Bi=new an(0,0,0,0),Vi=[],Hi=function(){function e(e){this.id=P(),this.animators=[],this.currentStates=[],this.states={},this._init(e)}return e.prototype._init=function(e){this.attr(e)},e.prototype.drift=function(e,t,n){switch(this.draggable){case`horizontal`:t=0;break;case`vertical`:e=0;break}var r=this.transform;r||=this.transform=[1,0,0,1,0,0],r[4]+=e,r[5]+=t,this.decomposeTransform(),this.markRedraw()},e.prototype.beforeUpdate=function(){},e.prototype.afterUpdate=function(){},e.prototype.update=function(){this.updateTransform(),this.__dirty&&this.updateInnerText()},e.prototype.updateInnerText=function(e){var t=this._textContent;if(t&&(!t.ignore||e)){this.textConfig||={};var n=this.textConfig,r=n.local,i=t.innerTransformable,a=void 0,o=void 0,s=!1;i.parent=r?this:null;var l=!1;i.copyTransform(t);var u=n.position!=null,d=n.autoOverflowArea,f=void 0;if((d||u)&&(f=Bi,n.layoutRect?f.copy(n.layoutRect):f.copy(this.getBoundingRect()),r||f.applyTransform(this.transform)),u){this.calculateTextPosition?this.calculateTextPosition(zi,n,f):Tn(zi,n,f),i.x=zi.x,i.y=zi.y,a=zi.align,o=zi.verticalAlign;var p=n.origin;if(p&&n.rotation!=null){var m=void 0,h=void 0;p===`center`?(m=f.width*.5,h=f.height*.5):(m=wn(p[0],f.width),h=wn(p[1],f.height)),l=!0,i.originX=-i.x+m+(r?0:f.x),i.originY=-i.y+h+(r?0:f.y)}}n.rotation!=null&&(i.rotation=n.rotation);var g=n.offset;g&&(i.x+=g[0],i.y+=g[1],l||(i.originX=-g[0],i.originY=-g[1]));var _=this._innerTextDefaultStyle||={};if(d){var v=_.overflowRect=_.overflowRect||new an(0,0,0,0);i.getLocalTransform(Vi),Et(Vi,Vi),an.copy(v,f),v.applyTransform(Vi)}else _.overflowRect=null;var y=n.inside==null?typeof n.position==`string`&&n.position.indexOf(`inside`)>=0:n.inside,b=void 0,x=void 0,S=void 0;y&&this.canBeInsideText()?(b=n.insideFill,x=n.insideStroke,(b==null||b===`auto`)&&(b=this.getInsideTextFill()),(x==null||x===`auto`)&&(x=this.getInsideTextStroke(b),S=!0)):(b=n.outsideFill,x=n.outsideStroke,(b==null||b===`auto`)&&(b=this.getOutsideFill()),(x==null||x===`auto`)&&(x=this.getOutsideStroke(b),S=!0)),b||=`#000`,(b!==_.fill||x!==_.stroke||S!==_.autoStroke||a!==_.align||o!==_.verticalAlign)&&(s=!0,_.fill=b,_.stroke=x,_.autoStroke=S,_.align=a,_.verticalAlign=o,t.setDefaultTextStyle(_)),t.__dirty|=1,s&&t.dirtyStyle(!0)}},e.prototype.canBeInsideText=function(){return!0},e.prototype.getInsideTextFill=function(){return`#fff`},e.prototype.getInsideTextStroke=function(e){return`#000`},e.prototype.getOutsideFill=function(){return this.__zr&&this.__zr.isDarkMode()?Pi:Ni},e.prototype.getOutsideStroke=function(e){var t=this.__zr&&this.__zr.getBackgroundColor(),n=typeof t==`string`&&Pr(t);n||=[255,255,255,1];for(var r=n[3],i=this.__zr.isDarkMode(),a=0;a<3;a++)n[a]=n[a]*r+(i?0:255)*(1-r);return n[3]=1,Br(n,`rgba`)},e.prototype.traverse=function(e,t){},e.prototype.attrKV=function(e,t){e===`textConfig`?this.setTextConfig(t):e===`textContent`?this.setTextContent(t):e===`clipPath`?this.setClipPath(t):e===`extra`?(this.extra=this.extra||{},R(this.extra,t)):this[e]=t},e.prototype.hide=function(){this.ignore=!0,this.markRedraw()},e.prototype.show=function(){this.ignore=!1,this.markRedraw()},e.prototype.attr=function(e,t){if(typeof e==`string`)this.attrKV(e,t);else if(ye(e))for(var n=ue(e),r=0;r<n.length;r++){var i=n[r];this.attrKV(i,e[i])}return this.markRedraw(),this},e.prototype.saveCurrentToNormalState=function(e){this._innerSaveToNormal(e);for(var t=this._normalState,n=0;n<this.animators.length;n++){var r=this.animators[n],i=r.__fromStateTransition;if(!(r.getLoop()||i&&i!==`__zr_normal__`)){var a=r.targetName,o=a?t[a]:t;r.saveTo(o)}}},e.prototype._innerSaveToNormal=function(e){var t=this._normalState;t||=this._normalState={},e.textConfig&&!t.textConfig&&(t.textConfig=this.textConfig),this._savePrimaryToNormal(e,t,Li)},e.prototype._savePrimaryToNormal=function(e,t,n){for(var r=0;r<n.length;r++){var i=n[r];e[i]!=null&&!(i in t)&&(t[i]=this[i])}},e.prototype.hasState=function(){return this.currentStates.length>0},e.prototype.getState=function(e){return this.states[e]},e.prototype.ensureState=function(e){var t=this.states;return t[e]||(t[e]={}),t[e]},e.prototype.clearStates=function(e){this.useState(Ii,!1,e)},e.prototype.useState=function(e,t,n,r){var i=e===Ii;if(!(!this.hasState()&&i)){var a=this.currentStates,o=this.stateTransition;if(!(ne(a,e)>=0&&(t||a.length===1))){var s;if(this.stateProxy&&!i&&(s=this.stateProxy(e)),s||=this.states&&this.states[e],!s&&!i){F(`State `+e+` not exists.`);return}i||this.saveCurrentToNormalState(s);var l=this._textContent,u=Xi(this,l,s,r);u&&!this.__inHover&&(this.__inHover=u),this._applyStateObj(e,s,this._normalState,t,Qi(this,n,o),o);var d=this._textGuide;return l&&l.useState(e,t,n,!!u),d&&d.useState(e,t,n,!!u),i?(this.currentStates=[],this._normalState={}):t?this.currentStates.push(e):this.currentStates=[e],this._updateAnimationTargets(),this.markRedraw(),!u&&this.__inHover&&(this.__inHover=0,this.__dirty&=-2),s}}},e.prototype.useStates=function(e,t,n){if(!e.length)this.clearStates();else{var r=[],i=this.currentStates,a=e.length,o=a===i.length;if(o){for(var s=0;s<a;s++)if(e[s]!==i[s]){o=!1;break}}if(o)return;for(var s=0;s<a;s++){var l=e[s],u=void 0;this.stateProxy&&(u=this.stateProxy(l,e)),u||=this.states[l],u&&r.push(u)}var d=r[a-1],f=this._textContent,p=Xi(this,f,d,n);p&&!this.__inHover&&(this.__inHover=p);var m=this._mergeStates(r),h=this.stateTransition;this.saveCurrentToNormalState(m),this._applyStateObj(e.join(`,`),m,this._normalState,!1,Qi(this,t,h),h);var g=this._textGuide;f&&f.useStates(e,t,!!p),g&&g.useStates(e,t,!!p),this._updateAnimationTargets(),this.currentStates=e.slice(),this.markRedraw(),!p&&this.__inHover&&(this.__inHover=0,this.__dirty&=-2)}},e.prototype.isSilent=function(){for(var e=this;e;){if(e.silent)return!0;var t=e.__hostTarget;e=t?e.ignoreHostSilent?null:t:e.parent}return!1},e.prototype._updateAnimationTargets=function(){for(var e=0;e<this.animators.length;e++){var t=this.animators[e];t.targetName&&t.changeTarget(this[t.targetName])}},e.prototype.removeState=function(e){var t=ne(this.currentStates,e);if(t>=0){var n=this.currentStates.slice();n.splice(t,1),this.useStates(n)}},e.prototype.replaceState=function(e,t,n){var r=this.currentStates.slice(),i=ne(r,e),a=ne(r,t)>=0;i>=0?a?r.splice(i,1):r[i]=t:n&&!a&&r.push(t),this.useStates(r)},e.prototype.toggleState=function(e,t){t?this.useState(e,!0):this.removeState(e)},e.prototype._mergeStates=function(e){for(var t={},n,r=0;r<e.length;r++){var i=e[r];R(t,i),i.textConfig&&(n||={},R(n,i.textConfig))}return n&&(t.textConfig=n),t},e.prototype._applyStateObj=function(e,t,n,r,i,a){if(this.__inHover!==1){var o=!(t&&r);t&&t.textConfig?(this.textConfig=R({},r?this.textConfig:n.textConfig),R(this.textConfig,t.textConfig)):o&&n.textConfig&&(this.textConfig=n.textConfig);for(var s={},l=!1,u=0;u<Li.length;u++){var d=Li[u],f=i&&Ri[d];t&&t[d]!=null?f?(l=!0,s[d]=t[d]):this[d]=t[d]:o&&n[d]!=null&&(f?(l=!0,s[d]=n[d]):this[d]=n[d])}if(!i)for(var u=0;u<this.animators.length;u++){var p=this.animators[u],m=p.targetName;p.getLoop()||p.__changeFinalValue(m?(t||n)[m]:t||n)}l&&this._transitionState(e,s,a)}},e.prototype._attachComponent=function(e){if(!(e.__zr&&!e.__hostTarget)&&e!==this){var t=this.__zr;t&&e.addSelfToZr(t),e.__zr=t,e.__hostTarget=this}},e.prototype._detachComponent=function(e){e.__zr&&e.removeSelfFromZr(e.__zr),e.__zr=null,e.__hostTarget=null},e.prototype.getClipPath=function(){return this._clipPath},e.prototype.setClipPath=function(e){this._clipPath&&this._clipPath!==e&&this.removeClipPath(),this._attachComponent(e),this._clipPath=e,this.markRedraw()},e.prototype.removeClipPath=function(){var e=this._clipPath;e&&(this._detachComponent(e),this._clipPath=null,this.markRedraw())},e.prototype.getTextContent=function(){return this._textContent},e.prototype.setTextContent=function(e){var t=this._textContent;t!==e&&(t&&t!==e&&this.removeTextContent(),e.innerTransformable=new Xn,this._attachComponent(e),this._textContent=e,this.markRedraw())},e.prototype.setTextConfig=function(e){this.textConfig||={},R(this.textConfig,e),this.markRedraw()},e.prototype.removeTextConfig=function(){this.textConfig=null,this.markRedraw()},e.prototype.removeTextContent=function(){var e=this._textContent;e&&(e.innerTransformable=null,this._detachComponent(e),this._textContent=null,this._innerTextDefaultStyle=null,this.markRedraw())},e.prototype.getTextGuideLine=function(){return this._textGuide},e.prototype.setTextGuideLine=function(e){this._textGuide&&this._textGuide!==e&&this.removeTextGuideLine(),this._attachComponent(e),this._textGuide=e,this.markRedraw()},e.prototype.removeTextGuideLine=function(){var e=this._textGuide;e&&(this._detachComponent(e),this._textGuide=null,this.markRedraw())},e.prototype.markRedraw=function(){this.__dirty|=1;var e=this.__zr;e&&(this.__inHover?e.refreshHover():e.refresh()),this.__hostTarget&&this.__hostTarget.markRedraw()},e.prototype.dirty=function(){this.markRedraw()},e.prototype.addSelfToZr=function(e){if(this.__zr!==e){this.__zr=e;var t=this.animators;if(t)for(var n=0;n<t.length;n++)e.animation.addAnimator(t[n]);this._clipPath&&this._clipPath.addSelfToZr(e),this._textContent&&this._textContent.addSelfToZr(e),this._textGuide&&this._textGuide.addSelfToZr(e)}},e.prototype.removeSelfFromZr=function(e){if(this.__zr){this.__zr=null;var t=this.animators;if(t)for(var n=0;n<t.length;n++)e.animation.removeAnimator(t[n]);this._clipPath&&this._clipPath.removeSelfFromZr(e),this._textContent&&this._textContent.removeSelfFromZr(e),this._textGuide&&this._textGuide.removeSelfFromZr(e)}},e.prototype.animate=function(e,t,n){var r=new Oi(e?this[e]:this,t,n);return e&&(r.targetName=e),this.addAnimator(r,e),r},e.prototype.addAnimator=function(e,t){var n=this.__zr,r=this;e.during(function(){r.updateDuringAnimation(t)}).done(function(){var t=r.animators,n=ne(t,e);n>=0&&t.splice(n,1)}),this.animators.push(e),n&&n.animation.addAnimator(e),n&&n.wakeUp()},e.prototype.updateDuringAnimation=function(e){this.markRedraw()},e.prototype.stopAnimation=function(e,t){for(var n=this.animators,r=n.length,i=[],a=0;a<r;a++){var o=n[a];!e||e===o.scope?o.stop(t):i.push(o)}return this.animators=i,this},e.prototype.animateTo=function(e,t,n){Ui(this,e,t,n)},e.prototype.animateFrom=function(e,t,n){Ui(this,e,t,n,!0)},e.prototype._transitionState=function(e,t,n,r){for(var i=Ui(this,t,n,r),a=0;a<i.length;a++)i[a].__fromStateTransition=e},e.prototype.getBoundingRect=function(){return null},e.prototype.getPaintRect=function(){return null},e.initDefaultProps=(function(){var t=e.prototype;t.type=`element`,t.name=``,t.ignore=t.silent=t.ignoreHostSilent=t.isGroup=t.draggable=t.dragging=t.ignoreClip=!1,t.__inHover=0,t.__dirty=1;function n(e,n,r,i){Object.defineProperty(t,e,{get:function(){if(!this[n]){var e=this[n]=[];a(this,e)}return this[n]},set:function(e){this[r]=e[0],this[i]=e[1],this[n]=e,a(this,e)}});function a(e,t){Object.defineProperty(t,0,{get:function(){return e[r]},set:function(t){e[r]=t}}),Object.defineProperty(t,1,{get:function(){return e[i]},set:function(t){e[i]=t}})}}Object.defineProperty&&(n(`position`,`_legacyPos`,`x`,`y`),n(`scale`,`_legacyScale`,`scaleX`,`scaleY`),n(`origin`,`_legacyOrigin`,`originX`,`originY`))})(),e}();ie(Hi,ki),ie(Hi,Xn);function Ui(e,t,n,r,i){n||={};var a=[];Yi(e,``,e,t,n,r,a,i);var o=a.length,s=!1,l=n.done,u=n.aborted,d=function(){s=!0,o--,o<=0&&(s?l&&l():u&&u())},f=function(){o--,o<=0&&(s?l&&l():u&&u())};o||l&&l(),a.length>0&&n.during&&a[0].during(function(e,t){n.during(t)});for(var p=0;p<a.length;p++){var m=a[p];d&&m.done(d),f&&m.aborted(f),n.force&&m.duration(n.duration),m.start(n.easing)}return a}function Wi(e,t,n){for(var r=0;r<n;r++)e[r]=t[r]}function Gi(e){return ae(e[0])}function Ki(e,t,n){if(ae(t[n]))if(ae(e[n])||(e[n]=[]),xe(t[n])){var r=t[n].length;e[n].length!==r&&(e[n]=new t[n].constructor(r),Wi(e[n],t[n],r))}else{var i=t[n],a=e[n],o=i.length;if(Gi(i))for(var s=i[0].length,l=0;l<o;l++)a[l]?Wi(a[l],i[l],s):a[l]=Array.prototype.slice.call(i[l]);else Wi(a,i,o);a.length=i.length}else e[n]=t[n]}function qi(e,t){return e===t||ae(e)&&ae(t)&&Ji(e,t)}function Ji(e,t){var n=e.length;if(n!==t.length)return!1;for(var r=0;r<n;r++)if(e[r]!==t[r])return!1;return!0}function Yi(e,t,n,r,i,a,o,s){for(var l=ue(r),u=i.duration,d=i.delay,f=i.additive,p=i.setToFinal,m=!ye(a),h=e.animators,g=[],_=0;_<l.length;_++){var v=l[_],y=r[v];if(y!=null&&n[v]!=null&&(m||a[v]))if(ye(y)&&!ae(y)&&!Ce(y)){if(t){s||(n[v]=y,e.updateDuringAnimation(t));continue}Yi(e,v,n[v],y,i,a&&a[v],o,s)}else g.push(v);else s||(n[v]=y,e.updateDuringAnimation(t),g.push(v))}var b=g.length;if(!f&&b)for(var x=0;x<h.length;x++){var S=h[x];if(S.targetName===t&&S.stopTracks(g)){var C=ne(h,S);h.splice(C,1)}}if(i.force||(g=ce(g,function(e){return!qi(r[e],n[e])}),b=g.length),b>0||i.force&&!o.length){var w=void 0,T=void 0,E=void 0;if(s){T={},p&&(w={});for(var x=0;x<b;x++){var v=g[x];T[v]=n[v],p?w[v]=r[v]:n[v]=r[v]}}else if(p){E={};for(var x=0;x<b;x++){var v=g[x];E[v]=mi(n[v]),Ki(n,r,v)}}var S=new Oi(n,!1,!1,f?ce(h,function(e){return e.targetName===t}):null);S.targetName=t,i.scope&&(S.scope=i.scope),p&&w&&S.whenWithKeys(0,w,g),E&&S.whenWithKeys(0,E,g),S.whenWithKeys(u??500,s?T:r,g).delay(d||0),e.addAnimator(S,t),o.push(S)}}function Xi(e,t,n,r){return!(n&&n.hoverLayer||r)||Zi(e)||t&&Zi(t)?0:1}function Zi(e){return e.type===`text`||e.type===`tspan`}function Qi(e,t,n){return!t&&!e.__inHover&&n&&n.duration>0}var $i=`__zr_style_`+Math.round(Math.random()*10),ea={shadowBlur:0,shadowOffsetX:0,shadowOffsetY:0,shadowColor:`#000`,opacity:1,blend:`source-over`},ta={style:{shadowBlur:!0,shadowOffsetX:!0,shadowOffsetY:!0,shadowColor:!0,opacity:!0}};ea[$i]=!0;var na=[`z`,`z2`,`invisible`],ra=[`invisible`],ia=function(e){p(t,e);function t(t){return e.call(this,t)||this}return t.prototype._init=function(t){for(var n=ue(t),r=0;r<n.length;r++){var i=n[r];i===`style`?this.useStyle(t[i]):e.prototype.attrKV.call(this,i,t[i])}this.style||this.useStyle({})},t.prototype.beforeBrush=function(e){},t.prototype.afterBrush=function(){},t.prototype.innerBeforeBrush=function(){},t.prototype.innerAfterBrush=function(){},t.prototype.shouldBePainted=function(e,t,n,r){var i=this.transform;if(this.ignore||this.invisible||this.style.opacity===0||this.culling&&bee(this,e,t)||i&&!i[0]&&!i[3])return!1;if(n&&this.__clipPaths&&this.__clipPaths.length){for(var a=0;a<this.__clipPaths.length;++a)if(this.__clipPaths[a].isZeroArea())return!1}if(r&&this.parent)for(var o=this.parent;o;){if(o.ignore)return!1;o=o.parent}return!0},t.prototype.contain=function(e,t){return this.rectContain(e,t)},t.prototype.traverse=function(e,t){e.call(t,this)},t.prototype.rectContain=function(e,t){var n=this.transformCoordToLocal(e,t);return this.getBoundingRect().contain(n[0],n[1])},t.prototype.getPaintRect=function(){var e=this._paintRect;if(!this._paintRect||this.__dirty){var t=this.transform,n=this.getBoundingRect(),r=this.style,i=r.shadowBlur||0,a=r.shadowOffsetX||0,o=r.shadowOffsetY||0;e=this._paintRect||=new an(0,0,0,0),t?an.applyTransform(e,n,t):e.copy(n),(i||a||o)&&(e.width+=i*2+Math.abs(a),e.height+=i*2+Math.abs(o),e.x=Math.min(e.x,e.x+a-i),e.y=Math.min(e.y,e.y+o-i));var s=this.dirtyRectTolerance;e.isZero()||(e.x=Math.floor(e.x-s),e.y=Math.floor(e.y-s),e.width=Math.ceil(e.width+1+s*2),e.height=Math.ceil(e.height+1+s*2))}return e},t.prototype.setPrevPaintRect=function(e){e?(this._prevPaintRect=this._prevPaintRect||new an(0,0,0,0),this._prevPaintRect.copy(e)):this._prevPaintRect=null},t.prototype.getPrevPaintRect=function(){return this._prevPaintRect},t.prototype.animateStyle=function(e){return this.animate(`style`,e)},t.prototype.updateDuringAnimation=function(e){e===`style`?this.dirtyStyle():this.markRedraw()},t.prototype.attrKV=function(t,n){t===`style`?this.style?this.setStyle(n):this.useStyle(n):e.prototype.attrKV.call(this,t,n)},t.prototype.setStyle=function(e,t){return typeof e==`string`?this.style[e]=t:R(this.style,e),this.dirtyStyle(),this},t.prototype.dirtyStyle=function(e){e||this.markRedraw(),this.__dirty|=2,this._rect&&=null},t.prototype.dirty=function(){this.dirtyStyle()},t.prototype.styleChanged=function(){return!!(this.__dirty&2)},t.prototype.styleUpdated=function(){this.__dirty&=-3},t.prototype.createStyle=function(e){return Ve(ea,e)},t.prototype.useStyle=function(e){e[$i]||(e=this.createStyle(e)),this.style=e,this.dirtyStyle()},t.prototype._useHoverStyle=function(e){this.__hoverStyle=e},t.prototype.isStyleObject=function(e){return e[$i]},t.prototype._innerSaveToNormal=function(t){e.prototype._innerSaveToNormal.call(this,t);var n=this._normalState;t.style&&!n.style&&(n.style=this._mergeStyle(this.createStyle(),this.style)),this._savePrimaryToNormal(t,n,na)},t.prototype._applyStateObj=function(t,n,r,i,a,o){e.prototype._applyStateObj.call(this,t,n,r,i,a,o);var s=!(n&&i),l=this.__inHover===1,u;if(n&&n.style?a?i?u=n.style:(u=this._mergeStyle(this.createStyle(),r.style),this._mergeStyle(u,n.style)):(u=this._mergeStyle(this.createStyle(),i?this.style:r.style),this._mergeStyle(u,n.style)):s&&(u=r.style),u)if(a){var d=this.style;if(this.style=this.createStyle(s?{}:d),s)for(var f=ue(d),p=0;p<f.length;p++){var m=f[p];m in u&&(u[m]=u[m],this.style[m]=d[m])}for(var h=ue(u),p=0;p<h.length;p++){var m=h[p];this.style[m]=this.style[m]}this._transitionState(t,{style:u},o,this.getAnimationStyleProps())}else l?this._useHoverStyle(u):this.useStyle(u);if(!l)for(var g=this.__inHover?ra:na,p=0;p<g.length;p++){var m=g[p];n&&n[m]!=null?this[m]=n[m]:s&&r[m]!=null&&(this[m]=r[m])}},t.prototype._mergeStates=function(t){for(var n=e.prototype._mergeStates.call(this,t),r,i=0;i<t.length;i++){var a=t[i];a.style&&(r||={},this._mergeStyle(r,a.style))}return r&&(n.style=r),n},t.prototype._mergeStyle=function(e,t){return R(e,t),e},t.prototype.getAnimationStyleProps=function(){return ta},t.initDefaultProps=(function(){var e=t.prototype;e.type=`displayable`,e.invisible=!1,e.z=0,e.z2=0,e.zlevel=0,e.culling=!1,e.cursor=`pointer`,e.rectHover=!1,e.incremental=0,e._rect=null,e.dirtyRectTolerance=0,e.__dirty=3})(),t}(Hi),aa=new an(0,0,0,0),oa=new an(0,0,0,0);function bee(e,t,n){return aa.copy(e.getBoundingRect()),e.transform&&aa.applyTransform(e.transform),oa.width=t,oa.height=n,!aa.intersect(oa)}var sa=Math.min,ca=Math.max,la=Math.sin,ua=Math.cos,da=Math.PI*2,fa=Dt(),pa=Dt(),ma=Dt();function ha(e,t,n,r,i,a){i[0]=sa(e,n),i[1]=sa(t,r),a[0]=ca(e,n),a[1]=ca(t,r)}var ga=[],_a=[];function va(e,t,n,r,i,a,o,s,l,u){var d=pr,f=ur,p=d(e,n,i,o,ga);l[0]=1/0,l[1]=1/0,u[0]=-1/0,u[1]=-1/0;for(var m=0;m<p;m++){var h=f(e,n,i,o,ga[m]);l[0]=sa(h,l[0]),u[0]=ca(h,u[0])}p=d(t,r,a,s,_a);for(var m=0;m<p;m++){var g=f(t,r,a,s,_a[m]);l[1]=sa(g,l[1]),u[1]=ca(g,u[1])}l[0]=sa(e,l[0]),u[0]=ca(e,u[0]),l[0]=sa(o,l[0]),u[0]=ca(o,u[0]),l[1]=sa(t,l[1]),u[1]=ca(t,u[1]),l[1]=sa(s,l[1]),u[1]=ca(s,u[1])}function xee(e,t,n,r,i,a,o,s){var l=vr,u=gr,d=ca(sa(l(e,n,i),1),0),f=ca(sa(l(t,r,a),1),0),p=u(e,n,i,d),m=u(t,r,a,f);o[0]=sa(e,i,p),o[1]=sa(t,a,m),s[0]=ca(e,i,p),s[1]=ca(t,a,m)}function See(e,t,n,r,i,a,o,s,l){var u=Ht,d=Ut,f=Math.abs(i-a);if(f%da<1e-4&&f>1e-4){s[0]=e-n,s[1]=t-r,l[0]=e+n,l[1]=t+r;return}if(fa[0]=ua(i)*n+e,fa[1]=la(i)*r+t,pa[0]=ua(a)*n+e,pa[1]=la(a)*r+t,u(s,fa,pa),d(l,fa,pa),i%=da,i<0&&(i+=da),a%=da,a<0&&(a+=da),i>a&&!o?a+=da:i<a&&o&&(i+=da),o){var p=a;a=i,i=p}for(var m=0;m<a;m+=Math.PI/2)m>i&&(ma[0]=ua(m)*n+e,ma[1]=la(m)*r+t,u(s,ma,s),d(l,ma,l))}var ya={M:1,L:2,C:3,Q:4,A:5,Z:6,R:7},ba=[],xa=[],Sa=[],Ca=[],wa=[],Ta=[],Ea=Math.min,Da=Math.max,Oa=Math.cos,ka=Math.sin,Aa=Math.abs,ja=Math.PI,Ma=ja*2,Na=typeof Float32Array<`u`,Pa=[];function Fa(e){return Math.round(e/ja*1e8)/1e8%2*ja}function Ia(e,t){var n=Fa(e[0]);n<0&&(n+=Ma);var r=n-e[0],i=e[1];i+=r,!t&&i-n>=Ma?i=n+Ma:t&&n-i>=Ma?i=n-Ma:!t&&n>i?i=n+(Ma-Fa(n-i)):t&&n<i&&(i=n-(Ma-Fa(i-n))),e[0]=n,e[1]=i}var La=function(){function e(e){this.dpr=1,this._xi=0,this._yi=0,this._x0=0,this._y0=0,this._len=0,e&&(this._saveData=!1),this._saveData&&(this.data=[])}return e.prototype.increaseVersion=function(){this._version++},e.prototype.getVersion=function(){return this._version},e.prototype.setScale=function(e,t,n){n||=0,n>0&&(this._ux=Aa(n/ji/e)||0,this._uy=Aa(n/ji/t)||0)},e.prototype.setDPR=function(e){this.dpr=e},e.prototype.setContext=function(e){this._ctx=e},e.prototype.getContext=function(){return this._ctx},e.prototype.beginPath=function(){return this._ctx&&this._ctx.beginPath(),this.reset(),this},e.prototype.reset=function(){this._saveData&&(this._len=0),this._pathSegLen&&(this._pathSegLen=null,this._pathLen=0),this._version++},e.prototype.moveTo=function(e,t){return this._drawPendingPt(),this.addData(ya.M,e,t),this._ctx&&this._ctx.moveTo(e,t),this._x0=e,this._y0=t,this._xi=e,this._yi=t,this},e.prototype.lineTo=function(e,t){var n=Aa(e-this._xi),r=Aa(t-this._yi),i=n>this._ux||r>this._uy;if(this.addData(ya.L,e,t),this._ctx&&i&&this._ctx.lineTo(e,t),i)this._xi=e,this._yi=t,this._pendingPtDist=0;else{var a=n*n+r*r;a>this._pendingPtDist&&(this._pendingPtX=e,this._pendingPtY=t,this._pendingPtDist=a)}return this},e.prototype.bezierCurveTo=function(e,t,n,r,i,a){return this._drawPendingPt(),this.addData(ya.C,e,t,n,r,i,a),this._ctx&&this._ctx.bezierCurveTo(e,t,n,r,i,a),this._xi=i,this._yi=a,this},e.prototype.quadraticCurveTo=function(e,t,n,r){return this._drawPendingPt(),this.addData(ya.Q,e,t,n,r),this._ctx&&this._ctx.quadraticCurveTo(e,t,n,r),this._xi=n,this._yi=r,this},e.prototype.arc=function(e,t,n,r,i,a){this._drawPendingPt(),Pa[0]=r,Pa[1]=i,Ia(Pa,a),r=Pa[0],i=Pa[1];var o=i-r;return this.addData(ya.A,e,t,n,n,r,o,0,+!a),this._ctx&&this._ctx.arc(e,t,n,r,i,a),this._xi=Oa(i)*n+e,this._yi=ka(i)*n+t,this},e.prototype.arcTo=function(e,t,n,r,i){return this._drawPendingPt(),this._ctx&&this._ctx.arcTo(e,t,n,r,i),this},e.prototype.rect=function(e,t,n,r){return this._drawPendingPt(),this._ctx&&this._ctx.rect(e,t,n,r),this.addData(ya.R,e,t,n,r),this},e.prototype.closePath=function(){this._drawPendingPt(),this.addData(ya.Z);var e=this._ctx,t=this._x0,n=this._y0;return e&&e.closePath(),this._xi=t,this._yi=n,this},e.prototype.fill=function(e){e&&e.fill(),this.toStatic()},e.prototype.stroke=function(e){e&&e.stroke(),this.toStatic()},e.prototype.len=function(){return this._len},e.prototype.setData=function(e){if(this._saveData){var t=e.length;!(this.data&&this.data.length===t)&&Na&&(this.data=new Float32Array(t));for(var n=0;n<t;n++)this.data[n]=e[n];this._len=t}},e.prototype.appendPath=function(e){if(this._saveData){e instanceof Array||(e=[e]);for(var t=e.length,n=0,r=this._len,i=0;i<t;i++)n+=e[i].len();var a=this.data;if(Na&&(a instanceof Float32Array||!a)&&(this.data=new Float32Array(r+n),r>0&&a))for(var o=0;o<r;o++)this.data[o]=a[o];for(var i=0;i<t;i++)for(var s=e[i].data,o=0;o<s.length;o++)this.data[r++]=s[o];this._len=r}},e.prototype.addData=function(e,t,n,r,i,a,o,s,l){if(this._saveData){var u=this.data;this._len+arguments.length>u.length&&(this._expandData(),u=this.data);for(var d=0;d<arguments.length;d++)u[this._len++]=arguments[d]}},e.prototype._drawPendingPt=function(){this._pendingPtDist>0&&(this._ctx&&this._ctx.lineTo(this._pendingPtX,this._pendingPtY),this._pendingPtDist=0)},e.prototype._expandData=function(){if(!(this.data instanceof Array)){for(var e=[],t=0;t<this._len;t++)e[t]=this.data[t];this.data=e}},e.prototype.toStatic=function(){if(this._saveData){this._drawPendingPt();var e=this.data;e instanceof Array&&(e.length=this._len,Na&&this._len>11&&(this.data=new Float32Array(e)))}},e.prototype.getBoundingRect=function(){Sa[0]=Sa[1]=wa[0]=wa[1]=Number.MAX_VALUE,Ca[0]=Ca[1]=Ta[0]=Ta[1]=-Number.MAX_VALUE;var e=this.data,t=0,n=0,r=0,i=0,a;for(a=0;a<this._len;){var o=e[a++],s=a===1;switch(s&&(t=e[a],n=e[a+1],r=t,i=n),o){case ya.M:t=r=e[a++],n=i=e[a++],wa[0]=r,wa[1]=i,Ta[0]=r,Ta[1]=i;break;case ya.L:ha(t,n,e[a],e[a+1],wa,Ta),t=e[a++],n=e[a++];break;case ya.C:va(t,n,e[a++],e[a++],e[a++],e[a++],e[a],e[a+1],wa,Ta),t=e[a++],n=e[a++];break;case ya.Q:xee(t,n,e[a++],e[a++],e[a],e[a+1],wa,Ta),t=e[a++],n=e[a++];break;case ya.A:var l=e[a++],u=e[a++],d=e[a++],f=e[a++],p=e[a++],m=e[a++]+p;a+=1;var h=!e[a++];s&&(r=Oa(p)*d+l,i=ka(p)*f+u),See(l,u,d,f,p,m,h,wa,Ta),t=Oa(m)*d+l,n=ka(m)*f+u;break;case ya.R:r=t=e[a++],i=n=e[a++];var g=e[a++],_=e[a++];ha(r,i,r+g,i+_,wa,Ta);break;case ya.Z:t=r,n=i;break}Ht(Sa,Sa,wa),Ut(Ca,Ca,Ta)}return a===0&&(Sa[0]=Sa[1]=Ca[0]=Ca[1]=0),new an(Sa[0],Sa[1],Ca[0]-Sa[0],Ca[1]-Sa[1])},e.prototype._calculateLength=function(){var e=this.data,t=this._len,n=this._ux,r=this._uy,i=0,a=0,o=0,s=0;this._pathSegLen||=[];for(var l=this._pathSegLen,u=0,d=0,f=0;f<t;){var p=e[f++],m=f===1;m&&(i=e[f],a=e[f+1],o=i,s=a);var h=-1;switch(p){case ya.M:i=o=e[f++],a=s=e[f++];break;case ya.L:var g=e[f++],_=e[f++],v=g-i,y=_-a;(Aa(v)>n||Aa(y)>r||f===t-1)&&(h=Math.sqrt(v*v+y*y),i=g,a=_);break;case ya.C:var b=e[f++],x=e[f++],g=e[f++],_=e[f++],S=e[f++],C=e[f++];h=lee(i,a,b,x,g,_,S,C,10),i=S,a=C;break;case ya.Q:var b=e[f++],x=e[f++],g=e[f++],_=e[f++];h=fee(i,a,b,x,g,_,10),i=g,a=_;break;case ya.A:var w=e[f++],T=e[f++],E=e[f++],D=e[f++],O=e[f++],k=e[f++],A=k+O;f+=1,m&&(o=Oa(O)*E+w,s=ka(O)*D+T),h=Da(E,D)*Ea(Ma,Math.abs(k)),i=Oa(A)*E+w,a=ka(A)*D+T;break;case ya.R:o=i=e[f++],s=a=e[f++];var j=e[f++],M=e[f++];h=j*2+M*2;break;case ya.Z:var v=o-i,y=s-a;h=Math.sqrt(v*v+y*y),i=o,a=s;break}h>=0&&(l[d++]=h,u+=h)}return this._pathLen=u,u},e.prototype.rebuildPath=function(e,t){var n=this.data,r=this._ux,i=this._uy,a=this._len,o,s,l,u,d,f,p=t<1,m,h,g=0,_=0,v,y=0,b,x;if(!(p&&(this._pathSegLen||this._calculateLength(),m=this._pathSegLen,h=this._pathLen,v=t*h,!v)))lo:for(var S=0;S<a;){var C=n[S++],w=S===1;switch(w&&(l=n[S],u=n[S+1],o=l,s=u),C!==ya.L&&y>0&&(e.lineTo(b,x),y=0),C){case ya.M:o=l=n[S++],s=u=n[S++],e.moveTo(l,u);break;case ya.L:d=n[S++],f=n[S++];var T=Aa(d-l),E=Aa(f-u);if(T>r||E>i){if(p){var D=m[_++];if(g+D>v){var O=(v-g)/D;e.lineTo(l*(1-O)+d*O,u*(1-O)+f*O);break lo}g+=D}e.lineTo(d,f),l=d,u=f,y=0}else{var k=T*T+E*E;k>y&&(b=d,x=f,y=k)}break;case ya.C:var A=n[S++],j=n[S++],M=n[S++],N=n[S++],P=n[S++],F=n[S++];if(p){var D=m[_++];if(g+D>v){var O=(v-g)/D;mr(l,A,M,P,O,ba),mr(u,j,N,F,O,xa),e.bezierCurveTo(ba[1],xa[1],ba[2],xa[2],ba[3],xa[3]);break lo}g+=D}e.bezierCurveTo(A,j,M,N,P,F),l=P,u=F;break;case ya.Q:var A=n[S++],j=n[S++],M=n[S++],N=n[S++];if(p){var D=m[_++];if(g+D>v){var O=(v-g)/D;yr(l,A,M,O,ba),yr(u,j,N,O,xa),e.quadraticCurveTo(ba[1],xa[1],ba[2],xa[2]);break lo}g+=D}e.quadraticCurveTo(A,j,M,N),l=M,u=N;break;case ya.A:var I=n[S++],L=n[S++],R=n[S++],ee=n[S++],te=n[S++],ne=n[S++],re=n[S++],ie=!n[S++],ae=R>ee?R:ee,z=Aa(R-ee)>.001,oe=te+ne,se=!1;if(p){var D=m[_++];g+D>v&&(oe=te+ne*(v-g)/D,se=!0),g+=D}if(z&&e.ellipse?e.ellipse(I,L,R,ee,re,te,oe,ie):e.arc(I,L,ae,te,oe,ie),se)break lo;w&&(o=Oa(te)*R+I,s=ka(te)*ee+L),l=Oa(oe)*R+I,u=ka(oe)*ee+L;break;case ya.R:o=l=n[S],s=u=n[S+1],d=n[S++],f=n[S++];var ce=n[S++],le=n[S++];if(p){var D=m[_++];if(g+D>v){var ue=v-g;e.moveTo(d,f),e.lineTo(d+Ea(ue,ce),f),ue-=ce,ue>0&&e.lineTo(d+ce,f+Ea(ue,le)),ue-=le,ue>0&&e.lineTo(d+Da(ce-ue,0),f+le),ue-=ce,ue>0&&e.lineTo(d,f+Da(le-ue,0));break lo}g+=D}e.rect(d,f,ce,le);break;case ya.Z:if(p){var D=m[_++];if(g+D>v){var O=(v-g)/D;e.lineTo(l*(1-O)+o*O,u*(1-O)+s*O);break lo}g+=D}e.closePath(),l=o,u=s}}},e.prototype.clone=function(){var t=new e,n=this.data;return t.data=n.slice?n.slice():Array.prototype.slice.call(n),t._len=this._len,t},e.prototype.canSave=function(){return!!this._saveData},e.CMD=ya,e.initDefaultProps=(function(){var t=e.prototype;t._saveData=!0,t._ux=0,t._uy=0,t._pendingPtDist=0,t._version=0})(),e}();function Ra(e,t,n,r,i,a,o){if(i===0)return!1;var s=i,l=0,u=e;if(o>t+s&&o>r+s||o<t-s&&o<r-s||a>e+s&&a>n+s||a<e-s&&a<n-s)return!1;if(e!==n)l=(t-r)/(e-n),u=(e*r-n*t)/(e-n);else return Math.abs(a-e)<=s/2;var d=l*a-o+u;return d*d/(l*l+1)<=s/2*s/2}function za(e,t,n,r,i,a,o,s,l,u,d){if(l===0)return!1;var f=l;return d>t+f&&d>r+f&&d>a+f&&d>s+f||d<t-f&&d<r-f&&d<a-f&&d<s-f||u>e+f&&u>n+f&&u>i+f&&u>o+f||u<e-f&&u<n-f&&u<i-f&&u<o-f?!1:hr(e,t,n,r,i,a,o,s,u,d,null)<=f/2}function Cee(e,t,n,r,i,a,o,s,l){if(o===0)return!1;var u=o;return l>t+u&&l>r+u&&l>a+u||l<t-u&&l<r-u&&l<a-u||s>e+u&&s>n+u&&s>i+u||s<e-u&&s<n-u&&s<i-u?!1:dee(e,t,n,r,i,a,s,l,null)<=u/2}var Ba=Math.PI*2;function Va(e){return e%=Ba,e<0&&(e+=Ba),e}var Ha=Math.PI*2;function Ua(e,t,n,r,i,a,o,s,l){if(o===0)return!1;var u=o;s-=e,l-=t;var d=Math.sqrt(s*s+l*l);if(d-u>n||d+u<n)return!1;if(Math.abs(r-i)%Ha<1e-4)return!0;if(a){var f=r;r=Va(i),i=Va(f)}else r=Va(r),i=Va(i);r>i&&(i+=Ha);var p=Math.atan2(l,s);return p<0&&(p+=Ha),p>=r&&p<=i||p+Ha>=r&&p+Ha<=i}function Wa(e,t,n,r,i,a){if(a>t&&a>r||a<t&&a<r||r===t)return 0;var o=(a-t)/(r-t),s=r<t?1:-1;(o===1||o===0)&&(s=r<t?.5:-.5);var l=o*(n-e)+e;return l===i?1/0:l>i?s:0}var Ga=La.CMD,Ka=Math.PI*2,qa=1e-4;function Ja(e,t){return Math.abs(e-t)<qa}var Ya=[-1,-1,-1],Xa=[-1,-1];function Za(){var e=Xa[0];Xa[0]=Xa[1],Xa[1]=e}function wee(e,t,n,r,i,a,o,s,l,u){if(u>t&&u>r&&u>a&&u>s||u<t&&u<r&&u<a&&u<s)return 0;var d=fr(t,r,a,s,u,Ya);if(d===0)return 0;for(var f=0,p=-1,m=void 0,h=void 0,g=0;g<d;g++){var _=Ya[g],v=_===0||_===1?.5:1;ur(e,n,i,o,_)<l||(p<0&&(p=pr(t,r,a,s,Xa),Xa[1]<Xa[0]&&p>1&&Za(),m=ur(t,r,a,s,Xa[0]),p>1&&(h=ur(t,r,a,s,Xa[1]))),p===2?_<Xa[0]?f+=m<t?v:-v:_<Xa[1]?f+=h<m?v:-v:f+=s<h?v:-v:_<Xa[0]?f+=m<t?v:-v:f+=s<m?v:-v)}return f}function Tee(e,t,n,r,i,a,o,s){if(s>t&&s>r&&s>a||s<t&&s<r&&s<a)return 0;var l=uee(t,r,a,s,Ya);if(l===0)return 0;var u=vr(t,r,a);if(u>=0&&u<=1){for(var d=0,f=gr(t,r,a,u),p=0;p<l;p++){var m=Ya[p]===0||Ya[p]===1?.5:1,h=gr(e,n,i,Ya[p]);h<o||(Ya[p]<u?d+=f<t?m:-m:d+=a<f?m:-m)}return d}else{var m=Ya[0]===0||Ya[0]===1?.5:1,h=gr(e,n,i,Ya[0]);return h<o?0:a<t?m:-m}}function Qa(e,t,n,r,i,a,o,s){if(s-=t,s>n||s<-n)return 0;var l=Math.sqrt(n*n-s*s);Ya[0]=-l,Ya[1]=l;var u=Math.abs(r-i);if(u<1e-4)return 0;if(u>=Ka-1e-4){r=0,i=Ka;var d=a?1:-1;return o>=Ya[0]+e&&o<=Ya[1]+e?d:0}if(r>i){var f=r;r=i,i=f}r<0&&(r+=Ka,i+=Ka);for(var p=0,m=0;m<2;m++){var h=Ya[m];if(h+e>o){var g=Math.atan2(s,h),d=a?1:-1;g<0&&(g=Ka+g),(g>=r&&g<=i||g+Ka>=r&&g+Ka<=i)&&(g>Math.PI/2&&g<Math.PI*1.5&&(d=-d),p+=d)}}return p}function $a(e,t,n,r,i){for(var a=e.data,o=e.len(),s=0,l=0,u=0,d=0,f=0,p,m,h=0;h<o;){var g=a[h++],_=h===1;switch(g===Ga.M&&h>1&&(n||(s+=Wa(l,u,d,f,r,i))),_&&(l=a[h],u=a[h+1],d=l,f=u),g){case Ga.M:d=a[h++],f=a[h++],l=d,u=f;break;case Ga.L:if(n){if(Ra(l,u,a[h],a[h+1],t,r,i))return!0}else s+=Wa(l,u,a[h],a[h+1],r,i)||0;l=a[h++],u=a[h++];break;case Ga.C:if(n){if(za(l,u,a[h++],a[h++],a[h++],a[h++],a[h],a[h+1],t,r,i))return!0}else s+=wee(l,u,a[h++],a[h++],a[h++],a[h++],a[h],a[h+1],r,i)||0;l=a[h++],u=a[h++];break;case Ga.Q:if(n){if(Cee(l,u,a[h++],a[h++],a[h],a[h+1],t,r,i))return!0}else s+=Tee(l,u,a[h++],a[h++],a[h],a[h+1],r,i)||0;l=a[h++],u=a[h++];break;case Ga.A:var v=a[h++],y=a[h++],b=a[h++],x=a[h++],S=a[h++],C=a[h++];h+=1;var w=!!(1-a[h++]);p=Math.cos(S)*b+v,m=Math.sin(S)*x+y,_?(d=p,f=m):s+=Wa(l,u,p,m,r,i);var T=(r-v)*x/b+v;if(n){if(Ua(v,y,x,S,S+C,w,t,T,i))return!0}else s+=Qa(v,y,x,S,S+C,w,T,i);l=Math.cos(S+C)*b+v,u=Math.sin(S+C)*x+y;break;case Ga.R:d=l=a[h++],f=u=a[h++];var E=a[h++],D=a[h++];if(p=d+E,m=f+D,n){if(Ra(d,f,p,f,t,r,i)||Ra(p,f,p,m,t,r,i)||Ra(p,m,d,m,t,r,i)||Ra(d,m,d,f,t,r,i))return!0}else s+=Wa(p,f,p,m,r,i),s+=Wa(d,m,d,f,r,i);break;case Ga.Z:if(n){if(Ra(l,u,d,f,t,r,i))return!0}else s+=Wa(l,u,d,f,r,i);l=d,u=f;break}}return!n&&!Ja(u,f)&&(s+=Wa(l,u,d,f,r,i)||0),s!==0}function Eee(e,t,n){return $a(e,0,!1,t,n)}function eo(e,t,n,r){return $a(e,t,!0,n,r)}var to=te({fill:`#000`,stroke:null,strokePercent:1,fillOpacity:1,strokeOpacity:1,lineDashOffset:0,lineWidth:1,lineCap:`butt`,miterLimit:10,strokeNoScale:!1,strokeFirst:!1},ea),no={style:te({fill:!0,stroke:!0,strokePercent:!0,fillOpacity:!0,strokeOpacity:!0,lineDashOffset:!0,lineWidth:!0,miterLimit:!0},ta.style)},ro=Zn.concat([`invisible`,`culling`,`z`,`z2`,`zlevel`,`parent`]),io=function(e){p(t,e);function t(t){return e.call(this,t)||this}return t.prototype.update=function(){var n=this;e.prototype.update.call(this);var r=this.style;if(r.decal){var i=this._decalEl=this._decalEl||new t;i.buildPath===t.prototype.buildPath&&(i.buildPath=function(e){n.buildPath(e,n.shape)}),i.silent=!0;var a=i.style;for(var o in r)a[o]!==r[o]&&(a[o]=r[o]);a.fill=r.fill?r.decal:null,a.decal=null,a.shadowColor=null,r.strokeFirst&&(a.stroke=null);for(var s=0;s<ro.length;++s)i[ro[s]]=this[ro[s]];i.__dirty|=1}else this._decalEl&&=null},t.prototype.getDecalElement=function(){return this._decalEl},t.prototype._init=function(t){var n=ue(t);this.shape=this.getDefaultShape();var r=this.getDefaultStyle();r&&this.useStyle(r);for(var i=0;i<n.length;i++){var a=n[i],o=t[a];a===`style`?this.style?R(this.style,o):this.useStyle(o):a===`shape`?R(this.shape,o):e.prototype.attrKV.call(this,a,o)}this.style||this.useStyle({})},t.prototype.getDefaultStyle=function(){return null},t.prototype.getDefaultShape=function(){return{}},t.prototype.canBeInsideText=function(){return this.hasFill()},t.prototype.getInsideTextFill=function(){var e=this.style.fill;if(e!==`none`){if(ge(e)){var t=Vr(e,0);return t>.5?Ni:t>.2?Fi:Pi}else if(e)return Pi}return Ni},t.prototype.getInsideTextStroke=function(e){var t=this.style.fill;if(ge(t)){var n=this.__zr;if(!!(n&&n.isDarkMode())==Vr(e,0)<.4)return t}},t.prototype.buildPath=function(e,t,n){},t.prototype.pathUpdated=function(){this.__dirty&=-5},t.prototype.getUpdatedPathProxy=function(e){return!this.path&&this.createPathProxy(),this.path.beginPath(),this.buildPath(this.path,this.shape,e),this.path},t.prototype.createPathProxy=function(){this.path=new La(!1)},t.prototype.hasStroke=function(){var e=this.style,t=e.stroke;return!(t==null||t===`none`||!(e.lineWidth>0))},t.prototype.hasFill=function(){var e=this.style.fill;return e!=null&&e!==`none`},t.prototype.getBoundingRect=function(){var e=this._rect,t=this.style,n=!e;if(n){var r=!1;this.path||(r=!0,this.createPathProxy());var i=this.path;(r||this.__dirty&4)&&(i.beginPath(),this.buildPath(i,this.shape,!1),this.pathUpdated()),e=i.getBoundingRect()}if(this._rect=e,this.hasStroke()&&this.path&&this.path.len()>0){var a=this._rectStroke||=e.clone();if(this.__dirty||n){a.copy(e);var o=t.strokeNoScale?this.getLineScale():1,s=t.lineWidth;if(!this.hasFill()){var l=this.strokeContainThreshold;s=Math.max(s,l??4)}o>1e-10&&(a.width+=s/o,a.height+=s/o,a.x-=s/o/2,a.y-=s/o/2)}return a}return e},t.prototype.contain=function(e,t){var n=this.transformCoordToLocal(e,t),r=this.getBoundingRect(),i=this.style;if(e=n[0],t=n[1],r.contain(e,t)){var a=this.path;if(this.hasStroke()){var o=i.lineWidth,s=i.strokeNoScale?this.getLineScale():1;if(s>1e-10&&(this.hasFill()||(o=Math.max(o,this.strokeContainThreshold)),eo(a,o/s,e,t)))return!0}if(this.hasFill())return Eee(a,e,t)}return!1},t.prototype.dirtyShape=function(){this.__dirty|=4,this._rect&&=null,this._decalEl&&this._decalEl.dirtyShape(),this.markRedraw()},t.prototype.dirty=function(){this.dirtyStyle(),this.dirtyShape()},t.prototype.animateShape=function(e){return this.animate(`shape`,e)},t.prototype.updateDuringAnimation=function(e){e===`style`?this.dirtyStyle():e===`shape`?this.dirtyShape():this.markRedraw()},t.prototype.attrKV=function(t,n){t===`shape`?this.setShape(n):e.prototype.attrKV.call(this,t,n)},t.prototype.setShape=function(e,t){var n=this.shape;return n||=this.shape={},typeof e==`string`?n[e]=t:R(n,e),this.dirtyShape(),this},t.prototype.shapeChanged=function(){return!!(this.__dirty&4)},t.prototype.createStyle=function(e){return Ve(to,e)},t.prototype._innerSaveToNormal=function(t){e.prototype._innerSaveToNormal.call(this,t);var n=this._normalState;t.shape&&!n.shape&&(n.shape=R({},this.shape))},t.prototype._applyStateObj=function(t,n,r,i,a,o){if(e.prototype._applyStateObj.call(this,t,n,r,i,a,o),this.__inHover!==1){var s=!(n&&i),l;if(n&&n.shape?a?i?l=n.shape:(l=R({},r.shape),R(l,n.shape)):(l=R({},i?this.shape:r.shape),R(l,n.shape)):s&&(l=r.shape),l)if(a){this.shape=R({},this.shape);for(var u={},d=ue(l),f=0;f<d.length;f++){var p=d[f];typeof l[p]==`object`?this.shape[p]=l[p]:u[p]=l[p]}this._transitionState(t,{shape:u},o)}else this.shape=l,this.dirtyShape()}},t.prototype._mergeStates=function(t){for(var n=e.prototype._mergeStates.call(this,t),r,i=0;i<t.length;i++){var a=t[i];a.shape&&(r||={},this._mergeStyle(r,a.shape))}return r&&(n.shape=r),n},t.prototype.getAnimationStyleProps=function(){return no},t.prototype.isZeroArea=function(){return!1},t.extend=function(e){var n=function(t){p(n,t);function n(n){var r=t.call(this,n)||this;return e.init&&e.init.call(r,n),r}return n.prototype.getDefaultStyle=function(){return I(e.style)},n.prototype.getDefaultShape=function(){return I(e.shape)},n}(t);for(var r in e)typeof e[r]==`function`&&(n.prototype[r]=e[r]);return n},t.initDefaultProps=(function(){var e=t.prototype;e.type=`path`,e.strokeContainThreshold=5,e.segmentIgnoreThreshold=0,e.subPixelOptimize=!1,e.autoBatch=!1,e.__dirty=7})(),t}(ia),ao=te({strokeFirst:!0,font:m,x:0,y:0,textAlign:`left`,textBaseline:`top`,miterLimit:2},to),oo=function(e){p(t,e);function t(){return e!==null&&e.apply(this,arguments)||this}return t.prototype.hasStroke=function(){return Un(this.style)},t.prototype.hasFill=function(){var e=this.style.fill;return e!=null&&e!==`none`},t.prototype.createStyle=function(e){return Ve(ao,e)},t.prototype.setBoundingRect=function(e){this._rect=e},t.prototype.getBoundingRect=function(){return this._rect||=aee(this.style),this._rect},t.initDefaultProps=(function(){var e=t.prototype;e.dirtyRectTolerance=10})(),t}(ia);oo.prototype.type=`tspan`;var so=te({x:0,y:0},ea),co={style:te({x:!0,y:!0,width:!0,height:!0,sx:!0,sy:!0,sWidth:!0,sHeight:!0},ta.style)};function lo(e){return!!(e&&typeof e!=`string`&&e.width&&e.height)}var uo=function(e){p(t,e);function t(){return e!==null&&e.apply(this,arguments)||this}return t.prototype.createStyle=function(e){return Ve(so,e)},t.prototype._getSize=function(e){var t=this.style,n=t[e];if(n!=null)return n;var r=lo(t.image)?t.image:this.__image;if(!r)return 0;var i=e===`width`?`height`:`width`,a=t[i];return a==null?r[e]:r[e]/r[i]*a},t.prototype.getWidth=function(){return this._getSize(`width`)},t.prototype.getHeight=function(){return this._getSize(`height`)},t.prototype.getAnimationStyleProps=function(){return co},t.prototype.getBoundingRect=function(){var e=this.style;return this._rect||=new an(e.x||0,e.y||0,this.getWidth(),this.getHeight()),this._rect},t}(ia);uo.prototype.type=`image`;function fo(e,t){var n=t.x,r=t.y,i=t.width,a=t.height,o=t.r,s,l,u,d;i<0&&(n+=i,i=-i),a<0&&(r+=a,a=-a),typeof o==`number`?s=l=u=d=o:o instanceof Array?o.length===1?s=l=u=d=o[0]:o.length===2?(s=u=o[0],l=d=o[1]):o.length===3?(s=o[0],l=d=o[1],u=o[2]):(s=o[0],l=o[1],u=o[2],d=o[3]):s=l=u=d=0;var f;s+l>i&&(f=s+l,s*=i/f,l*=i/f),u+d>i&&(f=u+d,u*=i/f,d*=i/f),l+u>a&&(f=l+u,l*=a/f,u*=a/f),s+d>a&&(f=s+d,s*=a/f,d*=a/f),e.moveTo(n+s,r),e.lineTo(n+i-l,r),l!==0&&e.arc(n+i-l,r+l,l,-Math.PI/2,0),e.lineTo(n+i,r+a-u),u!==0&&e.arc(n+i-u,r+a-u,u,0,Math.PI/2),e.lineTo(n+d,r+a),d!==0&&e.arc(n+d,r+a-d,d,Math.PI/2,Math.PI),e.lineTo(n,r+s),s!==0&&e.arc(n+s,r+s,s,Math.PI,Math.PI*1.5),e.closePath()}var po=Math.round;function mo(e,t,n){if(t){var r=t.x1,i=t.x2,a=t.y1,o=t.y2;e.x1=r,e.x2=i,e.y1=a,e.y2=o;var s=n&&n.lineWidth;return s?(po(r*2)===po(i*2)&&(e.x1=e.x2=go(r,s,!0)),po(a*2)===po(o*2)&&(e.y1=e.y2=go(a,s,!0)),e):e}}function ho(e,t,n){if(t){var r=t.x,i=t.y,a=t.width,o=t.height;e.x=r,e.y=i,e.width=a,e.height=o;var s=n&&n.lineWidth;return s?(e.x=go(r,s,!0),e.y=go(i,s,!0),e.width=Math.max(go(r+a,s,!1)-e.x,a===0?0:1),e.height=Math.max(go(i+o,s,!1)-e.y,o===0?0:1),e):e}}function go(e,t,n){if(!t)return e;var r=po(e*2);return(r+po(t))%2==0?r/2:(r+(n?1:-1))/2}var _o=function(){function e(){this.x=0,this.y=0,this.width=0,this.height=0}return e}(),vo={},yo=function(e){p(t,e);function t(t){return e.call(this,t)||this}return t.prototype.getDefaultShape=function(){return new _o},t.prototype.buildPath=function(e,t){var n,r,i,a;if(this.subPixelOptimize){var o=ho(vo,t,this.style);n=o.x,r=o.y,i=o.width,a=o.height,o.r=t.r,t=o}else n=t.x,r=t.y,i=t.width,a=t.height;t.r?fo(e,t):e.rect(n,r,i,a)},t.prototype.isZeroArea=function(){return!this.shape.width||!this.shape.height},t}(io);yo.prototype.type=`rect`;var bo={fill:`#000`},xo=2,So={},Co={style:te({fill:!0,stroke:!0,fillOpacity:!0,strokeOpacity:!0,lineWidth:!0,fontSize:!0,lineHeight:!0,width:!0,height:!0,textShadowColor:!0,textShadowBlur:!0,textShadowOffsetX:!0,textShadowOffsetY:!0,backgroundColor:!0,padding:!0,borderColor:!0,borderWidth:!0,borderRadius:!0},ta.style)},wo=function(e){p(t,e);function t(t){var n=e.call(this)||this;return n.type=`text`,n._children=[],n._defaultStyle=bo,n.attr(t),n}return t.prototype.childrenRef=function(){return this._children},t.prototype.update=function(){e.prototype.update.call(this),this.styleChanged()&&this._updateSubTexts();for(var t=0;t<this._children.length;t++){var n=this._children[t];n.zlevel=this.zlevel,n.z=this.z,n.z2=this.z2,n.culling=this.culling,n.cursor=this.cursor,n.invisible=this.invisible}},t.prototype.updateTransform=function(){var t=this.innerTransformable;t?(t.updateTransform(),t.transform&&(this.transform=t.transform)):e.prototype.updateTransform.call(this)},t.prototype.getLocalTransform=function(t){var n=this.innerTransformable;return n?n.getLocalTransform(t):e.prototype.getLocalTransform.call(this,t)},t.prototype.getComputedTransform=function(){return this.__hostTarget&&(this.__hostTarget.getComputedTransform(),this.__hostTarget.updateInnerText(!0)),e.prototype.getComputedTransform.call(this)},t.prototype._updateSubTexts=function(){this._childCursor=0,Ao(this.style),this.style.rich?this._updateRichTexts():this._updatePlainTexts(),this._children.length=this._childCursor,this.styleUpdated()},t.prototype.addSelfToZr=function(t){e.prototype.addSelfToZr.call(this,t);for(var n=0;n<this._children.length;n++)this._children[n].__zr=t},t.prototype.removeSelfFromZr=function(t){e.prototype.removeSelfFromZr.call(this,t);for(var n=0;n<this._children.length;n++)this._children[n].__zr=null},t.prototype.getBoundingRect=function(){if(this.styleChanged()&&this._updateSubTexts(),!this._rect){for(var e=new an(0,0,0,0),t=this._children,n=[],r=null,i=0;i<t.length;i++){var a=t[i],o=a.getBoundingRect(),s=a.getLocalTransform(n);s?(e.copy(o),e.applyTransform(s),r||=e.clone(),r.union(e)):(r||=o.clone(),r.union(o))}this._rect=r||e}return this._rect},t.prototype.setDefaultTextStyle=function(e){this._defaultStyle=e||bo},t.prototype.setTextContent=function(e){},t.prototype._mergeStyle=function(e,t){if(!t)return e;var n=t.rich,r=e.rich||n&&{};return R(e,t),n&&r?(this._mergeRich(r,n),e.rich=r):r&&(e.rich=r),e},t.prototype._mergeRich=function(e,t){for(var n=ue(t),r=0;r<n.length;r++){var i=n[r];e[i]=e[i]||{},R(e[i],t[i])}},t.prototype.getAnimationStyleProps=function(){return Co},t.prototype._getOrCreateChild=function(e){var t=this._children[this._childCursor];return(!t||!(t instanceof e))&&(t=new e),this._children[this._childCursor++]=t,t.__zr=this.__zr,t.parent=this,t},t.prototype._updatePlainTexts=function(){var e=this.style,t=e.font||`12px sans-serif`,n=e.padding,r=this._defaultStyle,i=e.x||0,a=e.y||0,o=e.align||r.align||`left`,s=e.verticalAlign||r.verticalAlign||`top`;zn(So,r.overflowRect,i,a,o,s),i=So.baseX,a=So.baseY;var l=jn(Fo(e),e,So.outerWidth,So.outerHeight),u=Io(e),d=!!e.backgroundColor,f=l.outerHeight,p=l.outerWidth,m=l.lines,h=l.lineHeight;this.isTruncated=!!l.isTruncated;var g=i,_=Sn(a,l.contentHeight,s);if(u||n){var v=xn(i,p,o),y=Sn(a,f,s);u&&this._renderBackground(e,e,v,y,p,f)}_+=h/2,n&&(g=Po(i,o,n),s===`top`?_+=n[0]:s===`bottom`&&(_-=n[2]));for(var b=0,x=!1,S=!1,C=No(`fill`in e?e.fill:(S=!0,r.fill)),w=Mo(`stroke`in e?e.stroke:!d&&(!r.autoStroke||S)?(b=xo,x=!0,r.stroke):null),T=e.textShadowBlur>0,E=0;E<m.length;E++){var D=this._getOrCreateChild(oo),O=D.createStyle();D.useStyle(O),O.text=m[E],O.x=g,O.y=_,o&&(O.textAlign=o),O.textBaseline=`middle`,O.opacity=e.opacity,O.strokeFirst=!0,T&&(O.shadowBlur=e.textShadowBlur||0,O.shadowColor=e.textShadowColor||`transparent`,O.shadowOffsetX=e.textShadowOffsetX||0,O.shadowOffsetY=e.textShadowOffsetY||0),O.stroke=w,O.fill=C,w&&(O.lineWidth=e.lineWidth||b,O.lineDash=e.lineDash,O.lineDashOffset=e.lineDashOffset||0),O.font=t,ko(O,e),_+=h,D.setBoundingRect(Hn(O,l.contentWidth,l.calculatedLineHeight,x?0:null))}},t.prototype._updateRichTexts=function(){var e=this.style,t=this._defaultStyle,n=e.align||t.align,r=e.verticalAlign||t.verticalAlign,i=e.x||0,a=e.y||0;zn(So,t.overflowRect,i,a,n,r),i=So.baseX,a=So.baseY;var o=Pn(Fo(e),e,So.outerWidth,So.outerHeight,n),s=o.width,l=o.outerWidth,u=o.outerHeight,d=e.padding;this.isTruncated=!!o.isTruncated;var f=xn(i,l,n),p=Sn(a,u,r),m=f,h=p;d&&(m+=d[3],h+=d[0]);var g=m+s;Io(e)&&this._renderBackground(e,e,f,p,l,u);for(var _=!!e.backgroundColor,v=0;v<o.lines.length;v++){for(var y=o.lines[v],b=y.tokens,x=b.length,S=y.lineHeight,C=y.width,w=0,T=m,E=g,D=x-1,O=void 0;w<x&&(O=b[w],!O.align||O.align===`left`);)this._placeToken(O,e,S,h,T,`left`,_),C-=O.width,T+=O.width,w++;for(;D>=0&&(O=b[D],O.align===`right`);)this._placeToken(O,e,S,h,E,`right`,_),C-=O.width,E-=O.width,D--;for(T+=(s-(T-m)-(g-E)-C)/2;w<=D;)O=b[w],this._placeToken(O,e,S,h,T+O.width/2,`center`,_),T+=O.width,w++;h+=S}},t.prototype._placeToken=function(e,t,n,r,i,a,o){var s=t.rich[e.styleName]||{};s.text=e.text;var l=e.verticalAlign,u=r+n/2;l===`top`?u=r+e.height/2:l===`bottom`&&(u=r+n-e.height/2),!e.isLineHolder&&Io(s)&&this._renderBackground(s,t,a===`right`?i-e.width:a===`center`?i-e.width/2:i,u-e.height/2,e.width,e.height);var d=!!s.backgroundColor,f=e.textPadding;f&&(i=Po(i,a,f),u-=e.height/2-f[0]-e.innerHeight/2);var p=this._getOrCreateChild(oo),m=p.createStyle();p.useStyle(m);var h=this._defaultStyle,g=!1,_=0,v=!1,y=No(`fill`in s?s.fill:`fill`in t?t.fill:(g=!0,h.fill)),b=Mo(`stroke`in s?s.stroke:`stroke`in t?t.stroke:!d&&!o&&(!h.autoStroke||g)?(_=xo,v=!0,h.stroke):null),x=s.textShadowBlur>0||t.textShadowBlur>0;m.text=e.text,m.x=i,m.y=u,x&&(m.shadowBlur=s.textShadowBlur||t.textShadowBlur||0,m.shadowColor=s.textShadowColor||t.textShadowColor||`transparent`,m.shadowOffsetX=s.textShadowOffsetX||t.textShadowOffsetX||0,m.shadowOffsetY=s.textShadowOffsetY||t.textShadowOffsetY||0),m.textAlign=a,m.textBaseline=`middle`,m.font=e.font||`12px sans-serif`,m.opacity=De(s.opacity,t.opacity,1),ko(m,s),b&&(m.lineWidth=De(s.lineWidth,t.lineWidth,_),m.lineDash=Ee(s.lineDash,t.lineDash),m.lineDashOffset=t.lineDashOffset||0,m.stroke=b),y&&(m.fill=y),p.setBoundingRect(Hn(m,e.contentWidth,e.contentHeight,v?0:null))},t.prototype._renderBackground=function(e,t,n,r,i,a){var o=e.backgroundColor,s=e.borderWidth,l=e.borderColor,u=o&&o.image,d=o&&!u,f=e.borderRadius,p=this,m,h;if(d||e.lineHeight||s&&l){m=this._getOrCreateChild(yo),m.useStyle(m.createStyle()),m.style.fill=null;var g=m.shape;g.x=n,g.y=r,g.width=i,g.height=a,g.r=f,m.dirtyShape()}if(d){var _=m.style;_.fill=o||null,_.fillOpacity=Ee(e.fillOpacity,1)}else if(u){h=this._getOrCreateChild(uo),h.onload=function(){p.dirtyStyle()};var v=h.style;v.image=o.image,v.x=n,v.y=r,v.width=i,v.height=a}if(s&&l){var _=m.style;_.lineWidth=s,_.stroke=l,_.strokeOpacity=Ee(e.strokeOpacity,1),_.lineDash=e.borderDash,_.lineDashOffset=e.borderDashOffset||0,m.strokeContainThreshold=0,m.hasFill()&&m.hasStroke()&&(_.strokeFirst=!0,_.lineWidth*=2)}var y=(m||h).style;y.shadowBlur=e.shadowBlur||0,y.shadowColor=e.shadowColor||`transparent`,y.shadowOffsetX=e.shadowOffsetX||0,y.shadowOffsetY=e.shadowOffsetY||0,y.opacity=De(e.opacity,t.opacity,1)},t.makeFont=function(e){var t=``;return Dee(e)&&(t=[e.fontStyle,e.fontWeight,Oo(e.fontSize),e.fontFamily||`sans-serif`].join(` `)),t&&je(t)||e.textFont||e.font},t}(ia),To={left:!0,right:1,center:1},Eo={top:1,bottom:1,middle:1},Do=[`fontStyle`,`fontWeight`,`fontSize`,`fontFamily`];function Oo(e){return typeof e==`string`&&(e.indexOf(`px`)!==-1||e.indexOf(`rem`)!==-1||e.indexOf(`em`)!==-1)?e:isNaN(+e)?`12px`:e+`px`}function ko(e,t){for(var n=0;n<Do.length;n++){var r=Do[n],i=t[r];i!=null&&(e[r]=i)}}function Dee(e){return e.fontSize!=null||e.fontFamily||e.fontWeight}function Ao(e){return jo(e),z(e.rich,jo),e}function jo(e){if(e){e.font=wo.makeFont(e);var t=e.align;t===`middle`&&(t=`center`),e.align=t==null||To[t]?t:`left`;var n=e.verticalAlign;n===`center`&&(n=`middle`),e.verticalAlign=n==null||Eo[n]?n:`top`,e.padding&&=ke(e.padding)}}function Mo(e,t){return e==null||t<=0||e===`transparent`||e===`none`?null:e.image||e.colorStops?`#000`:e}function No(e){return e==null||e===`none`?null:e.image||e.colorStops?`#000`:e}function Po(e,t,n){return t===`right`?e-n[1]:t===`center`?e+n[3]/2-n[1]/2:e+n[3]}function Fo(e){var t=e.text;return t!=null&&(t+=``),t}function Io(e){return!!(e.backgroundColor||e.lineHeight||e.borderWidth&&e.borderColor)}var Lo=1e-4,Ro=20;function zo(e){return e.replace(/^\s+|\s+$/g,``)}var Bo=Math.min,Vo=Math.max,Ho=Math.abs,Uo=Math.round,Wo=Math.floor,Go=Math.ceil,Ko=Math.pow,qo=Math.log,Jo=Math.LN10,Yo=Math.PI,Oee=Math.random;function Xo(e,t,n,r){var i=t[0],a=t[1],o=n[0],s=n[1],l=a-i,u=s-o;if(l===0)return u===0?o:(o+s)/2;if(r){if(l>0){if(e<=i)return o;if(e>=a)return s}else if(e>=i)return o;else if(e<=a)return s}else{if(e===i)return o;if(e===a)return s}return(e-i)/l*u+o}var Zo=kee;function kee(e,t,n){switch(e){case`center`:case`middle`:e=`50%`;break;case`left`:case`top`:e=`0%`;break;case`right`:case`bottom`:e=`100%`;break}return Qo(e,t,n)}function Qo(e,t,n){return ge(e)?$o(e)?parseFloat(e)/100*t+(n||0):parseFloat(e):e==null?NaN:+e}function $o(e){return!!zo(e).match(/%$/)}function es(e,t,n){return isNaN(t)?n?``+e:+e:(t=Bo(Vo(0,t),Ro),e=(+e).toFixed(t),n?e:+e)}function ts(e){return e.sort(function(e,t){return e-t}),e}function ns(e){if(e=+e,isNaN(e))return 0;if(e>1e-14){for(var t=1,n=0;n<15;n++,t*=10)if(Uo(e*t)/t===e)return n}return Aee(e)}function Aee(e){var t=e.toString().toLowerCase(),n=t.indexOf(`e`),r=n>0?+t.slice(n+1):0,i=n>0?n:t.length,a=t.indexOf(`.`);return Vo(0,(a<0?0:i-1-a)-r)}function jee(e,t,n){var r=Ho(e[1]-e[0]);if(!isFinite(r)||r===0)return NaN;var i=qo(2*Ho(n||1)*Ho(r))/Jo,a=qo(Ho(t))/Jo,o=Vo(0,Go(-i+a));return isFinite(o)||(o=NaN),o}function Mee(e,t){var n=se(e,function(e,t){return e+(isNaN(t)?0:t)},0);if(n===0)return[];for(var r=Ko(10,t),i=oe(e,function(e){return(isNaN(e)?0:e)/n*r*100}),a=r*100,o=oe(i,function(e){return Wo(e)}),s=se(o,function(e,t){return e+t},0),l=oe(i,function(e,t){return e-o[t]});s<a;){for(var u=-1/0,d=null,f=0,p=l.length;f<p;++f)l[f]>u&&(u=l[f],d=f);++o[d],l[d]=0,++s}return oe(o,function(e){return e/r})}function Nee(e,t){var n=Vo(ns(e),ns(t)),r=e+t;return n>Ro?r:es(r,n)}var rs=Ko(2,53)-1;function is(e){var t=Yo*2;return(e%t+t)%t}function as(e){return e>-Lo&&e<Lo}var os=/^(?:(\d{4})(?:[-\/](\d{1,2})(?:[-\/](\d{1,2})(?:[T ](\d{1,2})(?::(\d{1,2})(?::(\d{1,2})(?:[.,](\d+))?)?)?(Z|[\+\-]\d\d:?\d\d)?)?)?)?)?$/;function ss(e){if(e instanceof Date)return e;if(ge(e)){var t=os.exec(e);if(!t)return new Date(NaN);if(t[8]){var n=+t[4]||0;return t[8].toUpperCase()!==`Z`&&(n-=+t[8].slice(0,3)),new Date(Date.UTC(+t[1],(t[2]||1)-1,+t[3]||1,n,+(t[5]||0),+t[6]||0,t[7]?+t[7].substring(0,3):0))}else return new Date(+t[1],(t[2]||1)-1,+t[3]||1,+t[4]||0,+(t[5]||0),+t[6]||0,t[7]?+t[7].substring(0,3):0)}else if(e==null)return new Date(NaN);return new Date(Uo(e))}function cs(e){return Ko(10,ls(e))}function ls(e){if(e===0)return 0;var t=Wo(qo(e)/Jo);return e/Ko(10,t)>=10&&t++,t}function us(e,t){var n=ls(e),r=Ko(10,n),i=e/r;return e=(t===2?1:t?i<1.5?1:i<2.5?2:i<4?3:i<7?5:10:i<1?1:i<2?2:i<3?3:i<5?5:10)*r,es(e,-n)}function ds(e){var t=parseFloat(e);return t==e&&(t!==0||!ge(e)||e.indexOf(`x`)<=0)?t:NaN}function fs(e){return!isNaN(ds(e))}function ps(){return Uo(Oee()*9)}function ms(e,t){return t===0?e:ms(t,e%t)}function hs(e,t){return e==null?t:t==null?e:e*t/ms(e,t)}function gs(e){return e!=null&&isFinite(e)}var Pee=`[ECharts] `,_s={},Fee=typeof console<`u`&&console.warn&&console.log;function Iee(e,t,n){if(Fee){if(n){if(_s[t])return;_s[t]=!0}console[e](Pee+t)}}function vs(e,t){Iee(`error`,e,t)}function ys(e){throw Error(e)}function bs(e,t,n){return(t-e)*n+e}var xs=`series\0`,Ss=`\0_ec_\0`;function Cs(e){return e instanceof Array?e:e==null?[]:[e]}function ws(e,t,n){if(e){e[t]=e[t]||{},e.emphasis=e.emphasis||{},e.emphasis[t]=e.emphasis[t]||{};for(var r=0,i=n.length;r<i;r++){var a=n[r];!e.emphasis[t].hasOwnProperty(a)&&e[t].hasOwnProperty(a)&&(e.emphasis[t][a]=e[t][a])}}}var Ts=`fontStyle.fontWeight.fontSize.fontFamily.rich.tag.color.textBorderColor.textBorderWidth.width.height.lineHeight.align.verticalAlign.baseline.shadowColor.shadowBlur.shadowOffsetX.shadowOffsetY.textShadowColor.textShadowBlur.textShadowOffsetX.textShadowOffsetY.backgroundColor.borderColor.borderWidth.borderRadius.padding`.split(`.`);function Es(e){return ye(e)&&!me(e)&&!(e instanceof Date)?e.value:e}function Ds(e){return ye(e)&&!(e instanceof Array)}function Os(e,t,n){var r=n===`normalMerge`,i=n===`replaceMerge`,a=n===`replaceAll`;e||=[],t=(t||[]).slice();var o=ze();z(t,function(e,n){if(!ye(e)){t[n]=null;return}});var s=ks(e,o,n);return(r||i)&&As(s,e,o,t),r&&js(s,t),r||i?Ms(s,t,i):a&&Ns(s,t),Ps(s),s}function ks(e,t,n){var r=[];if(n===`replaceAll`)return r;for(var i=0;i<e.length;i++){var a=e[i];a&&a.id!=null&&t.set(a.id,i),r.push({existing:n===`replaceMerge`||zs(a)?null:a,newOption:null,keyInfo:null,brandNew:null})}return r}function As(e,t,n,r){z(r,function(i,a){if(!(!i||i.id==null)){var o=Is(i.id),s=n.get(o);if(s!=null){var l=e[s];Ae(!l.newOption,`Duplicated option on id "`+o+`".`),l.newOption=i,l.existing=t[s],r[a]=null}}})}function js(e,t){z(t,function(n,r){if(!(!n||n.name==null))for(var i=0;i<e.length;i++){var a=e[i].existing;if(!e[i].newOption&&a&&(a.id==null||n.id==null)&&!zs(n)&&!zs(a)&&Fs(`name`,a,n)){e[i].newOption=n,t[r]=null;return}}})}function Ms(e,t,n){z(t,function(t){if(t){for(var r,i=0;(r=e[i])&&(r.newOption||zs(r.existing)||r.existing&&t.id!=null&&!Fs(`id`,t,r.existing));)i++;r?(r.newOption=t,r.brandNew=n):e.push({newOption:t,brandNew:n,existing:null,keyInfo:null}),i++}})}function Ns(e,t){z(t,function(t){e.push({newOption:t,brandNew:!0,existing:null,keyInfo:null})})}function Ps(e){var t=ze();z(e,function(e){var n=e.existing;n&&t.set(n.id,e)}),z(e,function(e){var n=e.newOption;Ae(!n||n.id==null||!t.get(n.id)||t.get(n.id)===e,`id duplicates: `+(n&&n.id)),n&&n.id!=null&&t.set(n.id,e),!e.keyInfo&&(e.keyInfo={})}),z(e,function(e,n){var r=e.existing,i=e.newOption,a=e.keyInfo;if(ye(i)){if(a.name=i.name==null?r?r.name:xs+n:Is(i.name),r)a.id=Is(r.id);else if(i.id!=null)a.id=Is(i.id);else{var o=0;do a.id=`\0`+a.name+`\0`+o++;while(t.get(a.id))}t.set(a.id,e)}})}function Fs(e,t,n){var r=Ls(t[e],null),i=Ls(n[e],null);return r!=null&&i!=null&&r===i}function Is(e){return Ls(e,``)}function Ls(e,t){return e==null?t:ge(e)?e:ve(e)||_e(e)?e+``:t}function Rs(e){var t=e.name;return!!(t&&t.indexOf(xs))}function zs(e){return e&&e.id!=null&&Is(e.id).indexOf(Ss)===0}function Bs(e,t,n){z(e,function(e){var r=e.newOption;ye(r)&&(e.keyInfo.mainType=t,e.keyInfo.subType=Vs(t,r,e.existing,n))})}function Vs(e,t,n,r){return t.type?t.type:n?n.subType:r.determineSubType(e,t)}function Hs(e,t){if(t.dataIndexInside!=null)return t.dataIndexInside;if(t.dataIndex!=null)return me(t.dataIndex)?oe(t.dataIndex,function(t){return e.indexOfRawIndex(t)}):e.indexOfRawIndex(t.dataIndex);if(t.name!=null)return me(t.name)?oe(t.name,function(t){return e.indexOfName(t)}):e.indexOfName(t.name)}function Us(){var e=`__ec_inner_`+Lee++;return function(t){return t[e]||(t[e]={})}}var Lee=ps();function Ws(e,t,n){var r=Gs(t,n),i=r.mainTypeSpecified,a=r.queryOptionMap,o=r.others,s=n?n.defaultMainType:null;return!i&&s&&a.set(s,{}),a.each(function(t,r){var i=qs(e,r,t,{useDefault:s===r,enableAll:n&&n.enableAll!=null?n.enableAll:!0,enableNone:n&&n.enableNone!=null?n.enableNone:!0});o[r+`Models`]=i.models,o[r+`Model`]=i.models[0]}),o}function Gs(e,t){var n;if(ge(e)){var r={};r[e+`Index`]=0,n=r}else n=e;var i=ze(),a={},o=!1;return z(n,function(e,n){if(n===`dataIndex`||n===`dataIndexInside`){a[n]=e;return}var r=n.match(/^(\w+)(Index|Id|Name)$/)||[],s=r[1],l=(r[2]||``).toLowerCase();if(!(!s||!l||t&&t.includeMainTypes&&ne(t.includeMainTypes,s)<0)){o||=!!s;var u=i.get(s)||i.set(s,{});u[l]=e}}),{mainTypeSpecified:o,queryOptionMap:i,others:a}}var Ks={useDefault:!0,enableAll:!1,enableNone:!1};function qs(e,t,n,r){r||=Ks;var i=n.index,a=n.id,o=n.name,s={models:null,specified:i!=null||a!=null||o!=null};if(!s.specified){var l=void 0;return s.models=r.useDefault&&(l=e.getComponent(t))?[l]:[],s}if(i===`none`||i===!1){if(r.enableNone)return s.models=[],s;i=-1}return i===`all`&&(i=r.enableAll?a=o=null:-1),s.models=e.queryComponents({mainType:t,index:i,id:a,name:o}),s}function Ree(e,t,n){var r={};r[t+`Id`]=e[t+`Id`],r[t+`Index`]=e[t+`Index`],r[t+`Name`]=e[t+`Name`];var i={mainType:t,query:r};return n&&(i.subType=n),i}function zee(e,t,n){e.setAttribute?e.setAttribute(t,n):e[t]=n}function Js(e,t){return e.getAttribute?e.getAttribute(t):e[t]}function Ys(e,t,n,r,i){var a=t==null||t===`auto`;if(r==null)return r;if(ve(r)){var o=bs(n||0,r,i);return es(o,a?Math.max(ns(n||0),ns(r)):t)}else if(ge(r))return i<1?n:r;else{for(var s=[],l=n,u=r,d=Math.max(l?l.length:0,u.length),f=0;f<d;++f){var p=e.getDimensionInfo(f);if(p&&p.type===`ordinal`)s[f]=(i<1&&l?l:u)[f];else{var m=l&&l[f]?l[f]:0,h=u[f],o=bs(m,h,i);s[f]=es(o,a?Math.max(ns(m),ns(h)):t)}}return s}}(function(){function e(){}return e.prototype.reset=function(e,t,n,r){return this._list=e,this._step=r||=1,this._idx=t,this._end=n??(r>0?e.length:0),this.item=null,this.key=NaN,this},e.prototype.next=function(){return(this._step>0?this._idx<this._end:this._idx>=this._end)?(this.item=this._list[this._idx],this.key=this._idx+=this._step,!0):!1},e})();function Xs(){return[1/0,-1/0]}function Zs(e,t){tc(t)&&(t<e[0]&&(e[0]=t),t>e[1]&&(e[1]=t))}function Qs(e,t){tc(t)&&t<e[0]&&(e[0]=t)}function $s(e,t){tc(t)&&t>e[1]&&(e[1]=t)}function ec(e,t){nc(t[0],t[1])&&(t[0]<e[0]&&(e[0]=t[0]),t[1]>e[1]&&(e[1]=t[1]))}function tc(e){return e!=null&&isFinite(e)}function nc(e,t){return tc(e)&&tc(t)&&e<=t}function rc(e){var t=e[1]-e[0];return isFinite(t)&&t>=0}function ic(e){nc(e[0],e[1])&&e[0]>e[1]&&(e[0]=e[1])}function ac(){var e=`__ec_once_`+oc++;return function(t,n){He(t,e)||(t[e]=1,n())}}var oc=ps();function sc(e,t,n){var r=ze(),i=0;z(e,function(a){var o=t(a),s=r.get(o)||0;n&&n(a,s),!s&&!n&&(e[i++]=a),r.set(o,s+1)}),n||(e.length=i)}function Bee(e){return e.value+``}function Vee(e){return e+``}function Hee(e,t){return Ee(t,!0)?e.seriesIndex+2:0}function cc(e,t,n){var r=e.getData().count();return{progressiveRender:n.progressiveEnabled&&t.incrementalPrepareRender&&r>=n.threshold,large:e.get(`large`)&&r>=e.get(`largeThreshold`),modDataCount:e.get(`progressiveChunkMode`)===`mod`?e.getData().count():null}}function lc(e,t){return{seriesType:e,overallReset:t}}function uc(e){return{overallReset:e}}var dc=Us(),fc=function(e,t,n,r){if(r){var i=dc(r);i.dataIndex=n,i.dataType=t,i.seriesIndex=e,i.ssrType=`chart`,r.type===`group`&&r.traverse(function(r){var i=dc(r);i.seriesIndex=e,i.dataIndex=n,i.dataType=t,i.ssrType=`chart`})}},pc=ze([`tooltip`,`label`,`itemName`,`itemId`,`itemGroupId`,`itemChildGroupId`,`seriesName`]),mc=`original`,hc=`arrayRows`,gc=`objectRows`,_c=`keyedColumns`,vc=`typedArray`,yc=`unknown`,bc=`column`,Uee=[`getDom`,`getZr`,`getWidth`,`getHeight`,`getDevicePixelRatio`,`dispatchAction`,`isSSR`,`isDisposed`,`on`,`off`,`getDataURL`,`getConnectedDataURL`,`getOption`,`getId`,`updateLabelLayout`],xc=function(){function e(e){z(Uee,function(t){this[t]=fe(e[t],e)},this)}return e}();function Sc(e,t){return t.mainType===`series`?e.getViewOfSeriesModel(t):e.getViewOfComponentModel(t)}var Cc=1,wc={},Tc=Us(),Ec=Us(),Dc=[`emphasis`,`blur`,`select`],Oc=[`normal`,`emphasis`,`blur`,`select`],kc=`highlight`,Ac=`downplay`,jc=`select`,Mc=`unselect`,Nc=`toggleSelect`,Pc=`selectchanged`;function Fc(e){return e!=null&&e!==`none`}function Ic(e,t,n){e.onHoverStateChange&&(e.hoverState||0)!==n&&e.onHoverStateChange(t),e.hoverState=n}function Lc(e){Ic(e,`emphasis`,2)}function Rc(e){e.hoverState===2&&Ic(e,`normal`,0)}function zc(e){Ic(e,`blur`,1)}function Bc(e){e.hoverState===1&&Ic(e,`normal`,0)}function Wee(e){e.selected=!0}function Vc(e){e.selected=!1}function Hc(e,t,n){t(e,n)}function Uc(e,t,n){Hc(e,t,n),e.isGroup&&e.traverse(function(e){Hc(e,t,n)})}function Wc(e,t){switch(t){case`emphasis`:e.hoverState=2;break;case`normal`:e.hoverState=0;break;case`blur`:e.hoverState=1;break;case`select`:e.selected=!0}}function Gc(e,t,n,r){for(var i=e.style,a={},o=0;o<t.length;o++){var s=t[o];a[s]=i[s]??(r&&r[s])}for(var o=0;o<e.animators.length;o++){var l=e.animators[o];l.__fromStateTransition&&l.__fromStateTransition.indexOf(n)<0&&l.targetName===`style`&&l.saveTo(a,t)}return a}function Gee(e,t,n,r){var i=n&&ne(n,`select`)>=0,a=!1;if(e instanceof io){var o=Tc(e),s=i&&o.selectFill||o.normalFill,l=i&&o.selectStroke||o.normalStroke;if(Fc(s)||Fc(l)){r||={};var u=r.style||{};u.fill===`inherit`?(a=!0,r=R({},r),u=R({},u),u.fill=s):!Fc(u.fill)&&Fc(s)?(a=!0,r=R({},r),u=R({},u),u.fill=Ur(s)):!Fc(u.stroke)&&Fc(l)&&(a||(r=R({},r),u=R({},u)),u.stroke=Ur(l)),r.style=u}}if(r&&r.z2==null){a||(r=R({},r));var d=e.z2EmphasisLift;r.z2=e.z2+(d??10)}return r}function Kc(e,t,n){if(n&&n.z2==null){n=R({},n);var r=e.z2SelectLift;n.z2=e.z2+(r??9)}return n}function qc(e,t,n){var r=ne(e.currentStates,t)>=0,i=e.style.opacity,a=r?null:Gc(e,[`opacity`],t,{opacity:1});n||={};var o=n.style||{};return o.opacity??(n=R({},n),o=R({opacity:r?i:a.opacity*.1},o),n.style=o),n}function Jc(e,t){var n=this.states[e];if(this.style){if(e===`emphasis`)return Gee(this,e,t,n);if(e===`blur`)return qc(this,e,n);if(e===`select`)return Kc(this,e,n)}return n}function Kee(e){e.stateProxy=Jc;var t=e.getTextContent(),n=e.getTextGuideLine();t&&(t.stateProxy=Jc),n&&(n.stateProxy=Jc)}function Yc(e,t){!nl(e,t)&&!e.__highByOuter&&Uc(e,Lc)}function Xc(e,t){!nl(e,t)&&!e.__highByOuter&&Uc(e,Rc)}function Zc(e,t){e.__highByOuter|=1<<(t||0),Uc(e,Lc)}function Qc(e,t){!(e.__highByOuter&=~(1<<(t||0)))&&Uc(e,Rc)}function qee(e){Uc(e,zc)}function $c(e){Uc(e,Bc)}function el(e){Uc(e,Wee)}function tl(e){Uc(e,Vc)}function nl(e,t){return e.__highDownSilentOnTouch&&t.zrByTouch}function rl(e){var t=e.getModel(),n=[],r=[];t.eachComponent(function(t,i){var a=Ec(i),o=Sc(e,i),s=t===`series`;!s&&r.push(o),a.isBlured&&(o.group.traverse(function(e){Bc(e)}),s&&n.push(i)),a.isBlured=!1}),z(r,function(e){e&&e.toggleBlurSeries&&e.toggleBlurSeries(n,!1,t)})}function il(e,t,n,r){var i=r.getModel();n||=`coordinateSystem`;function a(e,t){for(var n=0;n<t.length;n++){var r=e.getItemGraphicEl(t[n]);r&&$c(r)}}if(e!=null&&!(!t||t===`none`)){var o=i.getSeriesByIndex(e),s=o.coordinateSystem;s&&s.master&&(s=s.master);var l=[];i.eachSeries(function(e){var i=o===e,u=e.coordinateSystem;if(u&&u.master&&(u=u.master),!(n===`series`&&!i||n===`coordinateSystem`&&!(u&&s?u===s:i)||t===`series`&&i)){if(r.getViewOfSeriesModel(e).group.traverse(function(e){e.__highByOuter&&i&&t===`self`||zc(e)}),ae(t))a(e.getData(),t);else if(ye(t))for(var d=ue(t),f=0;f<d.length;f++)a(e.getData(d[f]),t[d[f]]);l.push(e),Ec(e).isBlured=!0}}),i.eachComponent(function(e,t){if(e!==`series`){var n=r.getViewOfComponentModel(t);n&&n.toggleBlurSeries&&n.toggleBlurSeries(l,!0,i)}})}}function al(e,t,n){if(!(e==null||t==null)){var r=n.getModel().getComponent(e,t);if(r){Ec(r).isBlured=!0;var i=n.getViewOfComponentModel(r);!i||!i.focusBlurEnabled||i.group.traverse(function(e){zc(e)})}}}function ol(e,t,n){var r=e.seriesIndex,i=e.getData(t.dataType);if(i){var a=Hs(i,t);a=(me(a)?a[0]:a)||0;var o=i.getItemGraphicEl(a);if(!o)for(var s=i.count(),l=0;!o&&l<s;)o=i.getItemGraphicEl(l++);if(o){var u=dc(o);il(r,u.focus,u.blurScope,n)}else{var d=e.get([`emphasis`,`focus`]),f=e.get([`emphasis`,`blurScope`]);d!=null&&il(r,d,f,n)}}}function sl(e,t,n,r){var i={focusSelf:!1,dispatchers:null};if(e==null||e===`series`||t==null||n==null)return i;var a=r.getModel().getComponent(e,t);if(!a)return i;var o=r.getViewOfComponentModel(a);if(!o||!o.findHighDownDispatchers)return i;for(var s=o.findHighDownDispatchers(n),l,u=0;u<s.length;u++)if(dc(s[u]).focus===`self`){l=!0;break}return{focusSelf:l,dispatchers:s}}function cl(e,t,n){var r=dc(e),i=sl(r.componentMainType,r.componentIndex,r.componentHighDownName,n),a=i.dispatchers,o=i.focusSelf;a?(o&&al(r.componentMainType,r.componentIndex,n),z(a,function(e){return Yc(e,t)})):(il(r.seriesIndex,r.focus,r.blurScope,n),r.focus===`self`&&al(r.componentMainType,r.componentIndex,n),Yc(e,t))}function ll(e,t,n){rl(n);var r=dc(e),i=sl(r.componentMainType,r.componentIndex,r.componentHighDownName,n).dispatchers;i?z(i,function(e){return Xc(e,t)}):Xc(e,t)}function Jee(e,t,n){if(xl(t)){var r=t.dataType,i=Hs(e.getData(r),t);me(i)||(i=[i]),e[t.type===`toggleSelect`?`toggleSelect`:t.type===`select`?`select`:`unselect`](i,r)}}function ul(e){z(e.getAllData(),function(t){var n=t.data,r=t.type;n.eachItemGraphicEl(function(t,n){e.isSelected(n,r)?el(t):tl(t)})})}function Yee(e){var t=[];return e.eachSeries(function(e){z(e.getAllData(),function(n){n.data;var r=n.type,i=e.getSelectedDataIndices();if(i.length>0){var a={dataIndex:i,seriesIndex:e.seriesIndex};r!=null&&(a.dataType=r),t.push(a)}})}),t}function dl(e,t,n){vl(e,!0),Uc(e,Kee),ml(e,t,n)}function fl(e){vl(e,!1)}function pl(e,t,n,r){r?fl(e):dl(e,t,n)}function ml(e,t,n){var r=dc(e);t==null?r.focus&&=null:(r.focus=t,r.blurScope=n)}var hl=[`emphasis`,`blur`,`select`],gl={itemStyle:`getItemStyle`,lineStyle:`getLineStyle`,areaStyle:`getAreaStyle`};function _l(e,t,n,r){n||=`itemStyle`;for(var i=0;i<hl.length;i++){var a=hl[i],o=t.getModel([a,n]),s=e.ensureState(a);s.style=r?r(o):o[gl[n]]()}}function vl(e,t){var n=t===!1,r=e;e.highDownSilentOnTouch&&(r.__highDownSilentOnTouch=e.highDownSilentOnTouch),(!n||r.__highDownDispatcher)&&(r.__highByOuter=r.__highByOuter||0,r.__highDownDispatcher=!n)}function yl(e){return!!(e&&e.__highDownDispatcher)}function bl(e){var t=wc[e];return t==null&&Cc<=32&&(t=wc[e]=Cc++),t}function xl(e){var t=e.type;return t===`select`||t===`unselect`||t===`toggleSelect`}function Sl(e){var t=e.type;return t===`highlight`||t===`downplay`}function Xee(e){var t=Tc(e);t.normalFill=e.style.fill,t.normalStroke=e.style.stroke;var n=e.states.select||{};t.selectFill=n.style&&n.style.fill||null,t.selectStroke=n.style&&n.style.stroke||null}var Cl=La.CMD,Zee=[[],[],[]],wl=Math.sqrt,Tl=Math.atan2;function El(e,t){if(t){var n=e.data,r=e.len(),i,a,o,s,l,u,d=Cl.M,f=Cl.C,p=Cl.L,m=Cl.R,h=Cl.A,g=Cl.Q;for(o=0,s=0;o<r;){switch(i=n[o++],s=o,a=0,i){case d:a=1;break;case p:a=1;break;case f:a=3;break;case g:a=2;break;case h:var _=t[4],v=t[5],y=wl(t[0]*t[0]+t[1]*t[1]),b=wl(t[2]*t[2]+t[3]*t[3]),x=Tl(-t[1]/b,t[0]/y);n[o]*=y,n[o++]+=_,n[o]*=b,n[o++]+=v,n[o++]*=y,n[o++]*=b,n[o++]+=x,n[o++]+=x,o+=2,s=o;break;case m:u[0]=n[o++],u[1]=n[o++],Vt(u,u,t),n[s++]=u[0],n[s++]=u[1],u[0]+=n[o++],u[1]+=n[o++],Vt(u,u,t),n[s++]=u[0],n[s++]=u[1]}for(l=0;l<a;l++){var S=Zee[l];S[0]=n[o++],S[1]=n[o++],Vt(S,S,t),n[s++]=S[0],n[s++]=S[1]}}e.increaseVersion()}}var Dl=Math.sqrt,Ol=Math.sin,kl=Math.cos,Al=Math.PI;function jl(e){return Math.sqrt(e[0]*e[0]+e[1]*e[1])}function Ml(e,t){return(e[0]*t[0]+e[1]*t[1])/(jl(e)*jl(t))}function Nl(e,t){return(e[0]*t[1]<e[1]*t[0]?-1:1)*Math.acos(Ml(e,t))}function Pl(e,t,n,r,i,a,o,s,l,u,d){var f=Al/180*l,p=kl(f)*(e-n)/2+Ol(f)*(t-r)/2,m=-1*Ol(f)*(e-n)/2+kl(f)*(t-r)/2,h=p*p/(o*o)+m*m/(s*s);h>1&&(o*=Dl(h),s*=Dl(h));var g=(i===a?-1:1)*Dl((o*o*(s*s)-o*o*(m*m)-s*s*(p*p))/(o*o*(m*m)+s*s*(p*p)))||0,_=g*o*m/s,v=g*-s*p/o,y=(e+n)/2+kl(f)*_-Ol(f)*v,b=(t+r)/2+Ol(f)*_+kl(f)*v,x=Nl([1,0],[(p-_)/o,(m-v)/s]),S=[(p-_)/o,(m-v)/s],C=[(-1*p-_)/o,(-1*m-v)/s],w=Nl(S,C);if(Ml(S,C)<=-1&&(w=Al),Ml(S,C)>=1&&(w=0),w<0){var T=Math.round(w/Al*1e6)/1e6;w=Al*2+T%2*Al}d.addData(u,y,b,o,s,x,w,f,a)}var Fl=/([mlvhzcqtsa])([^mlvhzcqtsa]*)/gi,Il=/-?([0-9]*\.)?[0-9]+([eE]-?[0-9]+)?/g;function Ll(e){var t=new La;if(!e)return t;var n=0,r=0,i=n,a=r,o,s=La.CMD,l=e.match(Fl);if(!l)return t;for(var u=0;u<l.length;u++){for(var d=l[u],f=d.charAt(0),p=void 0,m=d.match(Il)||[],h=m.length,g=0;g<h;g++)m[g]=parseFloat(m[g]);for(var _=0;_<h;){var v=void 0,y=void 0,b=void 0,x=void 0,S=void 0,C=void 0,w=void 0,T=n,E=r,D=void 0,O=void 0;switch(f){case`l`:n+=m[_++],r+=m[_++],p=s.L,t.addData(p,n,r);break;case`L`:n=m[_++],r=m[_++],p=s.L,t.addData(p,n,r);break;case`m`:n+=m[_++],r+=m[_++],p=s.M,t.addData(p,n,r),i=n,a=r,f=`l`;break;case`M`:n=m[_++],r=m[_++],p=s.M,t.addData(p,n,r),i=n,a=r,f=`L`;break;case`h`:n+=m[_++],p=s.L,t.addData(p,n,r);break;case`H`:n=m[_++],p=s.L,t.addData(p,n,r);break;case`v`:r+=m[_++],p=s.L,t.addData(p,n,r);break;case`V`:r=m[_++],p=s.L,t.addData(p,n,r);break;case`C`:p=s.C,t.addData(p,m[_++],m[_++],m[_++],m[_++],m[_++],m[_++]),n=m[_-2],r=m[_-1];break;case`c`:p=s.C,t.addData(p,m[_++]+n,m[_++]+r,m[_++]+n,m[_++]+r,m[_++]+n,m[_++]+r),n+=m[_-2],r+=m[_-1];break;case`S`:v=n,y=r,D=t.len(),O=t.data,o===s.C&&(v+=n-O[D-4],y+=r-O[D-3]),p=s.C,T=m[_++],E=m[_++],n=m[_++],r=m[_++],t.addData(p,v,y,T,E,n,r);break;case`s`:v=n,y=r,D=t.len(),O=t.data,o===s.C&&(v+=n-O[D-4],y+=r-O[D-3]),p=s.C,T=n+m[_++],E=r+m[_++],n+=m[_++],r+=m[_++],t.addData(p,v,y,T,E,n,r);break;case`Q`:T=m[_++],E=m[_++],n=m[_++],r=m[_++],p=s.Q,t.addData(p,T,E,n,r);break;case`q`:T=m[_++]+n,E=m[_++]+r,n+=m[_++],r+=m[_++],p=s.Q,t.addData(p,T,E,n,r);break;case`T`:v=n,y=r,D=t.len(),O=t.data,o===s.Q&&(v+=n-O[D-4],y+=r-O[D-3]),n=m[_++],r=m[_++],p=s.Q,t.addData(p,v,y,n,r);break;case`t`:v=n,y=r,D=t.len(),O=t.data,o===s.Q&&(v+=n-O[D-4],y+=r-O[D-3]),n+=m[_++],r+=m[_++],p=s.Q,t.addData(p,v,y,n,r);break;case`A`:b=m[_++],x=m[_++],S=m[_++],C=m[_++],w=m[_++],T=n,E=r,n=m[_++],r=m[_++],p=s.A,Pl(T,E,n,r,C,w,b,x,S,p,t);break;case`a`:b=m[_++],x=m[_++],S=m[_++],C=m[_++],w=m[_++],T=n,E=r,n+=m[_++],r+=m[_++],p=s.A,Pl(T,E,n,r,C,w,b,x,S,p,t);break}}(f===`z`||f===`Z`)&&(p=s.Z,t.addData(p),n=i,r=a),o=p}return t.toStatic(),t}var Rl=function(e){p(t,e);function t(){return e!==null&&e.apply(this,arguments)||this}return t.prototype.applyTransform=function(e){},t}(io);function zl(e){return e.setData!=null}function Bl(e,t){var n=Ll(e),r=R({},t);return r.buildPath=function(e){var t=zl(e);if(t&&e.canSave()){e.appendPath(n);var r=e.getContext();r&&e.rebuildPath(r,1)}else{var r=t?e.getContext():e;r&&n.rebuildPath(r,1)}},r.applyTransform=function(e){El(n,e),this.dirtyShape()},r}function Vl(e,t){return new Rl(Bl(e,t))}function Hl(e,t){var n=Bl(e,t);return function(e){p(t,e);function t(t){var r=e.call(this,t)||this;return r.applyTransform=n.applyTransform,r.buildPath=n.buildPath,r}return t}(Rl)}function Ul(e,t){for(var n=[],r=e.length,i=0;i<r;i++){var a=e[i];n.push(a.getUpdatedPathProxy(!0))}var o=new io(t);return o.createPathProxy(),o.buildPath=function(e){if(zl(e)){e.appendPath(n);var t=e.getContext();t&&e.rebuildPath(t,1)}},o}var Wl=function(e){p(t,e);function t(t){var n=e.call(this)||this;return n.isGroup=!0,n._children=[],n.attr(t),n}return t.prototype.childrenRef=function(){return this._children},t.prototype.children=function(){return this._children.slice()},t.prototype.childAt=function(e){return this._children[e]},t.prototype.childOfName=function(e){for(var t=this._children,n=0;n<t.length;n++)if(t[n].name===e)return t[n]},t.prototype.childCount=function(){return this._children.length},t.prototype.add=function(e){return e&&e!==this&&e.parent!==this&&(this._children.push(e),this._doAdd(e)),this},t.prototype.addBefore=function(e,t){if(e&&e!==this&&e.parent!==this&&t&&t.parent===this){var n=this._children,r=n.indexOf(t);r>=0&&(n.splice(r,0,e),this._doAdd(e))}return this},t.prototype.replace=function(e,t){var n=ne(this._children,e);return n>=0&&this.replaceAt(t,n),this},t.prototype.replaceAt=function(e,t){var n=this._children,r=n[t];if(e&&e!==this&&e.parent!==this&&e!==r){n[t]=e,r.parent=null;var i=this.__zr;i&&r.removeSelfFromZr(i),this._doAdd(e)}return this},t.prototype._doAdd=function(e){e.parent&&e.parent.remove(e),e.parent=this;var t=this.__zr;t&&t!==e.__zr&&e.addSelfToZr(t),t&&t.refresh()},t.prototype.remove=function(e){var t=this.__zr,n=this._children,r=ne(n,e);return r<0?this:(n.splice(r,1),e.parent=null,t&&e.removeSelfFromZr(t),t&&t.refresh(),this)},t.prototype.removeAll=function(){for(var e=this._children,t=this.__zr,n=0;n<e.length;n++){var r=e[n];t&&r.removeSelfFromZr(t),r.parent=null}return e.length=0,this},t.prototype.eachChild=function(e,t){for(var n=this._children,r=0;r<n.length;r++){var i=n[r];e.call(t,i,r)}return this},t.prototype.traverse=function(e,t){for(var n=0;n<this._children.length;n++){var r=this._children[n],i=e.call(t,r);r.isGroup&&!i&&r.traverse(e,t)}return this},t.prototype.addSelfToZr=function(t){e.prototype.addSelfToZr.call(this,t);for(var n=0;n<this._children.length;n++)this._children[n].addSelfToZr(t)},t.prototype.removeSelfFromZr=function(t){e.prototype.removeSelfFromZr.call(this,t);for(var n=0;n<this._children.length;n++)this._children[n].removeSelfFromZr(t)},t.prototype.getBoundingRect=function(e){for(var t=new an(0,0,0,0),n=e||this._children,r=[],i=null,a=0;a<n.length;a++){var o=n[a];if(!(o.ignore||o.invisible)){var s=o.getBoundingRect(),l=o.getLocalTransform(r);l?(an.applyTransform(t,s,l),i||=t.clone(),i.union(t)):(i||=s.clone(),i.union(s))}}return i||t},t}(Hi);Wl.prototype.type=`group`;var Gl=function(){function e(){this.cx=0,this.cy=0,this.r=0}return e}(),Kl=function(e){p(t,e);function t(t){return e.call(this,t)||this}return t.prototype.getDefaultShape=function(){return new Gl},t.prototype.buildPath=function(e,t){e.moveTo(t.cx+t.r,t.cy),e.arc(t.cx,t.cy,t.r,0,Math.PI*2)},t}(io);Kl.prototype.type=`circle`;var ql=function(){function e(){this.cx=0,this.cy=0,this.rx=0,this.ry=0}return e}(),Jl=function(e){p(t,e);function t(t){return e.call(this,t)||this}return t.prototype.getDefaultShape=function(){return new ql},t.prototype.buildPath=function(e,t){var n=.5522848,r=t.cx,i=t.cy,a=t.rx,o=t.ry,s=a*n,l=o*n;e.moveTo(r-a,i),e.bezierCurveTo(r-a,i-l,r-s,i-o,r,i-o),e.bezierCurveTo(r+s,i-o,r+a,i-l,r+a,i),e.bezierCurveTo(r+a,i+l,r+s,i+o,r,i+o),e.bezierCurveTo(r-s,i+o,r-a,i+l,r-a,i),e.closePath()},t}(io);Jl.prototype.type=`ellipse`;var Yl=Math.PI,Xl=Yl*2,Zl=Math.sin,Ql=Math.cos,$l=Math.acos,eu=Math.atan2,tu=Math.abs,nu=Math.sqrt,ru=Math.max,iu=Math.min,au=1e-4;function ou(e,t,n,r,i,a,o,s){var l=n-e,u=r-t,d=o-i,f=s-a,p=f*l-d*u;if(!(p*p<au))return p=(d*(t-a)-f*(e-i))/p,[e+p*l,t+p*u]}function su(e,t,n,r,i,a,o){var s=e-n,l=t-r,u=(o?a:-a)/nu(s*s+l*l),d=u*l,f=-u*s,p=e+d,m=t+f,h=n+d,g=r+f,_=(p+h)/2,v=(m+g)/2,y=h-p,b=g-m,x=y*y+b*b,S=i-a,C=p*g-h*m,w=(b<0?-1:1)*nu(ru(0,S*S*x-C*C)),T=(C*b-y*w)/x,E=(-C*y-b*w)/x,D=(C*b+y*w)/x,O=(-C*y+b*w)/x,k=T-_,A=E-v,j=D-_,M=O-v;return k*k+A*A>j*j+M*M&&(T=D,E=O),{cx:T,cy:E,x0:-d,y0:-f,x1:T*(i/S-1),y1:E*(i/S-1)}}function cu(e){var t;if(me(e)){var n=e.length;if(!n)return e;t=n===1?[e[0],e[0],0,0]:n===2?[e[0],e[0],e[1],e[1]]:n===3?e.concat(e[2]):e}else t=[e,e,e,e];return t}function lu(e,t){var n,r=ru(t.r,0),i=ru(t.r0||0,0),a=r>0;if(!(!a&&!(i>0))){if(a||(r=i,i=0),i>r){var o=r;r=i,i=o}var s=t.startAngle,l=t.endAngle;if(!(isNaN(s)||isNaN(l))){var u=t.cx,d=t.cy,f=!!t.clockwise,p=tu(l-s),m=p>Xl&&p%Xl;if(m>au&&(p=m),!(r>au))e.moveTo(u,d);else if(p>Xl-au)e.moveTo(u+r*Ql(s),d+r*Zl(s)),e.arc(u,d,r,s,l,!f),i>au&&(e.moveTo(u+i*Ql(l),d+i*Zl(l)),e.arc(u,d,i,l,s,f));else{var h=void 0,g=void 0,_=void 0,v=void 0,y=void 0,b=void 0,x=void 0,S=void 0,C=void 0,w=void 0,T=void 0,E=void 0,D=void 0,O=void 0,k=void 0,A=void 0,j=r*Ql(s),M=r*Zl(s),N=i*Ql(l),P=i*Zl(l),F=p>au;if(F){var I=t.cornerRadius;I&&(n=cu(I),h=n[0],g=n[1],_=n[2],v=n[3]);var L=tu(r-i)/2;if(y=iu(L,_),b=iu(L,v),x=iu(L,h),S=iu(L,g),T=C=ru(y,b),E=w=ru(x,S),(C>au||w>au)&&(D=r*Ql(l),O=r*Zl(l),k=i*Ql(s),A=i*Zl(s),p<Yl)){var R=ou(j,M,k,A,D,O,N,P);if(R){var ee=j-R[0],te=M-R[1],ne=D-R[0],re=O-R[1],ie=1/Zl($l((ee*ne+te*re)/(nu(ee*ee+te*te)*nu(ne*ne+re*re)))/2),ae=nu(R[0]*R[0]+R[1]*R[1]);T=iu(C,(r-ae)/(ie+1)),E=iu(w,(i-ae)/(ie-1))}}}if(!F)e.moveTo(u+j,d+M);else if(T>au){var z=iu(_,T),oe=iu(v,T),se=su(k,A,j,M,r,z,f),ce=su(D,O,N,P,r,oe,f);e.moveTo(u+se.cx+se.x0,d+se.cy+se.y0),T<C&&z===oe?e.arc(u+se.cx,d+se.cy,T,eu(se.y0,se.x0),eu(ce.y0,ce.x0),!f):(z>0&&e.arc(u+se.cx,d+se.cy,z,eu(se.y0,se.x0),eu(se.y1,se.x1),!f),e.arc(u,d,r,eu(se.cy+se.y1,se.cx+se.x1),eu(ce.cy+ce.y1,ce.cx+ce.x1),!f),oe>0&&e.arc(u+ce.cx,d+ce.cy,oe,eu(ce.y1,ce.x1),eu(ce.y0,ce.x0),!f))}else e.moveTo(u+j,d+M),e.arc(u,d,r,s,l,!f);if(!(i>au)||!F)e.lineTo(u+N,d+P);else if(E>au){var z=iu(h,E),oe=iu(g,E),se=su(N,P,D,O,i,-oe,f),ce=su(j,M,k,A,i,-z,f);e.lineTo(u+se.cx+se.x0,d+se.cy+se.y0),E<w&&z===oe?e.arc(u+se.cx,d+se.cy,E,eu(se.y0,se.x0),eu(ce.y0,ce.x0),!f):(oe>0&&e.arc(u+se.cx,d+se.cy,oe,eu(se.y0,se.x0),eu(se.y1,se.x1),!f),e.arc(u,d,i,eu(se.cy+se.y1,se.cx+se.x1),eu(ce.cy+ce.y1,ce.cx+ce.x1),f),z>0&&e.arc(u+ce.cx,d+ce.cy,z,eu(ce.y1,ce.x1),eu(ce.y0,ce.x0),!f))}else e.lineTo(u+N,d+P),e.arc(u,d,i,l,s,f)}e.closePath()}}}var uu=function(){function e(){this.cx=0,this.cy=0,this.r0=0,this.r=0,this.startAngle=0,this.endAngle=Math.PI*2,this.clockwise=!0,this.cornerRadius=0}return e}(),du=function(e){p(t,e);function t(t){return e.call(this,t)||this}return t.prototype.getDefaultShape=function(){return new uu},t.prototype.buildPath=function(e,t){lu(e,t)},t.prototype.isZeroArea=function(){return this.shape.startAngle===this.shape.endAngle||this.shape.r===this.shape.r0},t}(io);du.prototype.type=`sector`;var fu=function(){function e(){this.cx=0,this.cy=0,this.r=0,this.r0=0}return e}(),pu=function(e){p(t,e);function t(t){return e.call(this,t)||this}return t.prototype.getDefaultShape=function(){return new fu},t.prototype.buildPath=function(e,t){var n=t.cx,r=t.cy,i=Math.PI*2;e.moveTo(n+t.r,r),e.arc(n,r,t.r,0,i,!1),e.moveTo(n+t.r0,r),e.arc(n,r,t.r0,0,i,!0)},t}(io);pu.prototype.type=`ring`;function mu(e,t,n,r){var i=[],a=[],o=[],s=[],l,u,d,f;if(r){d=[1/0,1/0],f=[-1/0,-1/0];for(var p=0,m=e.length;p<m;p++)Ht(d,d,e[p]),Ut(f,f,e[p]);Ht(d,d,r[0]),Ut(f,f,r[1])}for(var p=0,m=e.length;p<m;p++){var h=e[p];if(n)l=e[p?p-1:m-1],u=e[(p+1)%m];else if(p===0||p===m-1){i.push(Ot(e[p]));continue}else l=e[p-1],u=e[p+1];jt(a,u,l),Pt(a,a,t);var g=It(h,l),_=It(h,u),v=g+_;v!==0&&(g/=v,_/=v),Pt(o,a,-g),Pt(s,a,_);var y=At([],h,o),b=At([],h,s);r&&(Ut(y,y,d),Ht(y,y,f),Ut(b,b,d),Ht(b,b,f)),i.push(y),i.push(b)}return n&&i.push(i.shift()),i}function hu(e,t,n){var r=t.smooth,i=t.points;if(i&&i.length>=2){if(r){var a=mu(i,r,n,t.smoothConstraint);e.moveTo(i[0][0],i[0][1]);for(var o=i.length,s=0;s<(n?o:o-1);s++){var l=a[s*2],u=a[s*2+1],d=i[(s+1)%o];e.bezierCurveTo(l[0],l[1],u[0],u[1],d[0],d[1])}}else{e.moveTo(i[0][0],i[0][1]);for(var s=1,f=i.length;s<f;s++)e.lineTo(i[s][0],i[s][1])}n&&e.closePath()}}var gu=function(){function e(){this.points=null,this.smooth=0,this.smoothConstraint=null}return e}(),_u=function(e){p(t,e);function t(t){return e.call(this,t)||this}return t.prototype.getDefaultShape=function(){return new gu},t.prototype.buildPath=function(e,t){hu(e,t,!0)},t}(io);_u.prototype.type=`polygon`;var vu=function(){function e(){this.points=null,this.percent=1,this.smooth=0,this.smoothConstraint=null}return e}(),yu=function(e){p(t,e);function t(t){return e.call(this,t)||this}return t.prototype.getDefaultStyle=function(){return{stroke:`#000`,fill:null}},t.prototype.getDefaultShape=function(){return new vu},t.prototype.buildPath=function(e,t){hu(e,t,!1)},t}(io);yu.prototype.type=`polyline`;var bu={},xu=function(){function e(){this.x1=0,this.y1=0,this.x2=0,this.y2=0,this.percent=1}return e}(),Su=function(e){p(t,e);function t(t){return e.call(this,t)||this}return t.prototype.getDefaultStyle=function(){return{stroke:`#000`,fill:null}},t.prototype.getDefaultShape=function(){return new xu},t.prototype.buildPath=function(e,t){var n,r,i,a;if(this.subPixelOptimize){var o=mo(bu,t,this.style);n=o.x1,r=o.y1,i=o.x2,a=o.y2}else n=t.x1,r=t.y1,i=t.x2,a=t.y2;var s=t.percent;s!==0&&(e.moveTo(n,r),s<1&&(i=n*(1-s)+i*s,a=r*(1-s)+a*s),e.lineTo(i,a))},t.prototype.pointAt=function(e){var t=this.shape;return[t.x1*(1-e)+t.x2*e,t.y1*(1-e)+t.y2*e]},t}(io);Su.prototype.type=`line`;var Cu=[],wu=function(){function e(){this.x1=0,this.y1=0,this.x2=0,this.y2=0,this.cpx1=0,this.cpy1=0,this.percent=1}return e}();function Tu(e,t,n){var r=e.cpx2,i=e.cpy2;return r!=null||i!=null?[(n?dr:ur)(e.x1,e.cpx1,e.cpx2,e.x2,t),(n?dr:ur)(e.y1,e.cpy1,e.cpy2,e.y2,t)]:[(n?_r:gr)(e.x1,e.cpx1,e.x2,t),(n?_r:gr)(e.y1,e.cpy1,e.y2,t)]}var Eu=function(e){p(t,e);function t(t){return e.call(this,t)||this}return t.prototype.getDefaultStyle=function(){return{stroke:`#000`,fill:null}},t.prototype.getDefaultShape=function(){return new wu},t.prototype.buildPath=function(e,t){var n=t.x1,r=t.y1,i=t.x2,a=t.y2,o=t.cpx1,s=t.cpy1,l=t.cpx2,u=t.cpy2,d=t.percent;d!==0&&(e.moveTo(n,r),l==null||u==null?(d<1&&(yr(n,o,i,d,Cu),o=Cu[1],i=Cu[2],yr(r,s,a,d,Cu),s=Cu[1],a=Cu[2]),e.quadraticCurveTo(o,s,i,a)):(d<1&&(mr(n,o,l,i,d,Cu),o=Cu[1],l=Cu[2],i=Cu[3],mr(r,s,u,a,d,Cu),s=Cu[1],u=Cu[2],a=Cu[3]),e.bezierCurveTo(o,s,l,u,i,a)))},t.prototype.pointAt=function(e){return Tu(this.shape,e,!1)},t.prototype.tangentAt=function(e){var t=Tu(this.shape,e,!0);return Ft(t,t)},t}(io);Eu.prototype.type=`bezier-curve`;var Du=function(){function e(){this.cx=0,this.cy=0,this.r=0,this.startAngle=0,this.endAngle=Math.PI*2,this.clockwise=!0}return e}(),Ou=function(e){p(t,e);function t(t){return e.call(this,t)||this}return t.prototype.getDefaultStyle=function(){return{stroke:`#000`,fill:null}},t.prototype.getDefaultShape=function(){return new Du},t.prototype.buildPath=function(e,t){var n=t.cx,r=t.cy,i=Math.max(t.r,0),a=t.startAngle,o=t.endAngle,s=t.clockwise,l=Math.cos(a),u=Math.sin(a);e.moveTo(l*i+n,u*i+r),e.arc(n,r,i,a,o,!s)},t}(io);Ou.prototype.type=`arc`;var ku=function(e){p(t,e);function t(){var t=e!==null&&e.apply(this,arguments)||this;return t.type=`compound`,t}return t.prototype._updatePathDirty=function(){for(var e=this.shape.paths,t=this.shapeChanged(),n=0;n<e.length;n++)t||=e[n].shapeChanged();t&&this.dirtyShape()},t.prototype.beforeBrush=function(){this._updatePathDirty();for(var e=this.shape.paths||[],t=this.getGlobalScale(),n=0;n<e.length;n++)e[n].path||e[n].createPathProxy(),e[n].path.setScale(t[0],t[1],e[n].segmentIgnoreThreshold)},t.prototype.buildPath=function(e,t){for(var n=t.paths||[],r=0;r<n.length;r++)n[r].buildPath(e,n[r].shape,!0)},t.prototype.afterBrush=function(){for(var e=this.shape.paths||[],t=0;t<e.length;t++)e[t].pathUpdated()},t.prototype.getBoundingRect=function(){return this._updatePathDirty.call(this),io.prototype.getBoundingRect.call(this)},t}(io),Au=function(){function e(e){this.colorStops=e||[]}return e.prototype.addColorStop=function(e,t){this.colorStops.push({offset:e,color:t})},e}(),ju=function(e){p(t,e);function t(t,n,r,i,a,o){var s=e.call(this,a)||this;return s.x=t??0,s.y=n??0,s.x2=r??1,s.y2=i??0,s.type=`linear`,s.global=o||!1,s}return t}(Au),Mu=function(e){p(t,e);function t(t,n,r,i,a){var o=e.call(this,i)||this;return o.x=t??.5,o.y=n??.5,o.r=r??.5,o.type=`radial`,o.global=a||!1,o}return t}(Au),Nu=Math.min,Pu=Math.max,Fu=Math.abs,Iu=[0,0],Lu=[0,0],Ru=dn(),zu=Ru.minTv,Bu=Ru.maxTv,Vu=function(){function e(e,t){this._corners=[],this._axes=[],this._origin=[0,0];for(var n=0;n<4;n++)this._corners[n]=new Wt;for(var n=0;n<2;n++)this._axes[n]=new Wt;e&&this.fromBoundingRect(e,t)}return e.prototype.fromBoundingRect=function(e,t){var n=this._corners,r=this._axes,i=e.x,a=e.y,o=i+e.width,s=a+e.height;if(n[0].set(i,a),n[1].set(o,a),n[2].set(o,s),n[3].set(i,s),t)for(var l=0;l<4;l++)n[l].transform(t);Wt.sub(r[0],n[1],n[0]),Wt.sub(r[1],n[3],n[0]),r[0].normalize(),r[1].normalize();for(var l=0;l<2;l++)this._origin[l]=r[l].dot(n[0])},e.prototype.intersect=function(e,t,n){var r=!0,i=!t;return t&&Wt.set(t,0,0),Ru.reset(n,!i),!this._intersectCheckOneSide(this,e,i,1)&&(r=!1,i)||!this._intersectCheckOneSide(e,this,i,-1)&&(r=!1,i)||!i&&!Ru.negativeSize&&Wt.copy(t,r?Ru.useDir?Ru.dirMinTv:zu:Bu),r},e.prototype._intersectCheckOneSide=function(e,t,n,r){for(var i=!0,a=0;a<2;a++){var o=e._axes[a];if(e._getProjMinMaxOnAxis(a,e._corners,Iu),e._getProjMinMaxOnAxis(a,t._corners,Lu),Ru.negativeSize||Iu[1]<Lu[0]||Iu[0]>Lu[1]){if(i=!1,Ru.negativeSize||n)return i;var s=Fu(Lu[0]-Iu[1]),l=Fu(Iu[0]-Lu[1]);Nu(s,l)>Bu.len()&&(s<l?Wt.scale(Bu,o,-s*r):Wt.scale(Bu,o,l*r))}else if(!n){var s=Fu(Lu[0]-Iu[1]),l=Fu(Iu[0]-Lu[1]);(Ru.useDir||Nu(s,l)<zu.len())&&((s<l||!Ru.bidirectional)&&(Wt.scale(zu,o,s*r),Ru.useDir&&Ru.calcDirMTV()),(s>=l||!Ru.bidirectional)&&(Wt.scale(zu,o,-l*r),Ru.useDir&&Ru.calcDirMTV()))}}return i},e.prototype._getProjMinMaxOnAxis=function(e,t,n){for(var r=this._axes[e],i=this._origin,a=t[0].dot(r)+i[e],o=a,s=a,l=1;l<t.length;l++){var u=t[l].dot(r)+i[e];o=Nu(u,o),s=Pu(u,s)}n[0]=o+Ru.touchThreshold,n[1]=s-Ru.touchThreshold,Ru.negativeSize=n[1]<n[0]},e}(),Hu=[],Qee=function(e){p(t,e);function t(){var t=e!==null&&e.apply(this,arguments)||this;return t.notClear=!0,t.incremental=1,t._displayables=[],t._temporaryDisplayables=[],t._cursor=0,t}return t.prototype.traverse=function(e,t){e.call(t,this)},t.prototype.useStyle=function(){this.style={}},t.prototype._useHoverStyle=function(){this.__hoverStyle=null},t.prototype.getCursor=function(){return this._cursor},t.prototype.innerAfterBrush=function(){this._cursor=this._displayables.length},t.prototype.clearDisplaybles=function(){this._displayables=[],this._temporaryDisplayables=[],this._cursor=0,this.markRedraw(),this.notClear=!1},t.prototype.clearTemporalDisplayables=function(){this._temporaryDisplayables=[]},t.prototype.addDisplayable=function(e,t){t?this._temporaryDisplayables.push(e):this._displayables.push(e),this.markRedraw()},t.prototype.addDisplayables=function(e,t){t||=!1;for(var n=0;n<e.length;n++)this.addDisplayable(e[n],t)},t.prototype.getDisplayables=function(){return this._displayables},t.prototype.getTemporalDisplayables=function(){return this._temporaryDisplayables},t.prototype.eachPendingDisplayable=function(e){for(var t=this._cursor;t<this._displayables.length;t++)e&&e(this._displayables[t]);for(var t=0;t<this._temporaryDisplayables.length;t++)e&&e(this._temporaryDisplayables[t])},t.prototype.update=function(){this.updateTransform();for(var e=this._cursor;e<this._displayables.length;e++){var t=this._displayables[e];t.parent=this,t.update(),t.parent=null}for(var e=0;e<this._temporaryDisplayables.length;e++){var t=this._temporaryDisplayables[e];t.parent=this,t.update(),t.parent=null}},t.prototype.getBoundingRect=function(){if(!this._rect){for(var e=new an(1/0,1/0,-1/0,-1/0),t=0;t<this._displayables.length;t++){var n=this._displayables[t],r=n.getBoundingRect().clone();n.needLocalTransform()&&r.applyTransform(n.getLocalTransform(Hu)),e.union(r)}this._rect=e}return this._rect},t.prototype.contain=function(e,t){var n=this.transformCoordToLocal(e,t);if(this.getBoundingRect().contain(n[0],n[1])){for(var r=0;r<this._displayables.length;r++)if(this._displayables[r].contain(e,t))return!0}return!1},t}(ia),Uu=Us();function Wu(e,t,n,r,i){var a;if(t&&t.ecModel){var o=t.ecModel.getUpdatePayload();a=o&&o.animation}var s=t&&t.isAnimationEnabled(),l=e===`update`;if(s){var u=void 0,d=void 0,f=void 0;return r?(u=Ee(r.duration,200),d=Ee(r.easing,`cubicOut`),f=0):(u=t.getShallow(l?`animationDurationUpdate`:`animationDuration`),d=t.getShallow(l?`animationEasingUpdate`:`animationEasing`),f=t.getShallow(l?`animationDelayUpdate`:`animationDelay`)),a&&(a.duration!=null&&(u=a.duration),a.easing!=null&&(d=a.easing),a.delay!=null&&(f=a.delay)),he(f)&&(f=f(n,i)),he(u)&&(u=u(n)),{duration:u||0,delay:f,easing:d}}else return null}function Gu(e,t,n,r,i,a,o){var s=!1,l;he(i)?(o=a,a=i,i=null):ye(i)&&(a=i.cb,o=i.during,s=i.isFrom,l=i.removeOpt,i=i.dataIndex);var u=e===`leave`;u||t.stopAnimation(`leave`);var d=Wu(e,r,i,u?l||{}:null,r&&r.getAnimationDelayParams?r.getAnimationDelayParams(t,i):null);if(d&&d.duration>0){var f=d.duration,p=d.delay,m=d.easing,h={duration:f,delay:p||0,easing:m,done:a,force:!!a||!!o,setToFinal:!u,scope:e,during:o};s?t.animateFrom(n,h):t.animateTo(n,h)}else t.stopAnimation(),!s&&t.attr(n),o&&o(1),a&&a()}function Ku(e,t,n,r,i,a){Gu(`update`,e,t,n,r,i,a)}function qu(e,t,n,r,i,a){Gu(`enter`,e,t,n,r,i,a)}function Ju(e){if(!e.__zr)return!0;for(var t=0;t<e.animators.length;t++)if(e.animators[t].scope===`leave`)return!0;return!1}function Yu(e,t,n,r,i,a){Ju(e)||Gu(`leave`,e,t,n,r,i,a)}function Xu(e,t,n,r){e.removeTextContent(),e.removeTextGuideLine(),Yu(e,{style:{opacity:0}},t,n,r)}function Zu(e,t,n){function r(){e.parent&&e.parent.remove(e)}e.isGroup?e.traverse(function(e){e.isGroup||Xu(e,t,n,r)}):Xu(e,t,n,r)}function Qu(e){Uu(e).oldStyle=e.style}var $ee=l({Arc:()=>Ou,BezierCurve:()=>Eu,BoundingRect:()=>an,Circle:()=>Kl,CompoundPath:()=>ku,Ellipse:()=>Jl,Group:()=>Wl,HOVER_LAYER_FOR_INCREMENTAL:()=>2,HOVER_LAYER_FROM_THRESHOLD:()=>1,HOVER_LAYER_NO:()=>0,Image:()=>uo,IncrementalDisplayable:()=>Qee,Line:()=>Su,LinearGradient:()=>ju,OrientedBoundingRect:()=>Vu,Path:()=>io,Point:()=>Wt,Polygon:()=>_u,Polyline:()=>yu,RadialGradient:()=>Mu,Rect:()=>yo,Ring:()=>pu,Sector:()=>du,Text:()=>wo,WH:()=>td,XY:()=>ed,applyTransform:()=>fd,calcZ2Range:()=>ote,clipPointsByRect:()=>_d,clipRectByRect:()=>vd,createIcon:()=>yd,decomposeTransform:()=>Fd,ensureCopyRect:()=>Ad,ensureCopyTransform:()=>jd,expandOrShrinkRect:()=>Sd,extendPath:()=>tte,extendShape:()=>nd,getCurrentCanvasPainter:()=>cte,getShapeClass:()=>id,getTransform:()=>dd,groupTransition:()=>gd,initProps:()=>qu,isBoundingRectAxisAligned:()=>Od,isElementRemoved:()=>Ju,lineLineIntersect:()=>bd,linePolygonIntersect:()=>ite,makeImage:()=>od,makePath:()=>ad,mergePath:()=>cd,payloadDisableAnimation:()=>ste,registerShape:()=>rd,removeElement:()=>Yu,removeElementWithFadeOut:()=>Zu,resizePath:()=>ld,retrieveZInfo:()=>Md,setTooltipConfig:()=>Td,subPixelOptimize:()=>rte,subPixelOptimizeLine:()=>ud,subPixelOptimizeRect:()=>nte,transformDirection:()=>pd,traverseElements:()=>Dd,traverseUpdateZ:()=>Nd,updateProps:()=>Ku}),$u={},ed=[`x`,`y`],td=[`width`,`height`];function nd(e){return io.extend(e)}var ete=Hl;function tte(e,t){return ete(e,t)}function rd(e,t){$u[e]=t}function id(e){if($u.hasOwnProperty(e))return $u[e]}function ad(e,t,n,r){var i=Vl(e,t);return n&&(r===`center`&&(n=sd(n,i.getBoundingRect())),ld(i,n)),i}function od(e,t,n){var r=new uo({style:{image:e,x:t.x,y:t.y,width:t.width,height:t.height},onload:function(e){if(n===`center`){var i={width:e.width,height:e.height};r.setStyle(sd(t,i))}}});return r}function sd(e,t){var n=t.width/t.height,r=e.height*n,i;r<=e.width?i=e.height:(r=e.width,i=r/n);var a=e.x+e.width/2,o=e.y+e.height/2;return{x:a-r/2,y:o-i/2,width:r,height:i}}var cd=Ul;function ld(e,t){if(e.applyTransform){var n=e.getBoundingRect().calculateTransform(t);e.applyTransform(n)}}function ud(e,t){return mo(e,e,{lineWidth:t}),e}function nte(e,t){return ho(e,e,t),e}var rte=go;function dd(e,t){for(var n=bt([]);e&&e!==t;)St(n,e.getLocalTransform(),n),e=e.parent;return n}function fd(e,t,n){return t&&!ae(t)&&(t=Xn.getLocalTransform(t)),n&&(t=Et([],t)),Vt([],e,t)}function pd(e,t,n){var r=t[4]===0||t[5]===0||t[0]===0?1:Ho(2*t[4]/t[0]),i=t[4]===0||t[5]===0||t[2]===0?1:Ho(2*t[4]/t[2]),a=[e===`left`?-r:e===`right`?r:0,e===`top`?-i:e===`bottom`?i:0];return a=fd(a,t,n),Ho(a[0])>Ho(a[1])?a[0]>0?`right`:`left`:a[1]>0?`bottom`:`top`}function md(e){return!e.isGroup}function hd(e){return e.shape!=null}function gd(e,t,n){if(!e||!t)return;function r(e){var t={};return e.traverse(function(e){md(e)&&e.anid&&(t[e.anid]=e)}),t}function i(e){var t={x:e.x,y:e.y,rotation:e.rotation};return hd(e)&&(t.shape=I(e.shape)),t}var a=r(e);t.traverse(function(e){if(md(e)&&e.anid){var t=a[e.anid];if(t){var r=i(e);e.attr(i(t)),Ku(e,r,n,dc(e).dataIndex)}}})}function _d(e,t){return oe(e,function(e){var n=e[0];n=Vo(n,t.x),n=Bo(n,t.x+t.width);var r=e[1];return r=Vo(r,t.y),r=Bo(r,t.y+t.height),[n,r]})}function vd(e,t){var n=Vo(e.x,t.x),r=Bo(e.x+e.width,t.x+t.width),i=Vo(e.y,t.y),a=Bo(e.y+e.height,t.y+t.height);if(r>=n&&a>=i)return{x:n,y:i,width:r-n,height:a-i}}function yd(e,t,n){var r=R({rectHover:!0},t),i=r.style={strokeNoScale:!0};if(n||={x:-1,y:-1,width:2,height:2},e)return e.indexOf(`image://`)===0?(i.image=e.slice(8),te(i,n),new uo(r)):ad(e.replace(`path://`,``),r,n,`center`)}function ite(e,t,n,r,i){for(var a=0,o=i[i.length-1];a<i.length;a++){var s=i[a];if(bd(e,t,n,r,s[0],s[1],o[0],o[1]))return!0;o=s}}function bd(e,t,n,r,i,a,o,s){var l=n-e,u=r-t,d=o-i,f=s-a,p=xd(d,f,l,u);if(ate(p))return!1;var m=e-i,h=t-a,g=xd(m,h,l,u)/p;if(g<0||g>1)return!1;var _=xd(m,h,d,f)/p;return!(_<0||_>1)}function xd(e,t,n,r){return e*r-n*t}function ate(e){return e<=1e-6&&e>=-1e-6}function Sd(e,t,n,r,i){return t==null?e:(ve(t)?Cd[0]=Cd[1]=Cd[2]=Cd[3]=t:(Cd[0]=t[0],Cd[1]=t[1],Cd[2]=t[2],Cd[3]=t[3]),r&&(Cd[0]=Vo(0,Cd[0]),Cd[1]=Vo(0,Cd[1]),Cd[2]=Vo(0,Cd[2]),Cd[3]=Vo(0,Cd[3])),n&&(Cd[0]=-Cd[0],Cd[1]=-Cd[1],Cd[2]=-Cd[2],Cd[3]=-Cd[3]),wd(e,Cd,`x`,`width`,3,1,i&&i[0]||0),wd(e,Cd,`y`,`height`,0,2,i&&i[1]||0),e)}var Cd=[0,0,0,0];function wd(e,t,n,r,i,a,o){var s=t[a]+t[i],l=e[r];e[r]+=s,o=Vo(0,Bo(o,l)),e[r]<o?(e[r]=o,e[n]+=t[i]>=0?-t[i]:t[a]>=0?l+t[a]:Ho(s)>1e-8?(l-o)*t[i]/s:0):e[n]-=t[i]}function Td(e){var t=e.itemTooltipOption,n=e.componentModel,r=e.itemName,i=ge(t)?{formatter:t}:t,a=n.mainType,o=n.componentIndex,s={componentType:a,name:r,$vars:[`name`]};s[a+`Index`]=o;var l=e.formatterParamsExtra;l&&z(ue(l),function(e){He(s,e)||(s[e]=l[e],s.$vars.push(e))});var u=dc(e.el);u.componentMainType=a,u.componentIndex=o,u.tooltipConfig={name:r,option:te({content:r,encodeHTMLContent:!0,formatterParams:s},i)}}function Ed(e,t){var n;e.isGroup&&(n=t(e)),n||e.traverse(t)}function Dd(e,t){if(e)if(me(e))for(var n=0;n<e.length;n++)Ed(e[n],t);else Ed(e,t)}function Od(e){return!e||Ho(e[1])<kd&&Ho(e[2])<kd||Ho(e[0])<kd&&Ho(e[3])<kd}var kd=1e-5;function Ad(e,t){return e?an.copy(e,t):t.clone()}function jd(e,t){return t?xt(e||yt(),t):void 0}function Md(e){return{z:e.get(`z`)||0,zlevel:e.get(`zlevel`)||0}}function ote(e){var t=-1/0,n=1/0;Ed(e,function(e){r(e),r(e.getTextContent()),r(e.getTextGuideLine())});function r(e){if(!(!e||e.isGroup)){var t=e.currentStates;if(t.length)for(var n=0;n<t.length;n++)i(e.states[t[n]]);i(e)}}function i(e){if(e){var r=e.z2;r>t&&(t=r),r<n&&(n=r)}}return n>t&&(n=t=0),{min:n,max:t}}function Nd(e,t,n){Pd(e,t,n,-1/0)}function Pd(e,t,n,r){if(e.ignoreModelZ)return r;var i=e.getTextContent(),a=e.getTextGuideLine();if(e.isGroup)for(var o=e.childrenRef(),s=0;s<o.length;s++)r=Vo(Pd(o[s],t,n,r),r);else e.z=t,e.zlevel=n,r=Vo(e.z2||0,r);if(i&&(i.z=t,i.zlevel=n,isFinite(r)&&(i.z2=r+2)),a){var l=e.textGuideLineConfig;a.z=t,a.zlevel=n,isFinite(r)&&(a.z2=r+(l&&l.showAbove?1:-1))}return r}function ste(e){return e.animation={duration:0},e}function Fd(e,t){return t?xt(Id.transform,t):bt(Id.transform),Id.decomposeTransform(),Qn(e,Id),e}var Id=new Xn;Id.transform=yt();function cte(e){var t=e.getZr().painter;return t.getType()===`canvas`?t:null}rd(`circle`,Kl),rd(`ellipse`,Jl),rd(`sector`,du),rd(`ring`,pu),rd(`polygon`,_u),rd(`polyline`,yu),rd(`rect`,yo),rd(`line`,Su),rd(`bezierCurve`,Eu),rd(`arc`,Ou);var Ld={};function Rd(e,t){for(var n=0;n<Dc.length;n++){var r=Dc[n],i=t[r],a=e.ensureState(r);a.style=a.style||{},a.style.text=i}var o=e.currentStates.slice();e.clearStates(!0),e.setStyle({text:t.normal}),e.useStates(o,!0)}function zd(e,t,n){var r=e.labelFetcher,i=e.labelDataIndex,a=e.labelDimIndex,o=t.normal,s;r&&(s=r.getFormattedLabel(i,`normal`,null,a,o&&o.get(`formatter`),n==null?null:{interpolatedValue:n})),s??=he(e.defaultText)?e.defaultText(i,e,n):e.defaultText;for(var l={normal:s},u=0;u<Dc.length;u++){var d=Dc[u],f=t[d];l[d]=Ee(r?r.getFormattedLabel(i,d,null,a,f&&f.get(`formatter`)):null,s)}return l}function Bd(e,t,n,r){n||=Ld;for(var i=e instanceof wo,a=!1,o=0;o<Oc.length;o++){var s=t[Oc[o]];if(s&&s.getShallow(`show`)){a=!0;break}}var l=i?e:e.getTextContent();if(a){i||(l||(l=new wo,e.setTextContent(l)),e.stateProxy&&(l.stateProxy=e.stateProxy));var u=zd(n,t),d=t.normal,f=!!d.getShallow(`show`),p=Hd(d,r&&r.normal,n,!1,!i);p.text=u.normal,i||e.setTextConfig(Ud(d,n,!1));for(var o=0;o<Dc.length;o++){var m=Dc[o],s=t[m];if(s){var h=l.ensureState(m),g=!!Ee(s.getShallow(`show`),f);if(g!==f&&(h.ignore=!g),h.style=Hd(s,r&&r[m],n,!0,!i),h.style.text=u[m],!i){var _=e.ensureState(m);_.textConfig=Ud(s,n,!0)}}}l.silent=!!d.getShallow(`silent`),l.style.x!=null&&(p.x=l.style.x),l.style.y!=null&&(p.y=l.style.y),l.ignore=!f,l.useStyle(p),l.dirty(),n.enableTextSetter&&(Yd(l).setLabelText=function(e){var r=zd(n,t,e);Rd(l,r)})}else l&&(l.ignore=!0);e.dirty()}function Vd(e,t){t||=`label`;for(var n={normal:e.getModel(t)},r=0;r<Dc.length;r++){var i=Dc[r];n[i]=e.getModel([i,t])}return n}function Hd(e,t,n,r,i){var a={};return Wd(a,e,n,r,i),t&&R(a,t),a}function Ud(e,t,n){t||={};var r={},i,a=e.getShallow(`rotate`),o=Ee(e.getShallow(`distance`),n?null:5),s=e.getShallow(`offset`);return i=e.getShallow(`position`)||(n?null:`inside`),i===`outside`&&(i=t.defaultOutsidePosition||`top`),i!=null&&(r.position=i),s!=null&&(r.offset=s),a!=null&&(a*=Math.PI/180,r.rotation=a),o!=null&&(r.distance=o),r.outsideFill=e.get(`color`)===`inherit`?t.inheritColor||null:`auto`,t.autoOverflowArea!=null&&(r.autoOverflowArea=t.autoOverflowArea),t.layoutRect!=null&&(r.layoutRect=t.layoutRect),r}function Wd(e,t,n,r,i){n||=Ld;var a=t.ecModel,o=a&&a.option.textStyle,s=lte(t),l;if(s){l={};var u=`richInheritPlainLabel`,d=Ee(t.get(u),a?a.get(u):void 0);for(var f in s)if(s.hasOwnProperty(f)){var p=t.getModel([`rich`,f]);Jd(l[f]={},p,o,t,d,n,r,i,!1,!0)}}l&&(e.rich=l);var m=t.get(`overflow`);m&&(e.overflow=m);var h=t.get(`lineOverflow`);h&&(e.lineOverflow=h);var g=e,_=t.get(`minMargin`);if(_!=null)_=ve(_)?_/2:0,g.margin=[_,_,_,_],g.__marginType=Xd.minMargin;else{var v=t.get(`textMargin`);v!=null&&(g.margin=ke(v),g.__marginType=Xd.textMargin)}Jd(e,t,o,null,null,n,r,i,!0,!1)}function lte(e){for(var t;e&&e!==e.ecModel;){var n=(e.option||Ld).rich;if(n){t||={};for(var r=ue(n),i=0;i<r.length;i++){var a=r[i];t[a]=1}}e=e.parentModel}return t}var Gd=[`fontStyle`,`fontWeight`,`fontSize`,`fontFamily`,`textShadowColor`,`textShadowBlur`,`textShadowOffsetX`,`textShadowOffsetY`],Kd=[`align`,`lineHeight`,`width`,`height`,`tag`,`verticalAlign`,`ellipsis`],qd=[`padding`,`borderWidth`,`borderRadius`,`borderDashOffset`,`backgroundColor`,`borderColor`,`shadowColor`,`shadowBlur`,`shadowOffsetX`,`shadowOffsetY`];function Jd(e,t,n,r,i,a,o,s,l,u){n=!o&&n||Ld;var d=a&&a.inheritColor,f=t.getShallow(`color`),p=t.getShallow(`textBorderColor`),m=Ee(t.getShallow(`opacity`),n.opacity);(f===`inherit`||f===`auto`)&&(f=d||null),(p===`inherit`||p===`auto`)&&(p=d||null),s||(f||=n.color,p||=n.textBorderColor),f!=null&&(e.fill=f),p!=null&&(e.stroke=p);var h=Ee(t.getShallow(`textBorderWidth`),n.textBorderWidth);h!=null&&(e.lineWidth=h);var g=Ee(t.getShallow(`textBorderType`),n.textBorderType);g!=null&&(e.lineDash=g);var _=Ee(t.getShallow(`textBorderDashOffset`),n.textBorderDashOffset);_!=null&&(e.lineDashOffset=_),!o&&m==null&&!u&&(m=a&&a.defaultOpacity),m!=null&&(e.opacity=m),!o&&!s&&e.fill==null&&a.inheritColor&&(e.fill=a.inheritColor);for(var v=0;v<Gd.length;v++){var y=Gd[v],b=i!==!1&&r?De(t.getShallow(y),r.getShallow(y),n[y]):Ee(t.getShallow(y),n[y]);b!=null&&(e[y]=b)}for(var v=0;v<Kd.length;v++){var y=Kd[v],b=t.getShallow(y);b!=null&&(e[y]=b)}if(e.verticalAlign==null){var x=t.getShallow(`baseline`);x!=null&&(e.verticalAlign=x)}if(!l||!a.disableBox){for(var v=0;v<qd.length;v++){var y=qd[v],b=t.getShallow(y);b!=null&&(e[y]=b)}var S=t.getShallow(`borderType`);S!=null&&(e.borderDash=S),(e.backgroundColor===`auto`||e.backgroundColor===`inherit`)&&d&&(e.backgroundColor=d),(e.borderColor===`auto`||e.borderColor===`inherit`)&&d&&(e.borderColor=d)}}function ute(e,t){var n=t&&t.getModel(`textStyle`);return je([e.fontStyle||n&&n.getShallow(`fontStyle`)||``,e.fontWeight||n&&n.getShallow(`fontWeight`)||``,(e.fontSize||n&&n.getShallow(`fontSize`)||12)+`px`,e.fontFamily||n&&n.getShallow(`fontFamily`)||`sans-serif`].join(` `))}var Yd=Us();function dte(e,t,n,r){if(e){var i=Yd(e);i.prevValue=i.value,i.value=n;var a=t.normal;i.valueAnimation=a.get(`valueAnimation`),i.valueAnimation&&(i.precision=a.get(`precision`),i.defaultInterpolatedText=r,i.statesModels=t)}}var Xd={minMargin:1,textMargin:2},fte=[`textStyle`,`color`],Zd=[`fontStyle`,`fontWeight`,`fontSize`,`fontFamily`,`padding`,`lineHeight`,`rich`,`width`,`height`,`overflow`],Qd=new wo,$d=function(){function e(){}return e.prototype.getTextColor=function(e){var t=this.ecModel;return this.getShallow(`color`)||(!e&&t?t.get(fte):null)},e.prototype.getFont=function(){return ute({fontStyle:this.getShallow(`fontStyle`),fontWeight:this.getShallow(`fontWeight`),fontSize:this.getShallow(`fontSize`),fontFamily:this.getShallow(`fontFamily`)},this.ecModel)},e.prototype.getTextRect=function(e){for(var t={text:e,verticalAlign:this.getShallow(`verticalAlign`)||this.getShallow(`baseline`)},n=0;n<Zd.length;n++)t[Zd[n]]=this.getShallow(Zd[n]);return Qd.useStyle(t),Qd.update(),Qd.getBoundingRect()},e}(),ef=[[`lineWidth`,`width`],[`stroke`,`color`],[`opacity`],[`shadowBlur`],[`shadowOffsetX`],[`shadowOffsetY`],[`shadowColor`],[`lineDash`,`type`],[`lineDashOffset`,`dashOffset`],[`lineCap`,`cap`],[`lineJoin`,`join`],[`miterLimit`]],pte=ct(ef),mte=function(){function e(){}return e.prototype.getLineStyle=function(e){return pte(this,e)},e}(),tf=[[`fill`,`color`],[`stroke`,`borderColor`],[`lineWidth`,`borderWidth`],[`opacity`],[`shadowBlur`],[`shadowOffsetX`],[`shadowOffsetY`],[`shadowColor`],[`lineDash`,`borderType`],[`lineDashOffset`,`borderDashOffset`],[`lineCap`,`borderCap`],[`lineJoin`,`borderJoin`],[`miterLimit`,`borderMiterLimit`]],hte=ct(tf),nf=function(){function e(){}return e.prototype.getItemStyle=function(e,t){return hte(this,e,t)},e}(),rf=function(){function e(e,t,n){this.parentModel=t,this.ecModel=n,this.option=e}return e.prototype.init=function(e,t,n){for(var r=[],i=3;i<arguments.length;i++)r[i-3]=arguments[i]},e.prototype.mergeOption=function(e,t){L(this.option,e,!0)},e.prototype.get=function(e,t){return e==null?this.option:this._doGet(this.parsePath(e),!t&&this.parentModel)},e.prototype.getShallow=function(e,t){var n=this.option,r=n==null?n:n[e];if(r==null&&!t){var i=this.parentModel;i&&(r=i.getShallow(e))}return r},e.prototype.getModel=function(t,n){var r=t!=null,i=r?this.parsePath(t):null,a=r?this._doGet(i):this.option;return n||=this.parentModel&&this.parentModel.getModel(this.resolveParentPath(i)),new e(a,n,this.ecModel)},e.prototype.isEmpty=function(){return this.option==null},e.prototype.restoreData=function(){},e.prototype.clone=function(){var e=this.constructor;return new e(I(this.option))},e.prototype.parsePath=function(e){return typeof e==`string`?e.split(`.`):e},e.prototype.resolveParentPath=function(e){return e},e.prototype.isAnimationEnabled=function(){if(!Ke.node&&this.option){if(this.option.animation!=null)return!!this.option.animation;if(this.parentModel)return this.parentModel.isAnimationEnabled()}},e.prototype._doGet=function(e,t){var n=this.option;if(!e)return n;for(var r=0;r<e.length&&!(e[r]&&(n=n&&typeof n==`object`?n[e[r]]:null,n==null));r++);return n==null&&t&&(n=t._doGet(this.resolveParentPath(e),t.parentModel)),n},e}();et(rf),it(rf),ie(rf,mte),ie(rf,nf),ie(rf,ut),ie(rf,$d);function af(e){return e==null?0:e.length||1}function of(e){return e}var gte=function(){function e(e,t,n,r,i,a){this._old=e,this._new=t,this._oldKeyGetter=n||of,this._newKeyGetter=r||of,this.context=i,this._diffModeMultiple=a===`multiple`}return e.prototype.add=function(e){return this._add=e,this},e.prototype.update=function(e){return this._update=e,this},e.prototype.updateManyToOne=function(e){return this._updateManyToOne=e,this},e.prototype.updateOneToMany=function(e){return this._updateOneToMany=e,this},e.prototype.updateManyToMany=function(e){return this._updateManyToMany=e,this},e.prototype.remove=function(e){return this._remove=e,this},e.prototype.execute=function(){this[this._diffModeMultiple?`_executeMultiple`:`_executeOneToOne`]()},e.prototype._executeOneToOne=function(){var e=this._old,t=this._new,n={},r=Array(e.length),i=Array(t.length);this._initIndexMap(e,null,r,`_oldKeyGetter`),this._initIndexMap(t,n,i,`_newKeyGetter`);for(var a=0;a<e.length;a++){var o=r[a],s=n[o],l=af(s);if(l>1){var u=s.shift();s.length===1&&(n[o]=s[0]),this._update&&this._update(u,a)}else l===1?(n[o]=null,this._update&&this._update(s,a)):this._remove&&this._remove(a)}this._performRestAdd(i,n)},e.prototype._executeMultiple=function(){var e=this._old,t=this._new,n={},r={},i=[],a=[];this._initIndexMap(e,n,i,`_oldKeyGetter`),this._initIndexMap(t,r,a,`_newKeyGetter`);for(var o=0;o<i.length;o++){var s=i[o],l=n[s],u=r[s],d=af(l),f=af(u);if(d>1&&f===1)this._updateManyToOne&&this._updateManyToOne(u,l),r[s]=null;else if(d===1&&f>1)this._updateOneToMany&&this._updateOneToMany(u,l),r[s]=null;else if(d===1&&f===1)this._update&&this._update(u,l),r[s]=null;else if(d>1&&f>1)this._updateManyToMany&&this._updateManyToMany(u,l),r[s]=null;else if(d>1)for(var p=0;p<d;p++)this._remove&&this._remove(l[p]);else this._remove&&this._remove(l)}this._performRestAdd(a,r)},e.prototype._performRestAdd=function(e,t){for(var n=0;n<e.length;n++){var r=e[n],i=t[r],a=af(i);if(a>1)for(var o=0;o<a;o++)this._add&&this._add(i[o]);else a===1&&this._add&&this._add(i);t[r]=null}},e.prototype._initIndexMap=function(e,t,n,r){for(var i=this._diffModeMultiple,a=0;a<e.length;a++){var o=`_ec_`+this[r](e[a],a);if(i||(n[a]=o),t){var s=t[o],l=af(s);l===0?(t[o]=a,i&&n.push(o)):l===1?t[o]=[s,a]:s.push(a)}}},e}(),sf={Must:1,Might:2,Not:3},cf=Us();function lf(e){cf(e).datasetMap=ze()}function _te(e,t,n){var r={},i=df(t);if(!i||!e)return r;var a=[],o=[],s=t.ecModel,l=cf(s).datasetMap,u=i.uid+`_`+n.seriesLayoutBy,d,f;e=e.slice(),z(e,function(t,n){var i=ye(t)?t:e[n]={name:t};i.type===`ordinal`&&d==null&&(d=n,f=h(i)),r[i.name]=[]});var p=l.get(u)||l.set(u,{categoryWayDim:f,valueWayDim:0});z(e,function(e,t){var n=e.name,i=h(e);if(d==null){var s=p.valueWayDim;m(r[n],s,i),m(o,s,i),p.valueWayDim+=i}else if(d===t)m(r[n],0,i),m(a,0,i);else{var s=p.categoryWayDim;m(r[n],s,i),m(o,s,i),p.categoryWayDim+=i}});function m(e,t,n){for(var r=0;r<n;r++)e.push(t+r)}function h(e){var t=e.dimsDef;return t?t.length:1}return a.length&&(r.itemName=a),o.length&&(r.seriesName=o),r}function uf(e,t,n){var r={};if(!df(e))return r;var i=t.sourceFormat,a=t.dimensionsDefine,o;(i===`objectRows`||i===`keyedColumns`)&&z(a,function(e,t){(ye(e)?e.name:e)===`name`&&(o=t)});var s=function(){for(var e={},r={},s=[],l=0,u=Math.min(5,n);l<u;l++){var d=yte(t.data,i,t.seriesLayoutBy,a,t.startIndex,l);s.push(d);var f=d===sf.Not;if(f&&e.v==null&&l!==o&&(e.v=l),(e.n==null||e.n===e.v||!f&&s[e.n]===sf.Not)&&(e.n=l),p(e)&&s[e.n]!==sf.Not)return e;f||(d===sf.Might&&r.v==null&&l!==o&&(r.v=l),(r.n==null||r.n===r.v)&&(r.n=l))}function p(e){return e.v!=null&&e.n!=null}return p(e)?e:p(r)?r:null}();if(s){r.value=[s.v];var l=o??s.n;r.itemName=[l],r.seriesName=[l]}return r}function df(e){if(!e.get(`data`,!0))return qs(e.ecModel,`dataset`,{index:e.get(`datasetIndex`,!0),id:e.get(`datasetId`,!0)},Ks).models[0]}function vte(e){return!e.get(`transform`,!0)&&!e.get(`fromTransformResult`,!0)?[]:qs(e.ecModel,`dataset`,{index:e.get(`fromDatasetIndex`,!0),id:e.get(`fromDatasetId`,!0)},Ks).models}function ff(e,t){return yte(e.data,e.sourceFormat,e.seriesLayoutBy,e.dimensionsDefine,e.startIndex,t)}function yte(e,t,n,r,i,a){var o,s=5;if(xe(e))return sf.Not;var l,u;if(r){var d=r[a];ye(d)?(l=d.name,u=d.type):ge(d)&&(l=d)}if(u!=null)return u===`ordinal`?sf.Must:sf.Not;if(t===`arrayRows`){var f=e;if(n===`row`){for(var p=f[a],m=0;m<(p||[]).length&&m<s;m++)if((o=x(p[i+m]))!=null)return o}else for(var m=0;m<f.length&&m<s;m++){var h=f[i+m];if(h&&(o=x(h[a]))!=null)return o}}else if(t===`objectRows`){var g=e;if(!l)return sf.Not;for(var m=0;m<g.length&&m<s;m++){var _=g[m];if(_&&(o=x(_[l]))!=null)return o}}else if(t===`keyedColumns`){var v=e;if(!l)return sf.Not;var p=v[l];if(!p||xe(p))return sf.Not;for(var m=0;m<p.length&&m<s;m++)if((o=x(p[m]))!=null)return o}else if(t===`original`)for(var y=e,m=0;m<y.length&&m<s;m++){var _=y[m],b=Es(_);if(!me(b))return sf.Not;if((o=x(b[a]))!=null)return o}function x(e){var t=ge(e);if(e!=null&&isFinite(Number(e))&&e!==``)return t?sf.Might:sf.Not;if(t&&e!==`-`)return sf.Must}return sf.Not}var pf=function(){function e(e){this.data=e.data||(e.sourceFormat===`keyedColumns`?{}:[]),this.sourceFormat=e.sourceFormat||`unknown`,this.seriesLayoutBy=e.seriesLayoutBy||`column`,this.startIndex=e.startIndex||0,this.dimensionsDetectedCount=e.dimensionsDetectedCount,this.metaRawOption=e.metaRawOption;var t=this.dimensionsDefine=e.dimensionsDefine;if(t)for(var n=0;n<t.length;n++){var r=t[n];r.type==null&&ff(this,n)===sf.Must&&(r.type=`ordinal`)}}return e}();function mf(e){return e instanceof pf}function hf(e,t,n){n||=_f(e);var r=t.seriesLayoutBy,i=xte(e,n,r,t.sourceHeader,t.dimensions);return new pf({data:e,sourceFormat:n,seriesLayoutBy:r,dimensionsDefine:i.dimensionsDefine,startIndex:i.startIndex,dimensionsDetectedCount:i.dimensionsDetectedCount,metaRawOption:I(t)})}function gf(e){return new pf({data:e,sourceFormat:xe(e)?vc:mc})}function bte(e){return new pf({data:e.data,sourceFormat:e.sourceFormat,seriesLayoutBy:e.seriesLayoutBy,dimensionsDefine:I(e.dimensionsDefine),startIndex:e.startIndex,dimensionsDetectedCount:e.dimensionsDetectedCount})}function _f(e){var t=yc;if(xe(e))t=vc;else if(me(e)){e.length===0&&(t=hc);for(var n=0,r=e.length;n<r;n++){var i=e[n];if(i!=null){if(me(i)||xe(i)){t=hc;break}else if(ye(i)){t=gc;break}}}}else if(ye(e)){for(var a in e)if(He(e,a)&&ae(e[a])){t=_c;break}}return t}function xte(e,t,n,r,i){var a,o;if(!e)return{dimensionsDefine:Ste(i),startIndex:o,dimensionsDetectedCount:a};if(t===`arrayRows`){var s=e;r===`auto`||r==null?Cte(function(e){e!=null&&e!==`-`&&(ge(e)?o??=1:o=0)},n,s,10):o=ve(r)?r:+!!r,!i&&o===1&&(i=[],Cte(function(e,t){i[t]=e==null?``:e+``},n,s,1/0)),a=i?i.length:n===`row`?s.length:s[0]?s[0].length:null}else if(t===`objectRows`)i||=vf(e);else if(t===`keyedColumns`)i||(i=[],z(e,function(e,t){i.push(t)}));else if(t===`original`){var l=Es(e[0]);a=me(l)&&l.length||1}return{startIndex:o,dimensionsDefine:Ste(i),dimensionsDetectedCount:a}}function vf(e){for(var t=0,n;t<e.length&&!(n=e[t++]););if(n)return ue(n)}function Ste(e){if(e){var t=ze();return oe(e,function(e,n){e=ye(e)?e:{name:e};var r={name:e.name,displayName:e.displayName,type:e.type};if(r.name==null)return r;r.name+=``,r.displayName??=r.name;var i=t.get(r.name);return i?r.name+=`-`+i.count++:t.set(r.name,{count:1}),r})}}function Cte(e,t,n,r){if(t===`row`)for(var i=0;i<n.length&&i<r;i++)e(n[i]?n[i][0]:null,i);else for(var a=n[0]||[],i=0;i<a.length&&i<r;i++)e(a[i],i)}function wte(e){var t=e.sourceFormat;return t===`objectRows`||t===`keyedColumns`}var yf,bf,xf,Sf,Tte,Ete,Cf=function(){function e(e,t){var n=mf(e)?e:gf(e);this._source=n;var r=this._data=n.data,i=n.sourceFormat;n.seriesLayoutBy,i===`typedArray`&&(this._offset=0,this._dimSize=t,this._data=r),Ete(this,r,n)}return e.prototype.getSource=function(){return this._source},e.prototype.count=function(){return 0},e.prototype.getItem=function(e,t){},e.prototype.appendData=function(e){},e.prototype.clean=function(){},e.protoInitialize=function(){var t=e.prototype;t.pure=!1,t.persistent=!0}(),e.internalField=function(){var e;Ete=function(e,i,a){var o=a.sourceFormat,s=a.seriesLayoutBy,l=a.startIndex,u=a.dimensionsDefine,d=Tte[kf(o,s)];R(e,d),o===`typedArray`?(e.getItem=t,e.count=r,e.fillStorage=n):(e.getItem=fe(Ef(o,s),null,i,l,u),e.count=fe(Ate(o,s),null,i,l,u))};var t=function(e,t){e-=this._offset,t||=[];for(var n=this._data,r=this._dimSize,i=r*e,a=0;a<r;a++)t[a]=n[i+a];return t},n=function(e,t,n,r){for(var i=this._data,a=this._dimSize,o=0;o<a;o++){for(var s=r[o],l=s[0]==null?1/0:s[0],u=s[1]==null?-1/0:s[1],d=t-e,f=n[o],p=0;p<d;p++){var m=i[p*a+o];f[e+p]=m,m<l&&(l=m),m>u&&(u=m)}s[0]=l,s[1]=u}},r=function(){return this._data?this._data.length/this._dimSize:0};Tte=(e={},e[hc+`_`+bc]={pure:!0,appendData:i},e[hc+`_row`]={pure:!0,appendData:function(){throw Error(`Do not support appendData when set seriesLayoutBy: "row".`)}},e[gc]={pure:!0,appendData:i},e[_c]={pure:!0,appendData:function(e){var t=this._data;z(e,function(e,n){for(var r=t[n]||(t[n]=[]),i=0;i<(e||[]).length;i++)r.push(e[i])})}},e[mc]={appendData:i},e[vc]={persistent:!1,pure:!0,appendData:function(e){this._data=e},clean:function(){this._offset+=this.count(),this._data=null}},e);function i(e){for(var t=0;t<e.length;t++)this._data.push(e[t])}}(),e}(),wf=function(e){me(e)||vs(`series.data or dataset.source must be an array.`)};yf={},yf[hc+`_`+bc]=wf,yf[hc+`_row`]=wf,yf[gc]=wf,yf[_c]=function(e,t){for(var n=0;n<t.length;n++)t[n].name??vs(`dimension name must not be null/undefined.`)},yf[mc]=wf;var Tf=function(e,t,n,r){return e[r]},Dte=(bf={},bf[hc+`_`+bc]=function(e,t,n,r){return e[r+t]},bf[hc+`_row`]=function(e,t,n,r,i){r+=t;for(var a=i||[],o=e,s=0;s<o.length;s++){var l=o[s];a[s]=l?l[r]:null}return a},bf[gc]=Tf,bf[_c]=function(e,t,n,r,i){for(var a=i||[],o=0;o<n.length;o++){var s=n[o].name,l=s==null?null:e[s];a[o]=l?l[r]:null}return a},bf[mc]=Tf,bf);function Ef(e,t){return Dte[kf(e,t)]}var Ote=function(e,t,n){return e.length},kte=(xf={},xf[hc+`_`+bc]=function(e,t,n){return Math.max(0,e.length-t)},xf[hc+`_row`]=function(e,t,n){var r=e[0];return r?Math.max(0,r.length-t):0},xf[gc]=Ote,xf[_c]=function(e,t,n){var r=n[0].name,i=r==null?null:e[r];return i?i.length:0},xf[mc]=Ote,xf);function Ate(e,t){return kte[kf(e,t)]}var Df=function(e,t,n){return e[t]},Of=(Sf={},Sf[hc]=Df,Sf[gc]=function(e,t,n){return e[n]},Sf[_c]=Df,Sf[mc]=function(e,t,n){var r=Es(e);return r instanceof Array?r[t]:r},Sf[vc]=Df,Sf);function jte(e){return Of[e]}function kf(e,t){return e===`arrayRows`?e+`_`+t:e}function Af(e,t,n){if(e){var r=e.getRawDataItem(t);if(r!=null){var i=e.getStore(),a=i.getSource().sourceFormat;if(n!=null){var o=e.getDimensionIndex(n),s=i.getDimensionProperty(o);return jte(a)(r,o,s)}else{var l=r;return a===`original`&&(l=Es(r)),l}}}}var Mte=function(){function e(e,t){this._encode=e,this._schema=t}return e.prototype.get=function(){return{fullDimensions:this._getFullDimensionNames(),encode:this._encode}},e.prototype._getFullDimensionNames=function(){return this._cachedDimNames||=this._schema?this._schema.makeOutputDimensionNames():[],this._cachedDimNames},e}();function Nte(e,t){var n={},r=n.encode={},i=ze(),a=[],o=[],s={};z(e.dimensions,function(t){var n=e.getDimensionInfo(t),l=n.coordDim;if(l){var u=n.coordDimIndex;jf(r,l)[u]=t,n.isExtraCoord||(i.set(l,1),Fte(n.type)&&(a[0]=t),jf(s,l)[u]=e.getDimensionIndex(n.name)),n.defaultTooltip&&o.push(t)}pc.each(function(e,t){var i=jf(r,t),a=n.otherDims[t];a!=null&&a!==!1&&(i[a]=n.name)})});var l=[],u={};i.each(function(e,t){var n=r[t];u[t]=n[0],l=l.concat(n)}),n.dataDimsOnCoord=l,n.dataDimIndicesOnCoord=oe(l,function(t){return e.getDimensionInfo(t).storeDimIndex}),n.encodeFirstDimNotExtra=u;var d=r.label;d&&d.length&&(a=d.slice());var f=r.tooltip;return f&&f.length?o=f.slice():o.length||(o=a.slice()),r.defaultedLabel=a,r.defaultedTooltip=o,n.userOutput=new Mte(s,t),n}function jf(e,t){return e.hasOwnProperty(t)||(e[t]=[]),e[t]}function Pte(e){return e===`category`?`ordinal`:e===`time`?`time`:`float`}function Fte(e){return!(e===`ordinal`||e===`time`)}var Mf=function(){function e(e){this.otherDims={},e!=null&&R(this,e)}return e}();function Nf(e,t){var n=t&&t.type;return n===`ordinal`?e:(n===`time`&&!ve(e)&&e!=null&&e!==`-`&&(e=+ss(e)),e==null||e===``?NaN:Number(e))}ze({number:function(e){return parseFloat(e)},time:function(e){return+ss(e)},trim:function(e){return ge(e)?je(e):e}});var Ite={lt:function(e,t){return e<t},lte:function(e,t){return e<=t},gt:function(e,t){return e>t},gte:function(e,t){return e>=t}};(function(){function e(e,t){ve(t)||ys(``),this._opFn=Ite[e],this._rvalFloat=ds(t)}return e.prototype.evaluate=function(e){return ve(e)?this._opFn(e,this._rvalFloat):this._opFn(ds(e),this._rvalFloat)},e})(),function(){function e(e,t){var n=e===`desc`;this._resultLT=n?1:-1,t??=n?`min`:`max`,this._incomparable=t===`min`?-1/0:1/0}return e.prototype.evaluate=function(e,t){var n=ve(e)?e:ds(e),r=ve(t)?t:ds(t),i=isNaN(n),a=isNaN(r);if(i&&(n=this._incomparable),a&&(r=this._incomparable),i&&a){var o=ge(e),s=ge(t);o&&(n=s?e:0),s&&(r=o?t:0)}return n<r?this._resultLT:n>r?-this._resultLT:0},e}(),function(){function e(e,t){this._rval=t,this._isEQ=e,this._rvalTypeof=typeof t,this._rvalFloat=ds(t)}return e.prototype.evaluate=function(e){var t=e===this._rval;if(!t){var n=typeof e;n!==this._rvalTypeof&&(n===`number`||this._rvalTypeof===`number`)&&(t=ds(e)===this._rvalFloat)}return this._isEQ?t:!t},e}();function Pf(e){var t=``,n=-1/0,r=-1/0,i=1/0,a=1/0;return e&&(e.g!=null&&(t+=`G`+e.g,n=e.g),e.ge!=null&&(t+=`GE`+e.ge,r=e.ge),e.l!=null&&(t+=`L`+e.l,i=e.l),e.le!=null&&(t+=`LE`+e.le,a=e.le)),{key:t,g:n,ge:r,l:i,le:a}}function Ff(e,t){return t>e.g&&t>=e.ge&&t<e.l&&t<=e.le}var If=typeof Uint32Array>`u`?Array:Uint32Array,Lte=typeof Uint16Array>`u`?Array:Uint16Array,Lf=typeof Int32Array>`u`?Array:Int32Array,Rf=typeof Float64Array>`u`?Array:Float64Array,zf={float:Rf,int:Lf,ordinal:Array,number:Array,time:Rf},Bf;function Vf(e){return e>65535?If:Lte}function Rte(e){var t=e.constructor;return t===Array?e.slice():new t(e)}function Hf(e,t,n,r,i){var a=zf[n||`float`];if(i){var o=e[t],s=o&&o.length;if(s!==r){for(var l=new a(r),u=0;u<s;u++)l[u]=o[u];e[t]=l}}else e[t]=new a(r)}var Uf=function(){function e(){this._chunks=[],this._rawExtent=[],this._extent=[],this._count=0,this._rawCount=0,this._calcDimNameToIdx=ze()}return e.prototype.initData=function(e,t,n){this._provider=e,this._chunks=[],this._indices=null,this.getRawIndex=this._getRawIdxIdentity;var r=e.getSource(),i=this.defaultDimValueGetter=Bf[r.sourceFormat];this._dimValueGetter=n||i,this._rawExtent=[],wte(r),this._dimensions=oe(t,function(e){return{type:e.type,property:e.property}}),this._initDataFromProvider(0,e.count())},e.prototype.getProvider=function(){return this._provider},e.prototype.getSource=function(){return this._provider.getSource()},e.prototype.ensureCalculationDimension=function(e,t){var n=this._calcDimNameToIdx,r=this._dimensions,i=n.get(e);if(i!=null){if(r[i].type===t)return i}else i=r.length;return r[i]={type:t},n.set(e,i),this._chunks[i]=new zf[t||`float`](this._rawCount),this._rawExtent[i]=Xs(),i},e.prototype.collectOrdinalMeta=function(e,t){var n=this._chunks[e],r=this._dimensions[e],i=this._rawExtent,a=r.ordinalOffset||0,o=n.length;a===0&&(i[e]=Xs());for(var s=i[e],l=a;l<o;l++){var u=n[l]=t.parseAndCollect(n[l]);isNaN(u)||(s[0]=Math.min(u,s[0]),s[1]=Math.max(u,s[1]))}r.ordinalMeta=t,r.ordinalOffset=o,r.type=`ordinal`},e.prototype.getOrdinalMeta=function(e){return this._dimensions[e].ordinalMeta},e.prototype.getDimensionProperty=function(e){var t=this._dimensions[e];return t&&t.property},e.prototype.appendData=function(e){var t=this._provider,n=this.count();t.appendData(e);var r=t.count();return t.persistent||(r+=n),n<r&&this._initDataFromProvider(n,r,!0),[n,r]},e.prototype.appendValues=function(e,t){for(var n=this._chunks,r=this._dimensions,i=r.length,a=this._rawExtent,o=this.count(),s=o+Math.max(e.length,t||0),l=0;l<i;l++){var u=r[l];Hf(n,l,u.type,s,!0)}for(var d=[],f=o;f<s;f++)for(var p=f-o,m=0;m<i;m++){var u=r[m],h=Bf.arrayRows.call(this,e[p]||d,u.property,p,m);n[m][f]=h;var g=a[m];h<g[0]&&(g[0]=h),h>g[1]&&(g[1]=h)}return this._rawCount=this._count=s,{start:o,end:s}},e.prototype._initDataFromProvider=function(e,t,n){for(var r=this._provider,i=this._chunks,a=this._dimensions,o=a.length,s=this._rawExtent,l=oe(a,function(e){return e.property}),u=0;u<o;u++){var d=a[u];s[u]||(s[u]=Xs()),Hf(i,u,d.type,t,n)}if(r.fillStorage)r.fillStorage(e,t,i,s);else for(var f=[],p=e;p<t;p++){f=r.getItem(p,f);for(var m=0;m<o;m++){var h=i[m],g=this._dimValueGetter(f,l[m],p,m);h[p]=g;var _=s[m];g<_[0]&&(_[0]=g),g>_[1]&&(_[1]=g)}}!r.persistent&&r.clean&&r.clean(),this._rawCount=this._count=t,this._extent=[]},e.prototype.count=function(){return this._count},e.prototype.get=function(e,t){if(!(t>=0&&t<this._count))return NaN;var n=this._chunks[e];return n?n[this.getRawIndex(t)]:NaN},e.prototype.getValues=function(e,t){var n=[],r=[];if(t==null){t=e,e=[];for(var i=0;i<this._dimensions.length;i++)r.push(i)}else r=e;for(var i=0,a=r.length;i<a;i++)n.push(this.get(r[i],t));return n},e.prototype.getByRawIndex=function(e,t){if(!(t>=0&&t<this._rawCount))return NaN;var n=this._chunks[e];return n?n[t]:NaN},e.prototype.getSum=function(e){var t=this._chunks[e],n=0;if(t)for(var r=0,i=this.count();r<i;r++){var a=this.get(e,r);isNaN(a)||(n+=a)}return n},e.prototype.getMedian=function(e){var t=[];this.each([e],function(e){isNaN(e)||t.push(e)}),ts(t);var n=this.count();return n===0?0:n%2==1?t[(n-1)/2]:(t[n/2]+t[n/2-1])/2},e.prototype.indexOfRawIndex=function(e){if(e>=this._rawCount||e<0)return-1;if(!this._indices)return e;var t=this._indices,n=t[e];if(n!=null&&n<this._count&&n===e)return e;for(var r=0,i=this._count-1;r<=i;){var a=(r+i)/2|0;if(t[a]<e)r=a+1;else if(t[a]>e)i=a-1;else return a}return-1},e.prototype.getIndices=function(){var e,t=this._indices;if(t){var n=t.constructor,r=this._count;if(n===Array){e=new n(r);for(var i=0;i<r;i++)e[i]=t[i]}else e=new n(t.buffer,0,r)}else{var n=Vf(this._rawCount);e=new n(this.count());for(var i=0;i<e.length;i++)e[i]=i}return e},e.prototype.filter=function(e,t){if(!this._count)return this;for(var n=this.clone(),r=n.count(),i=new(Vf(n._rawCount))(r),a=[],o=e.length,s=0,l=e[0],u=n._chunks,d=0;d<r;d++){var f=void 0,p=n.getRawIndex(d);if(o===0)f=t(d);else if(o===1){var m=u[l][p];f=t(m,d)}else{for(var h=0;h<o;h++)a[h]=u[e[h]][p];a[h]=d,f=t.apply(null,a)}f&&(i[s++]=p)}return s<r&&(n._indices=i),n._count=s,n._extent=[],n._updateGetRawIdx(),n},e.prototype.selectRange=function(e){var t=this.clone(),n=t._count;if(!n)return this;var r=ue(e),i=r.length;if(!i)return this;var a=t.count(),o=new(Vf(t._rawCount))(a),s=0,l=r[0],u=e[l][0],d=e[l][1],f=t._chunks,p=!1;if(!t._indices){var m=0;if(i===1){for(var h=f[r[0]],g=0;g<n;g++){var _=h[g];(_>=u&&_<=d||isNaN(_))&&(o[s++]=m),m++}p=!0}else if(i===2){for(var h=f[r[0]],v=f[r[1]],y=e[r[1]][0],b=e[r[1]][1],g=0;g<n;g++){var _=h[g],x=v[g];(_>=u&&_<=d||isNaN(_))&&(x>=y&&x<=b||isNaN(x))&&(o[s++]=m),m++}p=!0}}if(!p)if(i===1)for(var g=0;g<a;g++){var S=t.getRawIndex(g),_=f[r[0]][S];(_>=u&&_<=d||isNaN(_))&&(o[s++]=S)}else for(var g=0;g<a;g++){for(var C=!0,S=t.getRawIndex(g),w=0;w<i;w++){var T=r[w],_=f[T][S];(_<e[T][0]||_>e[T][1])&&(C=!1)}C&&(o[s++]=t.getRawIndex(g))}return s<a&&(t._indices=o),t._count=s,t._extent=[],t._updateGetRawIdx(),t},e.prototype.map=function(e,t){var n=this.clone(e);return this._updateDims(n,e,t),n},e.prototype.modify=function(e,t){this._updateDims(this,e,t)},e.prototype._updateDims=function(e,t,n){for(var r=e._chunks,i=[],a=t.length,o=e.count(),s=[],l=e._rawExtent,u=0;u<t.length;u++)l[t[u]]=Xs();for(var d=0;d<o;d++){for(var f=e.getRawIndex(d),p=0;p<a;p++)s[p]=r[t[p]][f];s[a]=d;var m=n&&n.apply(null,s);if(m!=null){typeof m!=`object`&&(i[0]=m,m=i);for(var u=0;u<m.length;u++){var h=t[u],g=m[u],_=l[h],v=r[h];v&&(v[f]=g),g<_[0]&&(_[0]=g),g>_[1]&&(_[1]=g)}}}},e.prototype.lttbDownSample=function(e,t){var n=this.clone([e],!0),r=n._chunks[e],i=this.count(),a=0,o=Math.floor(1/t),s=this.getRawIndex(0),l,u,d,f=new(Vf(this._rawCount))(Math.min((Math.ceil(i/o)+2)*2,i));f[a++]=s;for(var p=1;p<i-1;p+=o){for(var m=Math.min(p+o,i-1),h=Math.min(p+o*2,i),g=(h+m)/2,_=0,v=m;v<h;v++){var y=this.getRawIndex(v),b=r[y];isNaN(b)||(_+=b)}_/=h-m;var x=p,S=Math.min(p+o,i),C=p-1,w=r[s];l=-1,d=x;for(var T=-1,E=0,v=x;v<S;v++){var y=this.getRawIndex(v),b=r[y];if(isNaN(b)){E++,T<0&&(T=y);continue}u=Math.abs((C-g)*(b-w)-(C-v)*(_-w)),u>l&&(l=u,d=y)}E>0&&E<S-x&&(f[a++]=Math.min(T,d),d=Math.max(T,d)),f[a++]=d,s=d}return f[a++]=this.getRawIndex(i-1),n._count=a,n._indices=f,n.getRawIndex=this._getRawIdx,n},e.prototype.minmaxDownSample=function(e,t){for(var n=this.clone([e],!0),r=n._chunks,i=Math.floor(1/t),a=r[e],o=this.count(),s=new(Vf(this._rawCount))(Math.ceil(o/i)*2),l=0,u=0;u<o;u+=i){var d=u,f=a[this.getRawIndex(d)],p=u,m=a[this.getRawIndex(p)],h=i;u+i>o&&(h=o-u);for(var g=0;g<h;g++){var _=a[this.getRawIndex(u+g)];_<f&&(f=_,d=u+g),_>m&&(m=_,p=u+g)}var v=this.getRawIndex(d),y=this.getRawIndex(p);d<p?(s[l++]=v,s[l++]=y):(s[l++]=y,s[l++]=v)}return n._count=l,n._indices=s,n._updateGetRawIdx(),n},e.prototype.downSample=function(e,t,n,r){for(var i=this.clone([e],!0),a=i._chunks,o=[],s=Math.floor(1/t),l=a[e],u=this.count(),d=i._rawExtent[e]=Xs(),f=new(Vf(this._rawCount))(Math.ceil(u/s)),p=0,m=0;m<u;m+=s){s>u-m&&(s=u-m,o.length=s);for(var h=0;h<s;h++)o[h]=l[this.getRawIndex(m+h)];var g=n(o),_=this.getRawIndex(Math.min(m+r(o,g)||0,u-1));l[_]=g,g<d[0]&&(d[0]=g),g>d[1]&&(d[1]=g),f[p++]=_}return i._count=p,i._indices=f,i._updateGetRawIdx(),i},e.prototype.each=function(e,t){if(this._count)for(var n=e.length,r=this._chunks,i=0,a=this.count();i<a;i++){var o=this.getRawIndex(i);switch(n){case 0:t(i);break;case 1:t(r[e[0]][o],i);break;case 2:t(r[e[0]][o],r[e[1]][o],i);break;default:for(var s=0,l=[];s<n;s++)l[s]=r[e[s]][o];l[s]=i,t.apply(null,l)}}},e.prototype.getDataExtent=function(e,t){var n=this._chunks[e],r=Xs();if(!n)return r;var i=this.count();if(!this._indices&&!t)return this._rawExtent[e].slice();var a=this._extent,o=a[e]||(a[e]={}),s=Pf(t),l=s.key,u=o[l];if(u)return u.slice();for(var d=r[0],f=r[1],p=0;p<i;p++){var m=n[this.getRawIndex(p)];(!t||Ff(s,m))&&(m<d&&(d=m),m>f&&(f=m))}return o[l]=[d,f]},e.prototype.getRawDataItem=function(e){var t=this.getRawIndex(e);if(this._provider.persistent)return this._provider.getItem(t);for(var n=[],r=this._chunks,i=0;i<r.length;i++)n.push(r[i][t]);return n},e.prototype.clone=function(t,n){var r=new e,i=this._chunks,a=t&&se(t,function(e,t){return e[t]=!0,e},{});if(a)for(var o=0;o<i.length;o++)r._chunks[o]=a[o]?Rte(i[o]):i[o];else r._chunks=i;return this._copyCommonProps(r),n||(r._indices=this._cloneIndices()),r._updateGetRawIdx(),r},e.prototype._copyCommonProps=function(e){e._count=this._count,e._rawCount=this._rawCount,e._provider=this._provider,e._dimensions=this._dimensions,e._extent=I(this._extent),e._rawExtent=I(this._rawExtent)},e.prototype._cloneIndices=function(){if(this._indices){var e=this._indices.constructor,t=void 0;if(e===Array){var n=this._indices.length;t=new e(n);for(var r=0;r<n;r++)t[r]=this._indices[r]}else t=new e(this._indices);return t}return null},e.prototype._getRawIdxIdentity=function(e){return e},e.prototype._getRawIdx=function(e){return e<this._count&&e>=0?this._indices[e]:-1},e.prototype._updateGetRawIdx=function(){this.getRawIndex=this._indices?this._getRawIdx:this._getRawIdxIdentity},e.internalField=function(){function e(e,t,n,r){return Nf(e[r],this._dimensions[r])}Bf={arrayRows:e,objectRows:function(e,t,n,r){return Nf(e[t],this._dimensions[r])},keyedColumns:e,original:function(e,t,n,r){var i=e&&(e.value==null?e:e.value);return Nf(i instanceof Array?i[r]:i,this._dimensions[r])},typedArray:function(e,t,n,r){return e[r]}}}(),e}(),Wf=Us(),Gf={float:`f`,int:`i`,ordinal:`o`,number:`n`,time:`t`},Kf=function(){function e(e){this.dimensions=e.dimensions,this._dimOmitted=e.dimensionOmitted,this.source=e.source,this._fullDimCount=e.fullDimensionCount,this._updateDimOmitted(e.dimensionOmitted)}return e.prototype.isDimensionOmitted=function(){return this._dimOmitted},e.prototype._updateDimOmitted=function(e){this._dimOmitted=e,e&&(this._dimNameMap||=zte(this.source))},e.prototype.getSourceDimensionIndex=function(e){return Ee(this._dimNameMap.get(e),-1)},e.prototype.getSourceDimension=function(e){var t=this.source.dimensionsDefine;if(t)return t[e]},e.prototype.makeStoreSchema=function(){for(var e=this._fullDimCount,t=wte(this.source),n=!Bte(e),r=``,i=[],a=0,o=0;a<e;a++){var s=void 0,l=void 0,u=void 0,d=this.dimensions[o];if(d&&d.storeDimIndex===a)s=t?d.name:null,l=d.type,u=d.ordinalMeta,o++;else{var f=this.getSourceDimension(a);f&&(s=t?f.name:null,l=f.type)}i.push({property:s,type:l,ordinalMeta:u}),t&&s!=null&&(!d||!d.isCalculationCoord)&&(r+=n?s.replace(/\`/g,"`1").replace(/\$/g,"`2"):s),r+=`$`,r+=Gf[l]||`f`,u&&(r+=u.uid),r+=`$`}var p=this.source;return{dimensions:i,hash:[p.seriesLayoutBy,p.startIndex,r].join(`$$`)}},e.prototype.makeOutputDimensionNames=function(){for(var e=[],t=0,n=0;t<this._fullDimCount;t++){var r=void 0,i=this.dimensions[n];if(i&&i.storeDimIndex===t)i.isCalculationCoord||(r=i.name),n++;else{var a=this.getSourceDimension(t);a&&(r=a.name)}e.push(r)}return e},e.prototype.appendCalculationDimension=function(e){this.dimensions.push(e),e.isCalculationCoord=!0,this._fullDimCount++,this._updateDimOmitted(!0)},e}();function qf(e){return e instanceof Kf}function Jf(e){for(var t=ze(),n=0;n<(e||[]).length;n++){var r=e[n],i=ye(r)?r.name:r;i!=null&&t.get(i)==null&&t.set(i,n)}return t}function zte(e){var t=Wf(e);return t.dimNameMap||=Jf(e.dimensionsDefine)}function Bte(e){return e>30}var Yf=ye,Xf=oe,Vte=typeof Int32Array>`u`?Array:Int32Array,Hte=`e\0\0`,Zf=-1,Ute=[`hasItemOption`,`_nameList`,`_idList`,`_invertedIndicesMap`,`_dimSummary`,`userOutput`,`_rawData`,`_dimValueGetter`,`_nameDimIdx`,`_idDimIdx`,`_nameRepeatCount`],Wte=[`_approximateExtent`],Qf,$f,ep,tp,np,rp,ip,ap=function(){function e(e,t){this.type=`list`,this._dimOmitted=!1,this._nameList=[],this._idList=[],this._visual={},this._layout={},this._itemVisuals=[],this._itemLayouts=[],this._graphicEls=[],this._approximateExtent={},this._calculationInfo={},this.hasItemOption=!1,this.TRANSFERABLE_METHODS=[`cloneShallow`,`downSample`,`minmaxDownSample`,`lttbDownSample`,`map`],this.CHANGABLE_METHODS=[`filterSelf`,`selectRange`],this.DOWNSAMPLE_METHODS=[`downSample`,`minmaxDownSample`,`lttbDownSample`];var n,r=!1;qf(e)?(n=e.dimensions,this._dimOmitted=e.isDimensionOmitted(),this._schema=e):(r=!0,n=e),n||=[`x`,`y`];for(var i={},a=[],o={},s=!1,l={},u=0;u<n.length;u++){var d=n[u],f=ge(d)?new Mf({name:d}):d instanceof Mf?d:new Mf(d),p=f.name;f.type=f.type||`float`,f.coordDim||(f.coordDim=p,f.coordDimIndex=0);var m=f.otherDims=f.otherDims||{};a.push(p),i[p]=f,l[p]!=null&&(s=!0),f.createInvertedIndices&&(o[p]=[]),r&&(f.storeDimIndex=u),m.itemName===0&&(this._nameDimIdx=f.storeDimIndex),m.itemId===0&&(this._idDimIdx=f.storeDimIndex)}if(this.dimensions=a,this._dimInfos=i,this._initGetDimensionInfo(s),this.hostModel=t,this._invertedIndicesMap=o,this._dimOmitted){var h=this._dimIdxToName=ze();z(a,function(e){h.set(i[e].storeDimIndex,e)})}}return e.prototype.getDimension=function(e){var t=this._recognizeDimIndex(e);if(t==null)return e;if(t=e,!this._dimOmitted)return this.dimensions[t];var n=this._dimIdxToName.get(t);if(n!=null)return n;var r=this._schema.getSourceDimension(t);if(r)return r.name},e.prototype.getDimensionIndex=function(e){var t=this._recognizeDimIndex(e);if(t!=null)return t;if(e==null)return-1;var n=this._getDimInfo(e);return n?n.storeDimIndex:this._dimOmitted?this._schema.getSourceDimensionIndex(e):-1},e.prototype._recognizeDimIndex=function(e){if(ve(e)||e!=null&&!isNaN(e)&&!this._getDimInfo(e)&&(!this._dimOmitted||this._schema.getSourceDimensionIndex(e)<0))return+e},e.prototype._getStoreDimIndex=function(e){return this.getDimensionIndex(e)},e.prototype.getDimensionInfo=function(e){return this._getDimInfo(this.getDimension(e))},e.prototype._initGetDimensionInfo=function(e){var t=this._dimInfos;this._getDimInfo=e?function(e){return t.hasOwnProperty(e)?t[e]:void 0}:function(e){return t[e]}},e.prototype.getDimensionsOnCoord=function(){return this._dimSummary.dataDimsOnCoord.slice()},e.prototype.mapDimension=function(e,t){var n=this._dimSummary;if(t==null)return n.encodeFirstDimNotExtra[e];var r=n.encode[e];return r?r[t]:null},e.prototype.mapDimensionsAll=function(e){return(this._dimSummary.encode[e]||[]).slice()},e.prototype.getStore=function(){return this._store},e.prototype.initData=function(e,t,n){var r=this,i;if(e instanceof Uf&&(i=e),!i){var a=this.dimensions,o=mf(e)||ae(e)?new Cf(e,a.length):e;i=new Uf;var s=Xf(a,function(e){return{type:r._dimInfos[e].type,property:e}});i.initData(o,s,n)}this._store=i,this._nameList=(t||[]).slice(),this._idList=[],this._nameRepeatCount={},this._doInit(0,i.count()),this._dimSummary=Nte(this,this._schema),this.userOutput=this._dimSummary.userOutput},e.prototype.appendData=function(e){var t=this._store.appendData(e);this._doInit(t[0],t[1])},e.prototype.appendValues=function(e,t){var n=this._store.appendValues(e,t&&t.length),r=n.start,i=n.end,a=this._shouldMakeIdFromName();if(this._updateOrdinalMeta(),t)for(var o=r;o<i;o++){var s=o-r;this._nameList[o]=t[s],a&&ip(this,o)}},e.prototype._updateOrdinalMeta=function(){for(var e=this._store,t=this.dimensions,n=0;n<t.length;n++){var r=this._dimInfos[t[n]];r.ordinalMeta&&e.collectOrdinalMeta(r.storeDimIndex,r.ordinalMeta)}},e.prototype._shouldMakeIdFromName=function(){var e=this._store.getProvider();return this._idDimIdx==null&&e.getSource().sourceFormat!==`typedArray`&&!e.fillStorage},e.prototype._doInit=function(e,t){if(!(e>=t)){var n=this._store.getProvider();this._updateOrdinalMeta();var r=this._nameList,i=this._idList;if(n.getSource().sourceFormat===`original`&&!n.pure)for(var a=[],o=e;o<t;o++){var s=n.getItem(o,a);if(!this.hasItemOption&&Ds(s)&&(this.hasItemOption=!0),s){var l=s.name;r[o]==null&&l!=null&&(r[o]=Ls(l,null));var u=s.id;i[o]==null&&u!=null&&(i[o]=Ls(u,null))}}if(this._shouldMakeIdFromName())for(var o=e;o<t;o++)ip(this,o);Qf(this)}},e.prototype.getApproximateExtent=function(e,t){return this._approximateExtent[e]||this._store.getDataExtent(this._getStoreDimIndex(e),t)},e.prototype.setApproximateExtent=function(e,t){t=this.getDimension(t),this._approximateExtent[t]=e.slice()},e.prototype.getCalculationInfo=function(e){return this._calculationInfo[e]},e.prototype.setCalculationInfo=function(e,t){Yf(e)?R(this._calculationInfo,e):this._calculationInfo[e]=t},e.prototype.getName=function(e){var t=this.getRawIndex(e),n=this._nameList[t];return n==null&&this._nameDimIdx!=null&&(n=ep(this,this._nameDimIdx,t)),n??=``,n},e.prototype._getCategory=function(e,t){var n=this._store.get(e,t),r=this._store.getOrdinalMeta(e);return r?r.categories[n]:n},e.prototype.getId=function(e){return $f(this,this.getRawIndex(e))},e.prototype.count=function(){return this._store.count()},e.prototype.get=function(e,t){var n=this._store,r=this._dimInfos[e];if(r)return n.get(r.storeDimIndex,t)},e.prototype.getByRawIndex=function(e,t){var n=this._store,r=this._dimInfos[e];if(r)return n.getByRawIndex(r.storeDimIndex,t)},e.prototype.getIndices=function(){return this._store.getIndices()},e.prototype.getDataExtent=function(e){return this._store.getDataExtent(this._getStoreDimIndex(e),null)},e.prototype.getSum=function(e){return this._store.getSum(this._getStoreDimIndex(e))},e.prototype.getMedian=function(e){return this._store.getMedian(this._getStoreDimIndex(e))},e.prototype.getValues=function(e,t){var n=this,r=this._store;return me(e)?r.getValues(Xf(e,function(e){return n._getStoreDimIndex(e)}),t):r.getValues(e)},e.prototype.hasValue=function(e){for(var t=this._dimSummary.dataDimIndicesOnCoord,n=0,r=t.length;n<r;n++)if(isNaN(this._store.get(t[n],e)))return!1;return!0},e.prototype.indexOfName=function(e){for(var t=0,n=this._store.count();t<n;t++)if(this.getName(t)===e)return t;return-1},e.prototype.getRawIndex=function(e){return this._store.getRawIndex(e)},e.prototype.indexOfRawIndex=function(e){return this._store.indexOfRawIndex(e)},e.prototype.rawIndexOf=function(e,t){var n=e&&this._invertedIndicesMap[e],r=n&&n[t];return r==null||isNaN(r)?Zf:r},e.prototype.each=function(e,t,n){"use strict";he(e)&&(n=t,t=e,e=[]);var r=n||this,i=Xf(tp(e),this._getStoreDimIndex,this);this._store.each(i,r?fe(t,r):t)},e.prototype.filterSelf=function(e,t,n){"use strict";he(e)&&(n=t,t=e,e=[]);var r=n||this,i=Xf(tp(e),this._getStoreDimIndex,this);return this._store=this._store.filter(i,r?fe(t,r):t),this},e.prototype.selectRange=function(e){"use strict";var t=this,n={},r=ue(e),i=[];return z(r,function(r){var a=t._getStoreDimIndex(r);n[a]=e[r],i.push(a)}),this._store=this._store.selectRange(n),this},e.prototype.mapArray=function(e,t,n){"use strict";he(e)&&(n=t,t=e,e=[]),n||=this;var r=[];return this.each(e,function(){r.push(t&&t.apply(this,arguments))},n),r},e.prototype.map=function(e,t,n,r){"use strict";var i=n||r||this,a=Xf(tp(e),this._getStoreDimIndex,this),o=rp(this);return o._store=this._store.map(a,i?fe(t,i):t),o},e.prototype.modify=function(e,t,n,r){var i=n||r||this,a=Xf(tp(e),this._getStoreDimIndex,this);this._store.modify(a,i?fe(t,i):t)},e.prototype.downSample=function(e,t,n,r){var i=rp(this);return i._store=this._store.downSample(this._getStoreDimIndex(e),t,n,r),i},e.prototype.minmaxDownSample=function(e,t){var n=rp(this);return n._store=this._store.minmaxDownSample(this._getStoreDimIndex(e),t),n},e.prototype.lttbDownSample=function(e,t){var n=rp(this);return n._store=this._store.lttbDownSample(this._getStoreDimIndex(e),t),n},e.prototype.getRawDataItem=function(e){return this._store.getRawDataItem(e)},e.prototype.getItemModel=function(e){var t=this.hostModel;return new rf(this.getRawDataItem(e),t,t&&t.ecModel)},e.prototype.diff=function(e){var t=this;return new gte(e?e.getStore().getIndices():[],this.getStore().getIndices(),function(t){return $f(e,t)},function(e){return $f(t,e)})},e.prototype.getVisual=function(e){var t=this._visual;return t&&t[e]},e.prototype.setVisual=function(e,t){this._visual=this._visual||{},Yf(e)?R(this._visual,e):this._visual[e]=t},e.prototype.getItemVisual=function(e,t){var n=this._itemVisuals[e];return(n&&n[t])??this.getVisual(t)},e.prototype.hasItemVisual=function(){return this._itemVisuals.length>0},e.prototype.ensureUniqueItemVisual=function(e,t){var n=this._itemVisuals,r=n[e];r||=n[e]={};var i=r[t];return i??(i=this.getVisual(t),me(i)?i=i.slice():Yf(i)&&(i=R({},i)),r[t]=i),i},e.prototype.setItemVisual=function(e,t,n){var r=this._itemVisuals[e]||{};this._itemVisuals[e]=r,Yf(t)?R(r,t):r[t]=n},e.prototype.clearAllVisual=function(){this._visual={},this._itemVisuals=[]},e.prototype.setLayout=function(e,t){Yf(e)?R(this._layout,e):this._layout[e]=t},e.prototype.getLayout=function(e){return this._layout[e]},e.prototype.getItemLayout=function(e){return this._itemLayouts[e]},e.prototype.setItemLayout=function(e,t,n){this._itemLayouts[e]=n?R(this._itemLayouts[e]||{},t):t},e.prototype.clearItemLayouts=function(){this._itemLayouts.length=0},e.prototype.setItemGraphicEl=function(e,t){fc(this.hostModel&&this.hostModel.seriesIndex,this.dataType,e,t),this._graphicEls[e]=t},e.prototype.getItemGraphicEl=function(e){return this._graphicEls[e]},e.prototype.eachItemGraphicEl=function(e,t){z(this._graphicEls,function(n,r){n&&e&&e.call(t,n,r)})},e.prototype.cloneShallow=function(t){return t||=new e(this._schema?this._schema:Xf(this.dimensions,this._getDimInfo,this),this.hostModel),np(t,this),t._store=this._store,t},e.prototype.wrapMethod=function(e,t){var n=this[e];he(n)&&(this.__wrappedMethods=this.__wrappedMethods||[],this.__wrappedMethods.push(e),this[e]=function(){var e=n.apply(this,arguments);return t.apply(this,[e].concat(Oe(arguments)))})},e.internalField=function(){Qf=function(e){var t=e._invertedIndicesMap;z(t,function(n,r){var i=e._dimInfos[r],a=i.ordinalMeta,o=e._store;if(a){n=t[r]=new Vte(a.categories.length);for(var s=0;s<n.length;s++)n[s]=Zf;for(var s=0;s<o.count();s++)n[o.get(i.storeDimIndex,s)]=s}})},ep=function(e,t,n){return Ls(e._getCategory(t,n),null)},$f=function(e,t){var n=e._idList[t];return n==null&&e._idDimIdx!=null&&(n=ep(e,e._idDimIdx,t)),n??=Hte+t,n},tp=function(e){return me(e)||(e=e==null?[]:[e]),e},rp=function(t){var n=new e(t._schema?t._schema:Xf(t.dimensions,t._getDimInfo,t),t.hostModel);return np(n,t),n},np=function(e,t){z(Ute.concat(t.__wrappedMethods||[]),function(n){t.hasOwnProperty(n)&&(e[n]=t[n])}),e.__wrappedMethods=t.__wrappedMethods,z(Wte,function(n){e[n]=I(t[n])}),e._calculationInfo=R({},t._calculationInfo)},ip=function(e,t){var n=e._nameList,r=e._idList,i=e._nameDimIdx,a=e._idDimIdx,o=n[t],s=r[t];if(o==null&&i!=null&&(n[t]=o=ep(e,i,t)),s==null&&a!=null&&(r[t]=s=ep(e,a,t)),s==null&&o!=null){var l=e._nameRepeatCount,u=l[o]=(l[o]||0)+1;s=o,u>1&&(s+=`__ec__`+u),r[t]=s}}}(),e}();function op(e,t){mf(e)||(e=gf(e)),t||={};var n=t.coordDimensions||[],r=t.dimensionsDefine||e.dimensionsDefine||[],i=ze(),a=[],o=Gte(e,n,r,t.dimensionsCount),s=t.canOmitUnusedDimensions&&Bte(o),l=r===e.dimensionsDefine,u=l?zte(e):Jf(r),d=t.encodeDefine;!d&&t.encodeDefaulter&&(d=t.encodeDefaulter(e,o));for(var f=ze(d),p=new Lf(o),m=0;m<p.length;m++)p[m]=-1;function h(e){var t=p[e];if(t<0){var n=r[e],i=ye(n)?n:{name:n},o=new Mf,s=i.name;return s!=null&&u.get(s)!=null&&(o.name=o.displayName=s),i.type!=null&&(o.type=i.type),i.displayName!=null&&(o.displayName=i.displayName),p[e]=a.length,o.storeDimIndex=e,a.push(o),o}return a[t]}if(!s)for(var m=0;m<o;m++)h(m);f.each(function(e,t){var n=Cs(e).slice();if(n.length===1&&!ge(n[0])&&n[0]<0){f.set(t,!1);return}var r=f.set(t,[]);z(n,function(e,n){var i=ge(e)?u.get(e):e;i!=null&&i<o&&(r[n]=i,_(h(i),t,n))})});var g=0;z(n,function(e){var t,n,r,i;if(ge(e))t=e,i={};else{i=e,t=i.name;var a=i.ordinalMeta;i.ordinalMeta=null,i=R({},i),i.ordinalMeta=a,n=i.dimsDef,r=i.otherDims,i.name=i.coordDim=i.coordDimIndex=i.dimsDef=i.otherDims=null}var s=f.get(t);if(s!==!1){if(s=Cs(s),!s.length)for(var u=0;u<(n&&n.length||1);u++){for(;g<o&&h(g).coordDim!=null;)g++;g<o&&s.push(g++)}z(s,function(e,a){var o=h(e);if(l&&i.type!=null&&(o.type=i.type),_(te(o,i),t,a),o.name==null&&n){var s=n[a];!ye(s)&&(s={name:s}),o.name=o.displayName=s.name,o.defaultTooltip=s.defaultTooltip}r&&te(o.otherDims,r)})}});function _(e,t,n){pc.get(t)==null?(e.coordDim=t,e.coordDimIndex=n,i.set(t,!0)):e.otherDims[t]=n}var v=t.generateCoord,y=t.generateCoordCount,b=y!=null;y=v?y||1:0;var x=v||`value`;function S(e){e.name??=e.coordDim}if(s)z(a,function(e){S(e)}),a.sort(function(e,t){return e.storeDimIndex-t.storeDimIndex});else for(var C=0;C<o;C++){var w=h(C);w.coordDim??(w.coordDim=sp(x,i,b),w.coordDimIndex=0,(!v||y<=0)&&(w.isExtraCoord=!0),y--),S(w),w.type==null&&(ff(e,C)===sf.Must||w.isExtraCoord&&(w.otherDims.itemName!=null||w.otherDims.seriesName!=null))&&(w.type=`ordinal`)}return sc(a,function(e){return e.name},function(e,t){t>0&&(e.name+=t-1)}),new Kf({source:e,dimensions:a,fullDimensionCount:o,dimensionOmitted:s})}function Gte(e,t,n,r){var i=Math.max(e.dimensionsDetectedCount||1,t.length,n.length,r||0);return z(t,function(e){var t;ye(e)&&(t=e.dimsDef)&&(i=Math.max(i,t.length))}),i}function sp(e,t,n){if(n||t.hasKey(e)){for(var r=0;t.hasKey(e+r);)r++;e+=r}return t.set(e,!0),e}var cp={},lp={},up=function(){function e(){this._normalMasterList=[],this._nonSeriesBoxMasterList=[]}return e.prototype.create=function(e,t){this._nonSeriesBoxMasterList=n(cp,!0),this._normalMasterList=n(lp,!1);function n(n,r){var i=[];return z(n,function(n,r){var a=n.create(e,t);i=i.concat(a||[])}),i}},e.prototype.update=function(e,t){z(this._normalMasterList,function(n){n.update&&n.update(e,t)})},e.prototype.getCoordinateSystems=function(){return this._normalMasterList.concat(this._nonSeriesBoxMasterList)},e.register=function(e,t){if(e===`matrix`||e===`calendar`){cp[e]=t;return}lp[e]=t},e.get=function(e){return lp[e]||cp[e]},e}();function dp(e){return!!cp[e]}function fp(e){pp.set(e.fullType,{getCoord2:void 0}).getCoord2=e.getCoord2}var pp=ze();function mp(e){var t=e.getShallow(`coord`,!0),n=1;if(t==null){var r=pp.get(e.type);r&&r.getCoord2&&(n=2,t=r.getCoord2(e))}return{coord:t,from:n}}function hp(e,t){var n=e.getShallow(`coordinateSystem`),r=e.getShallow(`coordinateSystemUsage`,!0),i=0;if(n){var a=e.mainType===`series`;r??=a?`data`:`box`,r===`data`?(i=1,a||(i=0)):r===`box`&&(i=2,!a&&!dp(n)&&(i=0))}return{coordSysType:n,kind:i}}function gp(e){var t=e.targetModel,n=e.coordSysType,r=e.coordSysProvider,i=e.isDefaultDataCoordSys;e.allowNotFound;var a=hp(t,!0),o=a.kind,s=a.coordSysType;if(i&&o!==1&&(o=1,s=n),o===0||s!==n)return 0;var l=r(n,t);return l?(o===1?t.coordinateSystem=l:t.boxCoordinateSystem=l,o):0}var _p=function(){function e(e){this.coordSysDims=[],this.axisMap=ze(),this.categoryAxisMap=ze(),this.coordSysName=e}return e}();function Kte(e){var t=e.get(`coordinateSystem`),n=new _p(t),r=vp[t];if(r)return r(e,n,n.axisMap,n.categoryAxisMap),n}var vp={cartesian2d:function(e,t,n,r){var i=e.getReferringComponents(`xAxis`,Ks).models[0],a=e.getReferringComponents(`yAxis`,Ks).models[0];t.coordSysDims=[`x`,`y`],n.set(`x`,i),n.set(`y`,a),yp(i)&&(r.set(`x`,i),t.firstCategoryDimIndex=0),yp(a)&&(r.set(`y`,a),t.firstCategoryDimIndex??=1)},singleAxis:function(e,t,n,r){var i=e.getReferringComponents(`singleAxis`,Ks).models[0];t.coordSysDims=[`single`],n.set(`single`,i),yp(i)&&(r.set(`single`,i),t.firstCategoryDimIndex=0)},polar:function(e,t,n,r){var i=e.getReferringComponents(`polar`,Ks).models[0],a=i.findAxisModel(`radiusAxis`),o=i.findAxisModel(`angleAxis`);t.coordSysDims=[`radius`,`angle`],n.set(`radius`,a),n.set(`angle`,o),yp(a)&&(r.set(`radius`,a),t.firstCategoryDimIndex=0),yp(o)&&(r.set(`angle`,o),t.firstCategoryDimIndex??=1)},geo:function(e,t,n,r){t.coordSysDims=[`lng`,`lat`]},parallel:function(e,t,n,r){var i=e.ecModel,a=i.getComponent(`parallel`,e.get(`parallelIndex`)),o=t.coordSysDims=a.dimensions.slice();z(a.parallelAxisIndex,function(e,a){var s=i.getComponent(`parallelAxis`,e),l=o[a];n.set(l,s),yp(s)&&(r.set(l,s),t.firstCategoryDimIndex??=a)})},matrix:function(e,t,n,r){var i=e.getReferringComponents(`matrix`,Ks).models[0];t.coordSysDims=[`x`,`y`];var a=i.getDimensionModel(`x`),o=i.getDimensionModel(`y`);n.set(`x`,a),n.set(`y`,o),r.set(`x`,a),r.set(`y`,o)}};function yp(e){return e.get(`type`)===`category`}function bp(e,t,n){n||={};var r=n.byIndex,i=n.stackedCoordDimension,a,o,s;xp(t)?a=t:(o=t.schema,a=o.dimensions,s=t.store);var l=!!(e&&e.get(`stack`)),u,d,f,p,m=!0;function h(e){return e.type!==`ordinal`&&e.type!==`time`}if(z(a,function(e,t){ge(e)&&(a[t]=e={name:e}),h(e)||(m=!1)}),z(a,function(e,t){l&&!e.isExtraCoord&&(!r&&!u&&e.ordinalMeta&&(u=e),!d&&h(e)&&(!m||e.coordDim!==`x`&&e.coordDim!==`angle`)&&(!i||i===e.coordDim)&&(d=e))}),d&&!r&&!u&&(r=!0),d){f=`__\0ecstackresult_`+e.id,p=`__\0ecstackedover_`+e.id,u&&(u.createInvertedIndices=!0);var g=d.coordDim,_=d.type,v=0;z(a,function(e){e.coordDim===g&&v++});var y={name:f,coordDim:g,coordDimIndex:v,type:_,isExtraCoord:!0,isCalculationCoord:!0,storeDimIndex:a.length},b={name:p,coordDim:p,coordDimIndex:v+1,type:_,isExtraCoord:!0,isCalculationCoord:!0,storeDimIndex:a.length+1};o?(s&&(y.storeDimIndex=s.ensureCalculationDimension(p,_),b.storeDimIndex=s.ensureCalculationDimension(f,_)),o.appendCalculationDimension(y),o.appendCalculationDimension(b)):(a.push(y),a.push(b))}return{stackedDimension:d&&d.name,stackedByDimension:u&&u.name,isStackedByIndex:r,stackedOverDimension:p,stackResultDimension:f}}function xp(e){return!qf(e.schema)}function Sp(e,t){return!!t&&t===e.getCalculationInfo(`stackedDimension`)}function Cp(e,t){return Sp(e,t)?e.getCalculationInfo(`stackResultDimension`):t}function wp(e,t){var n=e.get(`coordinateSystem`),r=up.get(n),i;return t&&t.coordSysDims&&(i=oe(t.coordSysDims,function(e){var n={name:e},r=t.axisMap.get(e);return r&&(n.type=Pte(r.get(`type`))),n})),i||=r&&(r.getDimensionsInfo?r.getDimensionsInfo():r.dimensions.slice())||[`x`,`y`],i}function qte(e,t,n){var r,i;return n&&z(e,function(e,a){var o=e.coordDim,s=n.categoryAxisMap.get(o);s&&(r??=a,e.ordinalMeta=s.getOrdinalMeta(),t&&(e.createInvertedIndices=!0)),e.otherDims.itemName!=null&&(i=!0)}),!i&&r!=null&&(e[r].otherDims.itemName=0),r}function Tp(e,t,n){n||={};var r=t.getSourceManager(),i,a=!1;e?(a=!0,i=gf(e)):(i=r.getSource(),a=i.sourceFormat===mc);var o=Kte(t),s=wp(t,o),l=n.useEncodeDefaulter,u=he(l)?l:l?pe(_te,s,t):null,d={coordDimensions:s,generateCoord:n.generateCoord,encodeDefine:t.getEncode(),encodeDefaulter:u,canOmitUnusedDimensions:!a},f=op(i,d),p=qte(f.dimensions,n.createInvertedIndices,o),m=a?null:r.getSharedDataStore(f),h=bp(t,{schema:f,store:m}),g=new ap(f,t);g.setCalculationInfo(h);var _=p!=null&&Jte(i)?function(e,t,n,r){return r===p?n:this.defaultDimValueGetter(e,t,n,r)}:null;return g.hasItemOption=!1,g.initData(a?i:m,null,_),g}function Jte(e){if(e.sourceFormat===`original`)return!me(Es(Yte(e.data||[])))}function Yte(e){for(var t=0;t<e.length&&e[t]==null;)t++;return e[t]}var Xte=Math.round(Math.random()*10);function Ep(e){return[e||``,Xte++].join(`_`)}function Zte(e){var t={};e.registerSubTypeDefaulter=function(e,n){var r=Ze(e);t[r.main]=n},e.determineSubType=function(n,r){var i=r.type;if(!i){var a=Ze(n).main;e.hasSubTypes(n)&&t[a]&&(i=t[a](r))}return i}}function Dp(e,t){e.topologicalTravel=function(e,t,r,i){if(!e.length)return;var a=n(t),o=a.graph,s=a.noEntryList,l={};for(z(e,function(e){l[e]=!0});s.length;){var u=s.pop(),d=o[u],f=!!l[u];f&&(r.call(i,u,d.originalDeps.slice()),delete l[u]),z(d.successor,f?m:p)}z(l,function(){throw Error(``)});function p(e){o[e].entryCount--,o[e].entryCount===0&&s.push(e)}function m(e){l[e]=!0,p(e)}};function n(e){var n={},a=[];return z(e,function(o){var s=r(n,o),l=i(s.originalDeps=t(o),e);s.entryCount=l.length,s.entryCount===0&&a.push(o),z(l,function(e){ne(s.predecessor,e)<0&&s.predecessor.push(e);var t=r(n,e);ne(t.successor,e)<0&&t.successor.push(o)})}),{graph:n,noEntryList:a}}function r(e,t){return e[t]||(e[t]={predecessor:[],successor:[]}),e[t]}function i(e,t){var n=[];return z(e,function(e){ne(t,e)>=0&&n.push(e)}),n}}function Op(e,t){return L(L({},e,!0),t,!0)}var Qte=Math.log(2);function kp(e,t,n,r,i,a){var o=r+`-`+i,s=e.length;if(a.hasOwnProperty(o))return a[o];if(t===1){var l=Math.round(Math.log((1<<s)-1&~i)/Qte);return e[n][l]}for(var u=r|1<<n,d=n+1;r&1<<d;)d++;for(var f=0,p=0,m=0;p<s;p++){var h=1<<p;h&i||(f+=(m%2?-1:1)*e[n][p]*kp(e,t-1,d,u,i|h,a),m++)}return a[o]=f,f}function $te(e,t){var n=[[e[0],e[1],1,0,0,0,-t[0]*e[0],-t[0]*e[1]],[0,0,0,e[0],e[1],1,-t[1]*e[0],-t[1]*e[1]],[e[2],e[3],1,0,0,0,-t[2]*e[2],-t[2]*e[3]],[0,0,0,e[2],e[3],1,-t[3]*e[2],-t[3]*e[3]],[e[4],e[5],1,0,0,0,-t[4]*e[4],-t[4]*e[5]],[0,0,0,e[4],e[5],1,-t[5]*e[4],-t[5]*e[5]],[e[6],e[7],1,0,0,0,-t[6]*e[6],-t[6]*e[7]],[0,0,0,e[6],e[7],1,-t[7]*e[6],-t[7]*e[7]]],r={},i=kp(n,8,0,0,0,r);if(i!==0){for(var a=[],o=0;o<8;o++)for(var s=0;s<8;s++)a[s]??(a[s]=0),a[s]+=((o+s)%2?-1:1)*kp(n,7,+(o===0),1<<o,1<<s,r)/i*t[o];return function(e,t,n){var r=t*a[6]+n*a[7]+1;e[0]=(t*a[0]+n*a[1]+a[2])/r,e[1]=(t*a[3]+n*a[4]+a[5])/r}}}var ene=`___zrEVENTSAVED`;function Ap(e,t,n,r,i){if(t.getBoundingClientRect&&Ke.domSupported&&!Np(t)){var a=t[ene]||(t[ene]={}),o=Mp(jp(t,a),a,i);if(o)return o(e,n,r),!0}return!1}function jp(e,t){var n=t.markers;if(n)return n;n=t.markers=[];for(var r=[`left`,`right`],i=[`top`,`bottom`],a=0;a<4;a++){var o=document.createElement(`div`),s=o.style,l=a%2,u=(a>>1)%2;s.cssText=[`position: absolute`,`visibility: hidden`,`padding: 0`,`margin: 0`,`border-width: 0`,`user-select: none`,`width:0`,`height:0`,r[l]+`:0`,i[u]+`:0`,r[1-l]+`:auto`,i[1-u]+`:auto`,``].join(`!important;`),e.appendChild(o),n.push(o)}return t.clearMarkers=function(){z(n,function(e){e.parentNode&&e.parentNode.removeChild(e)})},n}function Mp(e,t,n){for(var r=n?`invTrans`:`trans`,i=t[r],a=t.srcCoords,o=[],s=[],l=!0,u=0;u<4;u++){var d=e[u].getBoundingClientRect(),f=2*u,p=d.left,m=d.top;o.push(p,m),l=l&&a&&p===a[f]&&m===a[f+1],s.push(e[u].offsetLeft,e[u].offsetTop)}return l&&i?i:(t.srcCoords=o,t[r]=n?$te(s,o):$te(o,s))}function Np(e){return e.nodeName.toUpperCase()===`CANVAS`}var tne=/([&<>"'])/g,Pp={"&":`&amp;`,"<":`&lt;`,">":`&gt;`,'"':`&quot;`,"'":`&#39;`};function Fp(e){return e==null?``:(e+``).replace(tne,function(e,t){return Pp[t]})}var Ip={time:{month:[`January`,`February`,`March`,`April`,`May`,`June`,`July`,`August`,`September`,`October`,`November`,`December`],monthAbbr:[`Jan`,`Feb`,`Mar`,`Apr`,`May`,`Jun`,`Jul`,`Aug`,`Sep`,`Oct`,`Nov`,`Dec`],dayOfWeek:[`Sunday`,`Monday`,`Tuesday`,`Wednesday`,`Thursday`,`Friday`,`Saturday`],dayOfWeekAbbr:[`Sun`,`Mon`,`Tue`,`Wed`,`Thu`,`Fri`,`Sat`]},legend:{selector:{all:`All`,inverse:`Inv`}},toolbox:{brush:{title:{rect:`Box Select`,polygon:`Lasso Select`,lineX:`Horizontally Select`,lineY:`Vertically Select`,keep:`Keep Selections`,clear:`Clear Selections`}},dataView:{title:`Data View`,lang:[`Data View`,`Close`,`Refresh`]},dataZoom:{title:{zoom:`Zoom`,back:`Zoom Reset`}},magicType:{title:{line:`Switch to Line Chart`,bar:`Switch to Bar Chart`,stack:`Stack`,tiled:`Tile`}},restore:{title:`Restore`},saveAsImage:{title:`Save as Image`,lang:[`Right Click to Save Image`]}},series:{typeNames:{pie:`Pie chart`,bar:`Bar chart`,line:`Line chart`,scatter:`Scatter plot`,effectScatter:`Ripple scatter plot`,radar:`Radar chart`,tree:`Tree`,treemap:`Treemap`,boxplot:`Boxplot`,candlestick:`Candlestick`,k:`K line chart`,heatmap:`Heat map`,map:`Map`,parallel:`Parallel coordinate map`,lines:`Line graph`,graph:`Relationship graph`,sankey:`Sankey diagram`,funnel:`Funnel chart`,gauge:`Gauge`,pictorialBar:`Pictorial bar`,themeRiver:`Theme River Map`,sunburst:`Sunburst`,custom:`Custom chart`,chart:`Chart`}},aria:{general:{withTitle:`This is a chart about "{title}"`,withoutTitle:`This is a chart`},series:{single:{prefix:``,withName:` with type {seriesType} named {seriesName}.`,withoutName:` with type {seriesType}.`},multiple:{prefix:`. It consists of {seriesCount} series count.`,withName:` The {seriesId} series is a {seriesType} representing {seriesName}.`,withoutName:` The {seriesId} series is a {seriesType}.`,separator:{middle:``,end:``}}},data:{allData:`The data is as follows: `,partialData:`The first {displayCnt} items are: `,withName:`the data for {name} is {value}`,withoutName:`{value}`,separator:{middle:`, `,end:`. `}}}},Lp={time:{month:[`ä¸€æœˆ`,`äºŒæœˆ`,`ä¸‰æœˆ`,`å››æœˆ`,`äº”æœˆ`,`å…­æœˆ`,`ä¸ƒæœˆ`,`å…«æœˆ`,`ä¹æœˆ`,`åæœˆ`,`åä¸€æœˆ`,`åäºŒæœˆ`],monthAbbr:[`1æœˆ`,`2æœˆ`,`3æœˆ`,`4æœˆ`,`5æœˆ`,`6æœˆ`,`7æœˆ`,`8æœˆ`,`9æœˆ`,`10æœˆ`,`11æœˆ`,`12æœˆ`],dayOfWeek:[`æ˜ŸæœŸæ—¥`,`æ˜ŸæœŸä¸€`,`æ˜ŸæœŸäºŒ`,`æ˜ŸæœŸä¸‰`,`æ˜ŸæœŸå››`,`æ˜ŸæœŸäº”`,`æ˜ŸæœŸå…­`],dayOfWeekAbbr:[`æ—¥`,`ä¸€`,`äºŒ`,`ä¸‰`,`å››`,`äº”`,`å…­`]},legend:{selector:{all:`å…¨é€‰`,inverse:`åé€‰`}},toolbox:{brush:{title:{rect:`çŸ©å½¢é€‰æ‹©`,polygon:`åœˆé€‰`,lineX:`æ¨ªå‘é€‰æ‹©`,lineY:`çºµå‘é€‰æ‹©`,keep:`ä¿æŒé€‰æ‹©`,clear:`æ¸…é™¤é€‰æ‹©`}},dataView:{title:`æ•°æ®è§†å›¾`,lang:[`æ•°æ®è§†å›¾`,`å…³é—­`,`åˆ·æ–°`]},dataZoom:{title:{zoom:`åŒºåŸŸç¼©æ”¾`,back:`åŒºåŸŸç¼©æ”¾è¿˜åŽŸ`}},magicType:{title:{line:`åˆ‡æ¢ä¸ºæŠ˜çº¿å›¾`,bar:`åˆ‡æ¢ä¸ºæŸ±çŠ¶å›¾`,stack:`åˆ‡æ¢ä¸ºå †å `,tiled:`åˆ‡æ¢ä¸ºå¹³é“º`}},restore:{title:`è¿˜åŽŸ`},saveAsImage:{title:`ä¿å­˜ä¸ºå›¾ç‰‡`,lang:[`å³é”®å¦å­˜ä¸ºå›¾ç‰‡`]}},series:{typeNames:{pie:`é¥¼å›¾`,bar:`æŸ±çŠ¶å›¾`,line:`æŠ˜çº¿å›¾`,scatter:`æ•£ç‚¹å›¾`,effectScatter:`æ¶Ÿæ¼ªæ•£ç‚¹å›¾`,radar:`é›·è¾¾å›¾`,tree:`æ ‘å›¾`,treemap:`çŸ©å½¢æ ‘å›¾`,boxplot:`ç®±åž‹å›¾`,candlestick:`Kçº¿å›¾`,k:`Kçº¿å›¾`,heatmap:`çƒ­åŠ›å›¾`,map:`åœ°å›¾`,parallel:`å¹³è¡Œåæ ‡å›¾`,lines:`çº¿å›¾`,graph:`å…³ç³»å›¾`,sankey:`æ¡‘åŸºå›¾`,funnel:`æ¼æ–—å›¾`,gauge:`ä»ªè¡¨ç›˜å›¾`,pictorialBar:`è±¡å½¢æŸ±å›¾`,themeRiver:`ä¸»é¢˜æ²³æµå›¾`,sunburst:`æ—­æ—¥å›¾`,custom:`è‡ªå®šä¹‰å›¾è¡¨`,chart:`å›¾è¡¨`}},aria:{general:{withTitle:`è¿™æ˜¯ä¸€ä¸ªå…³äºŽâ€œ{title}â€çš„å›¾è¡¨ã€‚`,withoutTitle:`è¿™æ˜¯ä¸€ä¸ªå›¾è¡¨ï¼Œ`},series:{single:{prefix:``,withName:`å›¾è¡¨ç±»åž‹æ˜¯{seriesType}ï¼Œè¡¨ç¤º{seriesName}ã€‚`,withoutName:`å›¾è¡¨ç±»åž‹æ˜¯{seriesType}ã€‚`},multiple:{prefix:`å®ƒç”±{seriesCount}ä¸ªå›¾è¡¨ç³»åˆ—ç»„æˆã€‚`,withName:`ç¬¬{seriesId}ä¸ªç³»åˆ—æ˜¯ä¸€ä¸ªè¡¨ç¤º{seriesName}çš„{seriesType}ï¼Œ`,withoutName:`ç¬¬{seriesId}ä¸ªç³»åˆ—æ˜¯ä¸€ä¸ª{seriesType}ï¼Œ`,separator:{middle:`ï¼›`,end:`ã€‚`}}},data:{allData:`å…¶æ•°æ®æ˜¯â€”â€”`,partialData:`å…¶ä¸­ï¼Œå‰{displayCnt}é¡¹æ˜¯â€”â€”`,withName:`{name}çš„æ•°æ®æ˜¯{value}`,withoutName:`{value}`,separator:{middle:`ï¼Œ`,end:``}}}},Rp=`ZH`,zp=`EN`,Bp=zp,Vp={},Hp={},Up=Ke.domSupported?function(){return(document.documentElement.lang||navigator.language||navigator.browserLanguage||Bp).toUpperCase().indexOf(Rp)>-1?Rp:Bp}():Bp;function Wp(e,t){e=e.toUpperCase(),Hp[e]=new rf(t),Vp[e]=t}function Gp(e){if(ge(e)){var t=Vp[e.toUpperCase()]||{};return e===Rp||e===zp?I(t):L(I(t),I(Vp[Bp]),!1)}else return L(I(e),I(Vp[Bp]),!1)}function Kp(e){return Hp[e]}function qp(){return Hp[Bp]}Wp(zp,Ip),Wp(Rp,Lp);var nne=null;function Jp(){return nne}function Yp(e,t){var n=Jp(),r=t.breakOption,i=t.breakParsed;return!i&&n&&(i=n.parseAxisBreakOption(r,e)),i}function Xp(e){var t=e.brk;return t?t.breaks:[]}function Zp(e){var t=e.brk;return t?t.hasBreaks():!1}var Qp=1e3,$p=Qp*60,em=$p*60,tm=em*24,nm=tm*365,rm={year:/({yyyy}|{yy})/,month:/({MMMM}|{MMM}|{MM}|{M})/,day:/({dd}|{d})/,hour:/({HH}|{H}|{hh}|{h})/,minute:/({mm}|{m})/,second:/({ss}|{s})/,millisecond:/({SSS}|{S})/},im={year:`{yyyy}`,month:`{MMM}`,day:`{d}`,hour:`{HH}:{mm}`,minute:`{HH}:{mm}`,second:`{HH}:{mm}:{ss}`,millisecond:`{HH}:{mm}:{ss} {SSS}`},rne=`{yyyy}-{MM}-{dd} {HH}:{mm}:{ss} {SSS}`,am=`{yyyy}-{MM}-{dd}`,ine={year:`{yyyy}`,month:`{yyyy}-{MM}`,day:am,hour:am+` `+im.hour,minute:am+` `+im.minute,second:am+` `+im.second,millisecond:rne},om=[`year`,`month`,`day`,`hour`,`minute`,`second`,`millisecond`],ane=[`year`,`half-year`,`quarter`,`month`,`week`,`half-week`,`day`,`half-day`,`quarter-day`,`hour`,`minute`,`second`,`millisecond`];function one(e){return!ge(e)&&!he(e)?sne(e):e}function sne(e){e||={};var t={},n=!0;return z(om,function(t){n&&=e[t]==null}),z(om,function(r,i){var a=e[r];t[r]={};for(var o=null,s=i;s>=0;s--){var l=om[s],u=ye(a)&&!me(a)?a[l]:a,d=void 0;me(u)?(d=u.slice(),o=d[0]||``):ge(u)?(o=u,d=[o]):(o==null?o=im[r]:rm[l].test(o)||(o=t[l][l][0]+` `+o),d=[o],n&&(d[1]=`{primary|`+o+`}`)),t[r][l]=d}}),t}function sm(e,t){return e+=``,`0000`.substr(0,t-e.length)+e}function cm(e){switch(e){case`half-year`:case`quarter`:return`month`;case`week`:case`half-week`:return`day`;case`half-day`:case`quarter-day`:return`hour`;default:return e}}function cne(e){return e===cm(e)}function lne(e){switch(e){case`year`:case`month`:return`day`;case`millisecond`:return`millisecond`;default:return`second`}}function une(e,t,n,r){var i=ss(e),a=i[fne(n)](),o=i[dm(n)]()+1,s=Math.floor((o-1)/3)+1,l=i[fm(n)](),u=i[`get`+(n?`UTC`:``)+`Day`](),d=i[pm(n)](),f=(d-1)%12+1,p=i[mm(n)](),m=i[hm(n)](),h=i[pne(n)](),g=d>=12?`pm`:`am`,_=g.toUpperCase(),v=(r instanceof rf?r:Kp(r||Up)||qp()).getModel(`time`),y=v.get(`month`),b=v.get(`monthAbbr`),x=v.get(`dayOfWeek`),S=v.get(`dayOfWeekAbbr`);return(t||``).replace(/{a}/g,g+``).replace(/{A}/g,_+``).replace(/{yyyy}/g,a+``).replace(/{yy}/g,sm(a%100+``,2)).replace(/{Q}/g,s+``).replace(/{MMMM}/g,y[o-1]).replace(/{MMM}/g,b[o-1]).replace(/{MM}/g,sm(o,2)).replace(/{M}/g,o+``).replace(/{dd}/g,sm(l,2)).replace(/{d}/g,l+``).replace(/{eeee}/g,x[u]).replace(/{ee}/g,S[u]).replace(/{e}/g,u+``).replace(/{HH}/g,sm(d,2)).replace(/{H}/g,d+``).replace(/{hh}/g,sm(f+``,2)).replace(/{h}/g,f+``).replace(/{mm}/g,sm(p,2)).replace(/{m}/g,p+``).replace(/{ss}/g,sm(m,2)).replace(/{s}/g,m+``).replace(/{SSS}/g,sm(h,3)).replace(/{S}/g,h+``)}function dne(e,t,n,r,i){var a=null;if(ge(n))a=n;else if(he(n)){var o={time:e.time,level:e.time?e.time.level:0},s=Jp();s&&s.makeAxisLabelFormatterParamBreak(o,e.break),a=n(e.value,t,o)}else{var l=e.time;if(l){var u=n[l.lowerTimeUnit][l.upperTimeUnit];a=u[Math.min(l.level,u.length-1)]||``}else{var d=lm(e.value,i);a=n[d][d][0]}}return une(new Date(e.value),a,i,r)}function lm(e,t){var n=ss(e),r=n[dm(t)]()+1,i=n[fm(t)](),a=n[pm(t)](),o=n[mm(t)](),s=n[hm(t)](),l=n[pne(t)]()===0,u=l&&s===0,d=u&&o===0,f=d&&a===0,p=f&&i===1;return p&&r===1?`year`:p?`month`:f?`day`:d?`hour`:u?`minute`:l?`second`:`millisecond`}function um(e,t,n){switch(t){case`year`:e[hne(n)](0);case`month`:e[gne(n)](1);case`day`:e[_ne(n)](0);case`hour`:e[vne(n)](0);case`minute`:e[yne(n)](0);case`second`:e[bne(n)](0)}return e}function fne(e){return e?`getUTCFullYear`:`getFullYear`}function dm(e){return e?`getUTCMonth`:`getMonth`}function fm(e){return e?`getUTCDate`:`getDate`}function pm(e){return e?`getUTCHours`:`getHours`}function mm(e){return e?`getUTCMinutes`:`getMinutes`}function hm(e){return e?`getUTCSeconds`:`getSeconds`}function pne(e){return e?`getUTCMilliseconds`:`getMilliseconds`}function mne(e){return e?`setUTCFullYear`:`setFullYear`}function hne(e){return e?`setUTCMonth`:`setMonth`}function gne(e){return e?`setUTCDate`:`setDate`}function _ne(e){return e?`setUTCHours`:`setHours`}function vne(e){return e?`setUTCMinutes`:`setMinutes`}function yne(e){return e?`setUTCSeconds`:`setSeconds`}function bne(e){return e?`setUTCMilliseconds`:`setMilliseconds`}function xne(e){if(!fs(e))return ge(e)?e:`-`;var t=(e+``).split(`.`);return t[0].replace(/(\d{1,3})(?=(?:\d{3})+(?!\d))/g,`$1,`)+(t.length>1?`.`+t[1]:``)}var Sne=ke,Cne=[`a`,`b`,`c`,`d`,`e`,`f`,`g`],wne=function(e,t){return`{`+e+(t??``)+`}`};function Tne(e,t,n){me(t)||(t=[t]);var r=t.length;if(!r)return``;for(var i=t[0].$vars||[],a=0;a<i.length;a++){var o=Cne[a];e=e.replace(wne(o),wne(o,0))}for(var s=0;s<r;s++)for(var l=0;l<i.length;l++){var u=t[s][i[l]];e=e.replace(wne(Cne[l],s),n?Fp(u):u)}return e}function Ene(e,t){var n=ge(e)?{color:e,extraCssText:t}:e||{},r=n.color,i=n.type;t=n.extraCssText;var a=n.renderMode||`html`;return r?a===`html`?i===`subItem`?`<span style="display:inline-block;vertical-align:middle;margin-right:8px;margin-left:3px;border-radius:4px;width:4px;height:4px;background-color:`+Fp(r)+`;`+(t||``)+`"></span>`:`<span style="display:inline-block;margin-right:4px;border-radius:10px;width:10px;height:10px;background-color:`+Fp(r)+`;`+(t||``)+`"></span>`:{renderMode:a,content:`{`+(n.markerId||`markerX`)+`|}  `,style:i===`subItem`?{width:4,height:4,borderRadius:2,backgroundColor:r}:{width:10,height:10,borderRadius:5,backgroundColor:r}}:``}function Dne(e,t){return t||=`transparent`,ge(e)?e:ye(e)&&e.colorStops&&(e.colorStops[0]||{}).color||t}var gm=z,One=[`left`,`right`,`top`,`bottom`,`width`,`height`],_m=[[`width`,`left`,`right`],[`height`,`top`,`bottom`]];function kne(e,t,n,r,i){var a=0,o=0;r??=1/0,i??=1/0;var s=0;t.eachChild(function(l,u){var d=l.getBoundingRect(),f=t.childAt(u+1),p=f&&f.getBoundingRect(),m,h;if(e===`horizontal`){var g=d.width+(p?-p.x+d.x:0);m=a+g,m>r||l.newline?(a=0,m=g,o+=s+n,s=d.height):s=Math.max(s,d.height)}else{var _=d.height+(p?-p.y+d.y:0);h=o+_,h>i||l.newline?(a+=s+n,o=0,h=_,s=d.width):s=Math.max(s,d.width)}l.newline||(l.x=a,l.y=o,l.markRedraw(),e===`horizontal`?a=m+n:o=h+n)})}var vm=kne;pe(kne,`vertical`),pe(kne,`horizontal`);function Ane(e,t){return{left:e.getShallow(`left`,t),top:e.getShallow(`top`,t),right:e.getShallow(`right`,t),bottom:e.getShallow(`bottom`,t),width:e.getShallow(`width`,t),height:e.getShallow(`height`,t)}}function jne(e,t){var n=Nne(e,t,{enableLayoutOnlyByCenter:!0}),r=e.getBoxLayoutParams(),i,a;if(n.type===bm.point)a=n.refPoint,i=ym(r,{width:t.getWidth(),height:t.getHeight()});else{var o=e.get(`center`),s=me(o)?o:[o,o];i=ym(r,n.refContainer),a=n.boxCoordFrom===2?n.refPoint:[Zo(s[0],i.width)+i.x,Zo(s[1],i.height)+i.y]}return{viewRect:i,center:a}}function Mne(e,t){var n=jne(e,t),r=n.viewRect,i=n.center,a=e.get(`radius`);me(a)||(a=[0,a]);var o=Zo(r.width,t.getWidth()),s=Zo(r.height,t.getHeight()),l=Math.min(o,s),u=Zo(a[0],l/2),d=Zo(a[1],l/2);return{cx:i[0],cy:i[1],r0:u,r:d,viewRect:r}}function ym(e,t,n){n=Sne(n||0);var r=t.width,i=t.height,a=Zo(e.left,r),o=Zo(e.top,i),s=Zo(e.right,r),l=Zo(e.bottom,i),u=Zo(e.width,r),d=Zo(e.height,i),f=n[2]+n[0],p=n[1]+n[3],m=e.aspect;switch(isNaN(u)&&(u=r-s-p-a),isNaN(d)&&(d=i-l-f-o),m!=null&&(isNaN(u)&&isNaN(d)&&(m>r/i?u=r*.8:d=i*.8),isNaN(u)&&(u=m*d),isNaN(d)&&(d=u/m)),isNaN(a)&&(a=r-s-u-p),isNaN(o)&&(o=i-l-d-f),e.left||e.right){case`center`:a=r/2-u/2-n[3];break;case`right`:a=r-u-p;break}switch(e.top||e.bottom){case`middle`:case`center`:o=i/2-d/2-n[0];break;case`bottom`:o=i-d-f;break}a||=0,o||=0,isNaN(u)&&(u=r-p-a-(s||0)),isNaN(d)&&(d=i-f-o-(l||0));var h=new an((t.x||0)+a+n[3],(t.y||0)+o+n[0],u,d);return h.margin=n,h}var bm={rect:1,point:2};function Nne(e,t,n){var r,i,a,o=e.boxCoordinateSystem,s;if(o){var l=mp(e),u=l.coord,d=l.from;if(o.dataToLayout){a=bm.rect,s=d;var f=o.dataToLayout(u);r=f.contentRect||f.rect}else n&&n.enableLayoutOnlyByCenter&&o.dataToPoint&&(a=bm.point,s=d,i=o.dataToPoint(u))}return a??=bm.rect,a===bm.rect&&(r||={x:0,y:0,width:t.getWidth(),height:t.getHeight()},i=[r.x+r.width/2,r.y+r.height/2]),{type:a,refContainer:r,refPoint:i,boxCoordFrom:s}}function xm(e){var t=e.layoutMode||e.constructor.layoutMode;return ye(t)?t:t?{type:t}:null}function Sm(e,t,n){var r=n&&n.ignoreSize;!me(r)&&(r=[r,r]);var i=o(_m[0],0),a=o(_m[1],1);l(_m[0],e,i),l(_m[1],e,a);function o(n,i){var a={},o=0,l={},u=0,d=2;if(gm(n,function(t){l[t]=e[t]}),gm(n,function(e){He(t,e)&&(a[e]=l[e]=t[e]),s(a,e)&&o++,s(l,e)&&u++}),r[i])return s(t,n[1])?l[n[2]]=null:s(t,n[2])&&(l[n[1]]=null),l;if(u===d||!o)return l;if(o>=d)return a;for(var f=0;f<n.length;f++){var p=n[f];if(!He(a,p)&&He(e,p)){a[p]=e[p];break}}return a}function s(e,t){return e[t]!=null&&e[t]!==`auto`}function l(e,t,n){gm(e,function(e){t[e]=n[e]})}}function Cm(e){return Pne({},e)}function Pne(e,t){return t&&e&&gm(One,function(n){He(t,n)&&(e[n]=t[n])}),e}var Fne=Us(),wm=function(e){p(t,e);function t(t,n,r){var i=e.call(this,t,n,r)||this;return i.uid=Ep(`ec_cpt_model`),i}return t.prototype.init=function(e,t,n){this.mergeDefaultAndTheme(e,n)},t.prototype.mergeDefaultAndTheme=function(e,t){var n=xm(this),r=n?Cm(e):{};L(e,t.getTheme().get(this.mainType)),L(e,this.getDefaultOption()),n&&Sm(e,r,n)},t.prototype.mergeOption=function(e,t){L(this.option,e,!0);var n=xm(this);n&&Sm(this.option,e,n)},t.prototype.optionUpdated=function(e,t){},t.prototype.getDefaultOption=function(){var e=this.constructor;if(!$e(e))return e.defaultOption;var t=Fne(this);if(!t.defaultOption){for(var n=[],r=e;r;){var i=r.prototype.defaultOption;i&&n.push(i),r=r.superClass}for(var a={},o=n.length-1;o>=0;o--)a=L(a,n[o],!0);t.defaultOption=a}return t.defaultOption},t.prototype.getReferringComponents=function(e,t){var n=e+`Index`,r=e+`Id`;return qs(this.ecModel,e,{index:this.get(n,!0),id:this.get(r,!0)},t)},t.prototype.getBoxLayoutParams=function(){return Ane(this,!1)},t.prototype.getZLevelKey=function(){return``},t.prototype.setZLevel=function(e){this.option.zlevel=e},t.protoInitialize=function(){var e=t.prototype;e.type=`component`,e.id=``,e.name=``,e.mainType=``,e.subType=``,e.componentIndex=0}(),t}(rf);nt(wm,rf),st(wm),Zte(wm),Dp(wm,Ine);function Ine(e){var t=[];return z(wm.getClassesByMainType(e),function(e){t=t.concat(e.dependencies||e.prototype.dependencies||[])}),t=oe(t,function(e){return Ze(e).main}),e!==`dataset`&&ne(t,`dataset`)<=0&&t.unshift(`dataset`),t}var Lne=Us(),Rne=Us(),zne=function(){function e(){}return e.prototype.getColorFromPalette=function(e,t,n){var r=Cs(this.get(`color`,!0)),i=this.get(`colorLayer`,!0);return Hne(this,Lne,r,i,e,t,n)},e.prototype.clearColorPalette=function(){Une(this,Lne)},e}();function Bne(e,t,n,r){return Hne(e,Rne,Cs(e.get([`aria`,`decal`,`decals`])),null,t,n,r)}function Vne(e,t){for(var n=e.length,r=0;r<n;r++)if(e[r].length>t)return e[r];return e[n-1]}function Hne(e,t,n,r,i,a,o){a||=e;var s=t(a),l=s.paletteIdx||0,u=s.paletteNameMap=s.paletteNameMap||{};if(u.hasOwnProperty(i))return u[i];var d=o==null||!r?n:Vne(r,o);if(d||=n,!(!d||!d.length)){var f=d[l];return i&&(u[i]=f),s.paletteIdx=(l+1)%d.length,f}}function Une(e,t){t(e).paletteIdx=0,t(e).paletteNameMap={}}var Wne=/\{@(.+?)\}/g,Gne=function(){function e(){}return e.prototype.getDataParams=function(e,t){var n=this.getData(t),r=this.getRawValue(e,t),i=n.getRawIndex(e),a=n.getName(e),o=n.getRawDataItem(e),s=n.getItemVisual(e,`style`),l=s&&s[n.getItemVisual(e,`drawType`)||`fill`],u=s&&s.stroke,d=this.mainType,f=d===`series`,p=n.userOutput&&n.userOutput.get();return{componentType:d,componentSubType:this.subType,componentIndex:this.componentIndex,seriesType:f?this.subType:null,seriesIndex:this.seriesIndex,seriesId:f?this.id:null,seriesName:f?this.name:null,name:a,dataIndex:i,data:o,dataType:t,value:r,color:l,borderColor:u,dimensionNames:p?p.fullDimensions:null,encode:p?p.encode:null,$vars:[`seriesName`,`name`,`value`]}},e.prototype.getFormattedLabel=function(e,t,n,r,i,a){t||=`normal`;var o=this.getData(n),s=this.getDataParams(e,n);if(a&&(s.value=a.interpolatedValue),r!=null&&me(s.value)&&(s.value=s.value[r]),i||=o.getItemModel(e).get(t===`normal`?[`label`,`formatter`]:[t,`label`,`formatter`]),he(i))return s.status=t,s.dimensionIndex=r,i(s);if(ge(i))return Tne(i,s).replace(Wne,function(t,n){var r=n.length,i=n;i.charAt(0)===`[`&&i.charAt(r-1)===`]`&&(i=+i.slice(1,r-1));var s=Af(o,e,i);if(a&&me(a.interpolatedValue)){var l=o.getDimensionIndex(i);l>=0&&(s=a.interpolatedValue[l])}return s==null?``:s+``})},e.prototype.getRawValue=function(e,t){return Af(this.getData(t),e)},e.prototype.formatTooltip=function(e,t,n){},e}();function Tm(e){return new Kne(e)}var Kne=function(){function e(e){e||={},this._reset=e.reset,this._plan=e.plan,this._count=e.count,this._onDirty=e.onDirty,this._dirty=!0}return e.prototype.perform=function(e){var t=this._upstream,n=e&&e.skip;if(this._dirty&&t){var r=this.context;r.data=r.outputData=t.context.outputData}this.__pipeline&&(this.__pipeline.currentTask=this);var i;this._plan&&!n&&(i=this._plan(this.context));var a=u(this._modBy),o=this._modDataCount||0,s=u(e&&e.modBy),l=e&&e.modDataCount||0;(a!==s||o!==l)&&(i=`reset`);function u(e){return!(e>=1)&&(e=1),e}var d;(this._dirty||i===`reset`)&&(this._dirty=!1,d=this._doReset(n)),this._modBy=s,this._modDataCount=l;var f=e&&e.step;if(t?this._dueEnd=t._outputDueEnd:this._dueEnd=this._count?this._count(this.context):1/0,this._progress){var p=this._dueIndex,m=Math.min(f==null?1/0:this._dueIndex+f,this._dueEnd);if(!n&&(d||p<m)){var h=this._progress;if(me(h))for(var g=0;g<h.length;g++)this._doProgress(h[g],p,m,s,l);else this._doProgress(h,p,m,s,l)}this._dueIndex=m;var _=this._settedOutputEnd==null?m:this._settedOutputEnd;this._outputDueEnd=_}else this._dueIndex=this._outputDueEnd=this._settedOutputEnd==null?this._dueEnd:this._settedOutputEnd;return this.unfinished()},e.prototype.dirty=function(){this._dirty=!0,this._onDirty&&this._onDirty(this.context)},e.prototype._doProgress=function(e,t,n,r,i){qne.reset(t,n,r,i),this._callingProgress=e,this._callingProgress({start:t,end:n,count:n-t,next:qne.next},this.context)},e.prototype._doReset=function(e){this._dueIndex=this._outputDueEnd=this._dueEnd=0,this._settedOutputEnd=null;var t,n;!e&&this._reset&&(t=this._reset(this.context),t&&t.progress&&(n=t.forceFirstProgress,t=t.progress),me(t)&&!t.length&&(t=null)),this._progress=t,this._modBy=this._modDataCount=null;var r=this._downstream;return r&&r.dirty(),n},e.prototype.unfinished=function(){return this._progress&&this._dueIndex<this._dueEnd},e.prototype.pipe=function(e){(this._downstream!==e||this._dirty)&&(this._downstream=e,e._upstream=this,e.dirty())},e.prototype.dispose=function(){this._disposed||=(this._upstream&&(this._upstream._downstream=null),this._downstream&&(this._downstream._upstream=null),this._dirty=!1,!0)},e.prototype.getUpstream=function(){return this._upstream},e.prototype.getDownstream=function(){return this._downstream},e.prototype.setOutputEnd=function(e){this._outputDueEnd=this._settedOutputEnd=e},e}(),qne=function(){var e,t,n,r,i,a={reset:function(l,u,d,f){t=l,e=u,n=d,r=f,i=Math.ceil(r/n),a.next=n>1&&r>0?s:o}};return a;function o(){return t<e?t++:null}function s(){var a=t%i*n+Math.ceil(t/i),o=t>=e?null:a<r?a:t;return t++,o}}(),Jne=function(){function e(){}return e.prototype.getRawData=function(){throw Error(`not supported`)},e.prototype.getRawDataItem=function(e){throw Error(`not supported`)},e.prototype.cloneRawData=function(){},e.prototype.getDimensionInfo=function(e){},e.prototype.cloneAllDimensionInfo=function(){},e.prototype.count=function(){},e.prototype.retrieveValue=function(e,t){},e.prototype.retrieveValueFromItem=function(e,t){},e.prototype.convertValue=function(e,t){return Nf(e,t)},e}();function Yne(e,t){var n=new Jne,r=e.data,i=n.sourceFormat=e.sourceFormat,a=e.startIndex;e.seriesLayoutBy!==`column`&&ys(``);var o=[],s={},l=e.dimensionsDefine;if(l)z(l,function(e,t){var n=e.name,r={index:t,name:n,displayName:e.displayName};o.push(r),n!=null&&(He(s,n)&&ys(``),s[n]=r)});else for(var u=0;u<e.dimensionsDetectedCount;u++)o.push({index:u});var d=Ef(i,bc);t.__isBuiltIn&&(n.getRawDataItem=function(e){return d(r,a,o,e)},n.getRawData=fe(Xne,null,e)),n.cloneRawData=fe(Zne,null,e),n.count=fe(Ate(i,bc),null,r,a,o);var f=jte(i);n.retrieveValue=function(e,t){return p(d(r,a,o,e),t)};var p=n.retrieveValueFromItem=function(e,t){if(e!=null){var n=o[t];if(n)return f(e,t,n.name)}};return n.getDimensionInfo=fe(Qne,null,o,s),n.cloneAllDimensionInfo=fe($ne,null,o),n}function Xne(e){var t=e.sourceFormat;return ire(t)||ys(``),e.data}function Zne(e){var t=e.sourceFormat,n=e.data;if(ire(t)||ys(``),t===`arrayRows`){for(var r=[],i=0,a=n.length;i<a;i++)r.push(n[i].slice());return r}else if(t===`objectRows`){for(var r=[],i=0,a=n.length;i<a;i++)r.push(R({},n[i]));return r}}function Qne(e,t,n){if(n!=null){if(ve(n)||!isNaN(n)&&!He(t,n))return e[n];if(He(t,n))return t[n]}}function $ne(e){return I(e)}var ere=ze();function tre(e){e=I(e);var t=e.type,n=``;t||ys(n);var r=t.split(`:`);r.length!==2&&ys(n);var i=!1;r[0]===`echarts`&&(t=r[1],i=!0),e.__isBuiltIn=i,ere.set(t,e)}function nre(e,t,n){var r=Cs(e),i=r.length;i||ys(``);for(var a=0,o=i;a<o;a++){var s=r[a];t=rre(s,t,n,i===1?null:a),a!==o-1&&(t.length=Math.max(t.length,1))}return t}function rre(e,t,n,r){var i=``;t.length||ys(i),ye(e)||ys(i);var a=e.type,o=ere.get(a);o||ys(i);var s=oe(t,function(e){return Yne(e,o)});return oe(Cs(o.transform({upstream:s[0],upstreamList:s,config:I(e.config)})),function(e,n){var r=``;ye(e)||ys(r),e.data||ys(r),ire(_f(e.data))||ys(r);var i,a=t[0];if(a&&n===0&&!e.dimensions){var o=a.startIndex;o&&(e.data=a.data.slice(0,o).concat(e.data)),i={seriesLayoutBy:bc,sourceHeader:o,dimensions:a.metaRawOption.dimensions}}else i={seriesLayoutBy:bc,sourceHeader:0,dimensions:e.dimensions};return hf(e.data,i,null)})}function ire(e){return e===`arrayRows`||e===`objectRows`}var are=function(){function e(e){this._sourceList=[],this._storeList=[],this._upstreamSignList=[],this._versionSignBase=0,this._dirty=!0,this._sourceHost=e}return e.prototype.dirty=function(){this._setLocalSource([],[]),this._storeList=[],this._dirty=!0},e.prototype._setLocalSource=function(e,t){this._sourceList=e,this._upstreamSignList=t,this._versionSignBase++,this._versionSignBase>9e10&&(this._versionSignBase=0)},e.prototype._getVersionSign=function(){return this._sourceHost.uid+`_`+this._versionSignBase},e.prototype.prepareSource=function(){this._isDirty()&&(this._createSource(),this._dirty=!1)},e.prototype._createSource=function(){this._setLocalSource([],[]);var e=this._sourceHost,t=this._getUpstreamSourceManagers(),n=!!t.length,r,i;if(Em(e)){var a=e,o=void 0,s=void 0,l=void 0;if(n){var u=t[0];u.prepareSource(),l=u.getSource(),o=l.data,s=l.sourceFormat,i=[u._getVersionSign()]}else o=a.get(`data`,!0),s=xe(o)?vc:mc,i=[];var d=this._getSourceMetaRawOption()||{},f=l&&l.metaRawOption||{},p=Ee(d.seriesLayoutBy,f.seriesLayoutBy)||null,m=Ee(d.sourceHeader,f.sourceHeader),h=Ee(d.dimensions,f.dimensions);r=p!==f.seriesLayoutBy||!!m!=!!f.sourceHeader||h?[hf(o,{seriesLayoutBy:p,sourceHeader:m,dimensions:h},s)]:[]}else{var g=e;if(n){var _=this._applyTransform(t);r=_.sourceList,i=_.upstreamSignList}else r=[hf(g.get(`source`,!0),this._getSourceMetaRawOption(),null)],i=[]}this._setLocalSource(r,i)},e.prototype._applyTransform=function(e){var t=this._sourceHost,n=t.get(`transform`,!0),r=t.get(`fromTransformResult`,!0);r!=null&&e.length!==1&&ore(``);var i,a=[],o=[];return z(e,function(e){e.prepareSource();var t=e.getSource(r||0);r!=null&&!t&&ore(``),a.push(t),o.push(e._getVersionSign())}),n?i=nre(n,a,{datasetIndex:t.componentIndex}):r!=null&&(i=[bte(a[0])]),{sourceList:i,upstreamSignList:o}},e.prototype._isDirty=function(){if(this._dirty)return!0;for(var e=this._getUpstreamSourceManagers(),t=0;t<e.length;t++){var n=e[t];if(n._isDirty()||this._upstreamSignList[t]!==n._getVersionSign())return!0}},e.prototype.getSource=function(e){e||=0;var t=this._sourceList[e];if(!t){var n=this._getUpstreamSourceManagers();return n[0]&&n[0].getSource(e)}return t},e.prototype.getSharedDataStore=function(e){var t=e.makeStoreSchema();return this._innerGetDataStore(t.dimensions,e.source,t.hash)},e.prototype._innerGetDataStore=function(e,t,n){var r=0,i=this._storeList,a=i[r];a||=i[r]={};var o=a[n];if(!o){var s=this._getUpstreamSourceManagers()[0];Em(this._sourceHost)&&s?o=s._innerGetDataStore(e,t,n):(o=new Uf,o.initData(new Cf(t,e.length),e)),a[n]=o}return o},e.prototype._getUpstreamSourceManagers=function(){var e=this._sourceHost;if(Em(e)){var t=df(e);return t?[t.getSourceManager()]:[]}else return oe(vte(e),function(e){return e.getSourceManager()})},e.prototype._getSourceMetaRawOption=function(){var e=this._sourceHost,t,n,r;if(Em(e))t=e.get(`seriesLayoutBy`,!0),n=e.get(`sourceHeader`,!0),r=e.get(`dimensions`,!0);else if(!this._getUpstreamSourceManagers().length){var i=e;t=i.get(`seriesLayoutBy`,!0),n=i.get(`sourceHeader`,!0),r=i.get(`dimensions`,!0)}return{seriesLayoutBy:t,sourceHeader:n,dimensions:r}},e}();function Em(e){return e.mainType===`series`}function ore(e){throw Error(e)}var Dm={color:{},darkColor:{},size:{}},Om=Dm.color={theme:[`#5070dd`,`#b6d634`,`#505372`,`#ff994d`,`#0ca8df`,`#ffd10a`,`#fb628b`,`#785db0`,`#3fbe95`],neutral00:`#fff`,neutral05:`#f4f7fd`,neutral10:`#e8ebf0`,neutral15:`#dbdee4`,neutral20:`#cfd2d7`,neutral25:`#c3c5cb`,neutral30:`#b7b9be`,neutral35:`#aaacb2`,neutral40:`#9ea0a5`,neutral45:`#929399`,neutral50:`#86878c`,neutral55:`#797b7f`,neutral60:`#6d6e73`,neutral65:`#616266`,neutral70:`#54555a`,neutral75:`#48494d`,neutral80:`#3c3c41`,neutral85:`#303034`,neutral90:`#232328`,neutral95:`#17171b`,neutral99:`#000`,accent05:`#eff1f9`,accent10:`#e0e4f2`,accent15:`#d0d6ec`,accent20:`#c0c9e6`,accent25:`#b1bbdf`,accent30:`#a1aed9`,accent35:`#91a0d3`,accent40:`#8292cc`,accent45:`#7285c6`,accent50:`#6578ba`,accent55:`#5c6da9`,accent60:`#536298`,accent65:`#4a5787`,accent70:`#404c76`,accent75:`#374165`,accent80:`#2e3654`,accent85:`#252b43`,accent90:`#1b2032`,accent95:`#121521`,transparent:`rgba(0,0,0,0)`,highlight:`rgba(255,231,130,0.8)`};for(var km in R(Om,{primary:Om.neutral80,secondary:Om.neutral70,tertiary:Om.neutral60,quaternary:Om.neutral50,disabled:Om.neutral20,border:Om.neutral30,borderTint:Om.neutral20,borderShade:Om.neutral40,background:Om.neutral05,backgroundTint:`rgba(234,237,245,0.5)`,backgroundTransparent:`rgba(255,255,255,0)`,backgroundShade:Om.neutral10,shadow:`rgba(0,0,0,0.2)`,shadowTint:`rgba(129,130,136,0.2)`,axisLine:Om.neutral70,axisLineTint:Om.neutral40,axisTick:Om.neutral70,axisTickMinor:Om.neutral60,axisLabel:Om.neutral70,axisSplitLine:Om.neutral15,axisMinorSplitLine:Om.neutral05}),Om)if(Om.hasOwnProperty(km)){var sre=Om[km];km===`theme`?Dm.darkColor.theme=Om.theme.slice():km===`highlight`?Dm.darkColor.highlight=`rgba(255,231,130,0.4)`:km.indexOf(`accent`)===0?Dm.darkColor[km]=zr(sre,null,function(e){return e*.5},function(e){return Math.min(1,1.3-e)}):Dm.darkColor[km]=zr(sre,null,function(e){return e*.9},function(e){return 1-e**1.5})}Dm.size={xxs:2,xs:5,s:10,m:15,l:20,xl:30,xxl:40,xxxl:50};function Am(e,t){return t.type=e,t}function cre(e,t){var n=e.getData().getItemVisual(t,`style`)[e.visualDrawType];return Dne(n)}(function(){function e(){this.richTextStyles={},this._nextStyleNameId=ps()}return e.prototype._generateStyleName=function(){return`__EC_aUTo_`+this._nextStyleNameId++},e.prototype.makeTooltipMarker=function(e,t,n){var r=n===`richText`?this._generateStyleName():null,i=Ene({color:t,type:e,renderMode:n,markerId:r});return ge(i)?i:(this.richTextStyles[r]=i.style,i.content)},e.prototype.wrapRichTextStyle=function(e,t){var n={};me(t)?z(t,function(e){return R(n,e)}):R(n,t);var r=this._generateStyleName();return this.richTextStyles[r]=n,`{`+r+`|`+e+`}`},e})();function lre(e){var t=e.series,n=e.dataIndex,r=e.multipleSeries,i=t.getData(),a=i.mapDimensionsAll(`defaultedTooltip`),o=a.length,s=t.getRawValue(n),l=me(s),u=cre(t,n),d,f,p,m;if(o>1||l&&!o){var h=ure(s,t,n,a,u);d=h.inlineValues,f=h.inlineValueTypes,p=h.blocks,m=h.inlineValues[0]}else if(o){var g=i.getDimensionInfo(a[0]);m=d=Af(i,n,a[0]),f=g.type}else m=d=l?s[0]:s;var _=Rs(t),v=_&&t.name||``,y=i.getName(n),b=r?v:y;return Am(`section`,{header:v,noHeader:r||!_,sortParam:m,blocks:[Am(`nameValue`,{markerType:`item`,markerColor:u,name:b,noName:!je(b),value:d,valueType:f,rawDataIndex:i.getRawIndex(n)})].concat(p||[])})}function ure(e,t,n,r,i){var a=t.getData(),o=se(e,function(e,t,n){var r=a.getDimensionInfo(n);return e||=r&&r.tooltip!==!1&&r.displayName!=null},!1),s=[],l=[],u=[];r.length?z(r,function(e){d(Af(a,n,e),e)}):z(e,d);function d(e,t){var n=a.getDimensionInfo(t);!n||n.otherDims.tooltip===!1||(o?u.push(Am(`nameValue`,{markerType:`subItem`,markerColor:i,name:n.displayName,value:e,valueType:n.type})):(s.push(e),l.push(n.type)))}return{inlineValues:s,inlineValueTypes:l,blocks:u}}var jm=Us();function Mm(e,t){return e.getName(t)||e.getId(t)}var Nm=function(e){p(t,e);function t(){var t=e!==null&&e.apply(this,arguments)||this;return t._selectedDataIndicesMap={},t}return t.prototype.init=function(e,t,n){this.seriesIndex=this.componentIndex,this.dataTask=Tm({count:pre,reset:mre}),this.dataTask.context={model:this},this.mergeDefaultAndTheme(e,n),(jm(this).sourceManager=new are(this)).prepareSource();var r=this.getInitialData(e,n);gre(r,this),this.dataTask.context.data=r,jm(this).dataBeforeProcessed=r,dre(this),this._initSelectedMapFromData(r)},t.prototype.mergeDefaultAndTheme=function(e,t){var n=xm(this),r=n?Cm(e):{},i=this.subType;wm.hasClass(i)&&(i+=`Series`),L(e,t.getTheme().get(this.subType)),L(e,this.getDefaultOption()),ws(e,`label`,[`show`]),this.fillDataTextStyle(e.data),n&&Sm(e,r,n)},t.prototype.mergeOption=function(e,t){e=L(this.option,e,!0),this.fillDataTextStyle(e.data);var n=xm(this);n&&Sm(this.option,e,n);var r=jm(this).sourceManager;r.dirty(),r.prepareSource();var i=this.getInitialData(e,t);gre(i,this),this.dataTask.dirty(),this.dataTask.context.data=i,jm(this).dataBeforeProcessed=i,dre(this),this._initSelectedMapFromData(i)},t.prototype.fillDataTextStyle=function(e){if(e&&!xe(e))for(var t=[`show`],n=0;n<e.length;n++)e[n]&&e[n].label&&ws(e[n],`label`,t)},t.prototype.getInitialData=function(e,t){},t.prototype.appendData=function(e){this.getRawData().appendData(e.data)},t.prototype.getData=function(e){var t=Pm(this);if(t){var n=t.context.data;return e==null||!n.getLinkedData?n:n.getLinkedData(e)}else return jm(this).data},t.prototype.getAllData=function(){var e=this.getData();return e&&e.getLinkedDataAll?e.getLinkedDataAll():[{data:e}]},t.prototype.setData=function(e){var t=Pm(this);if(t){var n=t.context;n.outputData=e,t!==this.dataTask&&(n.data=e)}jm(this).data=e},t.prototype.getEncode=function(){var e=this.get(`encode`,!0);if(e)return ze(e)},t.prototype.getSourceManager=function(){return jm(this).sourceManager},t.prototype.getSource=function(){return this.getSourceManager().getSource()},t.prototype.getRawData=function(){return jm(this).dataBeforeProcessed},t.prototype.getColorBy=function(){return this.get(`colorBy`)||`series`},t.prototype.isColorBySeries=function(){return this.getColorBy()===`series`},t.prototype.getBaseAxis=function(){var e=this.coordinateSystem;return e&&e.getBaseAxis&&e.getBaseAxis()},t.prototype.indicesOfNearest=function(e,t,n,r){var i=this.getData(),a=this.coordinateSystem,o=a&&a.getAxis(e);if(!a||!o)return[];var s=o.dataToCoord(n);r??=1/0;for(var l=[],u=1/0,d=-1,f=0,p=i.getDimensionIndex(t),m=i.getStore(),h=0,g=m.count();h<g;h++){var _=m.get(p,h),v=s-o.dataToCoord(_),y=Math.abs(v);y<=r&&((y<u||y===u&&v>=0&&d<0)&&(u=y,d=v,f=0),v===d&&(l[f++]=h))}return l.length=f,l},t.prototype.formatTooltip=function(e,t,n){return lre({series:this,dataIndex:e,multipleSeries:t})},t.prototype.isAnimationEnabled=function(){var e=this.ecModel;if(Ke.node&&!(e&&e.ssr))return!1;var t=this.getShallow(`animation`);return t&&this.getData().count()>this.getShallow(`animationThreshold`)&&(t=!1),!!t},t.prototype.restoreData=function(){this.dataTask.dirty()},t.prototype.getColorFromPalette=function(e,t,n){var r=this.ecModel,i=zne.prototype.getColorFromPalette.call(this,e,t,n);return i||=r.getColorFromPalette(e,t,n),i},t.prototype.coordDimToDataDim=function(e){return this.getRawData().mapDimensionsAll(e)},t.prototype.getProgressive=function(){return this.get(`progressive`)},t.prototype.getProgressiveThreshold=function(){return this.get(`progressiveThreshold`)},t.prototype.select=function(e,t){this._innerSelect(this.getData(t),e)},t.prototype.unselect=function(e,t){var n=this.option.selectedMap;if(n){var r=this.option.selectedMode,i=this.getData(t);if(r===`series`||n===`all`){this.option.selectedMap={},this._selectedDataIndicesMap={};return}for(var a=0;a<e.length;a++){var o=e[a],s=Mm(i,o);n[s]=!1,this._selectedDataIndicesMap[s]=-1}}},t.prototype.toggleSelect=function(e,t){for(var n=[],r=0;r<e.length;r++)n[0]=e[r],this.isSelected(e[r],t)?this.unselect(n,t):this.select(n,t)},t.prototype.getSelectedDataIndices=function(){if(this.option.selectedMap===`all`)return[].slice.call(this.getData().getIndices());for(var e=this._selectedDataIndicesMap,t=ue(e),n=[],r=0;r<t.length;r++){var i=e[t[r]];i>=0&&n.push(i)}return n},t.prototype.isSelected=function(e,t){var n=this.option.selectedMap;if(!n)return!1;var r=this.getData(t);return(n===`all`||n[Mm(r,e)])&&!r.getItemModel(e).get([`select`,`disabled`])},t.prototype.isUniversalTransitionEnabled=function(){if(this.__universalTransitionEnabled)return!0;var e=this.option.universalTransition;return e?e===!0||e&&e.enabled:!1},t.prototype._innerSelect=function(e,t){var n,r,i=this.option,a=i.selectedMode,o=t.length;if(!(!a||!o)){if(a===`series`)i.selectedMap=`all`;else if(a===`multiple`){ye(i.selectedMap)||(i.selectedMap={});for(var s=i.selectedMap,l=0;l<o;l++){var u=t[l],d=Mm(e,u);s[d]=!0,this._selectedDataIndicesMap[d]=e.getRawIndex(u)}}else if(a===`single`||a===!0){var f=t[o-1],d=Mm(e,f);i.selectedMap=(n={},n[d]=!0,n),this._selectedDataIndicesMap=(r={},r[d]=e.getRawIndex(f),r)}}},t.prototype._initSelectedMapFromData=function(e){if(!this.option.selectedMap){var t=[];e.hasItemOption&&e.each(function(n){var r=e.getRawDataItem(n);r&&r.selected&&t.push(n)}),t.length>0&&this._innerSelect(e,t)}},t.registerClass=function(e){return wm.registerClass(e)},t.protoInitialize=function(){var e=t.prototype;e.type=`series.__base__`,e.seriesIndex=0,e.ignoreStyleOnData=!1,e.hasSymbolVisual=!1,e.defaultSymbol=`circle`,e.visualStyleAccessPath=`itemStyle`,e.visualDrawType=`fill`}(),t}(wm);ie(Nm,Gne),ie(Nm,zne),nt(Nm,wm);function dre(e){var t=e.name;Rs(e)||(e.name=fre(e)||t)}function fre(e){var t=e.getRawData(),n=t.mapDimensionsAll(`seriesName`),r=[];return z(n,function(e){var n=t.getDimensionInfo(e);n.displayName&&r.push(n.displayName)}),r.join(` `)}function pre(e){return e.model.getRawData().count()}function mre(e){var t=e.model;return t.setData(t.getRawData().cloneShallow()),hre}function hre(e,t){t.outputData&&e.end>t.outputData.count()&&t.model.getRawData().cloneShallow(t.outputData)}function gre(e,t){z(Be(e.CHANGABLE_METHODS,e.DOWNSAMPLE_METHODS),function(n){e.wrapMethod(n,pe(_re,t))})}function _re(e,t){var n=Pm(e);return n&&n.setOutputEnd((t||this).count()),t}function Pm(e){var t=(e.ecModel||{}).scheduler,n=t&&t.getPipeline(e.uid);if(n){var r=n.currentTask;if(r){var i=r.agentStubMap;i&&(r=i.get(e.uid))}return r}}var vre=io.extend({type:`triangle`,shape:{cx:0,cy:0,width:0,height:0},buildPath:function(e,t){var n=t.cx,r=t.cy,i=t.width/2,a=t.height/2;e.moveTo(n,r-a),e.lineTo(n+i,r+a),e.lineTo(n-i,r+a),e.closePath()}}),yre={line:Su,rect:yo,roundRect:yo,square:yo,circle:Kl,diamond:io.extend({type:`diamond`,shape:{cx:0,cy:0,width:0,height:0},buildPath:function(e,t){var n=t.cx,r=t.cy,i=t.width/2,a=t.height/2;e.moveTo(n,r-a),e.lineTo(n+i,r),e.lineTo(n,r+a),e.lineTo(n-i,r),e.closePath()}}),pin:io.extend({type:`pin`,shape:{x:0,y:0,width:0,height:0},buildPath:function(e,t){var n=t.x,r=t.y,i=t.width/5*3,a=Math.max(i,t.height),o=i/2,s=o*o/(a-o),l=r-a+o+s,u=Math.asin(s/o),d=Math.cos(u)*o,f=Math.sin(u),p=Math.cos(u),m=o*.6,h=o*.7;e.moveTo(n-d,l+s),e.arc(n,l,o,Math.PI-u,Math.PI*2+u),e.bezierCurveTo(n+d-f*m,l+s+p*m,n,r-h,n,r),e.bezierCurveTo(n,r-h,n-d+f*m,l+s+p*m,n-d,l+s),e.closePath()}}),arrow:io.extend({type:`arrow`,shape:{x:0,y:0,width:0,height:0},buildPath:function(e,t){var n=t.height,r=t.width,i=t.x,a=t.y,o=r/3*2;e.moveTo(i,a),e.lineTo(i+o,a+n),e.lineTo(i,a+n/4*3),e.lineTo(i-o,a+n),e.lineTo(i,a),e.closePath()}}),triangle:vre},bre={line:function(e,t,n,r,i){i.x1=e,i.y1=t+r/2,i.x2=e+n,i.y2=t+r/2},rect:function(e,t,n,r,i){i.x=e,i.y=t,i.width=n,i.height=r},roundRect:function(e,t,n,r,i){i.x=e,i.y=t,i.width=n,i.height=r,i.r=Math.min(n,r)/4},square:function(e,t,n,r,i){var a=Math.min(n,r);i.x=e,i.y=t,i.width=a,i.height=a},circle:function(e,t,n,r,i){i.cx=e+n/2,i.cy=t+r/2,i.r=Math.min(n,r)/2},diamond:function(e,t,n,r,i){i.cx=e+n/2,i.cy=t+r/2,i.width=n,i.height=r},pin:function(e,t,n,r,i){i.x=e+n/2,i.y=t+r/2,i.width=n,i.height=r},arrow:function(e,t,n,r,i){i.x=e+n/2,i.y=t+r/2,i.width=n,i.height=r},triangle:function(e,t,n,r,i){i.cx=e+n/2,i.cy=t+r/2,i.width=n,i.height=r}},Fm={};z(yre,function(e,t){Fm[t]=new e});var xre=io.extend({type:`symbol`,shape:{symbolType:``,x:0,y:0,width:0,height:0},calculateTextPosition:function(e,t,n){var r=Tn(e,t,n),i=this.shape;return i&&i.symbolType===`pin`&&t.position===`inside`&&(r.y=n.y+n.height*.4),r},buildPath:function(e,t,n){var r=t.symbolType;if(r!==`none`){var i=Fm[r];i||=(r=`rect`,Fm[r]),bre[r](t.x,t.y,t.width,t.height,i.shape),i.buildPath(e,i.shape,n)}}});function Sre(e,t){if(this.type!==`image`){var n=this.style;this.__isEmptyBrush?(n.stroke=e,n.fill=t||Dm.color.neutral00,n.lineWidth=2):this.shape.symbolType===`line`?n.stroke=e:n.fill=e,this.markRedraw()}}function Im(e,t,n,r,i,a,o){var s=e.indexOf(`empty`)===0;s&&(e=e.substr(5,1).toLowerCase()+e.substr(6));var l=e.indexOf(`image://`)===0?od(e.slice(8),new an(t,n,r,i),o?`center`:`cover`):e.indexOf(`path://`)===0?ad(e.slice(7),{},new an(t,n,r,i),o?`center`:`cover`):new xre({shape:{symbolType:e,x:t,y:n,width:r,height:i}});return l.__isEmptyBrush=s,l.setColor=Sre,a&&l.setColor(a),l}function Cre(e){return me(e)||(e=[+e,+e]),[e[0]||0,e[1]||0]}function wre(e,t){if(e!=null)return me(e)||(e=[e,e]),[Zo(e[0],t[0])||0,Zo(Ee(e[1],e[0]),t[1])||0]}var Tre=function(e){p(t,e);function t(){var n=e!==null&&e.apply(this,arguments)||this;return n.type=t.type,n.hasSymbolVisual=!0,n}return t.prototype.getInitialData=function(e){return Tp(null,this,{useEncodeDefaulter:!0})},t.prototype.getLegendIcon=function(e){var t=new Wl,n=Im(`line`,0,e.itemHeight/2,e.itemWidth,0,e.lineStyle.stroke,!1);t.add(n),n.setStyle(e.lineStyle);var r=this.getData().getVisual(`symbol`),i=this.getData().getVisual(`symbolRotate`),a=r===`none`?`circle`:r,o=e.itemHeight*.8,s=Im(a,(e.itemWidth-o)/2,(e.itemHeight-o)/2,o,o,e.itemStyle.fill);return t.add(s),s.setStyle(e.itemStyle),s.rotation=(e.iconRotate===`inherit`?i:e.iconRotate||0)*Math.PI/180,s.setOrigin([e.itemWidth/2,e.itemHeight/2]),a.indexOf(`empty`)>-1&&(s.style.stroke=s.style.fill,s.style.fill=Dm.color.neutral00,s.style.lineWidth=2),t},t.type=`series.line`,t.dependencies=[`grid`,`polar`],t.defaultOption={z:3,coordinateSystem:`cartesian2d`,legendHoverLink:!0,clip:!0,label:{position:`top`},endLabel:{show:!1,valueAnimation:!0,distance:8},lineStyle:{width:2,type:`solid`},emphasis:{scale:!0},step:!1,smooth:!1,smoothMonotone:null,symbol:`emptyCircle`,symbolSize:6,symbolRotate:null,showSymbol:!0,showAllSymbol:`auto`,connectNulls:!1,sampling:`none`,animationEasing:`linear`,progressive:0,hoverLayerThreshold:1/0,universalTransition:{divideShape:`clone`},triggerLineEvent:!1,triggerEvent:!1},t}(Nm);function Lm(e,t){var n=e.mapDimensionsAll(`defaultedLabel`),r=n.length;if(r===1){var i=Af(e,t,n[0]);return i==null?null:i+``}else if(r){for(var a=[],o=0;o<n.length;o++)a.push(Af(e,t,n[o]));return a.join(` `)}}function Ere(e,t){var n=e.mapDimensionsAll(`defaultedLabel`);if(!me(t))return t+``;for(var r=[],i=0;i<n.length;i++){var a=e.getDimensionIndex(n[i]);a>=0&&r.push(t[a])}return r.join(` `)}var Rm=function(e){p(t,e);function t(t,n,r,i){var a=e.call(this)||this;return a.updateData(t,n,r,i),a}return t.prototype._createSymbol=function(e,t,n,r,i,a){this.removeAll();var o=Im(e,-1,-1,2,2,null,a);o.attr({z2:Ee(i,100),culling:!0,scaleX:r[0]/2,scaleY:r[1]/2}),o.drift=Dre,this._symbolType=e,this.add(o)},t.prototype.stopSymbolAnimation=function(e){this.childAt(0).stopAnimation(null,e)},t.prototype.getSymbolType=function(){return this._symbolType},t.prototype.getSymbolPath=function(){return this.childAt(0)},t.prototype.highlight=function(){Zc(this.childAt(0))},t.prototype.downplay=function(){Qc(this.childAt(0))},t.prototype.setZ=function(e,t){var n=this.childAt(0);n.zlevel=e,n.z=t},t.prototype.setDraggable=function(e,t){var n=this.childAt(0);n.draggable=e,n.cursor=!t&&e?`move`:n.cursor},t.prototype.updateData=function(e,n,r,i){this.silent=!1;var a=e.getItemVisual(n,`symbol`)||`circle`,o=e.hostModel,s=t.getSymbolSize(e,n),l=t.getSymbolZ2(e,n),u=a!==this._symbolType,d=i&&i.disableAnimation;if(u){var f=e.getItemVisual(n,`symbolKeepAspect`);this._createSymbol(a,e,n,s,l,f)}else{var p=this.childAt(0);p.silent=!1;var m={scaleX:s[0]/2,scaleY:s[1]/2};d?p.attr(m):Ku(p,m,o,n),Qu(p)}if(this._updateCommon(e,n,s,r,i),u){var p=this.childAt(0);if(!d){var m={scaleX:this._sizeX,scaleY:this._sizeY,style:{opacity:p.style.opacity}};p.scaleX=p.scaleY=0,p.style.opacity=0,qu(p,m,o,n)}}d&&this.childAt(0).stopAnimation(`leave`)},t.prototype._updateCommon=function(e,t,n,r,i){var a=this.childAt(0),o=e.hostModel,s,l,u,d,f,p,m,h,g;if(r&&(s=r.emphasisItemStyle,l=r.blurItemStyle,u=r.selectItemStyle,d=r.focus,f=r.blurScope,m=r.labelStatesModels,h=r.hoverScale,g=r.cursorStyle,p=r.emphasisDisabled),!r||e.hasItemOption){var _=r&&r.itemModel?r.itemModel:e.getItemModel(t),v=_.getModel(`emphasis`);s=v.getModel(`itemStyle`).getItemStyle(),u=_.getModel([`select`,`itemStyle`]).getItemStyle(),l=_.getModel([`blur`,`itemStyle`]).getItemStyle(),d=v.get(`focus`),f=v.get(`blurScope`),p=v.get(`disabled`),m=Vd(_),h=v.getShallow(`scale`),g=_.getShallow(`cursor`)}var y=e.getItemVisual(t,`symbolRotate`);a.attr(`rotation`,(y||0)*Math.PI/180||0);var b=wre(e.getItemVisual(t,`symbolOffset`),n);b&&(a.x=b[0],a.y=b[1]),g&&a.attr(`cursor`,g);var x=e.getItemVisual(t,`style`),S=x.fill;if(a instanceof uo){var C=a.style;a.useStyle(R({image:C.image,x:C.x,y:C.y,width:C.width,height:C.height},x))}else a.__isEmptyBrush?a.useStyle(R({},x)):a.useStyle(x),a.style.decal=null,a.setColor(S,i&&i.symbolInnerColor),a.style.strokeNoScale=!0;var w=e.getItemVisual(t,`liftZ`),T=this._z2;w==null?T!=null&&(a.z2=T,this._z2=null):T??(this._z2=a.z2,a.z2+=w);var E=i&&i.useNameLabel;Bd(a,m,{labelFetcher:o,labelDataIndex:t,defaultText:D,inheritColor:S,defaultOpacity:x.opacity});function D(t){return E?e.getName(t):Lm(e,t)}this._sizeX=n[0]/2,this._sizeY=n[1]/2;var O=a.ensureState(`emphasis`);O.style=s,a.ensureState(`select`).style=u,a.ensureState(`blur`).style=l;var k=h==null||h===!0?Math.max(1.1,3/this._sizeY):isFinite(h)&&h>0?+h:1;O.scaleX=this._sizeX*k,O.scaleY=this._sizeY*k,this.setSymbolScale(1),pl(this,d,f,p)},t.prototype.setSymbolScale=function(e){this.scaleX=this.scaleY=e},t.prototype.fadeOut=function(e,t,n){var r=this.childAt(0),i=dc(this).dataIndex,a=n&&n.animation;if(this.silent=r.silent=!0,n&&n.fadeLabel){var o=r.getTextContent();o&&Yu(o,{style:{opacity:0}},t,{dataIndex:i,removeOpt:a,cb:function(){r.removeTextContent()}})}else r.removeTextContent();Yu(r,{style:{opacity:0},scaleX:0,scaleY:0},t,{dataIndex:i,cb:e,removeOpt:a})},t.getSymbolSize=function(e,t){return Cre(e.getItemVisual(t,`symbolSize`))},t.getSymbolZ2=function(e,t){return e.getItemVisual(t,`z2`)},t}(Wl);function Dre(e,t){this.parent.drift(e,t)}function zm(e,t,n,r){return t&&!isNaN(t[0])&&!isNaN(t[1])&&!(r&&r.isIgnore&&r.isIgnore(n))&&!(r&&r.clipShape&&!r.clipShape.contain(t[0],t[1]))&&e.getItemVisual(n,`symbol`)!==`none`}function Ore(e){return e!=null&&!ye(e)&&(e={isIgnore:e}),e||{}}function kre(e){var t=e.hostModel,n=t.getModel(`emphasis`);return{emphasisItemStyle:n.getModel(`itemStyle`).getItemStyle(),blurItemStyle:t.getModel([`blur`,`itemStyle`]).getItemStyle(),selectItemStyle:t.getModel([`select`,`itemStyle`]).getItemStyle(),focus:n.get(`focus`),blurScope:n.get(`blurScope`),emphasisDisabled:n.get(`disabled`),hoverScale:n.get(`scale`),labelStatesModels:Vd(t),cursorStyle:t.get(`cursor`)}}function Are(e,t,n,r,i,a,o){var s=new e(t,n,r,i);return s.setPosition(a),t.setItemGraphicEl(n,s),o.add(s),s}var jre=function(){function e(e){this.group=new Wl,this._SymbolCtor=e||Rm}return e.prototype.updateData=function(e,t){this._progressiveEls=null,t=Ore(t);var n=this.group,r=e.hostModel,i=this._data,a=this._SymbolCtor,o=t.disableAnimation,s=this._seriesScope=kre(e),l={disableAnimation:o},u=t.getSymbolPoint||function(t){return e.getItemLayout(t)};i||n.removeAll(),e.diff(i).add(function(r){var i=u(r);zm(e,i,r,t)&&Are(a,e,r,s,l,i,n)}).update(function(d,f){var p=i.getItemGraphicEl(f),m=u(d);if(!zm(e,m,d,t)){n.remove(p);return}var h=e.getItemVisual(d,`symbol`)||`circle`,g=p&&p.getSymbolType&&p.getSymbolType();if(!p||g&&g!==h)n.remove(p),p=new a(e,d,s,l),p.setPosition(m);else{p.updateData(e,d,s,l);var _={x:m[0],y:m[1]};o?p.attr(_):Ku(p,_,r)}n.add(p),e.setItemGraphicEl(d,p)}).remove(function(e){var t=i.getItemGraphicEl(e);t&&t.fadeOut(function(){n.remove(t)},r)}).execute(),this._getSymbolPoint=u,this._data=e},e.prototype.updateLayout=function(e){var t=this._data;if(t)for(var n=this,r=t.getStore(),i=0,a=r.count();i<a;i++){var o=t.getItemGraphicEl(i),s=n._getSymbolPoint(i);zm(t,s,i,e)?(o||=Are(n._SymbolCtor,t,i,n._seriesScope,{disableAnimation:!0},s,n.group),o.stopAnimation(),o.setPosition(s),o.markRedraw()):o&&(n.group.remove(o),t.setItemGraphicEl(i,null))}},e.prototype.incrementalPrepareUpdate=function(e){this._seriesScope=kre(e),this._data=null,this.group.removeAll()},e.prototype.incrementalUpdate=function(e,t,n,r){this._progressiveEls=[],r=Ore(r);function i(e){e.isGroup||(e.incremental=n,e.ensureState(`emphasis`).hoverLayer=2)}for(var a=e.start;a<e.end;a++){var o=t.getItemLayout(a);if(zm(t,o,a,r)){var s=new this._SymbolCtor(t,a,this._seriesScope);s.traverse(i),s.setPosition(o),this.group.add(s),t.setItemGraphicEl(a,s),this._progressiveEls.push(s)}}},e.prototype.eachRendered=function(e){Dd(this._progressiveEls||this.group,e)},e.prototype.remove=function(e){var t=this.group,n=this._data;n&&e?n.eachItemGraphicEl(function(e){e.fadeOut(function(){t.remove(e)},n.hostModel)}):t.removeAll()},e}();function Mre(e,t,n){var r=e.getBaseAxis(),i=e.getOtherAxis(r),a=Nre(i,n),o=r.dim,s=i.dim,l=t.mapDimension(s),u=t.mapDimension(o),d=+(s===`x`||s===`radius`),f=oe(e.dimensions,function(e){return t.mapDimension(e)}),p=!1,m=t.getCalculationInfo(`stackResultDimension`);return Sp(t,f[0])&&(p=!0,f[0]=m),Sp(t,f[1])&&(p=!0,f[1]=m),{dataDimsForPoint:f,valueStart:a,valueAxisDim:s,baseAxisDim:o,stacked:!!p,valueDim:l,baseDim:u,baseDataOffset:d,stackedOverDimension:t.getCalculationInfo(`stackedOverDimension`)}}function Nre(e,t){var n=0,r=e.scale.getExtent();return t===`start`?n=r[0]:t===`end`?n=r[1]:ve(t)&&!isNaN(t)?n=t:r[0]>0?n=r[0]:r[1]<0&&(n=r[1]),n}function Pre(e,t,n,r){var i=NaN;e.stacked&&(i=n.get(n.getCalculationInfo(`stackedOverDimension`),r)),isNaN(i)&&(i=e.valueStart);var a=e.baseDataOffset,o=[];return o[a]=n.get(e.baseDim,r),o[1-a]=i,t.dataToPoint(o)}function Bm(e,t){return!isFinite(e)||!isFinite(t)}var Fre=typeof Float32Array<`u`?Float32Array:void 0,Ire=typeof Float64Array<`u`?Float64Array:void 0;function Vm(e){return Hm({ctor:Fre},e).arr}function Hm(e,t){var n=e.arr,r=e.ctor;if(t>rs&&(t=rs),!n||e.typed&&n.length<t){var i=void 0;if(r)try{i=new r(t),e.typed=!0,n&&i.set(n)}catch{}if(!i&&(i=[],e.typed=!1,n))for(var a=0,o=n.length;a<o;a++)i[a]=n[a];e.arr=i}return e}function Lre(e,t){var n=[];return t.diff(e).add(function(e){n.push({cmd:`+`,idx:e})}).update(function(e,t){n.push({cmd:`=`,idx:t,idx1:e})}).remove(function(e){n.push({cmd:`-`,idx:e})}).execute(),n}function Rre(e,t,n,r,i,a,o,s){for(var l=Lre(e,t),u=[],d=[],f=[],p=[],m=[],h=[],g=[],_=Mre(i,t,o),v=e.getLayout(`points`)||[],y=t.getLayout(`points`)||[],b=0;b<l.length;b++){var x=l[b],S=!0,C=void 0,w=void 0;switch(x.cmd){case`=`:C=x.idx*2,w=x.idx1*2;var T=v[C],E=v[C+1],D=y[w],O=y[w+1];(isNaN(T)||isNaN(E))&&(T=D,E=O),u.push(T,E),d.push(D,O),f.push(n[C],n[C+1]),p.push(r[w],r[w+1]),g.push(t.getRawIndex(x.idx1));break;case`+`:var k=x.idx,A=_.dataDimsForPoint,j=i.dataToPoint([t.get(A[0],k),t.get(A[1],k)]);w=k*2,u.push(j[0],j[1]),d.push(y[w],y[w+1]);var M=Pre(_,i,t,k);f.push(M[0],M[1]),p.push(r[w],r[w+1]),g.push(t.getRawIndex(k));break;case`-`:S=!1}S&&(m.push(x),h.push(h.length))}h.sort(function(e,t){return g[e]-g[t]});for(var N=u.length,P=Vm(N),F=Vm(N),I=Vm(N),L=Vm(N),R=[],b=0;b<h.length;b++){var ee=h[b],te=b*2,ne=ee*2;P[te]=u[ne],P[te+1]=u[ne+1],F[te]=d[ne],F[te+1]=d[ne+1],I[te]=f[ne],I[te+1]=f[ne+1],L[te]=p[ne],L[te+1]=p[ne+1],R[b]=m[ee]}return{current:P,next:F,stackedOnCurrent:I,stackedOnNext:L,status:R}}var Um=Math.min,Wm=Math.max;function Gm(e,t,n,r,i,a,o,s,l){for(var u,d,f,p,m,h,g=n,_=0;_<r;_++){var v=t[g*2],y=t[g*2+1];if(g>=i||g<0)break;if(Bm(v,y)){if(l){g+=a;continue}break}if(g===n)e[a>0?`moveTo`:`lineTo`](v,y),f=v,p=y;else{var b=v-u,x=y-d;if(b*b+x*x<.5){g+=a;continue}if(o>0){for(var S=g+a,C=t[S*2],w=t[S*2+1];C===v&&w===y&&_<r;)_++,S+=a,g+=a,C=t[S*2],w=t[S*2+1],v=t[g*2],y=t[g*2+1],b=v-u,x=y-d;var T=_+1;if(l)for(;Bm(C,w)&&T<r;)T++,S+=a,C=t[S*2],w=t[S*2+1];var E=.5,D=0,O=0,k=void 0,A=void 0;if(T>=r||Bm(C,w))m=v,h=y;else{D=C-u,O=w-d;var j=v-u,M=C-v,N=y-d,P=w-y,F=void 0,I=void 0;if(s===`x`){F=Math.abs(j),I=Math.abs(M);var L=D>0?1:-1;m=v-L*F*o,h=y,k=v+L*I*o,A=y}else if(s===`y`){F=Math.abs(N),I=Math.abs(P);var R=O>0?1:-1;m=v,h=y-R*F*o,k=v,A=y+R*I*o}else F=Math.sqrt(j*j+N*N),I=Math.sqrt(M*M+P*P),E=I/(I+F),m=v-D*o*(1-E),h=y-O*o*(1-E),k=v+D*o*E,A=y+O*o*E,k=Um(k,Wm(C,v)),A=Um(A,Wm(w,y)),k=Wm(k,Um(C,v)),A=Wm(A,Um(w,y)),D=k-v,O=A-y,m=v-D*F/I,h=y-O*F/I,m=Um(m,Wm(u,v)),h=Um(h,Wm(d,y)),m=Wm(m,Um(u,v)),h=Wm(h,Um(d,y)),D=v-m,O=y-h,k=v+D*I/F,A=y+O*I/F}e.bezierCurveTo(f,p,m,h,v,y),f=k,p=A}else e.lineTo(v,y)}u=v,d=y,g+=a}return _}var zre=function(){function e(){this.smooth=0,this.smoothConstraint=!0}return e}(),Bre=function(e){p(t,e);function t(t){var n=e.call(this,t)||this;return n.type=`ec-polyline`,n}return t.prototype.getDefaultStyle=function(){return{stroke:Dm.color.neutral99,fill:null}},t.prototype.getDefaultShape=function(){return new zre},t.prototype.buildPath=function(e,t){var n=t.points,r=0,i=n.length/2;if(t.connectNulls){for(;i>0&&Bm(n[i*2-2],n[i*2-1]);i--);for(;r<i&&Bm(n[r*2],n[r*2+1]);r++);}for(;r<i;)r+=Gm(e,n,r,i,i,1,t.smooth,t.smoothMonotone,t.connectNulls)+1},t.prototype.getPointOn=function(e,t){this.path||(this.createPathProxy(),this.buildPath(this.path,this.shape));for(var n=this.path.data,r=La.CMD,i,a,o=t===`x`,s=[],l=0;l<n.length;){var u=n[l++],d=void 0,f=void 0,p=void 0,m=void 0,h=void 0,g=void 0,_=void 0;switch(u){case r.M:i=n[l++],a=n[l++];break;case r.L:if(d=n[l++],f=n[l++],_=o?(e-i)/(d-i):(e-a)/(f-a),_<=1&&_>=0){var v=o?(f-a)*_+a:(d-i)*_+i;return o?[e,v]:[v,e]}i=d,a=f;break;case r.C:d=n[l++],f=n[l++],p=n[l++],m=n[l++],h=n[l++],g=n[l++];var y=o?fr(i,d,p,h,e,s):fr(a,f,m,g,e,s);if(y>0)for(var b=0;b<y;b++){var x=s[b];if(x<=1&&x>=0){var v=o?ur(a,f,m,g,x):ur(i,d,p,h,x);return o?[e,v]:[v,e]}}i=h,a=g;break}}},t}(io),Vre=function(e){p(t,e);function t(){return e!==null&&e.apply(this,arguments)||this}return t}(zre),Hre=function(e){p(t,e);function t(t){var n=e.call(this,t)||this;return n.type=`ec-polygon`,n}return t.prototype.getDefaultShape=function(){return new Vre},t.prototype.buildPath=function(e,t){var n=t.points,r=t.stackedOnPoints,i=0,a=n.length/2,o=t.smoothMonotone;if(t.connectNulls){for(;a>0&&Bm(n[a*2-2],n[a*2-1]);a--);for(;i<a&&Bm(n[i*2],n[i*2+1]);i++);}for(;i<a;){var s=Gm(e,n,i,a,a,1,t.smooth,o,t.connectNulls);Gm(e,r,i+s-1,s,a,-1,t.stackedOnSmooth,o,t.connectNulls),i+=s+1,e.closePath()}},t}(io);function Km(){var e=Us();return function(t){var n=e(t),r=t.pipelineContext,i=!!n.large,a=!!n.progressiveRender,o=n.large=!!(r&&r.large),s=n.progressiveRender=!!(r&&r.progressiveRender);return(i!==o||a!==s)&&`reset`}}var Ure=Us(),Wre=Km(),qm=function(){function e(){this.group=new Wl,this.uid=Ep(`viewChart`),this.renderTask=Tm({plan:qre,reset:Jre}),this.renderTask.context={view:this}}return e.prototype.init=function(e,t){},e.prototype.render=function(e,t,n,r){},e.prototype.highlight=function(e,t,n,r){var i=e.getData(r&&r.dataType);i&&Kre(i,r,`emphasis`)},e.prototype.downplay=function(e,t,n,r){var i=e.getData(r&&r.dataType);i&&Kre(i,r,`normal`)},e.prototype.remove=function(e,t){this.group.removeAll()},e.prototype.dispose=function(e,t){},e.prototype.updateView=function(e,t,n,r){this.render(e,t,n,r)},e.prototype.updateVisual=function(e,t,n,r){this.render(e,t,n,r)},e.prototype.eachRendered=function(e){Dd(this.group,e)},e.markUpdateMethod=function(e,t){Ure(e).updateMethod=t},e.protoInitialize=function(){var t=e.prototype;t.type=`chart`}(),e}();function Gre(e,t,n){e&&yl(e)&&(t===`emphasis`?Zc:Qc)(e,n)}function Kre(e,t,n){var r=Hs(e,t),i=t&&t.highlightKey!=null?bl(t.highlightKey):null;r==null?e.eachItemGraphicEl(function(e){Gre(e,n,i)}):z(Cs(r),function(t){Gre(e.getItemGraphicEl(t),n,i)})}et(qm,[`dispose`]),st(qm);function qre(e){return Wre(e.model)}function Jre(e){var t=e.model,n=e.ecModel,r=e.api,i=e.payload,a=t.pipelineContext.progressiveRender,o=e.view,s=i&&Ure(i).updateMethod,l=a?`incrementalPrepareRender`:s&&o[s]?s:`render`;return l!==`render`&&o[l](t,n,r,i),Yre[l]}var Yre={incrementalPrepareRender:{progress:function(e,t){t.view.incrementalRender(e,t.model,t.ecModel,t.api,t.payload)}},render:{forceFirstProgress:!0,progress:function(e,t){t.view.render(t.model,t.ecModel,t.api,t.payload)}}};function Xre(e,t,n,r,i){var a=e.getArea(),o=a.x,s=a.y,l=a.width,u=a.height,d=n.get([`lineStyle`,`width`])||0;o-=d/2,s-=d/2,l+=d,u+=d,l=Math.ceil(l),o!==Math.floor(o)&&(o=Math.floor(o),l++);var f=new yo({shape:{x:o,y:s,width:l,height:u}});if(t){var p=e.getBaseAxis(),m=p.isHorizontal(),h=p.inverse;m?(h&&(f.shape.x+=l),f.shape.width=0):(h||(f.shape.y+=u),f.shape.height=0);var g=he(i)?function(e){i(e,f)}:null;qu(f,{shape:{width:l,height:u,x:o,y:s}},n,null,r,g)}return f}function Zre(e,t,n){var r=e.getArea(),i=es(r.r0,1),a=es(r.r,1),o=new du({shape:{cx:es(e.cx,1),cy:es(e.cy,1),r0:i,r:a,startAngle:r.startAngle,endAngle:r.endAngle,clockwise:r.clockwise}});return t&&(e.getBaseAxis().dim===`angle`?o.shape.endAngle=r.startAngle:o.shape.r=i,qu(o,{shape:{endAngle:r.endAngle,r:a}},n)),o}function Qre(e,t,n,r,i){return e?e.type===`polar`?Zre(e,t,n):e.type===`cartesian2d`?Xre(e,t,n,r,i):null:null}function $re(e,t){return e.type===t}var Jm=function(){function e(){}return e.prototype.isBlank=function(){return this._isBlank},e.prototype.setBlank=function(e){this._isBlank=e},e}();st(Jm);var eie=0,Ym=function(){function e(e){this.categories=e.categories||[],this._needCollect=e.needCollect,this._deduplication=e.deduplication,this.uid=++eie,this._onCollect=e.onCollect}return e.createByAxisModel=function(t){var n=t.option,r=n.data,i=r&&oe(r,tie);return new e({categories:i,needCollect:!i,deduplication:n.dedplication!==!1})},e.prototype.getOrdinal=function(e){return this._getOrCreateMap().get(e)},e.prototype.parseAndCollect=function(e){var t,n=this._needCollect;if(!ge(e)&&!n)return e;if(n&&!this._deduplication)return t=this.categories.length,this.categories[t]=e,this._onCollect&&this._onCollect(e,t),t;var r=this._getOrCreateMap();return t=r.get(e),t??(n?(t=this.categories.length,this.categories[t]=e,r.set(e,t),this._onCollect&&this._onCollect(e,t)):t=NaN),t},e.prototype._getOrCreateMap=function(){return this._map||=ze(this.categories)},e}();function tie(e){return ye(e)&&e.value!=null?e.value:e+``}var nie=ue({needTransform:1,normalize:1,scale:1,transformIn:1,transformOut:1,contain:1,getExtent:1,getExtentUnsafe:1,setExtent:1,setExtent2:1,getFilter:1,sanitize:1,getDefaultStartValue:1,freeze:1});function Xm(e,t,n){var r;e||={};var i=Jp();if(i){var a=i.createBreakScaleMapper(t,n);a.hasBreaks()&&(z(nie,function(t){a[t]&&(e[t]=fe(a[t],a))}),r=a)}return r??oie(e,n),{brk:r,mapper:e}}function rie(e,t){z(nie,function(n){e[n]=t[n]})}function iie(e,t){e.freeze=Ue}function Zm(e){return e.getExtentUnsafe(0,2)}function Qm(e,t){return e.getExtentUnsafe(1,t)||e.getExtentUnsafe(0,t)}function aie(e){var t=Qm(e,3);return t[1]-t[0]}function $m(e){var t=e.getExtentUnsafe(0,3);return t[1]-t[0]}function oie(e,t){var n=e||{},r=[];return n._extents=r,r[0]=t?t.slice():Xs(),R(n,sie),n}var sie={needTransform:function(){return!1},normalize:function(e){var t=this._extents[1]||this._extents[0];return t[1]===t[0]?.5:(e-t[0])/(t[1]-t[0])},scale:function(e){var t=this._extents[1]||this._extents[0];return e*(t[1]-t[0])+t[0]},transformIn:function(e){return e},transformOut:function(e){return e},contain:function(e){var t=Qm(this,null);return e>=t[0]&&e<=t[1]},getExtent:function(){return this._extents[0].slice()},getExtentUnsafe:function(e){return this._extents[e]},setExtent:function(e,t){cie(this._extents,0,e,t)},setExtent2:function(e,t,n){var r=this._extents;r[e]||(r[e]=r[0].slice()),cie(r,e,t,n)},freeze:function(){}};function cie(e,t,n,r){nc(n,r)&&(e[t][0]=n,e[t][1]=r)}function lie(e){return eh(e)||th(e)}function eh(e){return e.type===`interval`}function uie(e){return e.type===`time`}function th(e){return e.type===`log`}function nh(e){return e.type===`ordinal`}function die(e){var t=ls(e),n=Ko(10,t),r=Uo(e/n);return r?r===2?r=3:r===3?r=5:r*=2:r=1,es(r*n,-t)}function rh(e){return ns(e)+2}function ih(e,t){return qo(e)/qo(t)}function fie(e,t,n){var r=n&&n.lookup;if(r){for(var i=0;i<r.from.length;i++)if(e===r.from[i])return r.to[i]}return Ko(t,e)}function pie(e,t,n){var r=e.slice();if(r[0]===r[1]){var i=n&&n.ctnShp;if(r[0]!==0){var a=Ho(r[0]);t[1]||(r[1]+=a/2),r[0]-=a/2}else i&&(r[0]=-1),r[1]=1}return(!tc(r[0])||!tc(r[1]))&&(r[0]=0,r[1]=1),r[1]<r[0]&&r.reverse(),r}function mie(e,t){return[e[0]!==t[0],e[1]!==t[1]]}function hie(e,t){return e||=t,Uo(Vo(e,1))}function gie(e,t,n){var r=Zm(e),i=r[0],a=e.count(),o=Math.max((t||0)+1,1);i!==0&&o>1&&a/o>2&&(i=Math.round(Math.ceil(i/o)*o)),i!==r[0]&&l(r[0],!0,!0);for(var s=i;s<=r[1];s+=o)l(s,!1,s===r[0]||s===r[1]);s-o!==r[1]&&l(r[1],!0,!0);function l(e,t,r){n({value:e,offInterval:t},r)}}var _ie=function(e){p(t,e);function t(n){var r=e.call(this)||this;r.type=`ordinal`,r.parse=t.parse,rie(r,t.decoratedMethods);var i=n.ordinalMeta;i||=new Ym({}),me(i)&&(i=new Ym({categories:oe(i,function(e){return ye(e)?e.value:e})})),r._ordinalMeta=i;var a=Xm(null,null,n.extent||[0,i.categories.length-1]);return r._mapper=a.mapper,iie(r,a.mapper),r}return t.parse=function(e){return e==null?e=NaN:ge(e)?(e=this._ordinalMeta.getOrdinal(e),e??=NaN):e=Uo(e),e},t.prototype.getTicks=function(){var e=[];return gie(this,0,function(t){e.push(t)}),e},t.prototype.getMinorTicks=function(e){},t.prototype.setSortInfo=function(e){if(e==null){this._ordinalNumbersByTick=this._ticksByOrdinalNumber=null;return}for(var t=e.ordinalNumbers,n=this._ordinalNumbersByTick=[],r=this._ticksByOrdinalNumber=[],i=0,a=this._ordinalMeta.categories.length,o=Bo(a,t.length);i<o;++i){var s=n[i]=t[i];r[s]=i}for(var l=0;i<a;++i){for(;r[l]!=null;)l++;n[i]=l,r[l]=i}},t.prototype._getTickNumber=function(e){var t=this._ticksByOrdinalNumber;return t&&e>=0&&e<t.length?t[e]:e},t.prototype.getRawOrdinalNumber=function(e){var t=this._ordinalNumbersByTick;return t&&e>=0&&e<t.length?t[e]:e},t.prototype.getLabel=function(e){if(!this.isBlank()){var t=this.getRawOrdinalNumber(e.value),n=this._ordinalMeta.categories[t];return n==null?``:n+``}},t.prototype.count=function(){var e=Zm(this._mapper);return e[1]-e[0]+1},t.prototype.getOrdinalMeta=function(){return this._ordinalMeta},t.type=`ordinal`,t.decoratedMethods={needTransform:function(){return this._mapper.needTransform()},contain:function(e){return this._mapper.contain(this._getTickNumber(e))&&e>=0&&e<this._ordinalMeta.categories.length},normalize:function(e){return this._mapper.normalize(this._getTickNumber(e))},scale:function(e){return this.getRawOrdinalNumber(Uo(this._mapper.scale(e)))},transformIn:function(e,t){return this._mapper.transformIn(this._getTickNumber(e),t)},transformOut:function(e,t){return this.getRawOrdinalNumber(this._mapper.transformOut(e,t))},getExtent:function(){return this._mapper.getExtent()},getExtentUnsafe:function(e,t){return this._mapper.getExtentUnsafe(e,t)},setExtent:function(e,t){return this._mapper.setExtent(e,t)},setExtent2:function(e,t,n){return this._mapper.setExtent2(e,t,n)}},t}(Jm);Jm.registerClass(_ie);function vie(e,t,n,r){for(var i=e.getTicks({expandToNicedExtent:!0}),a=[],o=e.getExtent(),s=1;s<i.length;s++){var l=i[s],u=i[s-1];if(!(u.break||l.break)){for(var d=0,f=[],p=(l.value-u.value)/t,m=rh(p);d<t-1;){var h=es(u.value+(d+1)*p,m);h>o[0]&&h<o[1]&&f.push(h),d++}var g=Jp();g&&g.pruneTicksByBreak(`auto`,f,n,function(e){return e},r,o),a.push(f)}}return a}var ah=function(e){p(t,e);function t(n){var r=e.call(this)||this;return r.type=`interval`,r.parse=t.parse,n||={},r.brk=Xm(r,Yp(r,n),null).brk,r._cfg={interval:0,intervalPrecision:2,intervalCount:void 0,niceExtent:void 0},r}return t.parse=function(e){return e==null||e===``?NaN:Number(e)},t.prototype.getConfig=function(){return I(this._cfg)},t.prototype.setConfig=function(e){var t=Zm(this);this._cfg=e=I(e),e.niceExtent??=t.slice(),e.intervalPrecision??=rh(e.interval)},t.prototype.getTicks=function(e){e||={};var t=this._cfg,n=t.interval,r=Zm(this),i=t.niceExtent,a=t.intervalPrecision,o=Jp(),s=this.brk,l=o&&s,u=[];if(!n)return u;if(e.breakTicks===`only_break`&&l)return o.addBreaksToTicks(u,s.breaks,r),u;var d=3e3;r[0]<i[0]&&u.push({value:e.expandToNicedExtent?es(i[0]-n,a):r[0]});for(var f=function(e,t){return Uo((t-e)/n)},p=t.intervalCount,m=i[0],h=0;;h++){if(p==null){if(m>i[1]||!isFinite(m)||!isFinite(i[1]))break}else{if(h>p)break;m=Bo(m,i[1]),h===p&&(m=i[1])}if(u.push({value:m}),m=es(m+n,a),s){var g=s.calcNiceTickMultiple(m,f);g>=0&&(m=es(m+g*n,a))}if(u.length>0&&m===u[u.length-1].value)break;if(u.length>d)return[]}var _=u.length?u[u.length-1].value:i[1];return r[1]>_&&u.push({value:e.expandToNicedExtent?es(_+n,a):r[1]}),l&&o.pruneTicksByBreak(e.pruneByBreak,u,s.breaks,function(e){return e.value},t.interval,r),l&&e.breakTicks!==`none`&&o.addBreaksToTicks(u,s.breaks,r),u},t.prototype.getMinorTicks=function(e){return vie(this,e,Xp(this),this._cfg.interval)},t.prototype.getLabel=function(e,t){if(e==null)return``;var n=t&&t.precision;return n==null?n=ns(e.value)||0:n===`auto`&&(n=this._cfg.intervalPrecision),xne(es(e.value,n,!0))},t.type=`interval`,t}(Jm);Jm.registerClass(ah);var yie=function(e,t,n,r){for(;n<r;){var i=n+r>>>1;e[i][1]<t?n=i+1:r=i}return n},bie=function(e){p(t,e);function t(n){var r=e.call(this)||this;return r.type=`time`,r.parse=t.parse,r._locale=n.locale,r._useUTC=n.useUTC,r._interval=0,r.brk=Xm(r,Yp(r,n),null).brk,r}return t.prototype.getLabel=function(e){return une(e.value,ine[lne(cm(this._minLevelUnit))]||ine.second,this._useUTC,this._locale)},t.prototype.getFormattedLabel=function(e,t,n){return dne(e,t,n,this._locale,this._useUTC)},t.prototype.getTicks=function(e){e||={};var t=this._interval,n=Zm(this),r=Jp(),i=this.brk,a=r&&i,o=[];if(!t)return o;var s=this._useUTC;if(a&&e.breakTicks===`only_break`)return Jp().addBreaksToTicks(o,i.breaks,n),o;o=kie(this._minLevelUnit,this._approxInterval,s,n,$m(this),i);var l=om.length-1,u=0;return z(o,function(e){e.time&&(l=Math.min(l,ne(om,e.time.upperTimeUnit)),u=Math.max(u,e.time.level))}),a&&Jp().pruneTicksByBreak(e.pruneByBreak,o,i.breaks,function(e){return e.value},this._approxInterval,n),a&&e.breakTicks!==`none`&&Jp().addBreaksToTicks(o,i.breaks,n,function(e){for(var t=Math.max(ne(om,lm(e.vmin,s)),ne(om,lm(e.vmax,s))),n=0,r=0;r<om.length;r++)if(!xie(om[r],e.vmin,e.vmax,s)){n=r;break}var i=Math.min(n,l);return{level:u,lowerTimeUnit:om[Math.max(i,t)],upperTimeUnit:om[i]}}),o},t.prototype.getMinorTicks=function(e){return vie(this,e,Xp(this),this._interval)},t.prototype.setTimeInterval=function(e){this._interval=e.interval,this._approxInterval=e.approxInterval,this._minLevelUnit=e.minLevelUnit},t.parse=function(e){return ve(e)?Math.round(e):+ss(e)},t.type=`time`,t}(Jm),oh=[[`second`,Qp],[`minute`,$p],[`hour`,em],[`quarter-day`,em*6],[`half-day`,em*12],[`day`,tm*1.2],[`half-week`,tm*3.5],[`week`,tm*7],[`month`,tm*31],[`quarter`,tm*95],[`half-year`,nm/2],[`year`,nm]];function xie(e,t,n,r){return um(new Date(t),e,r).getTime()===um(new Date(n),e,r).getTime()}function Sie(e,t){return e/=tm,e>16?16:e>7.5?7:e>3.5?4:e>1.5?2:1}function Cie(e){var t=30*tm;return e/=t,e>6?6:e>3?3:e>2?2:1}function wie(e){return e/=em,e>12?12:e>6?6:e>3.5?4:e>2?2:1}function Tie(e,t){return e/=t?$p:Qp,e>30?30:e>20?20:e>15?15:e>10?10:e>5?5:e>2?2:1}function Eie(e){return Vo(us(e,!0),1)}function Die(e,t,n){var r=Math.max(0,ne(om,t)-1);return um(new Date(e),om[r],n).getTime()}function Oie(e,t){var n=new Date(0);n[e](1);var r=n.getTime();n[e](1+t);var i=n.getTime()-r;return function(e,t){return Math.max(0,Math.round((t-e)/i))}}function kie(e,t,n,r,i,a){var o=ane,s=0;function l(e,t,n,i,o,l,u){for(var d=Oie(o,e),f=t,p=new Date(f);f<n&&f<=r[1]&&(u.push({value:f}),!(s++>3e3));)if(p[o](p[i]()+e),f=p.getTime(),a){var m=a.calcNiceTickMultiple(f,d);m>0&&(p[o](p[i]()+m*e),f=p.getTime())}u.push({value:f,notAdd:f>r[1]})}function u(e,i,a){var o=[],s=!i.length;if(!xie(cm(e),r[0],r[1],n)){s&&(i=[{value:Die(r[0],e,n)},{value:r[1]}]);for(var u=0;u<i.length-1;u++){var d=i[u].value,f=i[u+1].value;if(d!==f){var p=void 0,m=void 0,h=void 0,g=!1;switch(e){case`year`:p=Math.max(1,Math.round(t/tm/365)),m=fne(n),h=mne(n);break;case`half-year`:case`quarter`:case`month`:p=Cie(t),m=dm(n),h=hne(n);break;case`week`:case`half-week`:case`day`:p=Sie(t,31),m=fm(n),h=gne(n),g=!0;break;case`half-day`:case`quarter-day`:case`hour`:p=wie(t),m=pm(n),h=_ne(n);break;case`minute`:p=Tie(t,!0),m=mm(n),h=vne(n);break;case`second`:p=Tie(t,!1),m=hm(n),h=yne(n);break;case`millisecond`:p=Eie(t),m=pne(n),h=bne(n);break}f>=r[0]&&d<=r[1]&&l(p,d,f,m,h,g,o),e===`year`&&a.length>1&&u===0&&a.unshift({value:a[0].value-p})}}for(var u=0;u<o.length;u++)a.push(o[u])}}for(var d=[],f=[],p=0,m=0,h=0;h<o.length;++h){var g=cm(o[h]);if(cne(o[h])&&(u(o[h],d[d.length-1]||[],f),g!==(o[h+1]?cm(o[h+1]):null))){if(f.length){m=p,f.sort(function(e,t){return e.value-t.value});for(var _=[],v=0;v<f.length;++v){var y=f[v].value;(v===0||f[v-1].value!==y)&&(_.push(f[v]),y>=r[0]&&y<=r[1]&&p++)}var b=i/t;if(p>b*1.5&&m>b/1.5||(d.push(_),p>b||e===o[h]))break}f=[]}}for(var x=ce(oe(d,function(e){return ce(e,function(e){return e.value>=r[0]&&e.value<=r[1]&&!e.notAdd})}),function(e){return e.length>0}),S=x.length-1,C=[],h=0;h<x.length;++h)for(var w=x[h],T=0;T<w.length;++T){var E=lm(w[T].value,n);C.push({value:w[T].value,time:{level:S-h,upperTimeUnit:E,lowerTimeUnit:E}})}sc(C,Bee,null),C.sort(function(e,t){return e.value-t.value});var D=C[0],O=C[C.length-1],k=lm(r[0],n),A=lm(r[1],n);return(!D||D.value>r[0])&&C.unshift({value:r[0],time:{level:0,upperTimeUnit:k,lowerTimeUnit:k},notNice:!0}),(!O||O.value<r[1])&&C.push({value:r[1],time:{level:0,upperTimeUnit:A,lowerTimeUnit:A},notNice:!0}),C}var Aie=function(e,t){var n=e.getExtent();if(n[0]===n[1]&&(n[0]-=tm,n[1]+=tm),n[1]===-1/0&&n[0]===1/0){var r=new Date;n[1]=+new Date(r.getFullYear(),r.getMonth(),r.getDate()),n[0]=n[1]-tm}e.setExtent(n[0],n[1]);var i=hie(t.splitNumber,10),a=$m(e)/i,o=t.minInterval,s=t.maxInterval;o!=null&&a<o&&(a=o),s!=null&&a>s&&(a=s);var l=oh.length,u=Math.min(yie(oh,a,0,l),l-1),d=oh[u][1],f=oh[Math.max(u-1,0)][0];e.setTimeInterval({approxInterval:a,interval:d,minLevelUnit:f})};Jm.registerClass(bie);var sh=0,ch=1,jie=2,Mie=function(e){p(t,e);function t(n){var r=e.call(this)||this;r.type=`log`,r.parse=ah.parse,r.base=n.logBase||10;var i=[],a=[],o=r._lookup={from:i,to:a};i[sh]=i[ch]=a[sh]=a[ch]=NaN,rie(r,t.mapperMethods);var s=Jp(),l=n.breakOption,u={lookup:o};return s&&s.parseAxisBreakOptionInwardTransform(l,r,{noNegative:!0},jie,u),r.powStub=new ah({breakParsed:u.original}),r.intervalStub=new ah({breakParsed:u.transformed}),iie(r,r.intervalStub),r}return t.prototype.getTicks=function(e){var t=this.base,n=this.powStub,r=Jp(),i=this.intervalStub,a={lookup:{from:i.getExtent(),to:n.getExtent()}};return oe(i.getTicks(e||{}),function(e){var i=e.value,o=fie(i,t,a),s;if(r){var l=r.getTicksBreakOutwardTransform(this,e,Xp(n),this._lookup);l&&(s=l.vBreak,o=l.tickVal)}return{value:o,break:s}},this)},t.prototype.getMinorTicks=function(e){return vie(this,e,Xp(this.powStub),this.intervalStub.getConfig().interval)},t.prototype.getLabel=function(e,t){return this.intervalStub.getLabel(e,t)},t.type=`log`,t.mapperMethods={needTransform:function(){return!0},normalize:function(e){return this.intervalStub.normalize(ih(e,this.base))},scale:function(e){return fie(this.intervalStub.scale(e),this.base,null)},transformIn:function(e,t){return e=ih(e,this.base),t&&t.depth===2?e:this.intervalStub.transformIn(e,t)},transformOut:function(e,t){var n=t?t.depth:null;return Nie.depth=n,Pie.lookup=this._lookup,fie(n===2?e:this.intervalStub.transformOut(e,Nie),this.base,Pie)},contain:function(e){return this.powStub.contain(e)},setExtent:function(e,t){this.setExtent2(0,e,t)},setExtent2:function(e,t,n){if(!(!nc(t,n)||t<=0||n<=0)){var r=Fie,i=Fie;if(e===0){var a=this._lookup;r=a.to,i=a.from}this.powStub.setExtent2(e,r[sh]=t,r[ch]=n);var o=this.base;this.intervalStub.setExtent2(e,i[sh]=ih(t,o),i[ch]=ih(n,o))}},getFilter:function(){return{g:0}},sanitize:function(e,t){return nc(t[0],t[1])&&gs(e)&&e<=0&&(e=t[0]),e},getDefaultStartValue:function(){return 1},getExtent:function(){return this.powStub.getExtent()},getExtentUnsafe:function(e,t){return t===null?this.powStub.getExtentUnsafe(e,null):this.intervalStub.getExtentUnsafe(e,t)}},t}(Jm);Jm.registerClass(Mie);var Nie={},Pie={},Fie=[],Iie={value:1,category:1,time:1,log:1},Lie=Us();function Rie(e){var t=e.get(`type`);return(t==null||!He(Iie,t)&&!Jm.getClass(t))&&(t=`value`),t}function zie(e,t,n){var r=Jp(),i;switch(r&&(i=qie(e,t,n)),t){case`category`:return new _ie({ordinalMeta:e.getOrdinalMeta?e.getOrdinalMeta():e.getCategories(),extent:Xs()});case`time`:return new bie({locale:e.ecModel.getLocaleModel(),useUTC:e.ecModel.get(`useUTC`),breakOption:i});case`log`:return new Mie({logBase:e.get(`logBase`),breakOption:i});case`value`:return new ah({breakOption:i});default:return new((Jm.getClass(t))||ah)({})}}function Bie(e,t,n){var r=n?Qm(e,null):e.getExtentUnsafe(0,null),i=r[0],a=r[1];return nc(i,a)?i===t||a===t?2:i<t&&a>t?1:3:3}function Vie(e){Lie(e).noOnMyZero=!0}function Hie(e){return Lie(e).noOnMyZero}function lh(e){var t=e.getLabelModel().get(`formatter`);if(e.type===`time`){var n=one(t);return function(t,r){return e.scale.getFormattedLabel(t,r,n)}}else if(ge(t))return function(n){var r=e.scale.getLabel(n);return t.replace(`{value}`,r??``)};else if(he(t)){if(e.type===`category`)return function(n,r){return t(Uie(e,n),n.value-e.scale.getExtent()[0],null)};var r=Jp();return function(n,i){var a=null;return r&&(a=r.makeAxisLabelFormatterParamBreak(a,n.break)),t(Uie(e,n),i,a)}}else return function(t){return e.scale.getLabel(t)}}function Uie(e,t){var n=e.scale;return nh(n)?n.getLabel(t):t.value}function Wie(e){return e.get(`interval`)??`auto`}function Gie(e){return e.type===`category`&&Wie(e.getLabelModel())===0}function Kie(e,t){var n={};return z(e.mapDimensionsAll(t),function(t){n[Cp(e,t)]=!0}),ue(n)}function uh(e){return e===`middle`||e===`center`}function dh(e){return e.getShallow(`show`)}function qie(e,t,n){var r=e.get(`breaks`,!0);if(r!=null)return!Jp()||!n||!Jie(t)?void 0:r}function Jie(e){return e!==`category`}function Yie(e,t,n,r,i,a){var o=th(e),s=o?e.intervalStub:e;if(s.setExtent(r[0],r[1]),o){var l=e.powStub,u={depth:2},d=e.transformOut(r[0],u),f=e.transformOut(r[1],u),p=mie(n,r);t[0]&&!p[0]&&(d=i[0]),t[1]&&!p[1]&&(f=i[1]),l.setExtent(d,f)}s.setConfig(a)}function fh(e,t){return nh(e)?e.getRawOrdinalNumber(t.value):t.value}function Xie(e,t){return nh(e)&&!!t.get(`boundaryGap`)}function Zie(e,t){if(e.length===t.length){for(var n=0;n<e.length;n++)if(e[n]!==t[n])return;return!0}}function Qie(e){for(var t=Xs(),n=Xs(),r=0;r<e.length;){var i=e[r++],a=e[r++];Bm(i,a)||(Zs(t,i),Zs(n,a))}return[t,n]}function $ie(e,t){var n=Qie(e),r=n[0],i=n[1],a=Qie(t),o=a[0],s=a[1];return Math.max(Math.abs(r[0]-o[0]),Math.abs(i[0]-s[0]),Math.abs(r[1]-o[1]),Math.abs(i[1]-s[1]))}function eae(e){return ve(e)?e:e?.5:0}function tae(e,t,n){if(n.valueDim==null)return[];for(var r=t.count(),i=Vm(r*2),a=0;a<r;a++){var o=Pre(n,e,t,a);i[a*2]=o[0],i[a*2+1]=o[1]}return i}function ph(e,t,n,r,i){var a=n.getBaseAxis(),o=a.dim===`x`||a.dim===`radius`?0:1,s=[],l=0,u=[],d=[],f=[],p=[];if(i){for(l=0;l<e.length;l+=2){var m=t||e;Bm(m[l],m[l+1])||p.push(e[l],e[l+1])}e=p}for(l=0;l<e.length-2;l+=2)switch(f[0]=e[l+2],f[1]=e[l+3],d[0]=e[l],d[1]=e[l+1],s.push(d[0],d[1]),r){case`end`:u[o]=f[o],u[1-o]=d[1-o],s.push(u[0],u[1]);break;case`middle`:var h=(d[o]+f[o])/2,g=[];u[o]=g[o]=h,u[1-o]=d[1-o],g[1-o]=f[1-o],s.push(u[0],u[1]),s.push(g[0],g[1]);break;default:u[o]=d[o],u[1-o]=f[1-o],s.push(u[0],u[1])}return s.push(e[l++],e[l++]),s}function nae(e,t){var n=[],r=e.length,i,a;function o(e,t,n){var r=e.coord;return{coord:n,color:Rr((n-r)/(t.coord-r),[e.color,t.color])}}for(var s=0;s<r;s++){var l=e[s],u=l.coord;if(u<0)i=l;else if(u>t){a?n.push(o(a,l,t)):i&&n.push(o(i,l,0),o(i,l,t));break}else i&&=(n.push(o(i,l,0)),null),n.push(l),a=l}return n}function rae(e,t,n){var r=e.getVisual(`visualMeta`);if(!(!r||!r.length||!e.count())&&t.type===`cartesian2d`){for(var i,a,o=r.length-1;o>=0;o--){var s=e.getDimensionInfo(r[o].dimension);if(i=s&&s.coordDim,i===`x`||i===`y`){a=r[o];break}}if(a){var l=t.getAxis(i),u=oe(a.stops,function(e){return{coord:l.toGlobalCoord(l.dataToCoord(e.value)),color:e.color}}),d=u.length,f=a.outerColors.slice();d&&u[0].coord>u[d-1].coord&&(u.reverse(),f.reverse());var p=nae(u,i===`x`?n.getWidth():n.getHeight()),m=p.length;if(!m&&d)return u[0].coord<0?f[1]?f[1]:u[d-1].color:f[0]?f[0]:u[0].color;var h=10,g=p[0].coord-h,_=p[m-1].coord+h,v=_-g;if(v<.001)return`transparent`;z(p,function(e){e.offset=(e.coord-g)/v}),p.push({offset:m?p[m-1].offset:.5,color:f[1]||`transparent`}),p.unshift({offset:m?p[0].offset:.5,color:f[0]||`transparent`});var y=new ju(0,0,0,0,p,!0);return y[i]=g,y[i+`2`]=_,y}}}function iae(e,t,n){var r=e.get(`showAllSymbol`),i=r===`auto`;if(!(r&&!i)){var a=n.getAxesByScale(`ordinal`)[0];if(a&&!(i&&aae(a,t))){var o=t.mapDimension(a.dim),s={};return z(a.getViewLabels(),function(e){e.tick.offInterval||(s[fh(a.scale,e.tick)]=1)}),function(e){return!s.hasOwnProperty(t.get(o,e))}}}}function aae(e,t){var n=e.getExtent(),r=Math.abs(n[1]-n[0])/e.scale.count();isNaN(r)&&(r=0);for(var i=t.count(),a=Math.max(1,Math.round(i/5)),o=0;o<i;o+=a)if(Rm.getSymbolSize(t,o)[+!!e.isHorizontal()]*1.5>r)return!1;return!0}function oae(e){for(var t=e.length/2;t>0&&Bm(e[t*2-2],e[t*2-1]);t--);return t-1}function sae(e,t){return[e[t*2],e[t*2+1]]}function cae(e,t,n){for(var r=e.length/2,i=n===`x`?0:1,a,o,s=0,l=-1,u=0;u<r;u++)if(o=e[u*2+i],!Bm(o,e[u*2+1-i])){if(u===0){a=o;continue}if(a<=t&&o>=t||a>=t&&o<=t){l=u;break}s=u,a=o}return{range:[s,l],t:(t-a)/(o-a)}}function lae(e){if(e.get([`endLabel`,`show`]))return!0;for(var t=0;t<Dc.length;t++)if(e.get([Dc[t],`endLabel`,`show`]))return!0;return!1}function uae(e,t,n,r){if($re(t,`cartesian2d`)){var i=r.getModel(`endLabel`),a=i.get(`valueAnimation`),o=r.getData(),s={lastFrameIndex:0},l=lae(r)?function(n,r){e._endLabelOnDuring(n,r,o,s,a,i,t)}:null,u=t.getBaseAxis().isHorizontal(),d=Xre(t,n,r,function(){var t=e._endLabel;t&&n&&s.originalX!=null&&t.attr({x:s.originalX,y:s.originalY})},l);if(!r.get(`clip`,!0)){var f=d.shape,p=Math.max(f.width,f.height);u?(f.y-=p,f.height+=p*2):(f.x-=p,f.width+=p*2)}return l&&l(1,d),d}else return Zre(t,n,r)}function dae(e,t){var n=t.getBaseAxis(),r=n.isHorizontal(),i=n.inverse,a=r?i?`right`:`left`:`center`,o=r?`middle`:i?`top`:`bottom`;return{normal:{align:e.get(`align`)||a,verticalAlign:e.get(`verticalAlign`)||o}}}var fae=function(e){p(t,e);function t(){return e!==null&&e.apply(this,arguments)||this}return t.prototype.init=function(){var e=new Wl,t=new jre;this.group.add(t.group),this._symbolDraw=t,this._lineGroup=e,this._changePolyState=fe(this._changePolyState,this)},t.prototype.render=function(e,t,n){var r=e.coordinateSystem,i=this.group,a=e.getData(),o=e.getModel(`lineStyle`),s=e.getModel(`areaStyle`),l=a.getLayout(`points`)||[],u=r.type===`polar`,d=this._coordSys,f=this._symbolDraw,p=this._polyline,m=this._polygon,h=this._lineGroup,g=!t.ssr&&e.get(`animation`),_=!s.isEmpty(),v=s.get(`origin`),y=Mre(r,a,v),b=_&&tae(r,a,y),x=e.get(`showSymbol`),S=e.get(`connectNulls`),C=x&&!u&&iae(e,a,r),w=this._data;w&&w.eachItemGraphicEl(function(e,t){e.__temp&&(i.remove(e),w.setItemGraphicEl(t,null))}),x||f.remove(),i.add(h);var T=!u&&e.get(`step`),E;r&&r.getArea&&e.get(`clip`,!0)&&(E=r.getArea(),E.width==null?E.r0&&(E.r0-=.5,E.r+=.5):(E.x-=.1,E.y-=.1,E.width+=.2,E.height+=.2)),this._clipShapeForSymbol=E;var D=rae(a,r,n)||a.getVisual(`style`)[a.getVisual(`drawType`)];if(!(p&&d.type===r.type&&T===this._step))x&&f.updateData(a,{isIgnore:C,clipShape:E,disableAnimation:!0,getSymbolPoint:function(e){return[l[e*2],l[e*2+1]]}}),g&&this._initSymbolLabelAnimation(a,r,E),T&&(b&&=ph(b,l,r,T,S),l=ph(l,null,r,T,S)),p=this._newPolyline(l),_?m=this._newPolygon(l,b):m&&=(h.remove(m),this._polygon=null),u||this._initOrUpdateEndLabel(e,r,Dne(D)),h.setClipPath(uae(this,r,!0,e));else{_&&!m?m=this._newPolygon(l,b):m&&!_&&(h.remove(m),m=this._polygon=null),u||this._initOrUpdateEndLabel(e,r,Dne(D));var O=h.getClipPath();O?qu(O,{shape:uae(this,r,!1,e).shape},e):h.setClipPath(uae(this,r,!0,e)),x&&f.updateData(a,{isIgnore:C,clipShape:E,disableAnimation:!0,getSymbolPoint:function(e){return[l[e*2],l[e*2+1]]}}),(!Zie(this._stackedOnPoints,b)||!Zie(this._points,l))&&(g?this._doUpdateAnimation(a,b,r,n,T,v,S):(T&&(b&&=ph(b,l,r,T,S),l=ph(l,null,r,T,S)),p.setShape({points:l}),m&&m.setShape({points:l,stackedOnPoints:b})))}var k=e.getModel(`emphasis`),A=k.get(`focus`),j=k.get(`blurScope`),M=k.get(`disabled`);if(p.useStyle(te(o.getLineStyle(),{fill:`none`,stroke:D,lineJoin:`bevel`})),_l(p,e,`lineStyle`),p.style.lineWidth>0&&e.get([`emphasis`,`lineStyle`,`width`])===`bolder`){var N=p.getState(`emphasis`).style;N.lineWidth=+p.style.lineWidth+1}dc(p).seriesIndex=e.seriesIndex,pl(p,A,j,M);var P=eae(e.get(`smooth`)),F=e.get(`smoothMonotone`);if(p.setShape({smooth:P,smoothMonotone:F,connectNulls:S}),m){var I=a.getCalculationInfo(`stackedOnSeries`),L=0;m.useStyle(te(s.getAreaStyle(),{fill:D,opacity:.7,lineJoin:`bevel`,decal:a.getVisual(`style`).decal})),I&&(L=eae(I.get(`smooth`))),m.setShape({smooth:P,stackedOnSmooth:L,smoothMonotone:F,connectNulls:S}),_l(m,e,`areaStyle`),dc(m).seriesIndex=e.seriesIndex,pl(m,A,j,M)}var R=this._changePolyState;a.eachItemGraphicEl(function(e){e&&(e.onHoverStateChange=R)}),this._polyline.onHoverStateChange=R,this._data=a,this._coordSys=r,this._stackedOnPoints=b,this._points=l,this._step=T,this._valueOrigin=v;var ee=e.get(`triggerEvent`),ne=e.get(`triggerLineEvent`),re=ne===!0||ee===!0||ee===`line`,ie=ne===!0||ee===!0||ee===`area`;this.packEventData(e,p,re),m&&this.packEventData(e,m,ie)},t.prototype.packEventData=function(e,t,n){dc(t).eventData=n?{componentType:`series`,componentSubType:`line`,componentIndex:e.componentIndex,seriesIndex:e.seriesIndex,seriesName:e.name,seriesType:`line`,selfType:t===this._polygon?`area`:`line`}:null},t.prototype.highlight=function(e,t,n,r){var i=e.getData(),a=Hs(i,r);if(this._changePolyState(`emphasis`),!(a instanceof Array)&&a!=null&&a>=0){var o=i.getLayout(`points`),s=i.getItemGraphicEl(a);if(!s){var l=o[a*2],u=o[a*2+1];if(Bm(l,u)||this._clipShapeForSymbol&&!this._clipShapeForSymbol.contain(l,u))return;var d=e.get(`zlevel`)||0,f=e.get(`z`)||0;s=new Rm(i,a),s.x=l,s.y=u,s.setZ(d,f);var p=s.getSymbolPath().getTextContent();p&&(p.zlevel=d,p.z=f,p.z2=this._polyline.z2+1),s.__temp=!0,i.setItemGraphicEl(a,s),s.stopSymbolAnimation(!0),this.group.add(s)}s.highlight()}else qm.prototype.highlight.call(this,e,t,n,r)},t.prototype.downplay=function(e,t,n,r){var i=e.getData(),a=Hs(i,r);if(this._changePolyState(`normal`),a!=null&&a>=0){var o=i.getItemGraphicEl(a);o&&(o.__temp?(i.setItemGraphicEl(a,null),this.group.remove(o)):o.downplay())}else qm.prototype.downplay.call(this,e,t,n,r)},t.prototype._changePolyState=function(e){var t=this._polygon;Wc(this._polyline,e),t&&Wc(t,e)},t.prototype._newPolyline=function(e){var t=this._polyline;return t&&this._lineGroup.remove(t),t=new Bre({shape:{points:e},segmentIgnoreThreshold:2,z2:10}),this._lineGroup.add(t),this._polyline=t,t},t.prototype._newPolygon=function(e,t){var n=this._polygon;return n&&this._lineGroup.remove(n),n=new Hre({shape:{points:e,stackedOnPoints:t},segmentIgnoreThreshold:2}),this._lineGroup.add(n),this._polygon=n,n},t.prototype._initSymbolLabelAnimation=function(e,t,n){var r,i,a=t.getBaseAxis(),o=a.inverse;t.type===`cartesian2d`?(r=a.isHorizontal(),i=!1):t.type===`polar`&&(r=a.dim===`angle`,i=!0);var s=e.hostModel,l=s.get(`animationDuration`);he(l)&&(l=l(null));var u=s.get(`animationDelay`)||0,d=he(u)?u(null):u;e.eachItemGraphicEl(function(e,a){var s=e;if(s){var f=[e.x,e.y],p=void 0,m=void 0,h=void 0;if(n)if(i){var g=n,_=t.pointToCoord(f);r?(p=g.startAngle,m=g.endAngle,h=-_[1]/180*Math.PI):(p=g.r0,m=g.r,h=_[0])}else{var v=n;r?(p=v.x,m=v.x+v.width,h=e.x):(p=v.y+v.height,m=v.y,h=e.y)}var y=m===p?0:(h-p)/(m-p);o&&(y=1-y);var b=he(u)?u(a):l*y+d,x=s.getSymbolPath(),S=x.getTextContent();s.attr({scaleX:0,scaleY:0}),s.animateTo({scaleX:1,scaleY:1},{duration:200,setToFinal:!0,delay:b}),S&&S.animateFrom({style:{opacity:0}},{duration:300,delay:b}),x.disableLabelAnimation=!0}})},t.prototype._initOrUpdateEndLabel=function(e,t,n){var r=e.getModel(`endLabel`);if(lae(e)){var i=e.getData(),a=this._polyline,o=i.getLayout(`points`);if(!o){a.removeTextContent(),this._endLabel=null;return}var s=this._endLabel;s||(s=this._endLabel=new wo({z2:200}),s.ignoreClip=!0,a.setTextContent(this._endLabel),a.disableLabelAnimation=!0);var l=oae(o);l>=0&&(Bd(a,Vd(e,`endLabel`),{inheritColor:n,labelFetcher:e,labelDataIndex:l,defaultText:function(e,t,n){return n==null?Lm(i,e):Ere(i,n)},enableTextSetter:!0},dae(r,t)),a.textConfig.position=null)}else this._endLabel&&=(this._polyline.removeTextContent(),null)},t.prototype._endLabelOnDuring=function(e,t,n,r,i,a,o){var s=this._endLabel,l=this._polyline;if(s){e<1&&r.originalX==null&&(r.originalX=s.x,r.originalY=s.y);var u=n.getLayout(`points`),d=n.hostModel,f=d.get(`connectNulls`),p=a.get(`precision`),m=a.get(`distance`)||0,h=o.getBaseAxis(),g=h.isHorizontal(),_=h.inverse,v=t.shape,y=_?g?v.x:v.y+v.height:g?v.x+v.width:v.y,b=(g?m:0)*(_?-1:1),x=(g?0:-m)*(_?-1:1),S=g?`x`:`y`,C=cae(u,y,S),w=C.range,T=w[1]-w[0],E=void 0;if(T>=1){if(T>1&&!f){var D=sae(u,w[0]);s.attr({x:D[0]+b,y:D[1]+x}),i&&(E=d.getRawValue(w[0]))}else{var D=l.getPointOn(y,S);D&&s.attr({x:D[0]+b,y:D[1]+x});var O=d.getRawValue(w[0]),k=d.getRawValue(w[1]);i&&(E=Ys(n,p,O,k,C.t))}r.lastFrameIndex=w[0]}else{var A=e===1||r.lastFrameIndex>0?w[0]:0,D=sae(u,A);i&&(E=d.getRawValue(A)),s.attr({x:D[0]+b,y:D[1]+x})}if(i){var j=Yd(s);typeof j.setLabelText==`function`&&j.setLabelText(E)}}},t.prototype._doUpdateAnimation=function(e,t,n,r,i,a,o){var s=this._polyline,l=this._polygon,u=e.hostModel,d=Rre(this._data,e,this._stackedOnPoints,t,this._coordSys,n,this._valueOrigin,a),f=d.current,p=d.stackedOnCurrent,m=d.next,h=d.stackedOnNext;if(i&&(p=ph(d.stackedOnCurrent,d.current,n,i,o),f=ph(d.current,null,n,i,o),h=ph(d.stackedOnNext,d.next,n,i,o),m=ph(d.next,null,n,i,o)),$ie(f,m)>3e3||l&&$ie(p,h)>3e3){s.stopAnimation(),s.setShape({points:m}),l&&(l.stopAnimation(),l.setShape({points:m,stackedOnPoints:h}));return}s.shape.__points=d.current,s.shape.points=f;var g={shape:{points:m}};d.current!==f&&(g.shape.__points=d.next),s.stopAnimation(),Ku(s,g,u),l&&(l.setShape({points:f,stackedOnPoints:p}),l.stopAnimation(),Ku(l,{shape:{stackedOnPoints:h}},u),s.shape.points!==l.shape.points&&(l.shape.points=s.shape.points));for(var _=[],v=d.status,y=0;y<v.length;y++)if(v[y].cmd===`=`){var b=e.getItemGraphicEl(v[y].idx1);b&&_.push({el:b,ptIdx:y})}s.animators&&s.animators.length&&s.animators[0].during(function(){l&&l.dirtyShape();for(var e=s.shape.__points,t=0;t<_.length;t++){var n=_[t].el,r=_[t].ptIdx*2;n.x=e[r],n.y=e[r+1],n.markRedraw()}})},t.prototype.remove=function(e){var t=this.group,n=this._data;this._lineGroup.removeAll(),this._symbolDraw.remove(!0),n&&n.eachItemGraphicEl(function(e,r){e.__temp&&(t.remove(e),n.setItemGraphicEl(r,null))}),this._polyline=this._polygon=this._coordSys=this._points=this._stackedOnPoints=this._endLabel=this._data=null},t.type=`line`,t}(qm);function pae(e,t){return{seriesType:e,plan:Km(),reset:function(e){var n=e.getData(),r=e.coordinateSystem,i=e.pipelineContext,a=t||i.large;if(r){var o=oe(r.dimensions,function(e){return n.mapDimension(e)}).slice(0,2),s=o.length,l=n.getCalculationInfo(`stackResultDimension`);Sp(n,o[0])&&(o[0]=l),Sp(n,o[1])&&(o[1]=l);var u=n.getStore(),d=n.getDimensionIndex(o[0]),f=n.getDimensionIndex(o[1]);return s&&{progress:function(e,t){for(var n=e.end-e.start,i=a&&Vm(n*s),o=[],l=[],p=e.start,m=0;p<e.end;p++){var h=void 0;if(s===1){var g=u.get(d,p);h=r.dataToPoint(g,null,l)}else o[0]=u.get(d,p),o[1]=u.get(f,p),h=r.dataToPoint(o,null,l);a?(i[m++]=h[0],i[m++]=h[1]):t.setItemLayout(p,h.slice())}a&&(t.setLayout(`points`,i),t.setLayout(`pointsRange`,{start:e.start,end:e.end}))}}}}}}var mae={average:function(e){for(var t=0,n=0,r=0;r<e.length;r++)isNaN(e[r])||(t+=e[r],n++);return n===0?NaN:t/n},sum:function(e){for(var t=0,n=0;n<e.length;n++)t+=e[n]||0;return t},max:function(e){for(var t=-1/0,n=0;n<e.length;n++)e[n]>t&&(t=e[n]);return isFinite(t)?t:NaN},min:function(e){for(var t=1/0,n=0;n<e.length;n++)e[n]<t&&(t=e[n]);return isFinite(t)?t:NaN},nearest:function(e){return e[0]}},hae=function(e){return Math.round(e.length/2)};function gae(e){return{seriesType:e,reset:function(e,t,n){var r=e.getData(),i=e.get(`sampling`),a=e.coordinateSystem,o=r.count();if(o>10&&a.type===`cartesian2d`&&i){var s=a.getBaseAxis(),l=a.getOtherAxis(s),u=s.getExtent(),d=n.getDevicePixelRatio(),f=Math.abs(u[1]-u[0])*(d||1),p=Math.round(o/f);if(isFinite(p)&&p>1){i===`lttb`?e.setData(r.lttbDownSample(r.mapDimension(l.dim),1/p)):i===`minmax`&&e.setData(r.minmaxDownSample(r.mapDimension(l.dim),1/p));var m=void 0;ge(i)?m=mae[i]:he(i)&&(m=i),m&&e.setData(r.downSample(r.mapDimension(l.dim),1/p,m,hae))}}}}}function _ae(e){e.registerChartView(fae),e.registerSeriesModel(Tre),e.registerLayout(pae(`line`,!0)),e.registerVisual({seriesType:`line`,reset:function(e){var t=e.getData(),n=e.getModel(`lineStyle`).getLineStyle();n&&!n.stroke&&(n.stroke=t.getVisual(`style`).fill),t.setVisual(`legendLineStyle`,n)}}),e.registerProcessor(e.PRIORITY.PROCESSOR.STATISTIC,gae(`line`))}var vae=Us(),mh=Us(),hh={estimate:1,determine:2};function gh(e){return{out:{noPxChangeTryDetermine:[]},kind:e}}function yae(e,t){var n=e.getLabelModel().get(`customValues`);if(n){var r=e.scale;return{labels:oe(xae(n,r),function(t,n){return{formattedLabel:lh(e)(t,n),rawLabel:r.getLabel(t),tick:t}})}}return e.type===`category`?Sae(e,t):Tae(e)}function bae(e,t,n){var r=e.scale,i=e.getTickModel().get(`customValues`);return i?{ticks:xae(i,r)}:e.type===`category`?wae(e,t):{ticks:r.getTicks(n)}}function xae(e,t){var n=t.getExtent(),r=[];return z(e,function(e){e=t.parse(e),e>=n[0]&&e<=n[1]&&r.push(e)}),sc(r,Vee,null),ts(r),oe(r,function(e){return{value:e}})}function Sae(e,t){var n=e.getLabelModel(),r=Cae(e,n,t);return!n.get(`show`)||e.scale.isBlank()?{labels:[]}:r}function Cae(e,t,n){var r=Dae(e),i=Wie(t),a=n.kind===hh.estimate;if(!a){var o=kae(r,i);if(o)return o}var s,l;he(i)?s=_h(e,i,!1):(l=i===`auto`?jae(e,n):i,s=_h(e,l,!1));var u={labels:s,labelCategoryInterval:l};return a?n.out.noPxChangeTryDetermine.push(function(){return Aae(r,i,u),!0}):Aae(r,i,u),u}function wae(e,t){var n=Eae(e),r=Wie(t),i=kae(n,r);if(i)return i;var a,o;if((!t.get(`show`)||e.scale.isBlank())&&(a=[]),he(r))a=_h(e,r,!0);else if(r===`auto`){var s=Cae(e,e.getLabelModel(),gh(hh.determine));o=s.labelCategoryInterval,a=oe(s.labels,function(e){return e.tick})}else o=r,a=_h(e,o,!0);return Aae(n,r,{ticks:a,tickCategoryInterval:o})}function Tae(e){var t=e.scale.getTicks(),n=lh(e);return{labels:oe(t,function(t,r){return{formattedLabel:n(t,r),rawLabel:e.scale.getLabel(t),tick:t}})}}var Eae=Oae(`axisTick`),Dae=Oae(`axisLabel`);function Oae(e){return function(t){return mh(t)[e]||(mh(t)[e]={list:[]})}}function kae(e,t){for(var n=0;n<e.list.length;n++)if(e.list[n].key===t)return e.list[n].value}function Aae(e,t,n){return e.list.push({key:t,value:n}),n}function jae(e,t){if(t.kind===hh.estimate){var n=e.calculateCategoryInterval(t);return t.out.noPxChangeTryDetermine.push(function(){return mh(e).autoInterval=n,!0}),n}return mh(e).autoInterval??(mh(e).autoInterval=e.calculateCategoryInterval(t))}function Mae(e,t){var n=t.kind,r=Fae(e),i=lh(e),a=(r.axisRotate-r.labelRotate)/180*Math.PI,o=e.scale,s=o.getExtent(),l=o.count();if(s[1]-s[0]<1)return 0;var u=1,d=40;l>d&&(u=Math.max(1,Math.floor(l/d)));for(var f=s[0],p=e.dataToCoord(f+1)-e.dataToCoord(f),m=Math.abs(p*Math.cos(a)),h=Math.abs(p*Math.sin(a)),g=0,_=0;f<=s[1];f+=u){var v=0,y=0,b=bn(i({value:f}),r.font,`center`,`top`);v=b.width*1.3,y=b.height*1.3,g=Math.max(g,v,7),_=Math.max(_,y,7)}var x=g/m,S=_/h;isNaN(x)&&(x=1/0),isNaN(S)&&(S=1/0);var C=Math.max(0,Math.floor(Math.min(x,S)));return n===hh.estimate?(t.out.noPxChangeTryDetermine.push(fe(Nae,null,e,C,l)),C):Pae(e,C,l)??C}function Nae(e,t,n){return Pae(e,t,n)==null}function Pae(e,t,n){var r=vae(e.model),i=e.getExtent(),a=r.lastAutoInterval,o=r.lastTickCount;if(a!=null&&o!=null&&Math.abs(a-t)<=1&&Math.abs(o-n)<=1&&a>t&&r.axisExtent0===i[0]&&r.axisExtent1===i[1])return a;r.lastTickCount=n,r.lastAutoInterval=t,r.axisExtent0=i[0],r.axisExtent1=i[1]}function Fae(e){var t=e.getLabelModel();return{axisRotate:e.getRotate?e.getRotate():e.isHorizontal&&!e.isHorizontal()?90:0,labelRotate:t.get(`rotate`)||0,font:t.getFont()}}function _h(e,t,n){var r=lh(e),i=e.scale,a=[],o=he(t);return gie(i,o?0:t,function(e,s){var l=i.getLabel(e);if(o){var u=!!t(e.value,l);if(e.offInterval=!u,!u&&!s)return}a.push(n?e:{formattedLabel:r(e),rawLabel:l,tick:e})}),a}var vh=Us();function Iae(e){vh(e).prepare={}}function Lae(e){vh(e).fullUpdate={}}function Rae(e){return vh(e).prepare}function yh(e){return vh(e).fullUpdate}var zae=ac(),bh=Us(),Bae=Us();function Vae(e,t){var n=e.model,r=bh(yh(n.ecModel)).keyed,i=r&&r.get(t);return i&&i.get(n.uid)}function Hae(e,t){return Gae(Vae(e,t))}function Uae(e,t){var n=[];return Wae(e.model.ecModel,function(e){for(var r=0;r<t.length;r++)t[r]&&e.serByIdx[t[r].seriesIndex]&&n.push(Gae(e))}),n}function Wae(e,t){var n=bh(yh(e)).keyed;n&&n.each(function(e,n){e.each(function(e,r){t(e,n,r)})})}function Gae(e){return{liPosMinGap:e?e.liPosMinGap:void 0}}function Kae(e,t){var n=e.model.ecModel,r=bh(yh(n)).axSer;r&&Jae(n,r.get(e.model.uid),t)}function qae(e,t,n){var r=Vae(e,t);r&&Jae(e.model.ecModel,r.sers,n)}function Jae(e,t,n){if(t)for(var r=0;r<t.length;r++){var i=t[r];e.isSeriesFiltered(i)||n(i)}}function Yae(e,t,n){var r=bh(yh(e)).keyed,i=r&&r.get(t);i&&i.each(function(e){n(e.axis)})}function Xae(e,t){var n=e.model,r=bh(yh(n.ecModel)).keys;r&&z(r.get(n.uid),function(e){t(e)})}function Zae(e){var t=Bae(Rae(e)),n=t.keyed||=ze();Wae(e,function(t,r,i){var a=n.get(r)||n.set(r,ze()),o=a.get(i)||a.set(i,{});t.metrics.liPosMinGap&&$ae.liPosMinGap(e,t,o)})}function Qae(e,t){$ae[e]=t}var $ae={};function eoe(e,t,n){if(e){var r=t.ecModel,i=bh(yh(r)),a=e.model.uid,o=i.axSer||=ze();(o.get(a)||o.set(a,[])).push(t);var s=t.subType,l=t.getBaseAxis()===e,u=roe.get(toe(s,l,n))||roe.get(toe(s,l,null));if(u){var d=i.keyed||=ze(),f=i.keys||=ze(),p=u.key,m=d.get(p)||d.set(p,ze()),h=m.get(a);h||(h=m.set(a,{axis:e,sers:[],serByIdx:[]}),h.metrics=u.getMetrics(e),(f.get(a)||f.set(a,[])).push(p)),h.sers.push(t),h.serByIdx[t.seriesIndex]=t}}}function toe(e,t,n){return e+`|&`+Ee(t,!0)+`|&`+(n||``)}function noe(e,t){var n=toe(t.seriesType,t.baseAxis,t.coordSysType);roe.set(n,t),zae(e,function(){e.registerProcessor(e.PRIORITY.PROCESSOR.AXIS_STATISTICS,{overallReset:Zae})})}var roe=ze(),ioe=.8;function xh(e,t){t||={};var n={w:NaN,w2:NaN},r=e.scale,i=t.fromStat,a=t.min,o=aie(r);gs(o)||(o=NaN);var s=e.getExtent(),l=Ho(s[1]-s[0]);return nh(r)?aoe(n,e,o,l):i&&ooe(n,e,o,l,i),a!=null&&(n.w=gs(n.w)?Vo(a,n.w):a),n}function aoe(e,t,n,r){var i=t.onBand,a=n+ +!!i;a===0&&(a=1),e.w=r/a,!i&&n&&r&&(e.w2=e.w*n/r)}function ooe(e,t,n,r,i){var a=!1,o=-1/0;z(i.key?[Hae(t,i.key)]:Uae(t,i.sers||[]),function(e){var t=e.liPosMinGap;t!=null&&(t>0?(t>o&&(o=t),a=!1):t===-2&&(a=!0))}),gs(n)&&n>0&&gs(o)?(e.w=r/n*o,e.w2=o):a&&(e.w=r*ioe,e.w2=e.w*n/r)}var soe=[0,1],coe=function(){function e(e,t,n){this.onBand=!1,this.inverse=!1,this.dim=e,this.scale=t,this._extent=n||[0,0]}return e.prototype.contain=function(e){var t=this._extent,n=Math.min(t[0],t[1]),r=Math.max(t[0],t[1]);return e>=n&&e<=r},e.prototype.containData=function(e){return this.scale.contain(this.scale.parse(e))},e.prototype.getExtent=function(){return this._extent.slice()},e.prototype.setExtent=function(e,t){var n=this._extent;n[0]=e,n[1]=t},e.prototype.dataToCoord=function(e,t){var n=this.scale;return e=n.normalize(n.parse(e)),Xo(e,soe,loe(this),t)},e.prototype.coordToData=function(e,t){var n=Xo(e,loe(this),soe,t);return this.scale.scale(n)},e.prototype.pointToData=function(e,t){},e.prototype.getTicksCoords=function(e){e||={};var t=e.tickModel||this.getTickModel(),n=oe(bae(this,t,{breakTicks:e.breakTicks,pruneByBreak:e.pruneByBreak}).ticks,function(e){return{coord:this.dataToCoord(fh(this.scale,e)),tick:e}},this),r=t.get(`alignWithLabel`),i=uoe(this,n,r);return oe(n,function(e){return{coord:e.coord,tickValue:e.tick.value,onBand:i}})},e.prototype.getMinorTicksCoords=function(){if(nh(this.scale))return[];var e=this.model.getModel(`minorTick`).get(`splitNumber`);return e>0&&e<100||(e=5),oe(this.scale.getMinorTicks(e),function(e){return oe(e,function(e){return{coord:this.dataToCoord(e),tickValue:e}},this)},this)},e.prototype.getViewLabels=function(e){return e||=gh(hh.determine),yae(this,e).labels},e.prototype.getLabelModel=function(){return this.model.getModel(`axisLabel`)},e.prototype.getTickModel=function(){return this.model.getModel(`axisTick`)},e.prototype.getBandWidth=function(){return xh(this,{min:1}).w},e.prototype.calculateCategoryInterval=function(e){return e||=gh(hh.determine),Mae(this,e)},e}();function loe(e){var t=e.getExtent();if(e.onBand){var n=(t[1]-t[0])/e.scale.count()/2;t[0]+=n,t[1]-=n}return t}function uoe(e,t,n){var r=t.length;if(!e.onBand||n||!r)return!1;var i=xh(e).w;if(!i)return!1;z(t,function(e){e.coord-=i/2});var a=e.scale.getExtent(),o=t[r-1];return o.tick.offInterval&&t.pop(),t.push({coord:o.coord+i,tick:{value:a[1]+1}}),!0}var doe=function(e){p(t,e);function t(t,n,r,i,a){var o=e.call(this,t,n,r)||this;return o.index=0,o.type=i||`value`,o.position=a||`bottom`,o}return t.prototype.isHorizontal=function(){var e=this.position;return e===`top`||e===`bottom`},t.prototype.getGlobalExtent=function(e){var t=this.getExtent();return t[0]=this.toGlobalCoord(t[0]),t[1]=this.toGlobalCoord(t[1]),e&&t[0]>t[1]&&t.reverse(),t},t.prototype.pointToData=function(e,t){return this.coordToData(this.toLocalCoord(e[this.dim===`x`?0:1]),t)},t.prototype.setCategorySortInfo=function(e){if(this.type!==`category`)return!1;this.model.option.categorySortInfo=e,this.scale.setSortInfo(e)},t}(coe),foe=[`label`,`labelLine`,`layoutOption`,`priority`,`defaultAttr`,`marginForce`,`minMarginForce`,`marginDefault`,`suggestIgnore`],poe=1,Sh=2,moe=poe|Sh;function Ch(e,t,n){n||=moe,t?e.dirty|=n:e.dirty&=~n}function hoe(e,t){return t||=moe,e.dirty==null||!!(e.dirty&t)}function wh(e){if(e)return hoe(e)&&goe(e,e.label,e),e}function goe(e,t,n){var r=t.getComputedTransform();e.transform=jd(e.transform,r);var i=e.localRect=Ad(e.localRect,t.getBoundingRect()),a=t.style,o=a.margin,s=n&&n.marginForce,l=n&&n.minMarginForce,u=n&&n.marginDefault,d=a.__marginType;d==null&&u&&(o=u,d=Xd.textMargin);for(var f=0;f<4;f++)_oe[f]=d===Xd.minMargin&&l&&l[f]!=null?l[f]:s&&s[f]!=null?s[f]:o?o[f]:0;d===Xd.textMargin&&Sd(i,_oe,!1,!1);var p=e.rect=Ad(e.rect,i);return r&&p.applyTransform(r),d===Xd.minMargin&&Sd(p,_oe,!1,!1),e.axisAligned=Od(r),(e.label=e.label||{}).ignore=t.ignore,Ch(e,!1),Ch(e,!0,Sh),e}var _oe=[0,0,0,0];function voe(e,t,n){return e.transform=jd(e.transform,n),e.localRect=Ad(e.localRect,t),e.rect=Ad(e.rect,t),n&&e.rect.applyTransform(n),e.axisAligned=Od(n),e.obb=void 0,(e.label=e.label||{}).ignore=!1,e}function yoe(e,t){if(e){e.label.x+=t.x,e.label.y+=t.y,e.label.markRedraw();var n=e.transform;n&&(n[4]+=t.x,n[5]+=t.y);var r=e.rect;r&&(r.x+=t.x,r.y+=t.y);var i=e.obb;i&&i.fromBoundingRect(e.localRect,n)}}function boe(e,t){for(var n=0;n<foe.length;n++){var r=foe[n];e[r]??(e[r]=t[r])}return wh(e)}function xoe(e){var t=e.obb;return(!t||hoe(e,Sh))&&(e.obb=t||=new Vu,t.fromBoundingRect(e.localRect,e.transform),Ch(e,!1,Sh)),t}function Soe(e,t,n,r,i){var a=e.length,o=ed[t],s=td[t];if(a<2)return!1;e.sort(function(e,t){return e.rect[o]-t.rect[o]});for(var l=0,u,d=!1,f=0,p=0;p<a;p++){var m=e[p],h=m.rect;u=h[o]-l,u<0&&(h[o]-=u,m.label[o]-=u,d=!0);var g=Math.max(-u,0);f+=g,l=h[o]+h[s]}f>0&&i&&C(-f/a,0,a);var _=e[0],v=e[a-1],y,b;x(),y<0&&w(-y,.8),b<0&&w(b,.8),x(),S(y,b,1),S(b,y,-1),x(),y<0&&T(-y),b<0&&T(b);function x(){y=_.rect[o]-n,b=r-v.rect[o]-v.rect[s]}function S(e,t,n){if(e<0){var r=Math.min(t,-e);if(r>0){C(r*n,0,a);var i=r+e;i<0&&w(-i*n,1)}else w(-e*n,1)}}function C(t,n,r){t!==0&&(d=!0);for(var i=n;i<r;i++){var a=e[i],s=a.rect;s[o]+=t,a.label[o]+=t}}function w(t,n){for(var r=[],i=0,l=1;l<a;l++){var u=e[l-1].rect,d=Math.max(e[l].rect[o]-u[o]-u[s],0);r.push(d),i+=d}if(i){var f=Math.min(Math.abs(t)/i,n);if(t>0)for(var l=0;l<a-1;l++){var p=r[l]*f;C(p,0,l+1)}else for(var l=a-1;l>0;l--){var p=r[l-1]*f;C(-p,l,a)}}}function T(e){var t=e<0?-1:1;e=Math.abs(e);for(var n=Math.ceil(e/(a-1)),r=0;r<a-1;r++)if(t>0?C(n,0,r+1):C(-n,a-r-1,a),e-=n,e<=0)return}return d}function Coe(e){var t=[];e.sort(function(e,t){return!!t.suggestIgnore-+!!e.suggestIgnore||t.priority-e.priority});function n(e){if(!e.ignore){var t=e.ensureState(`emphasis`);t.ignore??=!1}e.ignore=!0}for(var r=0;r<e.length;r++){var i=wh(e[r]);if(!i.label.ignore){for(var a=i.label,o=i.labelLine,s=!1,l=0;l<t.length;l++)if(woe(i,t[l],null,{touchThreshold:.05})){s=!0;break}s?(n(a),o&&n(o)):t.push(i)}}}function woe(e,t,n,r){return!e||!t||e.label&&e.label.ignore||t.label&&t.label.ignore||!e.rect.intersect(t.rect,n,r)?!1:e.axisAligned&&t.axisAligned?!0:xoe(e).intersect(xoe(t),n,r)}var Toe=null;function Th(){return Toe}var Eoe=`expandAxisBreak`,Eh=Math.PI,Doe=[[1,2,1,2],[5,3,5,3],[8,3,8,3]],Ooe=[[0,1,0,1],[0,3,0,3],[0,3,0,3]],Dh=Us(),koe=Us(),Aoe=function(){function e(e){this.recordMap={},this.resolveAxisNameOverlap=e}return e.prototype.ensureRecord=function(e){var t=e.axis.dim,n=e.componentIndex,r=this.recordMap,i=r[t]||(r[t]=[]);return i[n]||(i[n]={ready:{}})},e}();function joe(e,t,n,r){var i=n.axis,a=t.ensureRecord(n),o=[],s,l=Xoe(e.axisName)&&uh(e.nameLocation);z(r,function(e){var t=wh(e);if(!(!t||t.label.ignore)){o.push(t);var n=a.transGroup;l&&(n.transform?Et(Oh,n.transform):bt(Oh),t.transform&&St(Oh,Oh,t.transform),an.copy(kh,t.localRect),kh.applyTransform(Oh),s?s.union(kh):an.copy(s=new an(0,0,0,0),kh))}});var u=Math.abs(a.dirVec.x)>.1?`x`:`y`,d=a.transGroup[u];if(o.sort(function(e,t){return Math.abs(e.label[u]-d)-Math.abs(t.label[u]-d)}),l&&s){var f=i.getExtent(),p=Math.min(f[0],f[1]),m=Math.max(f[0],f[1])-p;s.union(new an(p,0,m,1))}a.stOccupiedRect=s,a.labelInfoList=o}var Oh=yt(),kh=new an(0,0,0,0),Moe=function(e,t,n,r,i,a){if(uh(e.nameLocation)){var o=a.stOccupiedRect;o&&Noe(voe({},o,a.transGroup.transform),r,i)}else Poe(a.labelInfoList,a.dirVec,r,i)};function Noe(e,t,n){var r=new Wt;woe(e,t,r,{direction:Math.atan2(n.y,n.x),bidirectional:!1,touchThreshold:.05})&&yoe(t,r)}function Poe(e,t,n,r){for(var i=Wt.dot(r,t)>=0,a=0,o=e.length;a<o;a++){var s=e[i?a:o-1-a];s.label.ignore||Noe(s,n,r)}}var Ah=function(){function e(e,t,n,r){this.group=new Wl,this._axisModel=e,this._api=t,this._local={},this._shared=r||new Aoe(Moe),this._resetCfgDetermined(n)}return e.prototype.updateCfg=function(e){var t=this._cfg.raw;t.position=e.position,t.labelOffset=e.labelOffset,this._resetCfgDetermined(t)},e.prototype.__getRawCfg=function(){return this._cfg.raw},e.prototype._resetCfgDetermined=function(e){var t=this._axisModel,n=t.getDefaultOption?t.getDefaultOption():{},r=Ee(e.axisName,t.get(`name`)),i=t.get(`nameMoveOverlap`);(i==null||i===`auto`)&&(i=Ee(e.defaultNameMoveOverlap,!0));var a={raw:e,position:e.position,rotation:e.rotation,nameDirection:Ee(e.nameDirection,1),tickDirection:Ee(e.tickDirection,1),labelDirection:Ee(e.labelDirection,1),labelOffset:Ee(e.labelOffset,0),silent:Ee(e.silent,!0),axisName:r,nameLocation:De(t.get(`nameLocation`),n.nameLocation,`end`),shouldNameMoveOverlap:Xoe(r)&&i,optionHideOverlap:t.get([`axisLabel`,`hideOverlap`]),showMinorTicks:t.get([`minorTick`,`show`])};this._cfg=a;var o=new Wl({x:a.position[0],y:a.position[1],rotation:a.rotation});o.updateTransform(),this._transformGroup=o;var s=this._shared.ensureRecord(t);s.transGroup=this._transformGroup,s.dirVec=new Wt(Math.cos(-a.rotation),Math.sin(-a.rotation))},e.prototype.build=function(e,t){var n=this;return e||={axisLine:!0,axisTickLabelEstimate:!1,axisTickLabelDetermine:!0,axisName:!0},z(Foe,function(r){e[r]&&Ioe[r](n._cfg,n._local,n._shared,n._axisModel,n.group,n._transformGroup,n._api,t||{})}),this},e.innerTextLayout=function(e,t,n){var r=is(t-e),i,a;return as(r)?(a=n>0?`top`:`bottom`,i=`center`):as(r-Eh)?(a=n>0?`bottom`:`top`,i=`center`):(a=`middle`,i=r>0&&r<Eh?n>0?`right`:`left`:n>0?`left`:`right`),{rotation:r,textAlign:i,textVerticalAlign:a}},e.makeAxisEventDataBase=function(e){var t={componentType:e.mainType,componentIndex:e.componentIndex};return t[e.mainType+`Index`]=e.componentIndex,t},e.isLabelSilent=function(e){var t=e.get(`tooltip`);return e.get(`silent`)||!(e.get(`triggerEvent`)||t&&t.show)},e}(),Foe=[`axisLine`,`axisTickLabelEstimate`,`axisTickLabelDetermine`,`axisName`],Ioe={axisLine:function(e,t,n,r,i,a,o){var s=r.get([`axisLine`,`show`]);if(s===`auto`&&(s=!0,e.raw.axisLineAutoShow!=null&&(s=!!e.raw.axisLineAutoShow)),s){var l=r.axis.getExtent(),u=a.transform,d=[l[0],0],f=[l[1],0],p=d[0]>f[0];u&&(Vt(d,d,u),Vt(f,f,u));var m=R({lineCap:`round`},r.getModel([`axisLine`,`lineStyle`]).getLineStyle()),h={strokeContainThreshold:e.raw.strokeContainThreshold||5,silent:!0,z2:1,style:m};if(r.get([`axisLine`,`breakLine`])&&Zp(r.axis.scale))Th().buildAxisBreakLine(r,i,a,h);else{var g=new Su(R({shape:{x1:d[0],y1:d[1],x2:f[0],y2:f[1]}},h));ud(g.shape,g.style.lineWidth),g.anid=`line`,i.add(g)}var _=r.get([`axisLine`,`symbol`]);if(_!=null){var v=r.get([`axisLine`,`symbolSize`]);ge(_)&&(_=[_,_]),(ge(v)||ve(v))&&(v=[v,v]);var y=wre(r.get([`axisLine`,`symbolOffset`])||0,v),b=v[0],x=v[1];z([{rotate:e.rotation+Math.PI/2,offset:y[0],r:0},{rotate:e.rotation-Math.PI/2,offset:y[1],r:Math.sqrt((d[0]-f[0])*(d[0]-f[0])+(d[1]-f[1])*(d[1]-f[1]))}],function(t,n){if(_[n]!==`none`&&_[n]!=null){var r=Im(_[n],-b/2,-x/2,b,x,m.stroke,!0),a=t.r+t.offset,o=p?f:d;r.attr({rotation:t.rotate,x:o[0]+a*Math.cos(e.rotation),y:o[1]-a*Math.sin(e.rotation),silent:!0,z2:11}),i.add(r)}})}}},axisTickLabelEstimate:function(e,t,n,r,i,a,o,s){Woe(t,i,s)&&Loe(e,t,n,r,i,a,o,hh.estimate)},axisTickLabelDetermine:function(e,t,n,r,i,a,o,s){Woe(t,i,s)&&Loe(e,t,n,r,i,a,o,hh.determine);var l=Hoe(e,i,a,r);Boe(e,t.labelLayoutList,l),Uoe(e,i,a,r,e.tickDirection)},axisName:function(e,t,n,r,i,a,o,s){var l=n.ensureRecord(r);t.nameEl&&=(i.remove(t.nameEl),l.nameLayout=l.nameLocation=null);var u=e.axisName;if(Xoe(u)){var d=e.nameLocation,f=e.nameDirection,p=r.getModel(`nameTextStyle`),m=r.get(`nameGap`)||0,h=r.axis.getExtent(),g=r.axis.inverse?-1:1,_=new Wt(0,0),v=new Wt(0,0);d===`start`?(_.x=h[0]-g*m,v.x=-g):d===`end`?(_.x=h[1]+g*m,v.x=g):(_.x=(h[0]+h[1])/2,_.y=e.labelOffset+f*m,v.y=f);var y=yt();v.transform(wt(y,y,e.rotation));var b=r.get(`nameRotate`);b!=null&&(b=b*Eh/180);var x,S;uh(d)?x=Ah.innerTextLayout(e.rotation,b??e.rotation,f):(x=Roe(e.rotation,d,b||0,h),S=e.raw.axisNameAvailableWidth,S!=null&&(S=Math.abs(S/Math.sin(x.rotation)),!isFinite(S)&&(S=null)));var C=p.getFont(),w=r.get(`nameTruncate`,!0)||{},T=w.ellipsis,E=Te(e.raw.nameTruncateMaxWidth,w.maxWidth,S),D=s.nameMarginLevel||0,O=new wo({x:_.x,y:_.y,rotation:x.rotation,silent:Ah.isLabelSilent(r),style:Hd(p,{text:u,font:C,overflow:`truncate`,width:E,ellipsis:T,fill:p.getTextColor()||r.get([`axisLine`,`lineStyle`,`color`]),align:p.get(`align`)||x.textAlign,verticalAlign:p.get(`verticalAlign`)||x.textVerticalAlign}),z2:1});if(Td({el:O,componentModel:r,itemName:u}),O.__fullText=u,O.anid=`name`,r.get(`triggerEvent`)){var k=Ah.makeAxisEventDataBase(r);k.targetType=`axisName`,k.name=u,dc(O).eventData=k}a.add(O),O.updateTransform(),t.nameEl=O;var A=l.nameLayout=wh({label:O,priority:O.z2,defaultAttr:{ignore:O.ignore},marginDefault:uh(d)?Doe[D]:Ooe[D]});if(l.nameLocation=d,i.add(O),O.decomposeTransform(),e.shouldNameMoveOverlap&&A){var j=n.ensureRecord(r);n.resolveAxisNameOverlap(e,n,r,A,v,j)}}}};function Loe(e,t,n,r,i,a,o,s){Koe(t)||Goe(e,t,i,s,r,o);var l=t.labelLayoutList;Joe(e,r,l,a),Qoe(r,e.rotation,l);var u=e.optionHideOverlap;zoe(r,l,u),u&&Coe(ce(l,function(e){return e&&!e.label.ignore})),joe(e,n,r,l)}function Roe(e,t,n,r){var i=is(n-e),a,o,s=r[0]>r[1],l=t===`start`&&!s||t!==`start`&&s;return as(i-Eh/2)?(o=l?`bottom`:`top`,a=`center`):as(i-Eh*1.5)?(o=l?`top`:`bottom`,a=`center`):(o=`middle`,a=i<Eh*1.5&&i>Eh/2?l?`left`:`right`:l?`right`:`left`),{rotation:i,textAlign:a,textVerticalAlign:o}}function zoe(e,t,n){var r=e.axis,i=e.get([`axisLabel`,`customValues`]);if(Gie(r))return;function a(e,a,o){var s=wh(t[a]),l=wh(t[o]),u=r.scale;if(!(!s||!l)){if(e==null){if(!n&&i)return;var d=Dh(s.label).labelInfo.tick;if(uie(u)&&d.notNice||nh(u)&&d.offInterval){jh(s.label);return}}if(e===!1||s.suggestIgnore){jh(s.label);return}if(l.suggestIgnore){jh(l.label);return}var f=.1;if(!n){var p=[0,0,0,0];s=boe({marginForce:p},s),l=boe({marginForce:p},l)}woe(s,l,null,{touchThreshold:f})&&jh(e?l.label:s.label)}}var o=e.get([`axisLabel`,`showMinLabel`]),s=e.get([`axisLabel`,`showMaxLabel`]),l=t.length;a(o,0,1),a(s,l-1,l-2)}function Boe(e,t,n){e.showMinorTicks||z(t,function(e){if(e&&e.label.ignore)for(var t=0;t<n.length;t++){var r=n[t],i=koe(r),a=Dh(e.label);if(i.tickValue!=null&&!i.onBand&&i.tickValue===a.labelInfo.tick.value){jh(r);return}}})}function jh(e){e&&(e.ignore=!0)}function Voe(e,t,n,r,i){for(var a=[],o=[],s=[],l=0;l<e.length;l++){var u=e[l].coord;o[0]=u,o[1]=0,s[0]=u,s[1]=n,t&&(Vt(o,o,t),Vt(s,s,t));var d=new Su({shape:{x1:o[0],y1:o[1],x2:s[0],y2:s[1]},style:r,z2:2,autoBatch:!0,silent:!0});ud(d.shape,d.style.lineWidth),d.anid=i+`_`+e[l].tickValue,a.push(d);var f=koe(d);f.onBand=!!e[l].onBand,f.tickValue=e[l].tickValue}return a}function Hoe(e,t,n,r){var i=r.axis,a=r.getModel(`axisTick`),o=a.get(`show`);if(o===`auto`&&(o=!0,e.raw.axisTickAutoShow!=null&&(o=!!e.raw.axisTickAutoShow)),!o||i.scale.isBlank())return[];for(var s=a.getModel(`lineStyle`),l=e.tickDirection*a.get(`length`),u=Voe(i.getTicksCoords(),n.transform,l,te(s.getLineStyle(),{stroke:r.get([`axisLine`,`lineStyle`,`color`])}),`ticks`),d=0;d<u.length;d++)t.add(u[d]);return u}function Uoe(e,t,n,r,i){var a=r.axis,o=r.getModel(`minorTick`);if(!(!e.showMinorTicks||a.scale.isBlank())){var s=a.getMinorTicksCoords();if(s.length)for(var l=o.getModel(`lineStyle`),u=i*o.get(`length`),d=te(l.getLineStyle(),te(r.getModel(`axisTick`).getLineStyle(),{stroke:r.get([`axisLine`,`lineStyle`,`color`])})),f=0;f<s.length;f++)for(var p=Voe(s[f],n.transform,u,d,`minorticks_`+f),m=0;m<p.length;m++)t.add(p[m])}}function Woe(e,t,n){if(Koe(e)){var r=e.axisLabelsCreationContext.out.noPxChangeTryDetermine;if(n.noPxChange){for(var i=!0,a=0;a<r.length;a++)i&&=r[a]();if(i)return!1}r.length&&(t.remove(e.labelGroup),qoe(e,null,null,null))}return!0}function Goe(e,t,n,r,i,a){var o=i.axis,s=Te(e.raw.axisLabelShow,i.get([`axisLabel`,`show`])),l=new Wl;n.add(l);var u=gh(r);if(!s||o.scale.isBlank()){qoe(t,[],l,u);return}var d=i.getModel(`axisLabel`),f=o.getViewLabels(u),p=(Te(e.raw.labelRotate,d.get(`rotate`))||0)*Eh/180,m=Ah.innerTextLayout(e.rotation,p,e.labelDirection),h=i.getCategories&&i.getCategories(!0),g=[],_=i.get(`triggerEvent`),v=1/0,y=-1/0;z(f,function(e,t){var n=e.tick,r=e.formattedLabel,s=e.rawLabel,u=d,p=fh(o.scale,n);if(h&&h[p]){var b=h[p];ye(b)&&b.textStyle&&(u=new rf(b.textStyle,d,i.ecModel))}var x=u.getTextColor()||i.get([`axisLine`,`lineStyle`,`color`]),S=u.getShallow(`align`,!0)||m.textAlign,C=Ee(u.getShallow(`alignMinLabel`,!0),S),w=Ee(u.getShallow(`alignMaxLabel`,!0),S),T=u.getShallow(`verticalAlign`,!0)||u.getShallow(`baseline`,!0)||m.textVerticalAlign,E=Ee(u.getShallow(`verticalAlignMinLabel`,!0),T),D=Ee(u.getShallow(`verticalAlignMaxLabel`,!0),T),O=10+(n.time?.level||0);v=Math.min(v,O),y=Math.max(y,O);var k=new wo({x:0,y:0,rotation:0,silent:Ah.isLabelSilent(i),z2:O,style:Hd(u,{text:r,align:t===0?C:t===f.length-1?w:S,verticalAlign:t===0?E:t===f.length-1?D:T,fill:he(x)?x(o.type===`category`?s:o.type===`value`?p+``:p,t):x})});k.anid=`label_`+p;var A=Dh(k);if(A.labelInfo=e,A.layoutRotation=m.rotation,Td({el:k,componentModel:i,itemName:r,formatterParamsExtra:{isTruncated:function(){return k.isTruncated},value:s,tickIndex:t}}),_){var j=Ah.makeAxisEventDataBase(i);j.targetType=`axisLabel`,j.value=s,j.tickIndex=t;var M=e.tick.break;if(M){var N=M.parsedBreak;j.break={start:N.vmin,end:N.vmax}}o.type===`category`&&(j.dataIndex=p),dc(k).eventData=j,M&&Zoe(i,a,k,M)}g.push(k),l.add(k)}),qoe(t,oe(g,function(e){return{label:e,priority:Dh(e).labelInfo.tick.break?e.z2+(y-v+1):e.z2,defaultAttr:{ignore:e.ignore}}}),l,u)}function Koe(e){return!!e.labelLayoutList}function qoe(e,t,n,r){e.labelLayoutList=t,e.labelGroup=n,e.axisLabelsCreationContext=r}function Joe(e,t,n,r){var i=t.get([`axisLabel`,`margin`]);z(n,function(n,a){var o=wh(n);if(o){var s=o.label,l=Dh(s);o.suggestIgnore=s.ignore,s.ignore=!1,Qn(Mh,Yoe);var u=t.axis;Mh.x=u.dataToCoord(fh(u.scale,l.labelInfo.tick)),Mh.y=e.labelOffset+e.labelDirection*i,Mh.rotation=l.layoutRotation,r.add(Mh),Mh.updateTransform(),r.remove(Mh),Mh.decomposeTransform(),Qn(s,Mh),s.markRedraw(),Ch(o,!0),wh(o)}})}var Mh=new yo,Yoe=new yo;function Xoe(e){return!!e}function Zoe(e,t,n,r){n.on(`click`,function(n){var i={type:Eoe,breaks:[{start:r.parsedBreak.breakOption.start,end:r.parsedBreak.breakOption.end}]};i[e.axis.dim+`AxisIndex`]=e.componentIndex,t.dispatchAction(i)})}function Qoe(e,t,n){var r=Jp();if(r){var i=r.retrieveAxisBreakPairs(n,function(e){return e&&Dh(e.label).labelInfo.tick.break},!0),a=e.get([`breakLabelLayout`,`moveOverlap`],!0);(a===!0||a===`auto`)&&z(i,function(r){Th().adjustBreakLabelPair(e.axis.inverse,t,[wh(n[r[0]]),wh(n[r[1]])])})}}function Nh(e,t,n){n||={};var r=t.axis,i={},a=r.getAxesOnZeroOf()[0],o=r.position,s=a?`onZero`:o,l=r.dim,u=[e.x,e.x+e.width,e.y,e.y+e.height],d={left:0,right:1,top:0,bottom:1,onZero:2},f=t.get(`offset`)||0,p=l===`x`?[u[2]-f,u[3]+f]:[u[0]-f,u[1]+f];if(a){var m=a.toGlobalCoord(a.dataToCoord(0));p[d.onZero]=Math.max(Math.min(m,p[1]),p[0])}i.position=[l===`y`?p[d[s]]:u[0],l===`x`?p[d[s]]:u[3]],i.rotation=Math.PI/2*(l===`x`?0:1),i.labelDirection=i.tickDirection=i.nameDirection={top:-1,bottom:1,left:-1,right:1}[o],i.labelOffset=a?p[d[o]]-p[d.onZero]:0,t.get([`axisTick`,`inside`])&&(i.tickDirection=-i.tickDirection),Te(n.labelInside,t.get([`axisLabel`,`inside`]))&&(i.labelDirection=-i.labelDirection);var h=t.get([`axisLabel`,`rotate`]);return i.labelRotate=s===`top`?-h:h,i.z2=1,i}function $oe(e){return e.coordinateSystem&&e.coordinateSystem.type===`cartesian2d`}function ese(e){var t={xAxisModel:null,yAxisModel:null};return z(t,function(n,r){var i=r.replace(/Model$/,``);t[r]=e.getReferringComponents(i,Ks).models[0]}),t}function tse(e,t,n,r,i,a){for(var o=Nh(e,n),s=!1,l=!1,u=0;u<t.length;u++)lie(t[u].getOtherAxis(n.axis).scale)&&(s=l=!0,n.axis.type===`category`&&n.axis.onBand&&(l=!1));return o.axisLineAutoShow=s,o.axisTickAutoShow=l,o.defaultNameMoveOverlap=a,new Ah(n,r,o,i)}function nse(e,t,n){var r=Nh(t,n);e.updateCfg(r)}var rse=Us(),ise=3,ase=function(){function e(e,t,n,r,i){var a=nh(e),o=a?t.getCategories().length:null,s;if(a){var l=t.getCategories(!0);s=l&&!l.length}var u=n.slice();(eh(e)||th(e)||uie(e))&&(Qs(u,Ph(e,t.get(`dataMin`,!0))),$s(u,Ph(e,t.get(`dataMax`,!0)))),rc(u)||(u[0]=u[1]=NaN);var d=[],f=[!1,!1],p=t.get(`min`,!0);p===`dataMin`?(d[0]=u[0],f[0]=!0):(d[0]=Ph(e,he(p)?p({min:u[0],max:u[1]}):p),f[0]=d[0]!=null);var m=t.get(`max`,!0);m===`dataMax`?(d[1]=u[1],f[1]=!0):(d[1]=Ph(e,he(m)?m({min:u[0],max:u[1]}):m),f[1]=d[1]!=null);var h=sse(e,t),g=a?null:u[1]-u[0]||Math.abs(u[0]);d[0]??=a?s?u[0]:o?0:NaN:u[0]-h[0]*g,d[1]??=a?s?u[1]:o?o-1:NaN:u[1]+h[1]*g,!tc(d[0])&&(d[0]=NaN),!tc(d[1])&&(d[1]=NaN);var _=s||we(d[0])||we(d[1])||a&&!o,v=eh(e),y=v&&t.needIncludeZero&&t.needIncludeZero();y&&(d[0]>0&&d[1]>0&&!f[0]&&(d[0]=0),d[0]<0&&d[1]<0&&!f[1]&&(d[1]=0));var b=!1;d[0]>d[1]&&(d.reverse(),b=!0);var x=Ph(e,t.get(`startValue`,!0)),S=x!=null;!gs(x)&&r&&(x=e.getDefaultStartValue?e.getDefaultStartValue():0),gs(x)&&(S||!v||y)&&(x<d[0]&&!f[0]?(d[0]=x,f[0]=!0):x>d[1]&&!f[1]&&(d[1]=x,f[1]=!0)),ose(this._i={scale:e,dataMM:u,noZoomEffMM:d,zoomMM:[],fixMM:f,zoomFixMM:[!1,!1],startValue:x,isBlank:_,incl0:y,tggAxInv:b,ctnShp:i},d)}return e.prototype.makeNoZoom=function(){return this._i.noZoomEffMM.slice()},e.prototype.makeFinal=function(){var e=this._i,t=e.zoomMM,n=e.noZoomEffMM,r=e.zoomFixMM,i=e.fixMM,a={fixMM:i,zoomFixMM:r,isBlank:e.isBlank,incl0:e.incl0,tggAxInv:e.tggAxInv,ctnShp:e.ctnShp,effMM:n.slice()},o=a.effMM;return t[0]!=null&&(o[0]=t[0],i[0]=r[0]=!0),t[1]!=null&&(o[1]=t[1],i[1]=r[1]=!0),ose(e,o),a},e.prototype.makeRenderInfo=function(){return{startValue:this._i.startValue}},e.prototype.setZoomMM=function(e,t){this._i.zoomMM[e]=t},e}();function ose(e,t){var n=e.scale,r=e.dataMM;n.sanitize&&(t[0]=n.sanitize(t[0],r),t[1]=n.sanitize(t[1],r),ic(t))}function Ph(e,t){return t==null?null:we(t)?NaN:e.parse(t)}function sse(e,t){var n;if(nh(e))n=[0,0];else{var r=t.get(`boundaryGap`);typeof r==`boolean`&&(r=null),n=me(r)?r:[r,r]}return[cse(n[0]),cse(n[1])]}function cse(e){return wn(typeof e==`boolean`?0:e,1)||0}function lse(e){var t=rse(e.scale);return t.extent||=Xs(),t}function use(e,t){lse(e).dimIdxInCoord=t.get(e.dim)}function dse(e,t){var n=e.scale,r=e.model,i=e.dim;n.rawExtentInfo||fse(n,e,i,r,t)}function fse(e,t,n,r,i){var a=lse(t),o=a.extent,s=!1;Kae(t,function(r){if(r.boxCoordinateSystem){var i=mp(r).coord,l=a.dimIdxInCoord;if(l>=0&&me(i)){var u=i[l];u!=null&&!me(u)&&Zs(o,e.parse(u))}}else if(r.coordinateSystem){var d=r.getData();if(d){var f=e.getFilter?e.getFilter():null;z(Kie(d,n),function(e){ec(o,d.getApproximateExtent(e,f))})}r.__requireStartValue&&r.__requireStartValue(t)&&(s=!0)}});var l=vse(e,t,r);mse(e,new ase(e,r,o,s,l),i),a.extent=null}function pse(e,t){var n=e.scale;mse(n,new ase(n,e.model,t,!1,!1),ise)}function mse(e,t,n){e.rawExtentInfo=t,t.from=n}function hse(e,t){gse.set(e,t)}var gse=ze();function _se(e,t,n,r,i){e.rawExtentInfo||pse({scale:e,model:t},i||Xs());var a=e.rawExtentInfo.makeFinal(),o=a.effMM;return e.setExtent(o[0],o[1]),e.setBlank(a.isBlank),r&&a.tggAxInv&&n&&!n.get(`legacyMinMaxDontInverseAxis`)&&(r.inverse=!r.inverse),a}function vse(e,t,n){var r=Xie(e,n),i=n.get(`containShape`,!0);if(i==null&&!r&&(i=!0),!i)return!1;var a=!1;return Xae(t,function(e){a=!!gse.get(e)||a}),a}function yse(e,t,n,r){if(n.ctnShp){var i;if(Xae(e,function(t){var n=gse.get(t);if(n){var a=n(e,r);a&&(i||=[0,0],Qs(i,a[0]),$s(i,a[1]),Vie(e))}}),i){var a=t.getExtent();if(nh(t))e.onBand||t.setExtent2(1,Bo(a[0],a[0]+i[0]),Vo(a[1],a[1]+i[1]));else{var o=a.slice();n.zoomFixMM[0]||(o[0]=Bo(o[0],t.transformOut(t.transformIn(o[0],null)+i[0],null))),n.zoomFixMM[1]||(o[1]=Vo(o[1],t.transformOut(t.transformIn(o[1],null)+i[1],null))),(o[0]<a[0]||o[1]>a[1])&&t.setExtent2(1,o[0],o[1])}}}}function bse(){Qae(`liPosMinGap`,xse)}function xse(e,t,n){var r=ze(),i=n.serUids,a=n.liPosMinGap,o,s=t.axis,l=s.scale,u=l.needTransform(),d=l.getFilter?l.getFilter():null,f=Pf(d);function p(n){Jae(e,t.sers,function(e){var t=e.getRawData(),r=t.getDimensionIndex(t.mapDimension(s.dim));r>=0&&n(r,e,t.getStore())})}var m=0;if(p(function(e,t,n){r.set(t.uid,1),(!i||!i.hasKey(t.uid))&&(o=!0),m+=n.count()}),(!i||i.keys().length!==r.keys().length)&&(o=!0),!o&&a!=null){t.liPosMinGap=a;return}Hm(Fh,m);var h=0;p(function(e,t,n){for(var r=0,i=n.count();r<i;++r){var a=n.get(e,r);isFinite(a)&&(!d||Ff(f,a))&&(u&&(a=l.transformIn(a,null)),Fh.arr[h++]=a)}});var g=Fh.typed?Fh.arr.subarray(0,h):(Fh.arr.length=h,Fh.arr);Fh.typed?g.sort():ts(g);for(var _=1/0,v=1;v<h;++v){var y=g[v]-g[v-1];y>0&&y<_&&(_=y)}n.liPosMinGap=t.liPosMinGap=gs(_)?_:h>0?-2:-1,n.serUids=r}var Fh=Hm({ctor:Ire},50);function Sse(e){return function(t,n){var r=xh(t,{fromStat:{key:e}});if(gs(r.w2))return[-r.w2/2,r.w2/2]}}function Ih(e,t){return e+`|&`+t}function Cse(e){return bse(),{liPosMinGap:!nh(e.scale)}}function wse(e,t,n,r){noe(e,{key:t,seriesType:n,coordSysType:r,getMetrics:Cse})}function Tse(e){return e.scale.rawExtentInfo.makeRenderInfo().startValue}var Ese={left:0,right:0,top:0,bottom:0},Lh=[`25%`,`25%`],Rh=`cartesian2d`,Dse=function(e){p(t,e);function t(){return e!==null&&e.apply(this,arguments)||this}return t.prototype.mergeDefaultAndTheme=function(t,n){var r=Cm(t.outerBounds);e.prototype.mergeDefaultAndTheme.apply(this,arguments),r&&t.outerBounds&&Sm(t.outerBounds,r)},t.prototype.mergeOption=function(t,n){e.prototype.mergeOption.apply(this,arguments),this.option.outerBounds&&t.outerBounds&&Sm(this.option.outerBounds,t.outerBounds)},t.type=`grid`,t.dependencies=[`xAxis`,`yAxis`],t.layoutMode=`box`,t.defaultOption={show:!1,z:0,left:`15%`,top:65,right:`10%`,bottom:80,containLabel:!1,outerBoundsMode:`auto`,outerBounds:Ese,outerBoundsContain:`all`,outerBoundsClampWidth:Lh[0],outerBoundsClampHeight:Lh[1],backgroundColor:Dm.color.transparent,borderWidth:1,borderColor:Dm.color.neutral30},t}(wm),Ose=ac(),kse=`__ec_stack_`;function Ase(e){return e.get(`stack`)||kse+e.seriesIndex}function jse(e,t){var n=Mse(e,t);return n.columnMap=Nse(n),n}function Mse(e,t){var n=Ih(t,Rh),r=[],i=xh(e,{fromStat:{key:n},min:1});return qae(e,n,function(e){r.push({barWidth:Zo(e.get(`barWidth`),i.w),barMaxWidth:Zo(e.get(`barMaxWidth`),i.w),barMinWidth:Zo(e.get(`barMinWidth`)||(Ise(e)?.5:1),i.w),barGap:e.get(`barGap`),barCategoryGap:e.get(`barCategoryGap`),defaultBarGap:e.get(`defaultBarGap`),stackId:Ase(e)})}),{bandWidthResult:i,seriesInfo:r}}function Nse(e){var t=e.bandWidthResult.w,n=t,r=0,i,a,o=[],s={};z(e.seriesInfo,function(e,t){t||(a=e.defaultBarGap||0);var l=e.stackId;He(s,l)||r++;var u=s[l];u||(u=s[l]={width:0,maxWidth:0},o.push(l));var d=e.barWidth;d&&!u.width&&(u.width=d,d=Bo(n,d),n-=d);var f=e.barMaxWidth;f&&(u.maxWidth=f);var p=e.barMinWidth;p&&(u.minWidth=p);var m=e.barGap;m!=null&&(a=m);var h=e.barCategoryGap;h!=null&&(i=h)}),i??=Vo(35-o.length*4,15)+`%`;var l=Zo(i,t),u=Zo(a,1),d=(n-l)/(r+(r-1)*u);d=Vo(d,0),z(o,function(e){var t=s[e],i=t.maxWidth,a=t.minWidth;if(t.width){var o=t.width;i&&(o=Bo(o,i)),a&&(o=Vo(o,a)),t.width=o,n-=o+u*o,r--}else{var o=d;i&&i<o&&(o=Bo(i,n)),a&&a>o&&(o=a),o!==d&&(t.width=o,n-=o+u*o,r--)}}),d=(n-l)/(r+(r-1)*u),d=Vo(d,0);var f=0,p;z(o,function(e){var t=s[e];t.width||=d,p=t,f+=t.width*(1+u)}),p&&(f-=p.width*u);var m={},h=-f/2;return z(o,function(e){var n=s[e];m[e]=m[e]||{bandWidth:t,offset:h,width:n.width},h+=n.width*(1+u)}),m}function Pse(e){return{seriesType:e,overallReset:function(t){var n=Ih(e,Rh);Yae(t,n,function(t){var r=jse(t,e);qae(t,n,function(e){var t=r.columnMap[Ase(e)];e.getData().setLayout({bandWidth:t.bandWidth,offset:t.offset,size:t.width})})})}}}function Fse(e){return{seriesType:e,plan:Km(),reset:function(e){if($oe(e)){var t=e.getData(),n=e.coordinateSystem,r=n.getBaseAxis(),i=n.getOtherAxis(r),a=t.getDimensionIndex(t.mapDimension(i.dim)),o=t.getDimensionIndex(t.mapDimension(r.dim)),s=e.get(`showBackground`,!0),l=t.mapDimension(i.dim),u=t.getCalculationInfo(`stackResultDimension`),d=Sp(t,l)&&!!t.getCalculationInfo(`stackedOnSeries`),f=i.isHorizontal(),p=i.toGlobalCoord(i.dataToCoord(Tse(i))),m=Ise(e),h=e.get(`barMinHeight`)||0,g=u&&t.getDimensionIndex(u),_=t.getLayout(`size`),v=t.getLayout(`offset`);return{progress:function(e,t){for(var r=e.count,i=m&&Vm(r*3),l=m&&s&&Vm(r*3),u=m&&Vm(r),y=n.master.getRect(),b=f?y.width:y.height,x,S=t.getStore(),C=0;(x=e.next())!=null;){var w=S.get(d?g:a,x),T=S.get(o,x),E=p,D=void 0;d&&(D=+w-S.get(a,x));var O=void 0,k=void 0,A=void 0,j=void 0;if(f){var M=n.dataToPoint([w,T]);d&&(E=n.dataToPoint([D,T])[0]),O=E,k=M[1]+v,A=M[0]-E,j=_,Ho(A)<h&&(A=(A<0?-1:1)*h)}else{var M=n.dataToPoint([T,w]);d&&(E=n.dataToPoint([T,D])[1]),O=M[0]+v,k=E,A=_,j=M[1]-E,Ho(j)<h&&(j=(j<=0?-1:1)*h)}m?(i[C]=O,i[C+1]=k,i[C+2]=f?A:j,l&&(l[C]=f?y.x:O,l[C+1]=f?k:y.y,l[C+2]=b),u[x]=x):t.setItemLayout(x,{x:O,y:k,width:A,height:j}),C+=3}m&&t.setLayout({largePoints:i,largeDataIndices:u,largeBackgroundPoints:l,valueAxisHorizontal:f})}}}}}}function Ise(e){return e.pipelineContext&&e.pipelineContext.large}function Lse(e){return Sse(Ih(e,Rh))}function Rse(e){Ose(e,function(){function t(t){var n=Ih(t,Rh);wse(e,n,t,Rh),hse(n,Lse(t))}t(`bar`),t(`pictorialBar`)})}var zse=function(e){p(t,e);function t(){var n=e!==null&&e.apply(this,arguments)||this;return n.type=t.type,n}return t.prototype.getInitialData=function(e,t){return Tp(null,this,{useEncodeDefaulter:!0})},t.prototype.getMarkerPosition=function(e,t,n){var r=this.coordinateSystem;if(r&&r.clampData){var i=r.clampData(e),a=r.dataToPoint(i);if(n)z(r.getAxes(),function(e,n){if(e.type===`category`&&t!=null){var r=e.getTicksCoords(),o=e.getTickModel().get(`alignWithLabel`),s=i[n],l=t[n]===`x1`||t[n]===`y1`;if(l&&!o&&(s+=1),r.length<2)return;if(r.length===2){a[n]=e.toGlobalCoord(e.getExtent()[+!!l]);return}for(var u=void 0,d=void 0,f=1,p=0;p<r.length;p++){var m=r[p].coord,h=p===r.length-1?r[p-1].tickValue+f:r[p].tickValue;if(h===s){d=m;break}else if(h<s)u=m;else if(u!=null&&h>s){d=(m+u)/2;break}p===1&&(f=h-r[0].tickValue)}d??(u?u&&(d=r[r.length-1].coord):d=r[0].coord),a[n]=e.toGlobalCoord(d)}});else{var o=this.getData(),s=o.getLayout(`offset`),l=o.getLayout(`size`),u=+!r.getBaseAxis().isHorizontal();a[u]+=s+l/2}return a}return[NaN,NaN]},t.prototype.__requireStartValue=function(e){return this.getBaseAxis()!==e},t.type=`series.__base_bar__`,t.defaultOption={z:2,coordinateSystem:`cartesian2d`,legendHoverLink:!0,barMinHeight:0,barMinAngle:0,large:!1,largeThreshold:400,progressive:3e3,progressiveChunkMode:`mod`,defaultBarGap:`10%`},t}(Nm);Nm.registerClass(zse);var Bse=function(e){p(t,e);function t(){var n=e!==null&&e.apply(this,arguments)||this;return n.type=t.type,n}return t.prototype.getInitialData=function(){return Tp(null,this,{useEncodeDefaulter:!0,createInvertedIndices:!!this.get(`realtimeSort`,!0)||null})},t.prototype.getProgressive=function(){return this.get(`large`)?this.get(`progressive`):!1},t.prototype.__preparePipelineContext=function(e,t){var n=cc(this,e,t);return n.progressiveRender&&(n.large=!0),n},t.prototype.brushSelector=function(e,t,n){return n.rect(t.getItemLayout(e))},t.type=`series.bar`,t.dependencies=[`grid`,`polar`],t.defaultOption=Op(zse.defaultOption,{clip:!0,roundCap:!1,showBackground:!1,backgroundStyle:{color:`rgba(180, 180, 180, 0.2)`,borderColor:null,borderWidth:0,borderType:`solid`,borderRadius:0,shadowBlur:0,shadowColor:null,shadowOffsetX:0,shadowOffsetY:0,opacity:1},select:{itemStyle:{borderColor:Dm.color.primary,borderWidth:2}},realtimeSort:!1}),t}(zse),zh=`\0__throttleOriginMethod`,Vse=`\0__throttleRate`,Hse=`\0__throttleType`;function Bh(e,t,n){var r,i=0,a=0,o=null,s,l,u,d;t||=0;function f(){a=new Date().getTime(),o=null,e.apply(l,u||[])}var p=function(){for(var e=[],p=0;p<arguments.length;p++)e[p]=arguments[p];r=new Date().getTime(),l=this,u=e;var m=d||t,h=d||n;d=null,s=r-(h?i:a)-m,clearTimeout(o),h?o=setTimeout(f,m):s>=0?f():o=setTimeout(f,-s),i=r};return p.clear=function(){o&&=(clearTimeout(o),null)},p.debounceNextCall=function(e){d=e},p}function Use(e,t,n,r){var i=e[t];if(i){var a=i[zh]||i,o=i[Hse];if(i[Vse]!==n||o!==r){if(n==null||!r)return e[t]=a;i=e[t]=Bh(a,n,r===`debounce`),i[zh]=a,i[Hse]=r,i[Vse]=n}return i}}function Wse(e,t){var n=e[t];n&&n[zh]&&(n.clear&&n.clear(),e[t]=n[zh])}var Gse=function(){function e(){this.cx=0,this.cy=0,this.r0=0,this.r=0,this.startAngle=0,this.endAngle=Math.PI*2,this.clockwise=!0}return e}(),Kse=function(e){p(t,e);function t(t){var n=e.call(this,t)||this;return n.type=`sausage`,n}return t.prototype.getDefaultShape=function(){return new Gse},t.prototype.buildPath=function(e,t){var n=t.cx,r=t.cy,i=Math.max(t.r0||0,0),a=Math.max(t.r,0),o=(a-i)*.5,s=i+o,l=t.startAngle,u=t.endAngle,d=t.clockwise,f=Math.PI*2,p=d?u-l<f:l-u<f;p||(l=u-(d?f:-f));var m=Math.cos(l),h=Math.sin(l),g=Math.cos(u),_=Math.sin(u);p?(e.moveTo(m*i+n,h*i+r),e.arc(m*s+n,h*s+r,o,-Math.PI+l,l,!d)):e.moveTo(m*a+n,h*a+r),e.arc(n,r,a,l,u,!d),e.arc(g*s+n,_*s+r,o,u-Math.PI*2,u-Math.PI,!d),i!==0&&e.arc(n,r,i,u,l,d)},t}(io);function qse(e,t){t||={};var n=t.isRoundCap;return function(t,r,i){var a=r.position;if(!a||a instanceof Array)return Tn(t,r,i);var o=e(a),s=r.distance==null?5:r.distance,l=this.shape,u=l.cx,d=l.cy,f=l.r,p=l.r0,m=(f+p)/2,h=l.startAngle,g=l.endAngle,_=(h+g)/2,v=n?Math.abs(f-p)/2:0,y=Math.cos,b=Math.sin,x=u+f*y(h),S=d+f*b(h),C=`left`,w=`top`;switch(o){case`startArc`:x=u+(p-s)*y(_),S=d+(p-s)*b(_),C=`center`,w=`top`;break;case`insideStartArc`:x=u+(p+s)*y(_),S=d+(p+s)*b(_),C=`center`,w=`bottom`;break;case`startAngle`:x=u+m*y(h)+Vh(h,s+v,!1),S=d+m*b(h)+Hh(h,s+v,!1),C=`right`,w=`middle`;break;case`insideStartAngle`:x=u+m*y(h)+Vh(h,-s+v,!1),S=d+m*b(h)+Hh(h,-s+v,!1),C=`left`,w=`middle`;break;case`middle`:x=u+m*y(_),S=d+m*b(_),C=`center`,w=`middle`;break;case`endArc`:x=u+(f+s)*y(_),S=d+(f+s)*b(_),C=`center`,w=`bottom`;break;case`insideEndArc`:x=u+(f-s)*y(_),S=d+(f-s)*b(_),C=`center`,w=`top`;break;case`endAngle`:x=u+m*y(g)+Vh(g,s+v,!0),S=d+m*b(g)+Hh(g,s+v,!0),C=`left`,w=`middle`;break;case`insideEndAngle`:x=u+m*y(g)+Vh(g,-s+v,!0),S=d+m*b(g)+Hh(g,-s+v,!0),C=`right`,w=`middle`;break;default:return Tn(t,r,i)}return t||={},t.x=x,t.y=S,t.align=C,t.verticalAlign=w,t}}function Jse(e,t,n,r){if(ve(r)){e.setTextConfig({rotation:r});return}else if(me(t)){e.setTextConfig({rotation:0});return}var i=e.shape,a=i.clockwise?i.startAngle:i.endAngle,o=i.clockwise?i.endAngle:i.startAngle,s=(a+o)/2,l,u=n(t);switch(u){case`startArc`:case`insideStartArc`:case`middle`:case`insideEndArc`:case`endArc`:l=s;break;case`startAngle`:case`insideStartAngle`:l=a;break;case`endAngle`:case`insideEndAngle`:l=o;break;default:e.setTextConfig({rotation:0});return}var d=Math.PI*1.5-l;u===`middle`&&d>Math.PI/2&&d<Math.PI*1.5&&(d-=Math.PI),e.setTextConfig({rotation:d})}function Vh(e,t,n){return t*Math.sin(e)*(n?-1:1)}function Hh(e,t,n){return t*Math.cos(e)*(n?1:-1)}function Uh(e,t,n){var r=e.get(`borderRadius`);if(r==null)return n?{cornerRadius:0}:null;me(r)||(r=[r,r,r,r]);var i=Math.abs(t.r||0-t.r0||0);return{cornerRadius:oe(r,function(e){return wn(e,i)})}}var Wh=Math.max,Gh=Math.min,Yse=function(e){p(t,e);function t(){var t=e.call(this)||this;return t.type=`bar`,t._isFirstFrame=!0,t}return t.prototype.render=function(e,t,n,r){this._model=e,this._removeOnRenderedListener(n),this._updateDrawMode(e);var i=e.get(`coordinateSystem`);(i===`cartesian2d`||i===`polar`)&&(this._progressiveEls=null,this._isLargeDraw?this._renderLarge(e,t,n):this._renderNormal(e,t,n,r))},t.prototype.incrementalPrepareRender=function(e){this._clear(),this._updateDrawMode(e),this._updateLargeClip(e)},t.prototype.incrementalRender=function(e,t){this._progressiveEls=[],this._incrementalRenderLarge(e,t)},t.prototype.eachRendered=function(e){Dd(this._progressiveEls||this.group,e)},t.prototype._updateDrawMode=function(e){var t=e.pipelineContext.large;(this._isLargeDraw==null||t!==this._isLargeDraw)&&(this._isLargeDraw=t,this._clear())},t.prototype._renderNormal=function(e,t,n,r){var i=this.group,a=e.getData(),o=this._data,s=e.coordinateSystem,l=s.getBaseAxis(),u;s.type===`cartesian2d`?u=l.isHorizontal():s.type===`polar`&&(u=l.dim===`angle`);var d=e.isAnimationEnabled()?e:null,f=Qse(e,s);f&&this._enableRealtimeSort(f,a,n);var p=e.get(`clip`,!0)||f,m=s.getArea();i.removeClipPath();var h=e.get(`roundCap`,!0),g=e.get(`showBackground`,!0),_=e.getModel(`backgroundStyle`),v=_.get(`borderRadius`)||0,y=[],b=this._backgroundEls,x=r&&r.isInitSort,S=r&&r.type===`changeAxisOrder`;function C(e){var t=Kh[s.type](a,e);if(!t)return null;var n=mce(s,u,t);return n.useStyle(_.getItemStyle()),s.type===`cartesian2d`?n.setShape(`r`,v):n.setShape(`cornerRadius`,v),y[e]=n,n}a.diff(o).add(function(t){var n=a.getItemModel(t),r=Kh[s.type](a,t,n);if(r&&(g&&C(t),!(!a.hasValue(t)||!rce[s.type](r)))){var o=!1;p&&(o=Xse[s.type](m,r));var _=Zse[s.type](e,a,t,r,u,d,l.model,!1,h);f&&(_.forceLabelAnimation=!0),oce(_,a,t,n,r,e,u,s.type===`polar`),x?_.attr({shape:r}):f?$se(f,d,_,r,t,u,!1,!1):qu(_,{shape:r},e,t),a.setItemGraphicEl(t,_),i.add(_),_.ignore=o}}).update(function(t,n){var r=a.getItemModel(t),w=Kh[s.type](a,t,r);if(w){if(g){var T=void 0;b.length===0?T=C(n):(T=b[n],T.useStyle(_.getItemStyle()),s.type===`cartesian2d`?T.setShape(`r`,v):T.setShape(`cornerRadius`,v),y[t]=T);var E=Kh[s.type](a,t),D=pce(u,E,s);Ku(T,{shape:D},d,t)}var O=o.getItemGraphicEl(n);if(!a.hasValue(t)||!rce[s.type](w)){i.remove(O);return}var k=!1;if(p&&(k=Xse[s.type](m,w),k&&i.remove(O)),O&&(O.type===`sector`&&h||O.type===`sausage`&&!h)&&(O&&Zu(O,e,n),O=null),O?Qu(O):O=Zse[s.type](e,a,t,w,u,d,l.model,!0,h),f&&(O.forceLabelAnimation=!0),S){var A=O.getTextContent();if(A){var j=Yd(A);j.prevValue!=null&&(j.prevValue=j.value)}}else oce(O,a,t,r,w,e,u,s.type===`polar`);x?O.attr({shape:w}):f?$se(f,d,O,w,t,u,!0,S):Ku(O,{shape:w},e,t,null),a.setItemGraphicEl(t,O),O.ignore=k,i.add(O)}}).remove(function(t){var n=o.getItemGraphicEl(t);n&&Zu(n,e,t)}).execute();var w=this._backgroundGroup||=new Wl;w.removeAll();for(var T=0;T<y.length;++T)w.add(y[T]);i.add(w),this._backgroundEls=y,this._data=a},t.prototype._renderLarge=function(e,t,n){this._clear(),uce(e,this.group),this._updateLargeClip(e)},t.prototype._incrementalRenderLarge=function(e,t){this._removeBackground(),uce(t,this.group,this._progressiveEls,!0)},t.prototype._updateLargeClip=function(e){var t=e.get(`clip`,!0)&&Qre(e.coordinateSystem,!1,e),n=this.group;t?n.setClipPath(t):n.removeClipPath()},t.prototype._enableRealtimeSort=function(e,t,n){var r=this;if(t.count()){var i=e.baseAxis;if(this._isFirstFrame)this._dispatchInitSort(t,e,n),this._isFirstFrame=!1;else{var a=function(e){var n=t.getItemGraphicEl(e),r=n&&n.shape;return r&&Math.abs(i.isHorizontal()?r.height:r.width)||0};this._onRendered=function(){r._updateSortWithinSameData(t,a,i,n)},n.getZr().on(`rendered`,this._onRendered)}}},t.prototype._dataSort=function(e,t,n){var r=[];return e.each(e.mapDimension(t.dim),function(e,t){var i=n(t);i??=NaN,r.push({dataIndex:t,mappedValue:i,ordinalNumber:e})}),r.sort(function(e,t){return t.mappedValue-e.mappedValue}),{ordinalNumbers:oe(r,function(e){return e.ordinalNumber})}},t.prototype._isOrderChangedWithinSameData=function(e,t,n){for(var r=n.scale,i=e.mapDimension(n.dim),a=Number.MAX_VALUE,o=0,s=r.getOrdinalMeta().categories.length;o<s;++o){var l=e.rawIndexOf(i,r.getRawOrdinalNumber(o)),u=l<0?Number.MIN_VALUE:t(e.indexOfRawIndex(l));if(u>a)return!0;a=u}return!1},t.prototype._isOrderDifferentInView=function(e,t){for(var n=t.scale,r=n.getExtent(),i=Math.max(0,r[0]),a=Math.min(r[1],n.getOrdinalMeta().categories.length-1);i<=a;++i)if(e.ordinalNumbers[i]!==n.getRawOrdinalNumber(i))return!0},t.prototype._updateSortWithinSameData=function(e,t,n,r){if(this._isOrderChangedWithinSameData(e,t,n)){var i=this._dataSort(e,n,t);this._isOrderDifferentInView(i,n)&&(this._removeOnRenderedListener(r),r.dispatchAction({type:`changeAxisOrder`,componentType:n.dim+`Axis`,axisId:n.index,sortInfo:i}))}},t.prototype._dispatchInitSort=function(e,t,n){var r=t.baseAxis,i=this._dataSort(e,r,function(n){return e.get(e.mapDimension(t.otherAxis.dim),n)});n.dispatchAction({type:`changeAxisOrder`,componentType:r.dim+`Axis`,isInitSort:!0,axisId:r.index,sortInfo:i})},t.prototype.remove=function(e,t){this._clear(this._model),this._removeOnRenderedListener(t)},t.prototype.dispose=function(e,t){this._removeOnRenderedListener(t)},t.prototype._removeOnRenderedListener=function(e){this._onRendered&&=(e.getZr().off(`rendered`,this._onRendered),null)},t.prototype._clear=function(e){var t=this.group,n=this._data;e&&e.isAnimationEnabled()&&n&&!this._isLargeDraw?(this._removeBackground(),this._backgroundEls=[],n.eachItemGraphicEl(function(t){Zu(t,e,dc(t).dataIndex)})):t.removeAll(),this._data=null,this._isFirstFrame=!0},t.prototype._removeBackground=function(){this.group.remove(this._backgroundGroup),this._backgroundGroup=null},t.type=`bar`,t}(qm),Xse={cartesian2d:function(e,t){var n=t.width<0?-1:1,r=t.height<0?-1:1;n<0&&(t.x+=t.width,t.width=-t.width),r<0&&(t.y+=t.height,t.height=-t.height);var i=e.x+e.width,a=e.y+e.height,o=Wh(t.x,e.x),s=Gh(t.x+t.width,i),l=Wh(t.y,e.y),u=Gh(t.y+t.height,a),d=s<o,f=u<l;return t.x=d&&o>i?s:o,t.y=f&&l>a?u:l,t.width=d?0:s-o,t.height=f?0:u-l,n<0&&(t.x+=t.width,t.width=-t.width),r<0&&(t.y+=t.height,t.height=-t.height),d||f},polar:function(e,t){var n=t.r0<=t.r?1:-1;if(n<0){var r=t.r;t.r=t.r0,t.r0=r}var i=Gh(t.r,e.r),a=Wh(t.r0,e.r0);t.r=i,t.r0=a;var o=i-a<0;if(n<0){var r=t.r;t.r=t.r0,t.r0=r}return o}},Zse={cartesian2d:function(e,t,n,r,i,a,o,s,l){var u=new yo({shape:R({},r),z2:1});if(u.__dataIndex=n,u.name=`item`,a){var d=u.shape,f=i?`height`:`width`;d[f]=0}return u},polar:function(e,t,n,r,i,a,o,s,l){var u=!i&&l?Kse:du,d=new u({shape:r,z2:1});if(d.name=`item`,d.calculateTextPosition=qse(ace(i),{isRoundCap:u===Kse}),a){var f=d.shape,p=i?`r`:`endAngle`,m={};f[p]=i?r.r0:r.startAngle,m[p]=r[p],(s?Ku:qu)(d,{shape:m},a)}return d}};function Qse(e,t){var n=e.get(`realtimeSort`,!0),r=t.getBaseAxis();if(n&&r.type===`category`&&t.type===`cartesian2d`)return{baseAxis:r,otherAxis:t.getOtherAxis(r)}}function $se(e,t,n,r,i,a,o,s){var l,u;a?(u={x:r.x,width:r.width},l={y:r.y,height:r.height}):(u={y:r.y,height:r.height},l={x:r.x,width:r.width}),s||(o?Ku:qu)(n,{shape:l},t,i,null);var d=t?e.baseAxis.model:null;(o?Ku:qu)(n,{shape:u},d,i)}function ece(e,t){for(var n=0;n<t.length;n++)if(!isFinite(e[t[n]]))return!0;return!1}var tce=[`x`,`y`,`width`,`height`],nce=[`cx`,`cy`,`r`,`startAngle`,`endAngle`],rce={cartesian2d:function(e){return!ece(e,tce)},polar:function(e){return!ece(e,nce)}},Kh={cartesian2d:function(e,t,n){var r=e.getItemLayout(t);if(!r)return null;var i=n?sce(n,r):0,a=r.width>0?1:-1,o=r.height>0?1:-1;return{x:r.x+a*i/2,y:r.y+o*i/2,width:r.width-a*i,height:r.height-o*i}},polar:function(e,t,n){var r=e.getItemLayout(t);return{cx:r.cx,cy:r.cy,r0:r.r0,r:r.r,startAngle:r.startAngle,endAngle:r.endAngle,clockwise:r.clockwise}}};function ice(e){return e.startAngle!=null&&e.endAngle!=null&&e.startAngle===e.endAngle}function ace(e){return function(e){var t=e?`Arc`:`Angle`;return function(e){switch(e){case`start`:case`insideStart`:case`end`:case`insideEnd`:return e+t;default:return e}}}(e)}function oce(e,t,n,r,i,a,o,s){var l=t.getItemVisual(n,`style`);if(!s){var u=r.get([`itemStyle`,`borderRadius`])||0;e.setShape(`r`,u)}else if(!a.get(`roundCap`)){var d=e.shape;R(d,Uh(r.getModel(`itemStyle`),d,!0)),e.setShape(d)}e.useStyle(l);var f=r.getShallow(`cursor`);f&&e.attr(`cursor`,f);var p=s?o?i.r>=i.r0?`endArc`:`startArc`:i.endAngle>=i.startAngle?`endAngle`:`startAngle`:o?hce(i,a.coordinateSystem):gce(i,a.coordinateSystem),m=Vd(r);Bd(e,m,{labelFetcher:a,labelDataIndex:n,defaultText:Lm(a.getData(),n),inheritColor:l.fill,defaultOpacity:l.opacity,defaultOutsidePosition:p});var h=e.getTextContent();if(s&&h){var g=r.get([`label`,`position`]);e.textConfig.inside=g===`middle`||null,Jse(e,g===`outside`?p:g,ace(o),r.get([`label`,`rotate`]))}dte(h,m,a.getRawValue(n),function(e){return Ere(t,e)});var _=r.getModel([`emphasis`]);pl(e,_.get(`focus`),_.get(`blurScope`),_.get(`disabled`)),_l(e,r),ice(i)&&(e.style.fill=`none`,e.style.stroke=`none`,z(e.states,function(e){e.style&&(e.style.fill=e.style.stroke=`none`)}))}function sce(e,t){var n=e.get([`itemStyle`,`borderColor`]);if(!n||n===`none`)return 0;var r=e.get([`itemStyle`,`borderWidth`])||0,i=isNaN(t.width)?Number.MAX_VALUE:Math.abs(t.width),a=isNaN(t.height)?Number.MAX_VALUE:Math.abs(t.height);return Math.min(r,i,a)}var cce=function(){function e(){}return e}(),lce=function(e){p(t,e);function t(t){var n=e.call(this,t)||this;return n.type=`largeBar`,n}return t.prototype.getDefaultShape=function(){return new cce},t.prototype.buildPath=function(e,t){for(var n=t.points,r=this.baseDimIdx,i=1-this.baseDimIdx,a=[],o=[],s=this.barWidth,l=0;l<n.length;l+=3)o[r]=s,o[i]=n[l+2],a[r]=n[l+r],a[i]=n[l+i],e.rect(a[0],a[1],o[0],o[1])},t}(io);function uce(e,t,n,r){var i=e.getData(),a=+!!i.getLayout(`valueAxisHorizontal`),o=i.getLayout(`largeDataIndices`),s=i.getLayout(`size`),l=e.getModel(`backgroundStyle`),u=i.getLayout(`largeBackgroundPoints`),d=r?Hee(e):0;if(u){var f=new lce({shape:{points:u},incremental:d,silent:!0,z2:0});f.baseDimIdx=a,f.largeDataIndices=o,f.barWidth=s,f.useStyle(l.getItemStyle()),t.add(f),n&&n.push(f)}var p=new lce({shape:{points:i.getLayout(`largePoints`)},incremental:d,ignoreCoarsePointer:!0,z2:1});p.baseDimIdx=a,p.largeDataIndices=o,p.barWidth=s,t.add(p),p.useStyle(i.getVisual(`style`)),p.style.stroke=null,dc(p).seriesIndex=e.seriesIndex,e.get(`silent`)||(p.on(`mousedown`,dce),p.on(`mousemove`,dce)),n&&n.push(p)}var dce=Bh(function(e){var t=this,n=fce(t,e.offsetX,e.offsetY);dc(t).dataIndex=n>=0?n:null},30,!1);function fce(e,t,n){for(var r=e.baseDimIdx,i=1-r,a=e.shape.points,o=e.largeDataIndices,s=[],l=[],u=e.barWidth,d=0,f=a.length/3;d<f;d++){var p=d*3;if(l[r]=u,l[i]=a[p+2],s[r]=a[p+r],s[i]=a[p+i],l[i]<0&&(s[i]+=l[i],l[i]=-l[i]),t>=s[0]&&t<=s[0]+l[0]&&n>=s[1]&&n<=s[1]+l[1])return o[d]}return-1}function pce(e,t,n){if($re(n,`cartesian2d`)){var r=t,i=n.getArea();return{x:e?r.x:i.x,y:e?i.y:r.y,width:e?r.width:i.width,height:e?i.height:r.height}}else{var i=n.getArea(),a=t;return{cx:i.cx,cy:i.cy,r0:e?i.r0:a.r0,r:e?i.r:a.r,startAngle:e?a.startAngle:0,endAngle:e?a.endAngle:Math.PI*2}}}function mce(e,t,n){return new(e.type===`polar`?du:yo)({shape:pce(t,n,e),silent:!0,z2:0})}function hce(e,t){return e.height===0?t.getOtherAxis(t.getBaseAxis()).inverse?`bottom`:`top`:e.height>0?`bottom`:`top`}function gce(e,t){return e.width===0?t.getOtherAxis(t.getBaseAxis()).inverse?`left`:`right`:e.width>=0?`right`:`left`}function _ce(e){e.registerChartView(Yse),e.registerSeriesModel(Bse),e.registerLayout(e.PRIORITY.VISUAL.LAYOUT,Pse(`bar`)),e.registerLayout(e.PRIORITY.VISUAL.PROGRESSIVE_LAYOUT,Fse(`bar`)),e.registerProcessor(e.PRIORITY.PROCESSOR.STATISTIC,gae(`bar`)),e.registerAction({type:`changeAxisOrder`,event:`changeAxisOrder`,update:`update`},function(e,t){var n=e.componentType||`series`;t.eachComponent({mainType:n,query:e},function(t){e.sortInfo&&t.axis.setCategorySortInfo(e.sortInfo)})}),Rse(e)}function vce(e,t){function n(t,n){var r=[];return t.eachComponent({mainType:`series`,subType:e,query:n},function(e){r.push(e.seriesIndex)}),r}z([[e+`ToggleSelect`,`toggleSelect`],[e+`Select`,`select`],[e+`UnSelect`,`unselect`]],function(e){t(e[0],function(t,r,i){t=R({},t),i.dispatchAction(R(t,{type:e[1],seriesIndex:n(r,t)}))})})}function qh(e,t,n,r,i){var a=e+t;n.isSilent(a)||r.eachComponent({mainType:`series`,subType:`pie`},function(e){for(var t=e.seriesIndex,r=e.option.selectedMap,o=i.selected,s=0;s<o.length;s++)if(o[s].seriesIndex===t){var l=e.getData(),u=Hs(l,i.fromActionPayload);n.trigger(a,{type:a,seriesId:e.id,name:me(u)?l.getName(u[0]):l.getName(u),selected:ge(r)?r:R({},r)})}})}function yce(e,t,n){e.on(`selectchanged`,function(e){var r=n.getModel();e.isFromClick?(qh(`map`,`selectchanged`,t,r,e),qh(`pie`,`selectchanged`,t,r,e)):e.fromAction===`select`?(qh(`map`,`selected`,t,r,e),qh(`pie`,`selected`,t,r,e)):e.fromAction===`unselect`&&(qh(`map`,`unselected`,t,r,e),qh(`pie`,`unselected`,t,r,e))})}function bce(e){return{seriesType:e,reset:function(e,t){var n=t.findComponents({mainType:`legend`});if(!(!n||!n.length)){var r=e.getData();r.filterSelf(function(e){for(var t=r.getName(e),i=0;i<n.length;i++)if(!n[i].isSelected(t))return!1;return!0})}}}}function xce(e,t,n){t=me(t)&&{coordDimensions:t}||R({encodeDefine:e.getEncode()},t);var r=e.getSource(),i=op(r,t).dimensions,a=new ap(i,e);return a.initData(r,n),a}var Sce=function(){function e(e,t){this._getDataWithEncodedVisual=e,this._getRawData=t}return e.prototype.getAllNames=function(){var e=this._getRawData();return e.mapArray(e.getName)},e.prototype.containName=function(e){return this._getRawData().indexOfName(e)>=0},e.prototype.indexOfName=function(e){return this._getDataWithEncodedVisual().indexOfName(e)},e.prototype.getItemVisual=function(e,t){return this._getDataWithEncodedVisual().getItemVisual(e,t)},e}(),Cce=Us(),wce=function(e){p(t,e);function t(){var n=e!==null&&e.apply(this,arguments)||this;return n.type=t.type,n}return t.prototype.init=function(t){e.prototype.init.apply(this,arguments),this.legendVisualProvider=new Sce(fe(this.getData,this),fe(this.getRawData,this)),this._defaultLabelLine(t)},t.prototype.mergeOption=function(){e.prototype.mergeOption.apply(this,arguments)},t.prototype.getInitialData=function(){return xce(this,{coordDimensions:[`value`],encodeDefaulter:pe(uf,this)})},t.prototype.getDataParams=function(t){var n=this.getData(),r=Cce(n),i=r.seats;if(!i){var a=[];n.each(n.mapDimension(`value`),function(e){a.push(e)}),i=r.seats=Mee(a,n.hostModel.get(`percentPrecision`))}var o=e.prototype.getDataParams.call(this,t);return o.percent=i[t]||0,o.$vars.push(`percent`),o},t.prototype._defaultLabelLine=function(e){ws(e,`labelLine`,[`show`]);var t=e.labelLine,n=e.emphasis.labelLine;t.show=t.show&&e.label.show,n.show=n.show&&e.emphasis.label.show},t.type=`series.pie`,t.defaultOption={z:2,legendHoverLink:!0,colorBy:`data`,center:[`50%`,`50%`],radius:[0,`50%`],clockwise:!0,startAngle:90,endAngle:`auto`,padAngle:0,minAngle:0,minShowLabelAngle:0,selectedOffset:10,percentPrecision:2,stillShowZeroSum:!0,coordinateSystemUsage:`box`,left:0,top:0,right:0,bottom:0,width:null,height:null,label:{rotate:0,show:!0,overflow:`truncate`,position:`outer`,alignTo:`none`,edgeDistance:`25%`,distanceToLabelLine:5},labelLine:{show:!0,length:15,length2:30,smooth:!1,minTurnAngle:90,maxSurfaceAngle:90,lineStyle:{width:1,type:`solid`}},itemStyle:{borderWidth:1,borderJoin:`round`},showEmptyCircle:!0,emptyCircleStyle:{color:`lightgray`,opacity:1},labelLayout:{hideOverlap:!0},emphasis:{scale:!0,scaleSize:5},avoidLabelOverlap:!0,animationType:`expansion`,animationDuration:1e3,animationTypeUpdate:`transition`,animationEasingUpdate:`cubicInOut`,animationDurationUpdate:500,animationEasing:`cubicInOut`},t}(Nm);fp({fullType:wce.type,getCoord2:function(e){return e.getShallow(`center`)}}),Math.PI*2,La.CMD;function Tce(e,t,n,r,i,a,o,s){var l=i-e,u=a-t,d=n-e,f=r-t,p=Math.sqrt(d*d+f*f);d/=p,f/=p;var m=(l*d+u*f)/p;s&&(m=Math.min(Math.max(m,0),1)),m*=p;var h=o[0]=e+m*d,g=o[1]=t+m*f;return Math.sqrt((h-i)*(h-i)+(g-a)*(g-a))}var Jh=new Wt,Yh=new Wt,Xh=new Wt,Zh=new Wt,Qh=new Wt,$h=[],eg=new Wt;function Ece(e,t){if(t<=180&&t>0){t=t/180*Math.PI,Jh.fromArray(e[0]),Yh.fromArray(e[1]),Xh.fromArray(e[2]),Wt.sub(Zh,Jh,Yh),Wt.sub(Qh,Xh,Yh);var n=Zh.len(),r=Qh.len();if(!(n<.001||r<.001)){Zh.scale(1/n),Qh.scale(1/r);var i=Zh.dot(Qh);if(Math.cos(t)<i){var a=Tce(Yh.x,Yh.y,Xh.x,Xh.y,Jh.x,Jh.y,$h,!1);eg.fromArray($h),eg.scaleAndAdd(Qh,a/Math.tan(Math.PI-t));var o=Xh.x===Yh.x?(eg.y-Yh.y)/(Xh.y-Yh.y):(eg.x-Yh.x)/(Xh.x-Yh.x);if(isNaN(o))return;o<0?Wt.copy(eg,Yh):o>1&&Wt.copy(eg,Xh),eg.toArray(e[1])}}}}function Dce(e,t,n){if(n<=180&&n>0){n=n/180*Math.PI,Jh.fromArray(e[0]),Yh.fromArray(e[1]),Xh.fromArray(e[2]),Wt.sub(Zh,Yh,Jh),Wt.sub(Qh,Xh,Yh);var r=Zh.len(),i=Qh.len();if(!(r<.001||i<.001)&&(Zh.scale(1/r),Qh.scale(1/i),Zh.dot(t)<Math.cos(n))){var a=Tce(Yh.x,Yh.y,Xh.x,Xh.y,Jh.x,Jh.y,$h,!1);eg.fromArray($h);var o=Math.PI/2,s=o+Math.acos(Qh.dot(t))-n;if(s>=o)Wt.copy(eg,Xh);else{eg.scaleAndAdd(Qh,a/Math.tan(Math.PI/2-s));var l=Xh.x===Yh.x?(eg.y-Yh.y)/(Xh.y-Yh.y):(eg.x-Yh.x)/(Xh.x-Yh.x);if(isNaN(l))return;l<0?Wt.copy(eg,Yh):l>1&&Wt.copy(eg,Xh)}eg.toArray(e[1])}}}function tg(e,t,n,r){var i=n===`normal`,a=i?e:e.ensureState(n);a.ignore=t;var o=r.get(`smooth`);o=o===!0?.3:Math.max(+o,0)||0,a.shape=a.shape||{},a.shape.smooth=o;var s=r.getModel(`lineStyle`).getLineStyle();i?e.useStyle(s):a.style=s}function Oce(e,t){var n=t.smooth,r=t.points;if(r)if(e.moveTo(r[0][0],r[0][1]),n>0&&r.length>=3){var i=Lt(r[0],r[1]),a=Lt(r[1],r[2]);if(!i||!a){e.lineTo(r[1][0],r[1][1]),e.lineTo(r[2][0],r[2][1]);return}var o=Math.min(i,a)*n,s=Bt([],r[1],r[0],o/i),l=Bt([],r[1],r[2],o/a),u=Bt([],s,l,.5);e.bezierCurveTo(s[0],s[1],s[0],s[1],u[0],u[1]),e.bezierCurveTo(l[0],l[1],l[0],l[1],r[2][0],r[2][1])}else for(var d=1;d<r.length;d++)e.lineTo(r[d][0],r[d][1])}function kce(e,t,n){var r=e.getTextGuideLine(),i=e.getTextContent();if(!i){r&&e.removeTextGuideLine();return}for(var a=t.normal,o=a.get(`show`),s=i.ignore,l=0;l<Oc.length;l++){var u=Oc[l],d=t[u],f=u===`normal`;if(d){var p=d.get(`show`);if((f?s:Ee(i.states[u]&&i.states[u].ignore,s))||!Ee(p,o)){var m=f?r:r&&r.states[u];m&&(m.ignore=!0),r&&tg(r,!0,u,d);continue}r||(r=new yu,e.setTextGuideLine(r),!f&&(s||!o)&&tg(r,!0,`normal`,t.normal),e.stateProxy&&(r.stateProxy=e.stateProxy)),tg(r,!1,u,d)}}if(r){te(r.style,n),r.style.fill=null;var h=a.get(`showAbove`),g=e.textGuideLineConfig=e.textGuideLineConfig||{};g.showAbove=h||!1,r.buildPath=Oce}}function Ace(e,t){t||=`labelLine`;for(var n={normal:e.getModel(t)},r=0;r<Dc.length;r++){var i=Dc[r];n[i]=e.getModel([i,t])}return n}var jce=Math.PI/180;function Mce(e,t,n,r,i,a,o,s,l,u){if(e.length<2)return;function d(e){for(var a=e.rB,o=a*a,s=0;s<e.list.length;s++){var l=e.list[s],u=Math.abs(l.label.y-n),d=r+l.len,f=d*d,p=t+(Math.sqrt(Math.abs((1-u*u/o)*f))+l.len2)*i,m=p-l.label.x;Pce(l,l.targetTextWidth-m*i,!0),l.label.x=p}}function f(e){for(var a={list:[],maxY:0},o={list:[],maxY:0},s=0;s<e.length;s++)if(e[s].labelAlignTo===`none`){var l=e[s],u=l.label.y>n?o:a,f=Math.abs(l.label.y-n);if(f>=u.maxY){var p=l.label.x-t-l.len2*i,m=r+l.len;u.rB=Math.abs(p)<m?Math.sqrt(f*f/(1-p*p/m/m)):m,u.maxY=f}u.list.push(l)}d(a),d(o)}for(var p=e.length,m=0;m<p;m++)if(e[m].position===`outer`&&e[m].labelAlignTo===`labelLine`){var h=e[m].label.x-u;e[m].linePoints[1][0]+=h,e[m].label.x=u}Soe(e,1,l,l+o)&&f(e)}function Nce(e,t,n,r,i,a,o,s){for(var l=[],u=[],d=Number.MAX_VALUE,f=-Number.MAX_VALUE,p=0;p<e.length;p++){var m=e[p].label;ng(e[p])||(m.x<t?(d=Math.min(d,m.x),l.push(e[p])):(f=Math.max(f,m.x),u.push(e[p])))}for(var p=0;p<e.length;p++){var h=e[p];if(!ng(h)&&h.linePoints){if(h.labelStyleWidth!=null)continue;var m=h.label,g=h.linePoints,_=void 0;_=h.labelAlignTo===`edge`?m.x<t?g[2][0]-h.labelDistance-o-h.edgeDistance:o+i-h.edgeDistance-g[2][0]-h.labelDistance:h.labelAlignTo===`labelLine`?m.x<t?d-o-h.bleedMargin:o+i-f-h.bleedMargin:m.x<t?m.x-o-h.bleedMargin:o+i-m.x-h.bleedMargin,h.targetTextWidth=_,Pce(h,_,!1)}}Mce(u,t,n,r,1,i,a,o,s,f),Mce(l,t,n,r,-1,i,a,o,s,d);for(var p=0;p<e.length;p++){var h=e[p];if(!ng(h)&&h.linePoints){var m=h.label,g=h.linePoints,v=h.labelAlignTo===`edge`,y=m.style.padding,b=y?y[1]+y[3]:0,x=m.style.backgroundColor?0:b,S=h.rect.width+x,C=g[1][0]-g[2][0];v?m.x<t?g[2][0]=o+h.edgeDistance+S+h.labelDistance:g[2][0]=o+i-h.edgeDistance-S-h.labelDistance:(m.x<t?g[2][0]=m.x+h.labelDistance:g[2][0]=m.x-h.labelDistance,g[1][0]=g[2][0]+C),g[1][1]=g[2][1]=m.y}}}function Pce(e,t,n){if(e.labelStyleWidth==null){var r=e.label,i=r.style,a=e.rect,o=i.backgroundColor,s=i.padding,l=s?s[1]+s[3]:0,u=i.overflow,d=a.width+(o?0:l);if(t<d||n){if(u&&u.match(`break`)){r.setStyle(`backgroundColor`,null),r.setStyle(`width`,t-l);var f=r.getBoundingRect();r.setStyle(`width`,Math.ceil(f.width)),r.setStyle(`backgroundColor`,o)}else{var p=t-l,m=t<d?p:n?p>e.unconstrainedWidth?null:p:null;r.setStyle(`width`,m)}Fce(a,r)}}}function Fce(e,t){Lce.rect=e,goe(Lce,t,Ice)}var Ice={minMarginForce:[null,0,null,0],marginDefault:[1,0,1,0]},Lce={};function ng(e){return e.position===`center`}function Rce(e){var t=e.getData(),n=[],r,i,a=!1,o=(e.get(`minShowLabelAngle`)||0)*jce,s=t.getLayout(`viewRect`),l=t.getLayout(`r`),u=s.width,d=s.x,f=s.y,p=s.height;function m(e){e.ignore=!0}function h(e){if(!e.ignore)return!0;for(var t in e.states)if(e.states[t].ignore===!1)return!0;return!1}t.each(function(e){var s=t.getItemGraphicEl(e),f=s.shape,g=s.getTextContent(),_=s.getTextGuideLine(),v=t.getItemModel(e),y=v.getModel(`label`),b=y.get(`position`)||v.get([`emphasis`,`label`,`position`]),x=y.get(`distanceToLabelLine`),S=y.get(`alignTo`),C=Zo(y.get(`edgeDistance`),u),w=y.get(`bleedMargin`);w??=Math.min(u,p)>200?10:2;var T=v.getModel(`labelLine`),E=T.get(`length`);E=Zo(E,u);var D=T.get(`length2`);if(D=Zo(D,u),Math.abs(f.endAngle-f.startAngle)<o){z(g.states,m),g.ignore=!0,_&&(z(_.states,m),_.ignore=!0);return}if(h(g)){var O=(f.startAngle+f.endAngle)/2,k=Math.cos(O),A=Math.sin(O),j,M,N,P;r=f.cx,i=f.cy;var F=b===`inside`||b===`inner`;if(b===`center`)j=f.cx,M=f.cy,P=`center`;else{var I=(F?(f.r+f.r0)/2*k:f.r*k)+r,L=(F?(f.r+f.r0)/2*A:f.r*A)+i;if(j=I+k*3,M=L+A*3,!F){var R=I+k*(E+l-f.r),ee=L+A*(E+l-f.r),te=R+(k<0?-1:1)*D,ne=ee;j=S===`edge`?k<0?d+C:d+u-C:te+(k<0?-x:x),M=ne,N=[[I,L],[R,ee],[te,ne]]}P=F?`center`:S===`edge`?k>0?`right`:`left`:k>0?`left`:`right`}var re=Math.PI,ie=0,ae=y.get(`rotate`);if(ve(ae))ie=re/180*ae;else if(b===`center`)ie=0;else if(ae===`radial`||ae===!0)ie=k<0?-O+re:-O;else if(ae===`tangential`||ae===`tangential-noflip`&&b!==`outside`&&b!==`outer`){var oe=Math.atan2(k,A);oe<0&&(oe=re*2+oe),A>0&&ae!==`tangential-noflip`&&(oe=re+oe),ie=oe-re}if(a=!!ie,g.x=j,g.y=M,g.rotation=ie,g.setStyle({verticalAlign:`middle`}),F){g.setStyle({align:P});var se=g.states.select;se&&(se.x+=g.x,se.y+=g.y)}else{var ce=new an(0,0,0,0);Fce(ce,g),n.push({label:g,labelLine:_,position:b,len:E,len2:D,minTurnAngle:T.get(`minTurnAngle`),maxSurfaceAngle:T.get(`maxSurfaceAngle`),surfaceNormal:new Wt(k,A),linePoints:N,textAlign:P,labelDistance:x,labelAlignTo:S,edgeDistance:C,bleedMargin:w,rect:ce,unconstrainedWidth:ce.width,labelStyleWidth:g.style.width})}s.setTextConfig({inside:F})}}),!a&&e.get(`avoidLabelOverlap`)&&Nce(n,r,i,l,u,p,d,f);for(var g=0;g<n.length;g++){var _=n[g],v=_.label,y=_.labelLine,b=isNaN(v.x)||isNaN(v.y);if(v){v.setStyle({align:_.textAlign}),b&&(z(v.states,m),v.ignore=!0);var x=v.states.select;x&&(x.x+=v.x,x.y+=v.y)}if(y){var S=_.linePoints;b||!S?(z(y.states,m),y.ignore=!0):(Ece(S,_.minTurnAngle),Dce(S,_.surfaceNormal,_.maxSurfaceAngle),y.setShape({points:S}),v.__hostTarget.textGuideLineConfig={anchor:new Wt(S[0][0],S[0][1])})}}}var zce=Math.PI*2,rg=Math.PI/180,Bce=lc(`pie`,Vce);function Vce(e,t){e.eachSeriesByType(`pie`,function(e){var n=e.getData(),r=n.mapDimension(`value`),i=Mne(e,t),a=i.cx,o=i.cy,s=i.r,l=i.r0,u=i.viewRect,d=-e.get(`startAngle`)*rg,f=e.get(`endAngle`),p=e.get(`padAngle`)*rg;f=f===`auto`?d-zce:-f*rg;var m=e.get(`minAngle`)*rg+p,h=0;n.each(r,function(e){!isNaN(e)&&h++});var g=n.getSum(r),_=Math.PI/(g||h)*2,v=e.get(`clockwise`),y=e.get(`roseType`),b=e.get(`stillShowZeroSum`),x=n.getDataExtent(r);x[0]=0;var S=v?1:-1,C=[d,f],w=S*p/2;Ia(C,!v),d=C[0],f=C[1];var T=Hce(e);T.startAngle=d,T.endAngle=f,T.clockwise=v,T.cx=a,T.cy=o,T.r=s,T.r0=l;var E=Math.abs(f-d),D=E,O=0,k=d;if(n.setLayout({viewRect:u,r:s}),n.each(r,function(e,t){var r;if(isNaN(e)){n.setItemLayout(t,{angle:NaN,startAngle:NaN,endAngle:NaN,clockwise:v,cx:a,cy:o,r0:l,r:y?NaN:s});return}r=y===`area`?E/h:g===0&&b?_:e*_,r<m?(r=m,D-=m):O+=e;var i=k+S*r,u=0,d=0;p>r?(u=k+S*r/2,d=u):(u=k+w,d=i-w),n.setItemLayout(t,{angle:r,startAngle:u,endAngle:d,clockwise:v,cx:a,cy:o,r0:l,r:y?Xo(e,x,[l,s]):s}),k=i}),D<zce&&h)if(D<=.001){var A=E/h;n.each(r,function(e,t){if(!isNaN(e)){var r=n.getItemLayout(t);r.angle=A;var i=0,a=0;A<p?(i=d+S*(t+1/2)*A,a=i):(i=d+S*t*A+w,a=d+S*(t+1)*A-w),r.startAngle=i,r.endAngle=a}})}else _=D/O,k=d,n.each(r,function(e,t){if(!isNaN(e)){var r=n.getItemLayout(t),i=r.angle===m?m:e*_,a=0,o=0;i<p?(a=k+S*i/2,o=a):(a=k+w,o=k+S*i-w),r.startAngle=a,r.endAngle=o,k+=S*i}})})}var Hce=Us(),Uce=function(e){p(t,e);function t(t,n,r){var i=e.call(this)||this;i.z2=2;var a=new wo;return i.setTextContent(a),i.updateData(t,n,r,!0),i}return t.prototype.updateData=function(e,t,n,r){var i=this,a=e.hostModel,o=e.getItemModel(t),s=o.getModel(`emphasis`),l=e.getItemLayout(t),u=R(Uh(o.getModel(`itemStyle`),l,!0),l);if(isNaN(u.startAngle)){i.setShape(u);return}if(r){i.setShape(u);var d=a.getShallow(`animationType`);a.ecModel.ssr?(qu(i,{scaleX:0,scaleY:0},a,{dataIndex:t,isFrom:!0}),i.originX=u.cx,i.originY=u.cy):d===`scale`?(i.shape.r=l.r0,qu(i,{shape:{r:l.r}},a,t)):n==null?(i.shape.endAngle=l.startAngle,Ku(i,{shape:{endAngle:l.endAngle}},a,t)):(i.setShape({startAngle:n,endAngle:n}),qu(i,{shape:{startAngle:l.startAngle,endAngle:l.endAngle}},a,t))}else Qu(i),Ku(i,{shape:u},a,t);i.useStyle(e.getItemVisual(t,`style`)),_l(i,o);var f=(l.startAngle+l.endAngle)/2,p=a.get(`selectedOffset`),m=Math.cos(f)*p,h=Math.sin(f)*p,g=o.getShallow(`cursor`);g&&i.attr(`cursor`,g),this._updateLabel(a,e,t),i.ensureState(`emphasis`).shape=R({r:l.r+(s.get(`scale`)&&s.get(`scaleSize`)||0)},Uh(s.getModel(`itemStyle`),l)),R(i.ensureState(`select`),{x:m,y:h,shape:Uh(o.getModel([`select`,`itemStyle`]),l)}),R(i.ensureState(`blur`),{shape:Uh(o.getModel([`blur`,`itemStyle`]),l)});var _=i.getTextGuideLine(),v=i.getTextContent();_&&R(_.ensureState(`select`),{x:m,y:h}),R(v.ensureState(`select`),{x:m,y:h}),pl(this,s.get(`focus`),s.get(`blurScope`),s.get(`disabled`))},t.prototype._updateLabel=function(e,t,n){var r=this,i=t.getItemModel(n),a=i.getModel(`labelLine`),o=t.getItemVisual(n,`style`),s=o&&o.fill,l=o&&o.opacity;Bd(r,Vd(i),{labelFetcher:t.hostModel,labelDataIndex:n,inheritColor:s,defaultOpacity:l,defaultText:e.getFormattedLabel(n,`normal`)||t.getName(n)});var u=r.getTextContent();r.setTextConfig({position:null,rotation:null}),u.attr({z2:10});var d=i.get([`label`,`position`]);if(d!==`outside`&&d!==`outer`)r.removeTextGuideLine();else{var f=this.getTextGuideLine();f||(f=new yu,this.setTextGuideLine(f)),kce(this,Ace(i),{stroke:s,opacity:De(a.get([`lineStyle`,`opacity`]),l,1)})}},t}(du),Wce=function(e){p(t,e);function t(){var t=e!==null&&e.apply(this,arguments)||this;return t.type=`pie`,t.ignoreLabelLineUpdate=!0,t}return t.prototype.render=function(e,t,n,r){var i=e.getData(),a=this._data,o=this.group,s;if(!a&&i.count()>0){for(var l=i.getItemLayout(0),u=1;isNaN(l&&l.startAngle)&&u<i.count();++u)l=i.getItemLayout(u);l&&(s=l.startAngle)}if(this._emptyCircleSector&&o.remove(this._emptyCircleSector),i.count()===0&&e.get(`showEmptyCircle`)){var d=new du({shape:I(Hce(e))});d.useStyle(e.getModel(`emptyCircleStyle`).getItemStyle()),this._emptyCircleSector=d,o.add(d)}i.diff(a).add(function(e){var t=new Uce(i,e,s);i.setItemGraphicEl(e,t),o.add(t)}).update(function(e,t){var n=a.getItemGraphicEl(t);n.updateData(i,e,s),n.off(`click`),o.add(n),i.setItemGraphicEl(e,n)}).remove(function(t){Zu(a.getItemGraphicEl(t),e,t)}).execute(),Rce(e),e.get(`animationTypeUpdate`)!==`expansion`&&(this._data=i)},t.prototype.dispose=function(){},t.prototype.containPoint=function(e,t){var n=t.getData().getItemLayout(0);if(n){var r=e[0]-n.cx,i=e[1]-n.cy,a=Math.sqrt(r*r+i*i);return a<=n.r&&a>=n.r0}},t.type=`pie`,t}(qm);function Gce(e){return{seriesType:e,reset:function(e,t){var n=e.getData();n.filterSelf(function(e){var t=n.mapDimension(`value`),r=n.get(t,e);return!(ve(r)&&!isNaN(r)&&r<0)})}}}function Kce(e){e.registerChartView(Wce),e.registerSeriesModel(wce),vce(`pie`,e.registerAction),e.registerLayout(Bce),e.registerProcessor(bce(`pie`)),e.registerProcessor(Gce(`pie`))}var ig=function(){function e(e,t){this.target=e,this.topTarget=t&&t.topTarget}return e}(),qce=function(){function e(e){this.handler=e,e.on(`mousedown`,this._dragStart,this),e.on(`mousemove`,this._drag,this),e.on(`mouseup`,this._dragEnd,this)}return e.prototype._dragStart=function(e){for(var t=e.target;t&&!t.draggable;)t=t.parent||t.__hostTarget;t&&(this._draggingTarget=t,t.dragging=!0,this._x=e.offsetX,this._y=e.offsetY,this.handler.dispatchToElement(new ig(t,e),`dragstart`,e.event))},e.prototype._drag=function(e){var t=this._draggingTarget;if(t){var n=e.offsetX,r=e.offsetY,i=n-this._x,a=r-this._y;this._x=n,this._y=r,t.drift(i,a,e),this.handler.dispatchToElement(new ig(t,e),`drag`,e.event);var o=this.handler.findHover(n,r,t).target,s=this._dropTarget;this._dropTarget=o,t!==o&&(s&&o!==s&&this.handler.dispatchToElement(new ig(s,e),`dragleave`,e.event),o&&o!==s&&this.handler.dispatchToElement(new ig(o,e),`dragenter`,e.event))}},e.prototype._dragEnd=function(e){var t=this._draggingTarget;t&&(t.dragging=!1),this.handler.dispatchToElement(new ig(t,e),`dragend`,e.event),this._dropTarget&&this.handler.dispatchToElement(new ig(this._dropTarget,e),`drop`,e.event),this._draggingTarget=null,this._dropTarget=null},e}(),Jce=/^(?:mouse|pointer|contextmenu|drag|drop)|click/,ag=[],Yce=Ke.browser.firefox&&+Ke.browser.version.split(`.`)[0]<39;function og(e,t,n,r){return n||={},r?Xce(e,t,n):Yce&&t.layerX!=null&&t.layerX!==t.offsetX?(n.zrX=t.layerX,n.zrY=t.layerY):t.offsetX==null?Xce(e,t,n):(n.zrX=t.offsetX,n.zrY=t.offsetY),n}function Xce(e,t,n){if(Ke.domSupported&&e.getBoundingClientRect){var r=t.clientX,i=t.clientY;if(Np(e)){var a=e.getBoundingClientRect();n.zrX=r-a.left,n.zrY=i-a.top;return}else if(Ap(ag,e,r,i)){n.zrX=ag[0],n.zrY=ag[1];return}}n.zrX=n.zrY=0}function sg(e){return e||window.event}function cg(e,t,n){if(t=sg(t),t.zrX!=null)return t;var r=t.type;if(r&&r.indexOf(`touch`)>=0){var i=r===`touchend`?t.changedTouches[0]:t.targetTouches[0];i&&og(e,i,t,n)}else{og(e,t,t,n);var a=Zce(t);t.zrDelta=a?a/120:-(t.detail||0)/3}var o=t.button;return t.which==null&&o!==void 0&&Jce.test(t.type)&&(t.which=o&1?1:o&2?3:o&4?2:0),t}function Zce(e){var t=e.wheelDelta;if(t)return t;var n=e.deltaX,r=e.deltaY;if(n==null||r==null)return t;var i=Math.abs(r===0?n:r),a=r>0?-1:r<0?1:n>0?-1:1;return 3*i*a}function Qce(e,t,n,r){e.addEventListener(t,n,r)}function $ce(e,t,n,r){e.removeEventListener(t,n,r)}var ele=function(e){e.preventDefault(),e.stopPropagation(),e.cancelBubble=!0},tle=function(){function e(){this._track=[]}return e.prototype.recognize=function(e,t,n){return this._doTrack(e,t,n),this._recognize(e)},e.prototype.clear=function(){return this._track.length=0,this},e.prototype._doTrack=function(e,t,n){var r=e.touches;if(r){for(var i={points:[],touches:[],target:t,event:e},a=0,o=r.length;a<o;a++){var s=r[a],l=og(n,s,{});i.points.push([l.zrX,l.zrY]),i.touches.push(s)}this._track.push(i)}},e.prototype._recognize=function(e){for(var t in lg)if(lg.hasOwnProperty(t)){var n=lg[t](this._track,e);if(n)return n}},e}();function nle(e){var t=e[1][0]-e[0][0],n=e[1][1]-e[0][1];return Math.sqrt(t*t+n*n)}function rle(e){return[(e[0][0]+e[1][0])/2,(e[0][1]+e[1][1])/2]}var lg={pinch:function(e,t){var n=e.length;if(n){var r=(e[n-1]||{}).points,i=(e[n-2]||{}).points||r;if(i&&i.length>1&&r&&r.length>1){var a=nle(r)/nle(i);!isFinite(a)&&(a=1),t.pinchScale=a;var o=rle(r);return t.pinchX=o[0],t.pinchY=o[1],{type:`pinch`,target:e[0].target,event:t}}}}},ile=`silent`;function ale(e,t,n){return{type:e,event:n,target:t.target,topTarget:t.topTarget,cancelBubble:!1,offsetX:n.zrX,offsetY:n.zrY,gestureEvent:n.gestureEvent,pinchX:n.pinchX,pinchY:n.pinchY,pinchScale:n.pinchScale,wheelDelta:n.zrDelta,zrByTouch:n.zrByTouch,which:n.which,stop:ole}}function ole(){ele(this.event)}var sle=function(e){p(t,e);function t(){var t=e!==null&&e.apply(this,arguments)||this;return t.handler=null,t}return t.prototype.dispose=function(){},t.prototype.setCursor=function(){},t}(ki),ug=function(){function e(e,t){this.x=e,this.y=t}return e}(),cle=[`click`,`dblclick`,`mousewheel`,`mouseout`,`mouseup`,`mousedown`,`mousemove`,`contextmenu`],dg=new an(0,0,0,0),lle=function(e){p(t,e);function t(t,n,r,i,a){var o=e.call(this)||this;return o._hovered=new ug(0,0),o.storage=t,o.painter=n,o.painterRoot=i,o._pointerSize=a,r||=new sle,o.proxy=null,o.setHandlerProxy(r),o._draggingMgr=new qce(o),o}return t.prototype.setHandlerProxy=function(e){this.proxy&&this.proxy.dispose(),e&&(z(cle,function(t){e.on&&e.on(t,this[t],this)},this),e.handler=this),this.proxy=e},t.prototype.mousemove=function(e){var t=e.zrX,n=e.zrY,r=fle(this,t,n),i=this._hovered,a=i.target;a&&!a.__zr&&(i=this.findHover(i.x,i.y),a=i.target);var o=this._hovered=r?new ug(t,n):this.findHover(t,n),s=o.target,l=this.proxy;l.setCursor&&l.setCursor(s?s.cursor:`default`),a&&s!==a&&this.dispatchToElement(i,`mouseout`,e),this.dispatchToElement(o,`mousemove`,e),s&&s!==a&&this.dispatchToElement(o,`mouseover`,e)},t.prototype.mouseout=function(e){var t=e.zrEventControl;t!==`only_globalout`&&this.dispatchToElement(this._hovered,`mouseout`,e),t!==`no_globalout`&&this.trigger(`globalout`,{type:`globalout`,event:e})},t.prototype.resize=function(){this._hovered=new ug(0,0)},t.prototype.dispatch=function(e,t){var n=this[e];n&&n.call(this,t)},t.prototype.dispose=function(){this.proxy.dispose(),this.storage=null,this.proxy=null,this.painter=null},t.prototype.setCursorStyle=function(e){var t=this.proxy;t.setCursor&&t.setCursor(e)},t.prototype.dispatchToElement=function(e,t,n){e||={};var r=e.target;if(!(r&&r.silent)){for(var i=`on`+t,a=ale(t,e,n);r&&(r[i]&&(a.cancelBubble=!!r[i].call(r,a)),r.trigger(t,a),r=r.__hostTarget?r.__hostTarget:r.parent,!a.cancelBubble););a.cancelBubble||(this.trigger(t,a),this.painter&&this.painter.eachOtherLayer&&this.painter.eachOtherLayer(function(e){typeof e[i]==`function`&&e[i].call(e,a),e.trigger&&e.trigger(t,a)}))}},t.prototype.findHover=function(e,t,n){var r=this.storage.getDisplayList(),i=new ug(e,t);if(dle(r,i,e,t,n),this._pointerSize&&!i.target){for(var a=[],o=this._pointerSize,s=o/2,l=new an(e-s,t-s,o,o),u=r.length-1;u>=0;u--){var d=r[u];d!==n&&!d.ignore&&!d.ignoreCoarsePointer&&(!d.parent||!d.parent.ignoreCoarsePointer)&&(dg.copy(d.getBoundingRect()),d.transform&&dg.applyTransform(d.transform),dg.intersect(l)&&a.push(d))}if(a.length){for(var f=4,p=Math.PI/12,m=Math.PI*2,h=0;h<s;h+=f)for(var g=0;g<m;g+=p)if(dle(a,i,e+h*Math.cos(g),t+h*Math.sin(g),n),i.target)return i}}return i},t.prototype.processGesture=function(e,t){this._gestureMgr||=new tle;var n=this._gestureMgr;t===`start`&&n.clear();var r=n.recognize(e,this.findHover(e.zrX,e.zrY,null).target,this.proxy.dom);if(t===`end`&&n.clear(),r){var i=r.type;e.gestureEvent=i;var a=new ug;a.target=r.target,this.dispatchToElement(a,i,r.event)}},t}(ki);z([`click`,`mousedown`,`mouseup`,`mousewheel`,`dblclick`,`contextmenu`],function(e){lle.prototype[e]=function(t){var n=t.zrX,r=t.zrY,i=fle(this,n,r),a,o;if((e!==`mouseup`||!i)&&(a=this.findHover(n,r),o=a.target),e===`mousedown`)this._downEl=o,this._downPoint=[t.zrX,t.zrY],this._upEl=o;else if(e===`mouseup`)this._upEl=o;else if(e===`click`){if(this._downEl!==this._upEl||!this._downPoint||Lt(this._downPoint,[t.zrX,t.zrY])>4)return;this._downPoint=null}this.dispatchToElement(a,e,t)}});function ule(e,t,n){if(e[e.rectHover?`rectContain`:`contain`](t,n)){for(var r=e,i=void 0,a=!1;r;){if(r.ignoreClip&&(a=!0),!a){var o=r.getClipPath();if(o&&!o.contain(t,n))return!1}r.silent&&(i=!0);var s=r.__hostTarget;r=s?r.ignoreHostSilent?null:s:r.parent}return!i||ile}return!1}function dle(e,t,n,r,i){for(var a=e.length-1;a>=0;a--){var o=e[a],s=void 0;if(o!==i&&!o.ignore&&(s=ule(o,n,r))&&(!t.topTarget&&(t.topTarget=o),s!==ile)){t.target=o;break}}}function fle(e,t,n){var r=e.painter;return t<0||t>r.getWidth()||n<0||n>r.getHeight()}var ple=32,fg=7;function mle(e){for(var t=0;e>=ple;)t|=e&1,e>>=1;return e+t}function hle(e,t,n,r){var i=t+1;if(i===n)return 1;if(r(e[i++],e[t])<0){for(;i<n&&r(e[i],e[i-1])<0;)i++;gle(e,t,i)}else for(;i<n&&r(e[i],e[i-1])>=0;)i++;return i-t}function gle(e,t,n){for(n--;t<n;){var r=e[t];e[t++]=e[n],e[n--]=r}}function _le(e,t,n,r,i){for(r===t&&r++;r<n;r++){for(var a=e[r],o=t,s=r,l;o<s;)l=o+s>>>1,i(a,e[l])<0?s=l:o=l+1;var u=r-o;switch(u){case 3:e[o+3]=e[o+2];case 2:e[o+2]=e[o+1];case 1:e[o+1]=e[o];break;default:for(;u>0;)e[o+u]=e[o+u-1],u--}e[o]=a}}function pg(e,t,n,r,i,a){var o=0,s=0,l=1;if(a(e,t[n+i])>0){for(s=r-i;l<s&&a(e,t[n+i+l])>0;)o=l,l=(l<<1)+1,l<=0&&(l=s);l>s&&(l=s),o+=i,l+=i}else{for(s=i+1;l<s&&a(e,t[n+i-l])<=0;)o=l,l=(l<<1)+1,l<=0&&(l=s);l>s&&(l=s);var u=o;o=i-l,l=i-u}for(o++;o<l;){var d=o+(l-o>>>1);a(e,t[n+d])>0?o=d+1:l=d}return l}function mg(e,t,n,r,i,a){var o=0,s=0,l=1;if(a(e,t[n+i])<0){for(s=i+1;l<s&&a(e,t[n+i-l])<0;)o=l,l=(l<<1)+1,l<=0&&(l=s);l>s&&(l=s);var u=o;o=i-l,l=i-u}else{for(s=r-i;l<s&&a(e,t[n+i+l])>=0;)o=l,l=(l<<1)+1,l<=0&&(l=s);l>s&&(l=s),o+=i,l+=i}for(o++;o<l;){var d=o+(l-o>>>1);a(e,t[n+d])<0?l=d:o=d+1}return l}function vle(e,t){var n=fg,r,i,a=0,o=[];r=[],i=[];function s(e,t){r[a]=e,i[a]=t,a+=1}function l(){for(;a>1;){var e=a-2;if(e>=1&&i[e-1]<=i[e]+i[e+1]||e>=2&&i[e-2]<=i[e]+i[e-1])i[e-1]<i[e+1]&&e--;else if(i[e]>i[e+1])break;d(e)}}function u(){for(;a>1;){var e=a-2;e>0&&i[e-1]<i[e+1]&&e--,d(e)}}function d(n){var o=r[n],s=i[n],l=r[n+1],u=i[n+1];i[n]=s+u,n===a-3&&(r[n+1]=r[n+2],i[n+1]=i[n+2]),a--;var d=mg(e[l],e,o,s,0,t);o+=d,s-=d,s!==0&&(u=pg(e[o+s-1],e,l,u,u-1,t),u!==0&&(s<=u?f(o,s,l,u):p(o,s,l,u)))}function f(r,i,a,s){var l=0;for(l=0;l<i;l++)o[l]=e[r+l];var u=0,d=a,f=r;if(e[f++]=e[d++],--s===0){for(l=0;l<i;l++)e[f+l]=o[u+l];return}if(i===1){for(l=0;l<s;l++)e[f+l]=e[d+l];e[f+s]=o[u];return}for(var p=n,m,h,g;;){m=0,h=0,g=!1;do if(t(e[d],o[u])<0){if(e[f++]=e[d++],h++,m=0,--s===0){g=!0;break}}else if(e[f++]=o[u++],m++,h=0,--i===1){g=!0;break}while((m|h)<p);if(g)break;do{if(m=mg(e[d],o,u,i,0,t),m!==0){for(l=0;l<m;l++)e[f+l]=o[u+l];if(f+=m,u+=m,i-=m,i<=1){g=!0;break}}if(e[f++]=e[d++],--s===0){g=!0;break}if(h=pg(o[u],e,d,s,0,t),h!==0){for(l=0;l<h;l++)e[f+l]=e[d+l];if(f+=h,d+=h,s-=h,s===0){g=!0;break}}if(e[f++]=o[u++],--i===1){g=!0;break}p--}while(m>=fg||h>=fg);if(g)break;p<0&&(p=0),p+=2}if(n=p,n<1&&(n=1),i===1){for(l=0;l<s;l++)e[f+l]=e[d+l];e[f+s]=o[u]}else if(i===0)throw Error();else for(l=0;l<i;l++)e[f+l]=o[u+l]}function p(r,i,a,s){var l=0;for(l=0;l<s;l++)o[l]=e[a+l];var u=r+i-1,d=s-1,f=a+s-1,p=0,m=0;if(e[f--]=e[u--],--i===0){for(p=f-(s-1),l=0;l<s;l++)e[p+l]=o[l];return}if(s===1){for(f-=i,u-=i,m=f+1,p=u+1,l=i-1;l>=0;l--)e[m+l]=e[p+l];e[f]=o[d];return}for(var h=n;;){var g=0,_=0,v=!1;do if(t(o[d],e[u])<0){if(e[f--]=e[u--],g++,_=0,--i===0){v=!0;break}}else if(e[f--]=o[d--],_++,g=0,--s===1){v=!0;break}while((g|_)<h);if(v)break;do{if(g=i-mg(o[d],e,r,i,i-1,t),g!==0){for(f-=g,u-=g,i-=g,m=f+1,p=u+1,l=g-1;l>=0;l--)e[m+l]=e[p+l];if(i===0){v=!0;break}}if(e[f--]=o[d--],--s===1){v=!0;break}if(_=s-pg(e[u],o,0,s,s-1,t),_!==0){for(f-=_,d-=_,s-=_,m=f+1,p=d+1,l=0;l<_;l++)e[m+l]=o[p+l];if(s<=1){v=!0;break}}if(e[f--]=e[u--],--i===0){v=!0;break}h--}while(g>=fg||_>=fg);if(v)break;h<0&&(h=0),h+=2}if(n=h,n<1&&(n=1),s===1){for(f-=i,u-=i,m=f+1,p=u+1,l=i-1;l>=0;l--)e[m+l]=e[p+l];e[f]=o[d]}else if(s===0)throw Error();else for(p=f-(s-1),l=0;l<s;l++)e[p+l]=o[l]}return{mergeRuns:l,forceMergeRuns:u,pushRun:s}}function hg(e,t,n,r){n||=0,r||=e.length;var i=r-n;if(!(i<2)){var a=0;if(i<ple){a=hle(e,n,r,t),_le(e,n,r,n+a,t);return}var o=vle(e,t),s=mle(i);do{if(a=hle(e,n,r,t),a<s){var l=i;l>s&&(l=s),_le(e,n,n+l,n+a,t),a=l}o.pushRun(n,a),o.mergeRuns(),i-=a,n+=a}while(i!==0);o.forceMergeRuns()}}var yle=!1;function gg(){yle||(yle=!0,console.warn(`z / z2 / zlevel of displayable is invalid, which may cause unexpected errors`))}function ble(e,t){return e.zlevel===t.zlevel?e.z===t.z?e.z2-t.z2:e.z-t.z:e.zlevel-t.zlevel}var xle=function(){function e(){this._roots=[],this._displayList=[],this._displayListLen=0,this.displayableSortFunc=ble}return e.prototype.traverse=function(e,t){for(var n=0;n<this._roots.length;n++)this._roots[n].traverse(e,t)},e.prototype.getDisplayList=function(e,t){t||=!1;var n=this._displayList;return(e||!n.length)&&this.updateDisplayList(t),n},e.prototype.updateDisplayList=function(e){this._displayListLen=0;for(var t=this._roots,n=this._displayList,r=0,i=t.length;r<i;r++)this._updateAndAddDisplayable(t[r],null,e);n.length=this._displayListLen,hg(n,ble)},e.prototype._updateAndAddDisplayable=function(e,t,n){if(!(e.ignore&&!n)){e.beforeUpdate(),e.update(),e.afterUpdate();var r=e.getClipPath(),i=t&&t.length,a=0,o=e.__clipPaths;if(!e.ignoreClip&&(i||r)){if(o||=e.__clipPaths=[],i)for(var s=0;s<t.length;s++)o[a++]=t[s];for(var l=r,u=e;l;)l.parent=u,l.updateTransform(),o[a++]=l,u=l,l=l.getClipPath()}if(o&&(o.length=a),e.childrenRef){for(var d=e.childrenRef(),f=0;f<d.length;f++){var p=d[f];e.__dirty&&(p.__dirty|=1),this._updateAndAddDisplayable(p,o,n)}e.__dirty=0}else{var m=e;isNaN(m.z)&&(gg(),m.z=0),isNaN(m.z2)&&(gg(),m.z2=0),isNaN(m.zlevel)&&(gg(),m.zlevel=0),this._displayList[this._displayListLen++]=m}var h=e.getDecalElement&&e.getDecalElement();h&&this._updateAndAddDisplayable(h,o,n);var g=e.getTextGuideLine();g&&this._updateAndAddDisplayable(g,o,n);var _=e.getTextContent();_&&this._updateAndAddDisplayable(_,o,n)}},e.prototype.addRoot=function(e){e.__zr&&e.__zr.storage===this||this._roots.push(e)},e.prototype.delRoot=function(e){if(e instanceof Array){for(var t=0,n=e.length;t<n;t++)this.delRoot(e[t]);return}var r=ne(this._roots,e);r>=0&&this._roots.splice(r,1)},e.prototype.delAllRoots=function(){this._roots=[],this._displayList=[],this._displayListLen=0},e.prototype.getRoots=function(){return this._roots},e.prototype.dispose=function(){this._displayList=null,this._roots=null},e}(),Sle=Ke.hasGlobalWindow&&(window.requestAnimationFrame&&window.requestAnimationFrame.bind(window)||window.msRequestAnimationFrame&&window.msRequestAnimationFrame.bind(window)||window.mozRequestAnimationFrame||window.webkitRequestAnimationFrame)||function(e){return setTimeout(e,16)};function _g(){return new Date().getTime()}var Cle=function(e){p(t,e);function t(t){var n=e.call(this)||this;return n._running=!1,n._time=0,n._pausedTime=0,n._pauseStart=0,n._paused=!1,t||={},n.stage=t.stage||{},n}return t.prototype.addClip=function(e){e.animation&&this.removeClip(e),this._head?(this._tail.next=e,e.prev=this._tail,e.next=null,this._tail=e):this._head=this._tail=e,e.animation=this},t.prototype.addAnimator=function(e){e.animation=this;var t=e.getClip();t&&this.addClip(t)},t.prototype.removeClip=function(e){if(e.animation){var t=e.prev,n=e.next;t?t.next=n:this._head=n,n?n.prev=t:this._tail=t,e.next=e.prev=e.animation=null}},t.prototype.removeAnimator=function(e){var t=e.getClip();t&&this.removeClip(t),e.animation=null},t.prototype.update=function(e){for(var t=_g()-this._pausedTime,n=t-this._time,r=this._head;r;){var i=r.next;r.step(t,n)?(r.ondestroy(),this.removeClip(r),r=i):r=i}this._time=t,e||(this.trigger(`frame`,n),this.stage.update&&this.stage.update())},t.prototype._startLoop=function(){var e=this;this._running=!0;function t(){e._running&&(Sle(t),!e._paused&&e.update())}Sle(t)},t.prototype.start=function(){this._running||(this._time=_g(),this._pausedTime=0,this._startLoop())},t.prototype.stop=function(){this._running=!1},t.prototype.pause=function(){this._paused||=(this._pauseStart=_g(),!0)},t.prototype.resume=function(){this._paused&&=(this._pausedTime+=_g()-this._pauseStart,!1)},t.prototype.clear=function(){for(var e=this._head;e;){var t=e.next;e.prev=e.next=e.animation=null,e=t}this._head=this._tail=null},t.prototype.isFinished=function(){return this._head==null},t.prototype.animate=function(e,t){t||={},this.start();var n=new Oi(e,t.loop);return this.addAnimator(n),n},t}(ki),wle=300,vg=Ke.domSupported,yg=(function(){var e=[`click`,`dblclick`,`mousewheel`,`wheel`,`mouseout`,`mouseup`,`mousedown`,`mousemove`,`contextmenu`],t=[`touchstart`,`touchend`,`touchmove`],n={pointerdown:1,pointerup:1,pointermove:1,pointerout:1};return{mouse:e,touch:t,pointer:oe(e,function(e){var t=e.replace(`mouse`,`pointer`);return n.hasOwnProperty(t)?t:e})}})(),Tle={mouse:[`mousemove`,`mouseup`],pointer:[`pointermove`,`pointerup`]},Ele=!1;function bg(e){var t=e.pointerType;return t===`pen`||t===`touch`}function Dle(e){e.touching=!0,e.touchTimer!=null&&(clearTimeout(e.touchTimer),e.touchTimer=null),e.touchTimer=setTimeout(function(){e.touching=!1,e.touchTimer=null},700)}function xg(e){e&&(e.zrByTouch=!0)}function Ole(e,t){return cg(e.dom,new Ale(e,t),!0)}function kle(e,t){for(var n=t,r=!1;n&&n.nodeType!==9&&!(r=n.domBelongToZr||n!==t&&n===e.painterRoot);)n=n.parentNode;return r}var Ale=function(){function e(e,t){this.stopPropagation=Ue,this.stopImmediatePropagation=Ue,this.preventDefault=Ue,this.type=t.type,this.target=this.currentTarget=e.dom,this.pointerType=t.pointerType,this.clientX=t.clientX,this.clientY=t.clientY}return e}(),Sg={mousedown:function(e){e=cg(this.dom,e),this.__mayPointerCapture=[e.zrX,e.zrY],this.trigger(`mousedown`,e)},mousemove:function(e){e=cg(this.dom,e);var t=this.__mayPointerCapture;t&&(e.zrX!==t[0]||e.zrY!==t[1])&&this.__togglePointerCapture(!0),this.trigger(`mousemove`,e)},mouseup:function(e){e=cg(this.dom,e),this.__togglePointerCapture(!1),this.trigger(`mouseup`,e)},mouseout:function(e){e=cg(this.dom,e);var t=e.toElement||e.relatedTarget;kle(this,t)||(this.__pointerCapturing&&(e.zrEventControl=`no_globalout`),this.trigger(`mouseout`,e))},wheel:function(e){Ele=!0,e=cg(this.dom,e),this.trigger(`mousewheel`,e)},mousewheel:function(e){Ele||(e=cg(this.dom,e),this.trigger(`mousewheel`,e))},touchstart:function(e){e=cg(this.dom,e),xg(e),this.__lastTouchMoment=new Date,this.handler.processGesture(e,`start`),Sg.mousemove.call(this,e),Sg.mousedown.call(this,e)},touchmove:function(e){e=cg(this.dom,e),xg(e),this.handler.processGesture(e,`change`),Sg.mousemove.call(this,e)},touchend:function(e){e=cg(this.dom,e),xg(e),this.handler.processGesture(e,`end`),Sg.mouseup.call(this,e),new Date-+this.__lastTouchMoment<wle&&Sg.click.call(this,e)},pointerdown:function(e){Sg.mousedown.call(this,e)},pointermove:function(e){bg(e)||Sg.mousemove.call(this,e)},pointerup:function(e){Sg.mouseup.call(this,e)},pointerout:function(e){bg(e)||Sg.mouseout.call(this,e)}};z([`click`,`dblclick`,`contextmenu`],function(e){Sg[e]=function(t){t=cg(this.dom,t),this.trigger(e,t)}});var Cg={pointermove:function(e){bg(e)||Cg.mousemove.call(this,e)},pointerup:function(e){Cg.mouseup.call(this,e)},mousemove:function(e){this.trigger(`mousemove`,e)},mouseup:function(e){var t=this.__pointerCapturing;this.__togglePointerCapture(!1),this.trigger(`mouseup`,e),t&&(e.zrEventControl=`only_globalout`,this.trigger(`mouseout`,e))}};function jle(e,t){var n=t.domHandlers;Ke.pointerEventsSupported?z(yg.pointer,function(r){wg(t,r,function(t){n[r].call(e,t)})}):(Ke.touchEventsSupported&&z(yg.touch,function(r){wg(t,r,function(i){n[r].call(e,i),Dle(t)})}),z(yg.mouse,function(r){wg(t,r,function(i){i=sg(i),t.touching||n[r].call(e,i)})}))}function Mle(e,t){Ke.pointerEventsSupported?z(Tle.pointer,n):Ke.touchEventsSupported||z(Tle.mouse,n);function n(n){function r(r){r=sg(r),kle(e,r.target)||(r=Ole(e,r),t.domHandlers[n].call(e,r))}wg(t,n,r,{capture:!0})}}function wg(e,t,n,r){e.mounted[t]=n,e.listenerOpts[t]=r,Qce(e.domTarget,t,n,r)}function Tg(e){var t=e.mounted;for(var n in t)t.hasOwnProperty(n)&&$ce(e.domTarget,n,t[n],e.listenerOpts[n]);e.mounted={}}var Nle=function(){function e(e,t){this.mounted={},this.listenerOpts={},this.touching=!1,this.domTarget=e,this.domHandlers=t}return e}(),Ple=function(e){p(t,e);function t(t,n){var r=e.call(this)||this;return r.__pointerCapturing=!1,r.dom=t,r.painterRoot=n,r._localHandlerScope=new Nle(t,Sg),vg&&(r._globalHandlerScope=new Nle(document,Cg)),jle(r,r._localHandlerScope),r}return t.prototype.dispose=function(){Tg(this._localHandlerScope),vg&&Tg(this._globalHandlerScope)},t.prototype.setCursor=function(e){this.dom.style&&(this.dom.style.cursor=e||`default`)},t.prototype.__togglePointerCapture=function(e){if(this.__mayPointerCapture=null,vg&&this.__pointerCapturing^+e){this.__pointerCapturing=e;var t=this._globalHandlerScope;e?Mle(this,t):Tg(t)}},t}(ki),Eg={},Fle={};function Ile(e){delete Fle[e]}function Lle(e){if(!e)return!1;if(typeof e==`string`)return Vr(e,1)<Mi;if(e.colorStops){for(var t=e.colorStops,n=0,r=t.length,i=0;i<r;i++)n+=Vr(t[i].color,1);return n/=r,n<Mi}return!1}var Rle=function(){function e(e,t,n){var r=this;this._sleepAfterStill=10,this._stillFrameAccum=0,this._needsRefresh=!0,this._needsRefreshHover=!1,this._darkMode=!1,n||={},this.dom=t,this.id=e;var i=new xle,a=n.renderer||`canvas`;Eg[a]||(a=ue(Eg)[0]),n.useDirtyRect=n.useDirtyRect!=null&&n.useDirtyRect;var o=new Eg[a](t,i,n,e),s=n.ssr||o.ssrOnly;this.storage=i,this.painter=o;var l=!Ke.node&&!Ke.worker&&!s?new Ple(o.getViewportRoot(),o.root):null,u=n.useCoarsePointer,d=u==null||u===`auto`?Ke.touchEventsSupported:!!u,f=44,p;d&&(p=Ee(n.pointerSize,f)),this.handler=new lle(i,o,l,o.root,p),this.animation=new Cle({stage:{update:s?null:function(){return r._flush(!1)}}}),s||this.animation.start()}return e.prototype.add=function(e){this._disposed||!e||(this.storage.addRoot(e),e.addSelfToZr(this),this.refresh())},e.prototype.remove=function(e){this._disposed||!e||(this.storage.delRoot(e),e.removeSelfFromZr(this),this.refresh())},e.prototype.configLayer=function(e,t){this._disposed||(this.painter.configLayer&&this.painter.configLayer(e,t),this.refresh())},e.prototype.setBackgroundColor=function(e){this._disposed||(this.painter.setBackgroundColor&&this.painter.setBackgroundColor(e),this.refresh(),this._backgroundColor=e,this._darkMode=Lle(e))},e.prototype.getBackgroundColor=function(){return this._backgroundColor},e.prototype.setDarkMode=function(e){this._darkMode=e},e.prototype.isDarkMode=function(){return this._darkMode},e.prototype.refreshImmediately=function(e){this._disposed||this._refresh({animUpdate:!e,refresh:!0,refreshHover:!1})},e.prototype._refresh=function(e){e.animUpdate&&this.animation.update(!0),this._needsRefresh=this._needsRefreshHover=!1,this.painter.refresh({refresh:e.refresh,refreshHover:e.refreshHover}),this._needsRefresh=this._needsRefreshHover=!1},e.prototype.refresh=function(){this._disposed||(this._needsRefresh=!0,this.animation.start())},e.prototype.flush=function(){this._disposed||this._flush(!0)},e.prototype._flush=function(e){var t,n=_g(),r=this._needsRefresh,i=this._needsRefreshHover;(r||i)&&(t=!0,this._refresh({animUpdate:e,refresh:r,refreshHover:i}));var a=_g();t?(this._stillFrameAccum=0,this.trigger(`rendered`,{elapsedTime:a-n})):this._sleepAfterStill>0&&(this._stillFrameAccum++,this._stillFrameAccum>this._sleepAfterStill&&this.animation.stop())},e.prototype.setSleepAfterStill=function(e){this._sleepAfterStill=e},e.prototype.wakeUp=function(){this._disposed||(this.animation.start(),this._stillFrameAccum=0)},e.prototype.refreshHover=function(){this._needsRefreshHover=!0},e.prototype.refreshHoverImmediately=function(){this._disposed||this._refresh({animUpdate:!1,refresh:!1,refreshHover:!0})},e.prototype.resize=function(e){this._disposed||(e||={},this.painter.resize(e.width,e.height),this.handler.resize())},e.prototype.clearAnimation=function(){this._disposed||this.animation.clear()},e.prototype.getWidth=function(){if(!this._disposed)return this.painter.getWidth()},e.prototype.getHeight=function(){if(!this._disposed)return this.painter.getHeight()},e.prototype.setCursorStyle=function(e){this._disposed||this.handler.setCursorStyle(e)},e.prototype.findHover=function(e,t){if(!this._disposed)return this.handler.findHover(e,t)},e.prototype.on=function(e,t,n){return this._disposed||this.handler.on(e,t,n),this},e.prototype.off=function(e,t){this._disposed||this.handler.off(e,t)},e.prototype.trigger=function(e,t){this._disposed||this.handler.trigger(e,t)},e.prototype.clear=function(){if(!this._disposed){for(var e=this.storage.getRoots(),t=0;t<e.length;t++)e[t]instanceof Wl&&e[t].removeSelfFromZr(this);this.storage.delAllRoots(),this.painter.clear()}},e.prototype.dispose=function(){this._disposed||(this.animation.stop(),this.clear(),this.storage.dispose(),this.painter.dispose(),this.handler.dispose(),this.animation=this.storage=this.painter=this.handler=null,this._disposed=!0,Ile(this.id))},e}();function zle(e,t){var n=new Rle(P(),e,t);return Fle[n.id]=n,n}function Ble(e,t){Eg[e]=t}var Dg;function Vle(e){if(typeof Dg==`function`)return Dg(e)}function Hle(e){Dg=e}var Ule=``;typeof navigator<`u`&&(Ule=navigator.platform||``);var Og=`rgba(0, 0ãß7ãmÊ×¬¢h­µç\šY™OËœÚÝÑÜšYÏÈLK\ÙSX^ÚY™OË\ÙSX^ÚYÏÈL_KÙ]ÛÛ™šYÕ˜[Y\Ø
KÍ^Ü\œÙ\Ž›ŽšM™[™\™\ŽžÙ˜]Î•Ê
K‹ŠOOžÑË™XYÊ™[™\š[™ÈØ\™^HX\˜
ÙJNÛ]O\Í

KO[Í

KÏZK››ÙT˜Y]\ÊŒK‹Ï\‹™‹\Ë™Ù]Ø\™^Q]J
KO\Ë™Ù]XYÜ˜[U]J
K[œÚ^™OËÚYÏÚKÚY[œÚ^™OËšZYÚÏÚKšZYÚU“Ê
NÜœÙ[XÝ[

˜
Kœ™[[Ý™J
KÊ‹K\ÙSX^ÚY
K˜]ŠšY]Ð›Þ	ÙH	ÙŸX
NÛ]O\˜\[™
Ø
K˜]ŠÛ\ÜØØ\™^K[X\
K\˜\[™
YœØ
NÚ˜\[™
X\šÙ\˜
K˜]ŠY\œ›ÝËIÝX
K˜]ŠšY]Ð›ÞLL
K˜]Š™Y–JK˜]Š™Y–XJK˜]ŠX\šÙ\•ÚYŠK˜]ŠX\šÙ\’ZYÚŠK˜]ŠÜšY[]]Ë\Ý\\™]™\œÙX
K˜\[™
]
K˜]ŠHLHL˜
K˜]Šš[K™]›Û][Û”Ý›ÚÙJK˜]ŠÝ›ÚÙX›Û™X
K˜\[™
X\šÙ\˜
K˜]ŠY[šËX\œ›ÝËY[™IÝX
K˜]ŠšY]Ð›ÞLL
K˜]Š™Y–JK˜]Š™Y–XJK˜]ŠX\šÙ\•ÚYJK˜]ŠX\šÙ\’ZYÚJK˜]ŠÜšY[]]Ø
K˜\[™
]
K˜]ŠHLHL˜
K˜]Šš[K›[šÔÝ›ÚÙJK˜]ŠÝ›ÚÙX›Û™X
K˜\[™
X\šÙ\˜
K˜]ŠY[šËX\œ›ÝË\Ý\IÝX
K˜]ŠšY]Ð›ÞLL
K˜]Š™Y–JK˜]Š™Y–XJK˜]ŠX\šÙ\•ÚYJK˜]ŠX\šÙ\’ZYÚJK˜]ŠÜšY[]]Ø
K˜\[™
]
K˜]ŠHLHLL˜
K˜]Šš[K›[šÔÝ›ÚÙJK˜]ŠÝ›ÚÙX›Û™X
KK˜\[™
™XÝ
K˜]ŠÛ\ÜØØ\™^KX˜XÚÙÜ›Ý[™
K˜]ŠÚY
K˜]ŠZYÚŠK˜]Šš[K˜˜XÚÙÜ›Ý[™ÛÛÜŠNÛ]ÏYZKœY[™ÊŒ‹ÏY‹ZKœY[™ÊŒŽÝI‰›K˜\[™
^
K˜]ŠÛ\ÜØØ\™^K]]X
K˜]ŠÌŠK˜]ŠXKœY[™ËÌŠK˜]Šš[K˜^\Õ^ÛÛÜŠK˜]Š›Û\Ú^™XK˜^\Ñ›ÛÚ^™JŒKŒJK˜]Š›Û]ÙZYÚ›Û
K˜]Š^X[˜ÚÜ˜ZYX
K˜]ŠÛZ[˜[X˜\Ù[[™XZYX
K^
JNÛ]UÊOOšKœY[™ÊÙKÌL
™Ë›Ú™XÝ
KOUÊOO™‹ZKœY[™ËYKÌL
—Ë›Ú™XÝX
K[K˜\[™
Ø
K˜]ŠÛ\ÜØØ\™^KX^\Ø
NØ‹˜\[™
[™X
K˜]ŠXKœY[™ÊK˜]Š˜ZKœY[™ÊK˜]ŠLX‹ZKœY[™ÊK˜]ŠL˜‹ZKœY[™ÊK˜]ŠÝ›ÚÙXK˜^\ÐÛÛÜŠK˜]ŠÝ›ÚÙK]ÚYJK‹˜\[™
[™X
K˜]ŠXKœY[™ÊK˜]Š˜KœY[™ÊK˜]ŠLXKœY[™ÊK˜]ŠL˜‹ZKœY[™ÊK˜]ŠÝ›ÚÙXK˜^\ÐÛÛÜŠK˜]ŠÝ›ÚÙK]ÚYJNÛ][˜^\ËžX™[ÏØ]›Û][Û˜Ï[˜^\ËžSX™[ÏØš\ÚXš[]XØ‹˜\[™
^
K˜]ŠÛ\ÜØØ\™^KX^\Ë[X™[Ø\™^KX^\Ë[X™[^
K˜]ŠKœY[™ÊÙËÌŠK˜]ŠX‹ZKœY[™ËÍ
K˜]Šš[K˜^\Õ^ÛÛÜŠK˜]Š›Û\Ú^™XK˜^\Ñ›ÛÚ^™JK˜]Š›Û]ÙZYÚ›Û
K˜]Š^X[˜ÚÜ˜ZYX
K^

K‹˜\[™
^
K˜]ŠÛ\ÜØØ\™^KX^\Ë[X™[Ø\™^KX^\Ë[X™[^X
K˜]ŠKœY[™ËÌÊK˜]ŠXKœY[™Ê×ËÌŠK˜]Šš[K˜^\Õ^ÛÛÜŠK˜]Š›Û\Ú^™XK˜^\Ñ›ÛÚ^™JK˜]Š›Û]ÙZYÚ›Û
K˜]Š^X[˜ÚÜ˜ZYX
K˜]Š˜[œÙ›Ü›X›Ý]JNL	ÚKœY[™ËÌßH	ÚKœY[™Ê×ËÌŸJX
K^
ÊNÛ]Ï[˜^\ËœÝYÙ\É‰›˜^\ËœÝYÙ\Ë›[™ÝŒÛ˜^\ËœÝYÙ\Î˜MÚYŠË›[™ÝŒ
^Û]O[K˜\[™
Ø
K˜]ŠÛ\ÜØØ\™^K\ÝYÙ\Ø
K[˜^\ËœÝYÙP›Ý[™\šY\ËV×NÚYŠ	‰›[™ÝOOPË›[™Ý
^Û]OLÝ™›Ü‘XXÚ
OžÛ‹œ\Ú
ÜÝ\™K[™JKO]J_Y[Ù^Û]OLKÐË›[™ÝÐË™›Ü‘XXÚ

ŠOOžÛ‹œ\Ú
ÜÝ\œŠ™K[™ŠŠÌJJ™_J_J_PË™›Ü‘XXÚ

ŠOOžÛ]Ï[–Ü—KÏZKœY[™ÊÛËœÝ\
™ËJÊÊKœY[™ÊÛË™[™
™ÊJKÌŽÜŒ	‰™K˜\[™
[™X
K˜]ŠXÊK˜]Š˜ÊK˜]ŠLXKœY[™ÊK˜]ŠL˜‹ZKœY[™ÊK˜]ŠÝ›ÚÙXÌ
K˜]ŠÝ›ÚÙK]ÚYJK˜]ŠÝ›ÚÙKY\Ú\œ˜^XHX
K˜]ŠÜXÚ]XŽ
KK˜\[™
^
K˜]ŠÛ\ÜØØ\™^K\ÝYÙK[X™[
K˜]Š
K˜]ŠX‹ZKœY[™ËÌKJK˜]Šš[K˜^\Õ^ÛÛÜŠK˜]Š›Û\Ú^™XK˜^\Ñ›ÛÚ^™KLŠK˜]Š^X[˜ÚÜ˜ZYX
K^

_J_ZYŠKœÚÝÑÜšY
^Û]O[K˜\[™
Ø
K˜]ŠÛ\ÜØØ\™^KYÜšY
NÙ›ÜŠ]LNÝÝ
ÊÊ^Û]]ÍZKœY[™ÊÙÊ›ŽÙK˜\[™
[™X
K˜]ŠXŠK˜]Š˜ŠK˜]ŠLXKœY[™ÊK˜]ŠL˜‹ZKœY[™ÊK˜]ŠÝ›ÚÙXK™ÜšYÛÛÜŠK˜]ŠÝ›ÚÙKY\Ú\œ˜^Xˆ˜
KK˜\[™
[™X
K˜]ŠXKœY[™ÊK˜]Š˜ZKœY[™ÊK˜]ŠLX‹ZKœY[™ËWÊ›ŠK˜]ŠL˜‹ZKœY[™ËWÊ›ŠK˜]ŠÝ›ÚÙXK™ÜšYÛÛÜŠK˜]ŠÝ›ÚÙKY\Ú\œ˜^Xˆ˜
__[]Ï[™]ÈX\ÚYŠ››Ù\Ë™›Ü‘XXÚ
OOžÝËœÙ]
KšYÞŠKž
KNžJKžJK›ÙN™_J_JKœ\[[™\Ë›[™ÝŒ
^Û]O[K˜\[™
Ø
K˜]ŠÛ\ÜØØ\™^K\\[[™\Ø
K[K˜\[™
Ø
K˜]ŠÛ\ÜØØ\™^K\\[[™K[[šÜØ
NÛœ\[[™\Ë™›Ü‘XXÚ
OžÚYŠ‹˜ÛÛ\Û™[YË›[™ÝOOL
\™]\›ŽÛ][‹˜ÛÛ\Û™[YË›X\
OOŠÚY™KÜÎË™Ù]
JK›ÙN›››Ù\Ë™š[™
OšYOOYJ_JJK™š[\ŠOO™KœÜÉ‰™K››ÙJKœÛÜ

K
OO™K››ÙKž]››ÙKž
NÙ›ÜŠ]OLÙO‹›[™ÝLNÙJÊÊ^Û]\–ÙWKO\–ÙJÌWNÝ˜\[™
[™X
K˜]ŠÛ\ÜØØ\™^K\\[[™KY]›Û][Û‹[[šØ
K˜]ŠX‹œÜËž
K˜]ŠLX‹œÜËžJK˜]Š˜KœÜËž
K˜]ŠL˜KœÜËžJK˜]ŠÝ›ÚÙXK›[šÔÝ›ÚÙJK˜]ŠÝ›ÚÙK]ÚYJK˜]ŠÝ›ÚÙKY\Ú\œ˜^X
_[]ÏLKÌOKLKÌLÚYŠ‹˜ÛÛ\Û™[YË™›Ü‘XXÚ
OOžÛ]]Ë™Ù]
JNÝ	‰ŠÏSX]›Z[ŠËž
KOSX]›X^
Kž
K]žJ_JKÈOOLKÌ	‰HOOKLKÌ
^Û]ZK››ÙT˜Y]\ÊY]Ì‹]Ë™Ù]
‹››ÙRY
NÛ	‰ŠžJÊÝJKÌ‹žO\‹[ËÍŠKK˜\[™
™XÝ
K˜]ŠÛ\ÜØØ\™^K\\[[™KX›Þ
K˜]ŠËLMJK˜]ŠXŠK˜]ŠÚYK\ÊÌÌ
K˜]ŠZYÚ
K˜]Šš[›Û™X
K˜]ŠÝ›ÚÙXK˜^\ÐÛÛÜŠK˜]ŠÝ›ÚÙK]ÚYKJK˜]Šž
K˜]ŠžX
__J_[][K˜\[™
Ø
K˜]ŠÛ\ÜØØ\™^K[[šÜØ
KO[™]ÈX\Ûœ\[[™\Ë™›Ü‘XXÚ
OOžÑKœÙ]
K››ÙRY™]ÈÙ]
K˜ÛÛ\Û™[YÊJ_JNÛ][›[šÜË™š[\ŠOOˆJ]Ëš\ÊKœÛÝ\˜ÙJ_]Ëš\ÊK\™Ù]
_K™Ù]
K\™Ù]
OËš\ÊKœÛÝ\˜ÙJJJNÕœÙ[XÝ[
[™X
K™]J
K™[\Š
K˜\[™
[™X
K˜]ŠÛ\ÜØOO˜Ø\™^K[[šÉÙK™\ÚYØØ\™^K[[šËKY\ÚY˜X
K˜]ŠXOOžÛ]]Ë™Ù]
KœÛÝ\˜ÙJK]Ë™Ù]
K\™Ù]
K[››Ù\Ë™š[™
OšYOOYKœÛÝ\˜ÙJKš\Ô\[[™T\™[ÛËÓX]œÜ\
ŠNšK››ÙT˜Y]\ËO[‹ž]žÏ[‹žK]žKOSX]œÜ\
J˜JÜÊœÊNÜ™]\›ˆž
ØKÝJœŸJK˜]ŠLXOOžÛ]]Ë™Ù]
KœÛÝ\˜ÙJK]Ë™Ù]
K\™Ù]
K[››Ù\Ë™š[™
OšYOOYKœÛÝ\˜ÙJKš\Ô\[[™T\™[ÛËÓX]œÜ\
ŠNšK››ÙT˜Y]\ËO[‹ž]žÏ[‹žK]žKOSX]œÜ\
J˜JÜÊœÊNÜ™]\›ˆžJÜËÝJœŸJK˜]Š˜OOžÛ]]Ë™Ù]
KœÛÝ\˜ÙJK]Ë™Ù]
K\™Ù]
K[››Ù\Ë™š[™
OšYOOYK\™Ù]
Kš\Ô\[[™T\™[ÛËÓX]œÜ\
ŠNšK››ÙT˜Y]\ËO]ž[‹žÏ]žK[‹žKOSX]œÜ\
J˜JÜÊœÊNÜ™]\›ˆ‹ž
ØKÝJœŸJK˜]ŠL˜OOžÛ]]Ë™Ù]
KœÛÝ\˜ÙJK]Ë™Ù]
K\™Ù]
K[››Ù\Ë™š[™
OšYOOYK\™Ù]
Kš\Ô\[[™T\™[ÛËÓX]œÜ\
ŠNšK››ÙT˜Y]\ËO]ž[‹žÏ]žK[‹žKOSX]œÜ\
J˜JÜÊœÊNÜ™]\›ˆ‹žJÜËÝJœŸJK˜]ŠÝ›ÚÙXK›[šÔÝ›ÚÙJK˜]ŠÝ›ÚÙK]ÚYJK˜]ŠÝ›ÚÙKY\Ú\œ˜^XOO™K™\ÚYØˆ˜›[
K˜]ŠX\šÙ\‹Y[™OO™K™›ÝÏOOX›ÜØ\™K™›ÝÏOOXšY\™XÝ[Û˜[Ø\›
Û[šËX\œ›ÝËY[™IÝJX›[
K˜]ŠX\šÙ\‹\Ý\OO™K™›ÝÏOOX˜XÚÝØ\™K™›ÝÏOOXšY\™XÝ[Û˜[Ø\›
Û[šËX\œ›ÝË\Ý\IÝJX›[
KœÙ[XÝ[
^
K™]J™š[\ŠOO™K›X™[
JK™[\Š
K˜\[™
^
K˜]ŠÛ\ÜØØ\™^K[[šË[X™[
K˜]ŠOOžÛ]]Ë™Ù]
KœÛÝ\˜ÙJK]Ë™Ù]
K\™Ù]
KJž
Û‹ž
KÌ‹O[‹žK]žKO[‹ž]žÜ™]\›ˆŠÚKÓX]œÜ\
J˜JÚJšJJŽJK˜]ŠXOOžÛ]]Ë™Ù]
KœÛÝ\˜ÙJK]Ë™Ù]
K\™Ù]
KJžJÛ‹žJKÌ‹O[‹ž]žO[‹žK]žKÏSX]œÜ\
JšJØJ˜JNÜ™]\›ˆŠËZKÛÊŽJK˜]Šš[K˜^\Õ^ÛÛÜŠK˜]Š›Û\Ú^™XK›X™[›ÛÚ^™JK˜]Š^X[˜ÚÜ˜ZYX
K˜]ŠÛZ[˜[X˜\Ù[[™XZYX
K˜]Š˜[œÙ›Ü›XOOžÛ]]Ë™Ù]
KœÛÝ\˜ÙJK]Ë™Ù]
K\™Ù]
KJž
Û‹ž
KÌ‹OJžJÛ‹žJKÌ‹O[‹ž]žÏ[‹žK]žKÏSX]œÜ\
J˜JÛÊ›ÊK[ËÜËOKXKÜË\ŠÛ
ŽZJÝJŽSX]˜][ŒŠËJJŒNÓX]”NÜ™]\›ŠŽLNL
I‰Š
ÏLN
K›Ý]J	ÜH	ÙH	ÙŸJXJK^
OO™K›X™[
NÛ]Ï[K˜\[™
Ø
K˜]ŠÛ\ÜØØ\™^K]™[™Ø
KÏ[™[™Ë›X\
OOžÛ]]Ë™Ù]
K››ÙRY
NÚYŠ]
\™]\›ˆ[Û]]ŠK\™Ù]
K^JK\™Ù]JKO[‹]žÏ\‹]žKÏSX]œÜ\
J˜JÛÊ›ÊKZK››ÙT˜Y]\ÊÌŽÜ™]\›žÛÜšYÚ[Ž\™Ù]›‹\™Ù]Nœ‹Y\ÝYŽœÏ›Û‹XKÜÊ››‹Y\ÝYLŽœÏ›Ü‹[ËÜÊ›œŸ_JK™š[\ŠOO™HOO[[
NÓËœÙ[XÝ[
[™X
K™]JÊK™[\Š
K˜\[™
[™X
K˜]ŠÛ\ÜØØ\™^K]™[™
K˜]ŠXOO™K›ÜšYÚ[‹ž
K˜]ŠLXOO™K›ÜšYÚ[‹žJK˜]Š˜OO™K˜Y\ÝYŠK˜]ŠL˜OO™K˜Y\ÝYLŠK˜]ŠÝ›ÚÙXK™]›Û][Û”Ý›ÚÙJK˜]ŠÝ›ÚÙK]ÚYJK˜]ŠÝ›ÚÙKY\Ú\œ˜^X
K˜]ŠX\šÙ\‹Y[™\›
Ø\œ›ÝËIÝJX
NÛ]O[K˜\[™
Ø
K˜]ŠÛ\ÜØØ\™^K[›Ù\Ø
KœÙ[XÝ[
Ø
K™]J››Ù\ÊK™[\Š
K˜\[™
Ø
K˜]ŠÛ\ÜØOO–ØØ\™^K[›ÙXK˜Û\ÜÓ˜[YOØØ\™^K[›ÙKKIÙK˜Û\ÜÓ˜[Y_X˜K™š[\Š›ÛÛX[ŠKš›Ú[Š
JNÐK™š[\ŠOO™KœÛÝ\˜ÙTÝ˜]YÞOOOXÝ]ÛÝ\˜ÙX
K˜\[™
Ú\˜ÛX
K˜]ŠÛ\ÜØØ\™^K[Ý]ÛÝ\˜ÙK[Ý™\›^X
K˜]ŠÞOOË™Ù]
KšY
Kž
K˜]ŠÞXOOË™Ù]
KšY
KžJK˜]Š˜K››ÙT˜Y]\ÊŒŠK˜]Šš[Í˜
K˜]ŠÝ›ÚÙXK˜ÛÛ\Û™[Ý›ÚÙJK˜]ŠÝ›ÚÙK]ÚYJKK™š[\ŠOO™KœÛÝ\˜ÙTÝ˜]YÞOOOX^X
K˜\[™
Ú\˜ÛX
K˜]ŠÛ\ÜØØ\™^KX^K[Ý™\›^X
K˜]ŠÞOOË™Ù]
KšY
Kž
K˜]ŠÞXOOË™Ù]
KšY
KžJK˜]Š˜K››ÙT˜Y]\ÊŒŠK˜]Šš[ØØØØ
K˜]ŠÝ›ÚÙXK˜ÛÛ\Û™[Ý›ÚÙJK˜]ŠÝ›ÚÙK]ÚYJKK™š[\ŠOO™KœÛÝ\˜ÙTÝ˜]YÞOOOXZ[
K˜\[™
Ú\˜ÛX
K˜]ŠÛ\ÜØØ\™^KXZ[[Ý™\›^X
K˜]ŠÞOOË™Ù]
KšY
Kž
K˜]ŠÞXOOË™Ù]
KšY
KžJK˜]Š˜K››ÙT˜Y]\ÊŒŠK˜]Šš[ÙYYX
K˜]ŠÝ›ÚÙXÌ
K˜]ŠÝ›ÚÙK]ÚYJNÛ]PK™š[\ŠOO™KœÛÝ\˜ÙTÝ˜]YÞOOOXX\šÙ]
NÚ‹˜\[™
Ú\˜ÛX
K˜]ŠÛ\ÜØØ\™^K[X\šÙ][Ý™\›^X
K˜]ŠÞOOË™Ù]
KšY
Kž
K˜]ŠÞXOOË™Ù]
KšY
KžJK˜]Š˜K››ÙT˜Y]\ÊŒŠK˜]Šš[Ú]X
K˜]ŠÝ›ÚÙXK˜ÛÛ\Û™[Ý›ÚÙJK˜]ŠÝ›ÚÙK]ÚYJKK™š[\ŠOOˆYKš\Ô\[[™T\™[	‰™KœÛÝ\˜ÙTÝ˜]YÞHOOXX\šÙ]	‰™K˜Û\ÜÓ˜[YHOOX[˜ÚÜ˜
K˜\[™
Ú\˜ÛX
K˜]ŠÞOOË™Ù]
KšY
Kž
K˜]ŠÞXOOË™Ù]
KšY
KžJK˜]Š˜K››ÙT˜Y]\ÊK˜]Šš[K˜ÛÛ\Û™[š[
K˜]ŠÝ›ÚÙXK˜ÛÛ\Û™[Ý›ÚÙJK˜]ŠÝ›ÚÙK]ÚYJNÛ]OZK››ÙT˜Y]\Ê‹ËZK››ÙT˜Y]\ÊŒKŒŽÚYŠ‹˜\[™
[™X
K˜]ŠÛ\ÜØØ\™^K[X\šÙ][[™X
K˜]ŠXOOË™Ù]
KšY
Kž
K˜]ŠLXOOË™Ù]
KšY
KžKSŠK˜]Š˜OOË™Ù]
KšY
KžSŠ“X]˜ÛÜÊX]”KÍŠJK˜]ŠL˜OOË™Ù]
KšY
KžJÓŠ“X]œÚ[ŠX]”KÍŠJK˜]ŠÝ›ÚÙXK˜ÛÛ\Û™[Ý›ÚÙJK˜]ŠÝ›ÚÙK]ÚYJK‹˜\[™
[™X
K˜]ŠÛ\ÜØØ\™^K[X\šÙ][[™X
K˜]ŠXOOË™Ù]
KšY
KžSŠ“X]˜ÛÜÊX]”KÍŠJK˜]ŠLXOOË™Ù]
KšY
KžJÓŠ“X]œÚ[ŠX]”KÍŠJK˜]Š˜OOË™Ù]
KšY
Kž
ÓŠ“X]˜ÛÜÊX]”KÍŠJK˜]ŠL˜OOË™Ù]
KšY
KžJÓŠ“X]œÚ[ŠX]”KÍŠJK˜]ŠÝ›ÚÙXK˜ÛÛ\Û™[Ý›ÚÙJK˜]ŠÝ›ÚÙK]ÚYJK‹˜\[™
[™X
K˜]ŠÛ\ÜØØ\™^K[X\šÙ][[™X
K˜]ŠXOOË™Ù]
KšY
Kž
ÓŠ“X]˜ÛÜÊX]”KÍŠJK˜]ŠLXOOË™Ù]
KšY
KžJÓŠ“X]œÚ[ŠX]”KÍŠJK˜]Š˜OOË™Ù]
KšY
Kž
K˜]ŠL˜OOË™Ù]
KšY
KžKSŠK˜]ŠÝ›ÚÙXK˜ÛÛ\Û™[Ý›ÚÙJK˜]ŠÝ›ÚÙK]ÚYJK‹˜\[™
Ú\˜ÛX
K˜]ŠÛ\ÜØØ\™^K[X\šÙ]YÝ
K˜]ŠÞOOË™Ù]
KšY
Kž
K˜]ŠÞXOOË™Ù]
KšY
KžKSŠK˜]Š˜JK˜]Šš[Ú]X
K˜]ŠÝ›ÚÙXK˜ÛÛ\Û™[Ý›ÚÙJK˜]ŠÝ›ÚÙK]ÚYŠK‹˜\[™
Ú\˜ÛX
K˜]ŠÛ\ÜØØ\™^K[X\šÙ]YÝ
K˜]ŠÞOOË™Ù]
KšY
KžSŠ“X]˜ÛÜÊX]”KÍŠJK˜]ŠÞXOOË™Ù]
KšY
KžJÓŠ“X]œÚ[ŠX]”KÍŠJK˜]Š˜JK˜]Šš[Ú]X
K˜]ŠÝ›ÚÙXK˜ÛÛ\Û™[Ý›ÚÙJK˜]ŠÝ›ÚÙK]ÚYŠK‹˜\[™
Ú\˜ÛX
K˜]ŠÛ\ÜØØ\™^K[X\šÙ]YÝ
K˜]ŠÞOOË™Ù]
KšY
Kž
ÓŠ“X]˜ÛÜÊX]”KÍŠJK˜]ŠÞXOOË™Ù]
KšY
KžJÓŠ“X]œÚ[ŠX]”KÍŠJK˜]Š˜JK˜]Šš[Ú]X
K˜]ŠÝ›ÚÙXK˜ÛÛ\Û™[Ý›ÚÙJK˜]ŠÝ›ÚÙK]ÚYŠKK™š[\ŠOO™Kš\Ô\[[™T\™[OOHL
K˜\[™
™XÝ
K˜]ŠOOË™Ù]
KšY
Kž[ËÌŠK˜]ŠXOOË™Ù]
KšY
KžK[ËÌŠK˜]ŠÚYÊK˜]ŠZYÚÊK˜]Šš[K˜ÛÛ\Û™[š[
K˜]ŠÝ›ÚÙXK˜ÛÛ\Û™[Ý›ÚÙJK˜]ŠÝ›ÚÙK]ÚYJKK™š[\ŠOO™Kš[™\XOOOHL
K˜\[™
[™X
K˜]ŠÛ\ÜØØ\™^KZ[™\XX
K˜]ŠXOOžÛ]]Ë™Ù]
KšY
KYKš\Ô\[[™T\™[ÛËÌŠÌMNšK››ÙT˜Y]\ÊÌMNÜ™]\›ˆKœÛÝ\˜ÙTÝ˜]YÞI‰ŠŠÏZK››ÙT˜Y]\ÊÌL
Kž
ÛŸJK˜]ŠLXOOžÛ]]Ë™Ù]
KšY
KYKš\Ô\[[™T\™[ÛÎšK››ÙT˜Y]\ÊŒŽÜ™]\›ˆžK[‹ÌŸJK˜]Š˜OOžÛ]]Ë™Ù]
KšY
KYKš\Ô\[[™T\™[ÛËÌŠÌMNšK››ÙT˜Y]\ÊÌMNÜ™]\›ˆKœÛÝ\˜ÙTÝ˜]YÞI‰ŠŠÏZK››ÙT˜Y]\ÊÌL
Kž
ÛŸJK˜]ŠL˜OOžÛ]]Ë™Ù]
KšY
KYKš\Ô\[[™T\™[ÛÎšK››ÙT˜Y]\ÊŒŽÜ™]\›ˆžJÛ‹ÌŸJK˜]ŠÝ›ÚÙXK˜ÛÛ\Û™[Ý›ÚÙJK˜]ŠÝ›ÚÙK]ÚYŠKK˜\[™
^
K˜]ŠOOžÛ]]Ë™Ù]
KšY
NÚYŠK˜Û\ÜÓ˜[YOOOX[˜ÚÜ˜
\™]\›ˆK›X™[Ù™œÙ]OO]›ÚYÝžž
ÙK›X™[Ù™œÙ]Û]ZK››ÙSX™[Ù™œÙ]ÙKœÛÝ\˜ÙTÝ˜]YÞI‰™K›X™[Ù™œÙ]OO]›ÚY	‰ŠŠÏLL
NÛ]YK›X™[Ù™œÙ]ÏÛŽÜ™]\›ˆž
ÜŸJK˜]ŠXOOžÛ]]Ë™Ù]
KšY
NÚYŠK˜Û\ÜÓ˜[YOOOX[˜ÚÜ˜
\™]\›ˆK›X™[Ù™œÙ]OOO]›ÚYÝžKLÎžJÙK›X™[Ù™œÙ]NÛ]KZK››ÙSX™[Ù™œÙ]ÙKœÛÝ\˜ÙTÝ˜]YÞI‰™K›X™[Ù™œÙ]OOO]›ÚY	‰Š‹OLL
NÛ]YK›X™[Ù™œÙ]OÏÛŽÜ™]\›ˆžJÜŸJK˜]ŠÛ\ÜØØ\™^K[›ÙK[X™[
K˜]Šš[OO™K˜Û\ÜÓ˜[YOOOX]›Û™YØK™]›Û][Û”Ý›ÚÙN™K˜Û\ÜÓ˜[YOOOX[˜ÚÜ˜ØÌ˜K˜ÛÛ\Û™[X™[ÛÛÜŠK˜]Š›Û\Ú^™XK›X™[›ÛÚ^™JK˜]Š›Û]ÙZYÚOO™K˜Û\ÜÓ˜[YOOOX[˜ÚÜ˜Ø›Û˜›Ü›X[
K˜]Š^X[˜ÚÜ˜OO™K˜Û\ÜÓ˜[YOOOX[˜ÚÜ˜ØZYX˜Ý\
K˜]ŠÛZ[˜[X˜\Ù[[™XOO™K˜Û\ÜÓ˜[YOOOX[˜ÚÜ˜ØZYX˜]]Ø
K^
OO™K›X™[
K˜[››Ý][ÛœË›[™ÝŒ
^Û]O[K˜\[™
Ø
K˜]ŠÛ\ÜØØ\™^KX[››Ý][ÛœØ
NÚYŠ˜[››Ý][ÛœË™›Ü‘XXÚ
OžÛ]]˜ÛÛÜ™[˜]\Ë›X\
OOŠÞŠKž
KNžJKžJ_JJNÚYŠ‹›[™ÝŒJY›ÜŠ]LÝ‹›[™ÝLNÝ
ÊÊYK˜\[™
[™X
K˜]ŠÛ\ÜØØ\™^KX[››Ý][Û‹[[™X
K˜]ŠX–ÝKž
K˜]ŠLX–ÝKžJK˜]Š˜–Ý
ÌWKž
K˜]ŠL˜–Ý
ÌWKžJK˜]ŠÝ›ÚÙXK˜^\ÐÛÛÜŠK˜]ŠÝ›ÚÙK]ÚYKJK˜]ŠÝ›ÚÙKY\Ú\œ˜^X
NÛ‹™›Ü‘XXÚ
OžÛ]YK˜\[™
Ø
K˜]ŠÛ\ÜØØ\™^KX[››Ý][Û˜
NÜ‹˜\[™
Ú\˜ÛX
K˜]ŠÞ‹ž
K˜]ŠÞX‹žJK˜]Š˜L
K˜]Šš[Ú]X
K˜]ŠÝ›ÚÙXK˜^\ÐÛÛÜŠK˜]ŠÝ›ÚÙK]ÚYKJK‹˜\[™
^
K˜]Š‹ž
K˜]ŠX‹žJK˜]Š^X[˜ÚÜ˜ZYX
K˜]ŠÛZ[˜[X˜\Ù[[™XÙ[˜[
K˜]Š›Û\Ú^™XL
K˜]Šš[K˜^\Õ^ÛÛÜŠK˜]Š›Û]ÙZYÚ›Û
K^
›[X™\Š_J_JK˜[››Ý][ÛœÐ›Þ
^Û]]Š˜[››Ý][ÛœÐ›Þž
K^J˜[››Ý][ÛœÐ›ÞžJKYK˜\[™
Ø
K˜]ŠÛ\ÜØØ\™^KX[››Ý][ÛœËX›Þ
KÏVË‹‹›˜[››Ý][Ûœ×K™š[\ŠOO™K^
KœÛÜ

K
OO™K›[X™\‹]›[X™\ŠKÏV×NÚYŠË™›Ü‘XXÚ

KJOOžÛ]Ï\‹˜\[™
^
K˜]Š
ÌL
K˜]ŠXŠÌL
ÊJÌJJŒMŠK˜]Š›Û\Ú^™XLJK˜]Šš[K˜^\Õ^ÛÛÜŠK˜]Š^X[˜ÚÜ˜Ý\
K˜]ŠÛZ[˜[X˜\Ù[[™XZYX
K^
	ÙK›[X™\ŸKˆ	ÙK^X
NÜËœ\Ú
Ê_JKË›[™ÝŒ
^Û]OLLÜË™›Ü‘XXÚ
OžÛ]]››ÙJ
K[‹™Ù]ÛÛ\]Y^[™Ý

NÙOSX]›X^
KŠNÛ]O[‹™Ù]›Þ

NÛSX]›X^
KšZYÚ
_JNÛ]OYJÌŒ
ÌLK[Ë›[™Ý
ŒMŠÌŒ
ÛÌ‹OZKœY[™ËYZKœY[™Ë]KÏZKœY[™ËÏY‹ZKœY[™Ë\ÝSX]›X^
KX]›Z[Š
JKSX]›X^
ËX]›Z[Š‹ÊJKË™›Ü‘XXÚ

KŠOOžÙK˜]Š
ÌL
K˜]ŠXŠÌL
ÊŠÌJJŒMŠ_JK‹š[œÙ\
™XÝ^
K˜]Š
K˜]ŠXŠK˜]ŠÚYJK˜]ŠZYÚ
K˜]Šš[Ú]X
K˜]ŠÝ›ÚÙXK˜^\ÐÛÛÜŠK˜]ŠÝ›ÚÙK]ÚYKJK˜]Šž
K˜]ŠžX
___ZYŠ››Ý\Ë›[™ÝŒ
^Û]O[K˜\[™
Ø
K˜]ŠÛ\ÜØØ\™^K[›Ý\Ø
NÛ››Ý\Ë™›Ü‘XXÚ
OžÛ]]Šž
K^JžJNÙK˜\[™
^
K˜]ŠŠK˜]ŠXŠK˜]Š^X[˜ÚÜ˜Ý\
K˜]Š›Û\Ú^™XLJK˜]Šš[K˜^\Õ^ÛÛÜŠK˜]Š›Û]ÙZYÚ›Û
K^
^
_J_ZYŠ˜XØÙ[\˜]ÜœË›[™ÝŒ
^Û]O[K˜\[™
Ø
K˜]ŠÛ\ÜØØ\™^KXXØÙ[\˜]ÜœØ
NÛ˜XØÙ[\˜]ÜœË™›Ü‘XXÚ
OžÛ]]Šž
K^JžJKOXˆH	ÛŸH	Ü‹LÌÌŸBˆ	ÛŠÍŒLŒH	Ü‹LÌÌŸBˆ	ÛŠÍŒLŒH	Ü‹LÌÌ‹NBˆ	ÛŠÍŒH	ÜŸBˆ	ÛŠÍŒLŒH	ÜŠÌÌÌŠÎBˆ	ÛŠÍŒLŒH	ÜŠÌÌÌŸBˆ	ÛŸH	ÜŠÌÌÌŸBˆ‚ˆÙK˜\[™
]
K˜]ŠJK˜]Šš[Ú]X
K˜]ŠÝ›ÚÙXK˜ÛÛ\Û™[Ý›ÚÙJK˜]ŠÝ›ÚÙK]ÚYJKK˜\[™
^
K˜]ŠŠÍŒÌŠK˜]ŠXŠÌÌÌŠÌMJK˜]Š^X[˜ÚÜ˜ZYX
K˜]Š›Û\Ú^™XL
K˜]Šš[K˜^\Õ^ÛÛÜŠK˜]Š›Û]ÙZYÚ›Û
K^
›˜[YJ_J_ZYŠ™XXØÙ[\˜]ÜœË›[™ÝŒ
^Û]O[K˜\[™
Ø
K˜]ŠÛ\ÜØØ\™^KYXXØÙ[\˜]ÜœØ
NÛ™XXØÙ[\˜]ÜœË™›Ü‘XXÚ
OžÛ]]Šž
K^JžJKOXˆH	ÛŠÍŒH	Ü‹LÌÌŸBˆ	ÛŠÌŒH	Ü‹LÌÌŸBˆ	ÛŠÌŒH	Ü‹LÌÌ‹NBˆ	ÛŸH	ÜŸBˆ	ÛŠÌŒH	ÜŠÌÌÌŠÎBˆ	ÛŠÌŒH	ÜŠÌÌÌŸBˆ	ÛŠÍŒH	ÜŠÌÌÌŸBˆ‚ˆÙK˜\[™
]
K˜]ŠJK˜]Šš[Ú]X
K˜]ŠÝ›ÚÙXK˜ÛÛ\Û™[Ý›ÚÙJK˜]ŠÝ›ÚÙK]ÚYJKK˜\[™
^
K˜]ŠŠÍŒÌŠK˜]ŠXŠÌÌÌŠÌMJK˜]Š^X[˜ÚÜ˜ZYX
K˜]Š›Û\Ú^™XL
K˜]Šš[K˜^\Õ^ÛÛÜŠK˜]Š›Û]ÙZYÚ›Û
K^
›˜[YJ_J__K˜]Ø
_KÝ[\Î•Ê
ÝØ\™^N™_O^ßJOOžÛ]TZÊZÊÊ
K]Ê
K[YU˜\šXX›\ÊKØ\™^KJNÜ™]\›˜ˆØ\™^KX˜XÚÙÜ›Ý[™Âˆš[ˆ	Ý˜˜XÚÙÜ›Ý[™ÛÛÜŸNÂˆBˆØ\™^KX^\È[™KØ\™^KX^\È]ÂˆÝ›ÚÙNˆ	Ý˜^\ÐÛÛÜŸNÂˆBˆØ\™^KX^\Ë[X™[Âˆš[ˆ	Ý˜^\Õ^ÛÛÜŸNÂˆBˆØ\™^K\ÝYÙK[X™[Âˆš[ˆ	Ý˜^\Õ^ÛÛÜŸNÂˆBˆØ\™^KYÜšY[™HÂˆÝ›ÚÙNˆ	Ý™ÜšYÛÛÜŸNÂˆBˆØ\™^K[›ÙHÚ\˜ÛHÂˆš[ˆ	Ý˜ÛÛ\Û™[š[NÂˆÝ›ÚÙNˆ	Ý˜ÛÛ\Û™[Ý›ÚÙ_NÂˆBˆØ\™^K[›ÙK[X™[Âˆš[ˆ	Ý˜ÛÛ\Û™[X™[ÛÛÜŸNÂˆBˆØ\™^K[[šÈÂˆÝ›ÚÙNˆ	Ý›[šÔÝ›ÚÙ_NÂˆBˆØ\™^K[[šËKY\ÚYÂˆÝ›ÚÙKY\Ú\œ˜^NˆÂˆBˆØ\™^K[[šË[X™[Âˆš[ˆ	Ý˜^\Õ^ÛÛÜŸNÂˆBˆØ\™^K]™[™[™HÂˆÝ›ÚÙNˆ	Ý™]›Û][Û”Ý›ÚÙ_NÂˆBˆØ\™^KX[››Ý][Û‹[[™HÂˆÝ›ÚÙNˆ	Ý˜[››Ý][Û”Ý›ÚÙ_NÂˆBˆØ\™^KX[››Ý][ÛˆÚ\˜ÛHÂˆš[ˆ	Ý˜[››Ý][Û‘š[NÂˆÝ›ÚÙNˆ	Ý˜[››Ý][Û”Ý›ÚÙ_NÂˆBˆØ\™^KX[››Ý][Ûˆ^Âˆš[ˆ	Ý˜[››Ý][Û•^ÛÛÜŸNÂˆBˆØ\™^KX[››Ý][ÛœËX›Þ™XÝÂˆš[ˆ	Ý˜[››Ý][Û‘š[NÂˆÝ›ÚÙNˆ	Ý˜[››Ý][Û”Ý›ÚÙ_NÂˆBˆØ\™^KX[››Ý][ÛœËX›Þ^Âˆš[ˆ	Ý˜[››Ý][Û•^ÛÛÜŸNÂˆBˆØ\™^K\\[[™KX›ÞÂˆÝ›ÚÙNˆ	Ý˜ÛÛ\Û™[Ý›ÚÙ_NÂˆBˆØ\™^K[›Ý\È^Âˆš[ˆ	Ý˜^\Õ^ÛÛÜŸNÂˆBˆKÝ[\Ø
__JJKM[
ÙXYÜ˜[NŠ
OO•JNÙ[˜Ý[ÛˆJJ^Û]YJÌNÌMMNLßÜ™]\›ˆSX]š[][
ŒMKJK]
ÓX]š[][
ËŒJK

ŒM
OŒ
KÍŽMMÌŽMŸY[˜Ý[Ûˆ
J^Û]LÙ›ÜŠ]LÛK›[™ÝÛŠÊÊ^Û]YK˜Ú\ÛÙP]
ŠNÝJJK]
Ü‹L\™]\›ˆY[˜Ý[Ûˆ
K
^Ü™]\›ˆ\[ÙˆOOX[X™\˜	‰“[X™\‹š\Ñš[š]JJI‰™HOOLÙN™

_Y[˜Ý[Ûˆ
K‹Š^Û]OYKÌ‹O\ÏÙJ‹ŒMKÏ]ÍËÏV×NÙ›ÜŠ]OLÙOMÎÙJÊÊ^Û]]JŠÙJŒMÊJ˜JŒ‹XNÜËœ\Ú
ÞšJÝN™J›ßJ_[]XIÜÖÌKžK	ÜÖÌKž_XÙ›ÜŠ]OLÙOË›[™ÝLNÙJÊÊ^Û]\ÖÙWK\ÖÙJÌWKOJžJÜ‹žJKÌ‹ÏYILOLÌN‹LKOXJŒKJ›ÊJŠÙJŒÌJÍÊK]ž
ÝKZK\‹ž]NÛ
ÏXÉÙK	ÙŸH	ÜK	Ú_H	Ü‹žK	Ü‹ž_X\™]\›ˆY[˜Ý[ÛˆM
K‹Š^Û]O]Ì‹O\ÏÝ
‹ŒMKÏYKÍËÏV×NÙ›ÜŠ]OLÙOMÎÙJÊÊ^Û]]JŠÙJŒŒÊJ˜JŒ‹XNÜËœ\Ú
Þ™J›ËNšJÝJ_[]XIÜÖÌKžK	ÜÖÌKž_XÙ›ÜŠ]OLÙOË›[™ÝLNÙJÊÊ^Û]\ÖÙWK\ÖÙJÌWKOJž
Ü‹ž
KÌ‹ÏYILOLÌN‹LKOXJŒKJ›ÊJŠÙJŒÍÊÌLJKZK]žJÝKZKO\‹žK]NÛ
ÏXÉÙK	ÙŸH	ÜK	Û_H	Ü‹žK	Ü‹ž_X\™]\›ˆY[˜Ý[Ûˆ
K
^Û]YKÌ‹]
‹KO]OYJ‹ŒÎÜ™]\›–ØIÛŸK	ÜŸXÉÛŠØ_K	ÜŠÊK\ŠJ‹ŒŸX	Û‹XJŒK_K	ÜŠÊK\ŠJ‹M_X	ÛŠØJ‹_K	ÜŠÊK\ŠJ‹Í_XÉÛ‹X_K	ÜŠÊK\ŠJ‹Ž_X	ÛŠØJ‹ŒßK	ÜŠÊK\ŠJ‹ŽM_X	ÛŸK	Ú_XKš›Ú[Š
_Y[˜Ý[ÛˆÍ
K‹Š^Ü™]\›–ØIÙK[ŸK	ÝXIÛŸK	ÜŸHKH	ÙJÛŸK	ÝXIÛŸK	ÜŸHKH	ÙK[ŸK	ÝX˜Kš›Ú[Š
_]˜\ˆÍŽKŽKMÍNKÍÍM[Ê


OOžÙ’Š
KÊ
KÐJ
KÕ

KžJ
KJ
KŒÊ
KÍUÊ

OOŠÙÛXZ[œÎ›™]ÈX\˜[œÚ][ÛœÎ–×_JKÜ™X]QY˜][]X
KŽOWÍ

KŽO^ÙÙ]ÛXZ[œÎ•Ê

OO›ŽK™ÛXZ[œËÙ]ÛXZ[œØ
KÙ]˜[œÚ][ÛœÎ•Ê

OO›ŽK˜[œÚ][ÛœËÙ]˜[œÚ][ÛœØ
KÙ]ÛXZ[œÎ•ÊOOžÚYŠJY›ÜŠ]ÙˆJ^Û]O]™ÛXZ[‹Jš][\ÏÏÖ×JK›X\
OOŠÛX™[™K›X™[JJNÛŽK™ÛXZ[œËœÙ]
KÛ˜[YN™K][\Î›ŸJ__KÙ]ÛXZ[œØ
KÙ]˜[œÚ][ÛœÎ•ÊOOžÙI‰ŠŽK˜[œÚ][ÛœÏYK™š[\ŠOO™K™œ›ÛOOOYKÏÊËØ\›ŠÞ[™Yš[ŽˆÙ[‹[ÛÜ˜[œÚ][ÛˆÛˆÛXZ[ˆ‰ÙK™œ›Û_Hˆ\È›ÝYX[š[™Ù[[™Ú[™HÚÚ\Y˜
KLJNˆL
K›X\
OOŠÙœ›ÛN™K™œ›ÛKÎ™KËX™[™K›X™[›ÚYJJJ_KÙ]˜[œÚ][ÛœØ
KÙ]ÛÛ™šYÎ•Ê

OO”ZÊË‹‹”PË˜Þ[™Yš[‹‹‹]Ê
K˜Þ[™Yš[ŸJKÙ]ÛÛ™šYØ
KÛX\Ž•Ê

OOžÜ]Ê
KŽOWÍ

_KÛX\˜
KÙ]XØÕ]N’ËÙ]XØÕ]N–]ËÙ]XYÜ˜[U]N”]ËÙ]XYÜ˜[U]N‰ËÙ]XØÑ\ØÜš\[ÛŽ–ËÙ]XØÑ\ØÜš\[ÛŽ–ßKUÊOOžÙŠKŽJKŽKœÙ]ÛXZ[œÊK™ÛXZ[œÊKŽKœÙ]˜[œÚ][ÛœÊK˜[œÚ][ÛœÊ_KÜ[]X
KM^Ü\œÙN•Ê\Þ[˜ÈOOžÛ]X]ØZ]ÊÞ[™Yš[˜JNÑË™XYÊ
K

_K\œÙX
_KÊKÙYYY˜[™ÛX
KÊ\ÚÝš[™Ø
KÊ™\ÛÛ™TÙYY
KÊÙ[™\˜]Q›Û]
KÊMÙ[™\˜]RÜš^›Û[›Ý[™\žX
KÊÙ[™\˜]PÛY™”]
KÊÍÙ[™\˜]PÛÛ™\Ú[Û”]
K^ØÛÛ\^žÛ[Ù[˜›Ø™H8¡¤ˆÙ[œÙH8¡¤ˆ™\ÜÛ™˜XÝXÙN˜[Y\™Ù[˜XÝXÙ\ØKÛÛ\XØ]YžÛ[Ù[˜Ù[œÙH8¡¤ˆ[˜[\ÙH8¡¤ˆ™\ÜÛ™˜XÝXÙN˜ÛÛÙ˜XÝXÙ\ØKÛX\ŽžÛ[Ù[˜Ù[œÙH8¡¤ˆØ]YÛÜš\ÙH8¡¤ˆ™\ÜÛ™˜XÝXÙN˜™\Ý˜XÝXÙ\ØKÚ[ÝXÎžÛ[Ù[˜XÝ8¡¤ˆÙ[œÙH8¡¤ˆ™\ÜÛ™˜XÝXÙN˜›Ý™[˜XÝXÙ\ØKÛÛ™\Ú[ÛŽžÛ[Ù[˜˜XÝXÙN˜\ÛÜ™\˜_KUÊ
K
OOžÛ]YKÌ‹]ÌŽÜ™]\›žØÛÛ\^žØÞ›‹Ì‹ÞNœ‹Ì‹ŒNŒÎ›‹œŸKÛÛ\XØ]YžØÞ›ŠÛ‹Ì‹ÞNœ‹Ì‹›‹NŒÎ›‹œŸKÚ[ÝXÎžØÞ›‹Ì‹ÞNœŠÜ‹Ì‹ŒNœ‹Î›‹œŸKÛX\ŽžØÞ›ŠÛ‹Ì‹ÞNœŠÜ‹Ì‹›‹Nœ‹Î›‹œŸKÛÛ™\Ú[ÛŽžØÞ›‹ÞNœ‹›Š‹ËNœŠ‹ËÎ›Š‹‹œŠ‹Ÿ__KÙ]ÛXZ[“^[Ý]Ø
KÍUÊ

OO”ZÊÊ
K]Ê
K[YU˜\šXX›\ÊK˜Þ[™Yš[‹Ù]Þ[™Yš[‘ÛXZ[ÛÛÜœØ
KNOLËÍ^Ù˜]Î•Ê
K‹ŠOOžÛ]O\‹™‹OZK™Ù]ÛXZ[œÊ
KÏZK™Ù]˜[œÚ][ÛœÊ
KÏZK™Ù]XYÜ˜[U]J
KZK™Ù]XØÕ]J
KOZK™Ù]XØÑ\ØÜš\[ÛŠ
KZK™Ù]ÛÛ™šYÊ
KTÍ

NÑË™XYÊ™[™\š[™ÈÞ[™Yš[ˆXYÜ˜[X
NÛ]YÚYOYšZYÚYœY[™ËÏYœÚÝÑÛXZ[‘\ØÜš\[ÛœËÏY˜›Ý[™\žP[\]YK\
Ú
Œ‹O[JÚ
Œ‹^ØÛÛ\^™‹˜ÛÛ\^™ËÛÛ\XØ]Y™‹˜ÛÛ\XØ]Y™ËÛX\Ž™‹˜ÛX\™ËÚ[ÝXÎ™‹˜Ú[ÝXÐ™ËÛÛ™\Ú[ÛŽ™‹˜ÛÛ™\Ú[Û™ßKU“Ê
NÞÊK‹\ÙSX^ÚYÏÈL
K˜]ŠšY]Ð›Þ	ÝŸH	Þ_X
K	‰ž˜\[™
]X
K^

KI‰ž˜\[™
\ØØ
K^
JNÛ]Ï^˜\[™
Ø
K˜]Š˜[œÙ›Ü›X˜[œÛ]J	ÚK	ÚJX
KÏ^
JKÏY
œÙYY
KTË˜\[™
Ø
K˜]ŠÛ\ÜØÞ[™Yš[‹X˜XÚÙÜ›Ý[™Ø
KOVØÛÛ\^ÛÛ\XØ]YÚ[ÝXØÛX\˜NÙ›ÜŠ]HÙˆJ^Û]PÖÙWNÕ˜\[™
™XÝ
K˜]ŠÛ\ÜØÞ[™Yš[‘ÛXZ[˜
K˜]Šž
K˜]ŠXžJK˜]ŠÚYÊK˜]ŠZYÚš
K˜]Šš[–ÙWJK˜]Šš[[ÜXÚ]X
K˜]ŠÝ›ÚÙX›Û™X
_[]TË˜\[™
Ø
K˜]ŠÛ\ÜØÞ[™Yš[‹X›Ý[™\šY\Ø
NÑ˜\[™
]
K˜]ŠÛ\ÜØÞ[™Yš[›Ý[™\žX
K˜]Š
KËÊJK˜]Šš[›Û™X
K˜\[™
]
K˜]ŠÛ\ÜØÞ[™Yš[›Ý[™\žX
K˜]ŠM
KÊÌLÊJK˜]Šš[›Û™X
K˜\[™
]
K˜]ŠÛ\ÜØÞ[™Yš[ÛY™˜
K˜]Š
JJK˜]Šš[›Û™X
NÛ]Ï\
‹ŒMKÏ[J‹ŒMNÔË˜\[™
]
K˜]ŠÛ\ÜØÞ[™Yš[ÛÛ™\Ú[Û˜
K˜]ŠÍ
Ì‹KÌ‹ËÊJK˜]Šš[‹˜ÛÛ™\Ú[ÛŠK˜]Šš[[ÜXÚ]XJNÛ]OTË˜\[™
Ø
K˜]ŠÛ\ÜØÞ[™Yš[‹[X™[Ø
NÙ›ÜŠ]HÙˆJ^Û]PÖÙWNÐK˜\[™
^
K˜]ŠÛ\ÜØÞ[™Yš[‘ÛXZ[“X™[
K˜]Š˜Þ
K˜]ŠXÏÝ˜ÞKLÌ˜ÞJK˜]Š^X[˜ÚÜ˜ZYX
K˜]ŠÛZ[˜[X˜\Ù[[™XZYX
K^
K˜Ú\]

KÕ\\Ø\ÙJ
JÙKœÛXÙJJJ_ZYŠK˜\[™
^
K˜]ŠÛ\ÜØÞ[™Yš[‘ÛXZ[“X™[
K˜]ŠÌŠK˜]ŠXÏÛKÌ‹LL›KÌŠK˜]Š^X[˜ÚÜ˜ZYX
K˜]ŠÛZ[˜[X˜\Ù[[™XZYX
K^
ÛÛ™\Ú[Û˜
KÊ^Û]OTË˜\[™
Ø
K˜]ŠÛ\ÜØÞ[™Yš[‹\ÝX]\Ø
NÙ›ÜŠ]ÙˆJ^Û]PÖÝKXÝNÙK˜\[™
^
K˜]ŠÛ\ÜØÞ[™Yš[”ÝX]X
K˜]Š‹˜Þ
K˜]ŠX‹˜ÞKLL
K˜]Š^X[˜ÚÜ˜ZYX
K˜]ŠÛZ[˜[X˜\Ù[[™XZYX
K^
‹›[Ù[
KK˜\[™
^
K˜]ŠÛ\ÜØÞ[™Yš[”ÝX]X
K˜]Š‹˜Þ
K˜]ŠX‹˜ÞJÍJK˜]Š^X[˜ÚÜ˜ZYX
K˜]ŠÛZ[˜[X˜\Ù[[™XZYX
K^
‹œ˜XÝXÙJ_YK˜\[™
^
K˜]ŠÛ\ÜØÞ[™Yš[”ÝX]X
K˜]ŠÌŠK˜]ŠXKÌŠÎ
K˜]Š^X[˜ÚÜ˜ZYX
K˜]ŠÛZ[˜[X˜\Ù[[™XZYX
K^
˜ÛÛ™\Ú[Û‹œ˜XÝXÙJ_[]TË˜\[™
Ø
K˜]ŠÛ\ÜØÞ[™Yš[‹Z][\Ø
NÙ›ÜŠ]HÙ–ØÛÛ\^ÛÛ\XØ]YÚ[ÝXØÛX\˜ÛÛ™\Ú[Û˜J^Û]XK™Ù]
JNÚYŠ]š][\Ë›[™ÝOOL
XÛÛ[YNÛ]PÖÙWKYOOOXÛÛ™\Ú[Û˜O]š][\ËÏLÜ‰‰š][\Ë›[™ÝšNI‰ŠÏ]š][\Ë›[™ÝZNKO]š][\ËœÛXÙJNJJNÛ]ÎÚYŠŠ^Û]OYÏÌŒŽŒMÜÏ[‹˜ÞJÙ_Y[ÙHÏ[‹˜ÞJÊÏÌNŒMJNÚYŠË‹‹šWK™›Ü‘XXÚ

ŠOOžÛ]O\ÊÜŠŒÌOZ‹˜\[™
Ø
KÏXK˜\[™
^
K˜]ŠÛ\ÜØÞ[™Yš[’][U^
K˜]Š
K˜]ŠX‹ÌŠK˜]Š^X[˜ÚÜ˜ZYX
K˜]ŠÛZ[˜[X˜\Ù[[™XÙ[˜[
K^
›X™[
K]›X™[›[™Ý
ËO[Ë››ÙJ
NÚYŠI‰\[ÙˆK™Ù]›ÞOX[˜Ý[Û˜
^Û]O]K™Ù]›Þ

NÙKÚYŒ	‰ŠYKÚY
_[][
ÌŒ[‹˜ÞYÌŽØK˜]Š˜[œÙ›Ü›X˜[œÛ]J	ÙŸK	Ú_JX
KKš[œÙ\
™XÝ^
K˜]ŠÛ\ÜØÞ[™Yš[’][X
K˜]Š
K˜]ŠX
K˜]ŠÚY
K˜]ŠZYÚŠK˜]Šž
K˜]ŠžX
K˜]Šš[–ÙWJK˜]Šš[[ÜXÚ]XŽMJKË˜]ŠÌŠK˜]ŠX‹ÌŠ_JKÏŒ
^Û]\ÊÚK›[™Ý
ŒÌX
ÉÛßH[Ü™XOZ‹˜\[™
Ø
KXK˜\[™
^
K˜]ŠÛ\ÜØÞ[™Yš[’][U^
K˜]Š
K˜]ŠX‹ÌŠK˜]Š^X[˜ÚÜ˜ZYX
K˜]ŠÛZ[˜[X˜\Ù[[™XÙ[˜[
K^
ŠKO\‹›[™Ý
Ë[››ÙJ
NÚYŠ	‰\[Ùˆ™Ù]›ÞOX[˜Ý[Û˜
^Û]OY™Ù]›Þ

NÙKÚYŒ	‰ŠOYKÚY
_[]]JÌŒ[‹˜ÞY‹ÌŽØK˜]Š˜[œÙ›Ü›X˜[œÛ]J	ÜK	ÝJX
KKš[œÙ\
™XÝ^
K˜]ŠÛ\ÜØÞ[™Yš[’][SÝ™\™›ÝØ
K˜]Š
K˜]ŠX
K˜]ŠÚYŠK˜]ŠZYÚŠK˜]Šž
K˜]ŠžX
K˜]Šš[–ÙWJK˜]Šš[[ÜXÚ]XŠK˜]Š‹ÌŠK˜]ŠX‹ÌŠ__ZYŠË›[™ÝŒ
^Û]O^œÙ[XÝ
YœØ
K™[\J
OÞ˜\[™
YœØ
NžœÙ[XÝ
YœØ
KXÞ[™Yš[‹X\œ›ÝËIÝXÙK˜\[™
X\šÙ\˜
K˜]ŠYŠK˜]ŠšY]Ð›ÞLL
K˜]Š™Y–JK˜]Š™Y–XJK˜]ŠX\šÙ\•ÚYŠK˜]ŠX\šÙ\’ZYÚŠK˜]ŠÜšY[]]Ë\Ý\\™]™\œÙX
K˜\[™
]
K˜]ŠHLHL˜
K˜]ŠÛ\ÜØÞ[™Yš[\œ›ÝÒXY
NÛ]TË˜\[™
Ø
K˜]ŠÛ\ÜØÞ[™Yš[‹X\œ›ÝÜØ
NÛË™›Ü‘XXÚ
OOžÛ]PÖÙK™œ›ÛWKOPÖÙK×NÚYŠ]ZJ\™]\›ŽÚYŠK™œ›ÛOOOYKÊ^ÑËØ\›ŠÞ[™Yš[ˆ™[™\™\ŽˆÚÚ\[™ÈÙ[‹[ÛÜÛˆÛXZ[ˆ‰ÙK™œ›Û_H˜
NÜ™]\›Ÿ[]O]˜ÞÏ]˜ÞKÏZK˜ÞZK˜ÞKOJJÜÊKÌ‹JÊÛ
KÌ‹\ËXK[[ËOSX]œÜ\
Š™ŠÜ
œ
K[J‹ŒMKÏK\ÛKÏY‹ÛK]JÙÊšOY
×ÊšÜ‹˜\[™
]
K˜]ŠÛ\ÜØÞ[™Yš[\œ›ÝÓ[™X
K˜]ŠIØ_K	ÛßHIÝŸK	Þ_H	ÜßK	ÛX
K˜]Šš[›Û™X
K˜]ŠX\šÙ\‹Y[™\›
ÉÛŸJX
KK›X™[	‰œ‹˜\[™
^
K˜]ŠÛ\ÜØÞ[™Yš[\œ›ÝÓX™[
K˜]ŠŠK˜]ŠXKMŠK˜]Š^X[˜ÚÜ˜ZYX
K˜]ŠÛZ[˜[X˜\Ù[[™X]]Ø
K^
K›X™[
_J_\É‰”Ë˜\[™
^
K˜]ŠÛ\ÜØÞ[™Yš[•]X
K˜]ŠÌŠK˜]ŠXZÌŠK˜]Š^X[˜ÚÜ˜ZYX
K˜]ŠÛZ[˜[X˜\Ù[[™XZYX
K^
Ê_K˜]Ø
_KÍUÊ

OO”ZÊÊ
K]Ê
K[YU˜\šXX›\ÊK˜Þ[™Yš[‹Ù]Þ[™Yš[•[YX
K^Ü\œÙ\ŽžMŽœŽK™[™\™\ŽÍÝ[\Î•Ê

OOžÛ]O]Í

NÜ™]\›˜‚K˜Þ[™Yš[‘ÛXZ[ˆÂ‚B\Ý›ÚÙNˆ›Û™NÂ‚_B‚K˜Þ[™Yš[‘ÛXZ[“X™[Â‚BY›Û\Ú^™Nˆ	ÙK™ÛXZ[‘›ÛÚ^™_\Â‚BY›Û]ÙZYÚˆ›ÛÂ‚BYš[ˆ	ÙK›X™[ÛÛÜŸNÂ‚_B‚K˜Þ[™Yš[”ÝX]HÂ‚BY›Û\Ú^™Nˆ	ÙKš][Q›ÛÚ^™KL_\Â‚BYš[ˆ	ÙK^ÛÛÜŸNÂ‚BY›Û\Ý[Nˆ][XÎÂ‚_B‚K˜Þ[™Yš[’][HÂ‚BYš[[ÜXÚ]NˆŽMNÂ‚B\Ý›ÚÙNˆ	ÙK˜›Ý[™\žPÛÛÜŸNÂ‚B\Ý›ÚÙK]ÚYˆNÂ‚_B‚K˜Þ[™Yš[’][U^Â‚BY›Û\Ú^™Nˆ	ÙKš][Q›ÛÚ^™_\Â‚BYš[ˆ	ÙK^ÛÛÜŸNÂ‚_B‚K˜Þ[™Yš[’][SÝ™\™›ÝÈÂ‚BYš[[ÜXÚ]NˆŽÂ‚B\Ý›ÚÙNˆ	ÙK˜›Ý[™\žPÛÛÜŸNÂ‚B\Ý›ÚÙK]ÚYˆNÂ‚B\Ý›ÚÙKY\Ú\œ˜^NˆÈŽÂ‚_B‚K˜Þ[™Yš[›Ý[™\žHÂ‚B\Ý›ÚÙNˆ	ÙK˜›Ý[™\žPÛÛÜŸNÂ‚B\Ý›ÚÙK]ÚYˆ	ÙK˜›Ý[™\žUÚYNÂ‚B\Ý›ÚÙKY\Ú\œ˜^NˆˆÎÂ‚_B‚K˜Þ[™Yš[ÛY™ˆÂ‚B\Ý›ÚÙNˆ	ÙK˜ÛY™ÛÛÜŸNÂ‚B\Ý›ÚÙK]ÚYˆ	ÙK˜ÛY™•ÚYNÂ‚_B‚K˜Þ[™Yš[ÛÛ™\Ú[ÛˆÂ‚B\Ý›ÚÙNˆ	ÙK˜›Ý[™\žPÛÛÜŸNÂ‚B\Ý›ÚÙK]ÚYˆKNÂ‚B\Ý›ÚÙKY\Ú\œ˜^NˆŽÂ‚_B‚K˜Þ[™Yš[\œ›ÝÓ[™HÂ‚B\Ý›ÚÙNˆ	ÙK˜\œ›ÝÐÛÛÜŸNÂ‚B\Ý›ÚÙK]ÚYˆ	ÙK˜\œ›ÝÕÚYNÂ‚BYš[ˆ›Û™NÂ‚_B‚K˜Þ[™Yš[\œ›ÝÒXYÂ‚BYš[ˆ	ÙK˜\œ›ÝÐÛÛÜŸNÂ‚B\Ý›ÚÙNˆ›Û™NÂ‚_B‚K˜Þ[™Yš[\œ›ÝÓX™[Â‚BY›Û\Ú^™Nˆ	ÙKš][Q›ÛÚ^™KL_\Â‚BYš[ˆ	ÙK^ÛÛÜŸNÂ‚_B‚K˜Þ[™Yš[•]HÂ‚BY›Û\Ú^™Nˆ	ÙK™ÛXZ[‘›ÛÚ^™JÌŸ\Â‚BY›Û]ÙZYÚˆ›ÛÂ‚BYš[ˆ	ÙK›X™[ÛÛÜŸNÂ‚_B‚XKÝ[\Ø
__JJKNKÎKÎKÎKKNKKÍÍŽKKMMNKMKÎKÎKŽKNKŽO[Ê


OOžÒÊ
KÕ

KžJ
KJ
KNOXÎOXÎOXÎOV×KO[™]ÈX\NOUÊOO“ÝÊKJ
JKØ[š]^™U^
KOUÊOOžÜÝÚ]Ú
K\J^ØØ\ÙX\›Z[˜[œ™]\›žË‹‹™K˜[YNNJK˜[YJ_NØØ\ÙX›Û\›Z[˜[œ™]\›žË‹‹™K˜[YNNJK›˜[YJ_NØØ\ÙXÙ\]Y[˜ÙXœ™]\›žË‹‹™K[[Y[Î™K™[[Y[Ë›X\
J_NØØ\ÙXÚÚXÙXœ™]\›žË‹‹™K[\›˜]]™\Î™K˜[\›˜]]™\Ë›X\
J_NØØ\ÙXÜ[Û˜[œ™]\›žË‹‹™K[[Y[™JK™[[Y[
_NØØ\ÙX™\]][Û˜œ™]\›žË‹‹™K[[Y[™JK™[[Y[
KÙ\\˜]ÜŽ™KœÙ\\˜]ÜÙJKœÙ\\˜]ÜŠN›ÚYNØØ\ÙXÜXÚX[œ™]\›žË‹‹™K^NJK^
___KØ[š]^™P\Ý›ÙX
KUÊ

OOžØNOXÎOXÎOXÎK›[™ÝLK˜ÛX\Š
K]Ê
KË™XYÊÔ˜Z[›ØYH]X˜\ÙHÛX\™Y
_KÛX\˜
KÍUÊOOžØNO]NJJKË™XYÊÔ˜Z[›ØYH]HÙ]˜J_KÙ]]X
KÍUÊ

OO˜NKÙ]]X
KŽO^ØÛX\Ž‘Ù]]N“ÍÙ]]NšÍY[N•ÊOOžÛ]^Ë‹‹™K˜[YNNJK›˜[YJKYš[š][ÛŽ™JK™Yš[š][ÛŠKÛÛ[Y[™K˜ÛÛ[Y[ÝNJK˜ÛÛ[Y[
N›ÚYNÑË™XYÊÔ˜Z[›ØYHY[™È[N˜›˜[YJKKš\Ê›˜[YJI‰‘ËØ\›ŠÔ˜Z[›ØYH[H	ÉÝ›˜[Y_IÈ\È[™XYHYš[™YˆÝ™\Üš][™Ë˜
KÎKœ\Ú

KKœÙ]
›˜[YK
_KY[X
KÙ][\Î•Ê

OO˜ÎKÙ][\Ø
KÙ][N•ÊOO›K™Ù]
JKÙ][X
KÙ]XØÕ]N•ÊOOžÛÎO]NJJKœ™\XÙJ×—ÊËÙË
KË™XYÊÔ˜Z[›ØYHXØÙ\ÜÚXš[]H]HÙ]˜J_KÙ]XØÕ]X
KÙ]XØÕ]N•Ê

OO›ÎKÙ]XØÕ]X
KÙ]XØÑ\ØÜš\[ÛŽ•ÊOOžÜÎO]NJJKœ™\XÙJ×—ÊËÙË˜
KË™XYÊÔ˜Z[›ØYHXØÙ\ÜÚXš[]H\ØÜš\[ÛˆÙ]˜J_KÙ]XØÑ\ØÜš\[Û˜
KÙ]XØÑ\ØÜš\[ÛŽ•Ê

OOœÎKÙ]XØÑ\ØÜš\[Û˜
KÙ]XYÜ˜[U]N“ÍÙ]XYÜ˜[U]NšÍKO^ØÛÛ\XÝ[ÙNˆLKY[™ÎŒL™\XØ[Ù\\˜][ÛŽŽÜš^›Û[Ù\\˜][ÛŽŒL\˜Ô˜Y]\ÎŒL›ÛÚ^™NŒM›Û˜[Z[N˜[Û›ÜÜXÙX\›Z[˜[š[˜Ñ‘‘‘Ì\›Z[˜[Ý›ÚÙN˜Ì\›Z[˜[^ÛÛÜŽ˜Ì›Û•\›Z[˜[š[˜Ñ‘‘‘‘‘˜›Û•\›Z[˜[Ý›ÚÙN˜Ì›Û•\›Z[˜[^ÛÛÜŽ˜Ì[™PÛÛÜŽ˜ÌÝ›ÚÙUÚYŒ‹X\šÙ\‘š[˜ÌÛÛ[Y[š[˜ÑNNNÛÛ[Y[Ý›ÚÙN˜ÎÛÛ[Y[^ÛÛÜŽ˜Í˜ÜXÚX[š[˜ÑŒL‘˜ÜXÚX[Ý›ÚÙN˜ÎÐØ[S˜[YPÛÛÜŽ˜Ì˜ÚÝÓX\šÙ\œÎˆLX\šÙ\”˜Y]\Î_KMK×ˆÊÎ–×KY—^ÌË_×KY—^ÍŸ_×KY—^ÎJIŠÎœ™ØŸ™Ø˜_ÛÛ_ØŸXŸÚÚÛXŸÚÛÚ
W
×ÉJË‹ËWJ×
I–ØK^—JÉÚKK×–×È‰Ë‹WJÉËM[™]ÈÙ]
ØÛÛ\XÝ[ÙXY[™Ø™\XØ[Ù\\˜][Û˜Üš^›Û[Ù\\˜][Û˜\˜Ô˜Y]\Ø›ÛÚ^™X›Û˜[Z[X\›Z[˜[š[\›Z[˜[Ý›ÚÙX\›Z[˜[^ÛÛÜ˜›Û•\›Z[˜[š[›Û•\›Z[˜[Ý›ÚÙX›Û•\›Z[˜[^ÛÛÜ˜[™PÛÛÜ˜Ý›ÚÙUÚYX\šÙ\‘š[ÛÛ[Y[š[ÛÛ[Y[Ý›ÚÙXÛÛ[Y[^ÛÛÜ˜ÜXÚX[š[ÜXÚX[Ý›ÚÙX[S˜[YPÛÛÜ˜ÚÝÓX\šÙ\œØX\šÙ\”˜Y]\ØJKUÊOO™OÓØš™XÝšÙ^\ÊJK™]™\žJOO™OOOX˜Z[›ØYMš\ÊJJNˆLK\Ô˜Z[›ØYÝ[SÜ[ÛœØ
KUÊOO™OØ˜Z[›ØY[ˆI‰™Kœ˜Z[›ØYÙKœ˜Z[›ØY“
JOÙNžßNžßK^˜XÝ˜Z[›ØYÝ™\œšY\Ø
KUÊOOžÚYŠY_
JJ\™]\›žßNÛ]Ü˜Z[›ØYÝ™ÒY›‹[YNœ‹ÛÚÎšK‹‹˜_OYNÜ™]\›ˆ_K^˜XÝ[YSÝ™\œšY\Ø
KNOUÊ
K
OOžÚYŠ\[ÙˆHOXÝš[™Ø
\™]\›ˆÛ]YKš[J
NÜ™]\›ˆM\Ý
ŠOÛŽKØ[š]^™PÛÛÜ•˜[YX
KMUÊ
K
OOžÚYŠ\[ÙˆHOXÝš[™Ø
\™]\›ˆÛ]YKš[J
NÜ™]\›ˆ\Ý
ŠOÛŽKØ[š]^™Q›Û˜[Z[U˜[YX
KOUÊ
K
OOžÛ]]\[ÙˆOOX[X™\˜ÙN\[ÙˆOOXÝš[™ØÓ[X™\‹œ\œÙQ›Ø]
JN“˜SŽÜ™]\›ˆ[X™\‹š\Ñš[š]JŠI‰›LÛŽKØ[š]^™S[X™\•˜[YX
KUÊOOžÛ]]\[ÙˆOOX[X™\˜ÙN\[ÙˆOOXÝš[™ØÓ[X™\‹œ\œÙQ›Ø]
JN“˜SŽÜ™]\›ˆ[X™\‹š\Ñš[š]J
I‰ŒÝ›ÚYK\œÙU[YQ›ÛÚ^™X
KUÊOOžÛ]RM
K™›Û˜[Z[KK™›Û˜[Z[JKS
K™›ÛÚ^™JOÏÜK™›ÛÚ^™NÜ™]\›žË‹‹œK›Û˜[Z[N›ÛÚ^™N›‹\›Z[˜[š[›NJKœÙXÛÛ™šÙÏÏÙKœÙXÛÛ™\žPÛÛÜ‹K\›Z[˜[š[
K\›Z[˜[Ý›ÚÙN›NJKœÙXÛÛ™\žP›Ü™\ÛÛÜÏÙK›[™PÛÛÜ‹K\›Z[˜[Ý›ÚÙJK\›Z[˜[^ÛÛÜŽ›NJKœÙXÛÛ™\žU^ÛÛÜÏÙK^ÛÛÜ‹K\›Z[˜[^ÛÛÜŠK›Û•\›Z[˜[š[›NJK›XZ[šÙÏÏÙK˜˜XÚÙÜ›Ý[™K››Û•\›Z[˜[š[
K›Û•\›Z[˜[Ý›ÚÙN›NJKœš[X\žP›Ü™\ÛÛÜÏÙK›[™PÛÛÜ‹K››Û•\›Z[˜[Ý›ÚÙJK›Û•\›Z[˜[^ÛÛÜŽ›NJKœš[X\žU^ÛÛÜÏÙK^ÛÛÜ‹K››Û•\›Z[˜[^ÛÛÜŠK[™PÛÛÜŽ›NJK›[™PÛÛÜ‹K›[™PÛÛÜŠKX\šÙ\‘š[›NJK›[™PÛÛÜ‹K›X\šÙ\‘š[
KÛÛ[Y[š[›NJK›X™[˜XÚÙÜ›Ý[™ÏÙK\X\žPÛÛÜ‹K˜ÛÛ[Y[š[
KÛÛ[Y[Ý›ÚÙN›NJK\X\žP›Ü™\ÛÛÜÏÙK›[™PÛÛÜ‹K˜ÛÛ[Y[Ý›ÚÙJKÛÛ[Y[^ÛÛÜŽ›NJK\X\žU^ÛÛÜÏÙK^ÛÛÜ‹K˜ÛÛ[Y[^ÛÛÜŠKÜXÚX[š[›NJK\X\žPÛÛÜÏÙKœÙXÛÛ™\žPÛÛÜ‹KœÜXÚX[š[
KÜXÚX[Ý›ÚÙN›NJK\X\žP›Ü™\ÛÛÜÏÙKœÙXÛÛ™\žP›Ü™\ÛÛÜ‹KœÜXÚX[Ý›ÚÙJK[S˜[YPÛÛÜŽ›NJK]PÛÛÜÏÙK^ÛÛÜ‹Kœ[S˜[YPÛÛÜŠ__KZ[[YQY˜][Ø
KÎOUÊOOžÛ]]]Ê
KT
Ë‹‹’Ê
K‹‹[YU˜\šXX›\ÏÏÞßK‹‹‘
J_JK^Ë‹‹œ˜Z[›ØYÏÞßK‹‹”
J_NÜ™]\›žØÛÛ\XÝ[ÙNœ‹˜ÛÛ\XÝ[ÙOÏÛ‹˜ÛÛ\XÝ[ÙKY[™ÎšJ‹œY[™Ë‹œY[™ÊK™\XØ[Ù\\˜][ÛŽšJ‹™\XØ[Ù\\˜][Û‹‹™\XØ[Ù\\˜][ÛŠKÜš^›Û[Ù\\˜][ÛŽšJ‹šÜš^›Û[Ù\\˜][Û‹‹šÜš^›Û[Ù\\˜][ÛŠK\˜Ô˜Y]\ÎšJ‹˜\˜Ô˜Y]\Ë‹˜\˜Ô˜Y]\ÊK›ÛÚ^™NšJ‹™›ÛÚ^™K‹™›ÛÚ^™JK›Û˜[Z[N’M
‹™›Û˜[Z[K‹™›Û˜[Z[JK\›Z[˜[š[›NJ‹\›Z[˜[š[‹\›Z[˜[š[
K\›Z[˜[Ý›ÚÙN›NJ‹\›Z[˜[Ý›ÚÙK‹\›Z[˜[Ý›ÚÙJK\›Z[˜[^ÛÛÜŽ›NJ‹\›Z[˜[^ÛÛÜ‹‹\›Z[˜[^ÛÛÜŠK›Û•\›Z[˜[š[›NJ‹››Û•\›Z[˜[š[‹››Û•\›Z[˜[š[
K›Û•\›Z[˜[Ý›ÚÙN›NJ‹››Û•\›Z[˜[Ý›ÚÙK‹››Û•\›Z[˜[Ý›ÚÙJK›Û•\›Z[˜[^ÛÛÜŽ›NJ‹››Û•\›Z[˜[^ÛÛÜ‹‹››Û•\›Z[˜[^ÛÛÜŠK[™PÛÛÜŽ›NJ‹›[™PÛÛÜ‹‹›[™PÛÛÜŠKÝ›ÚÙUÚYšJ‹œÝ›ÚÙUÚY‹œÝ›ÚÙUÚY
KX\šÙ\‘š[›NJ‹›X\šÙ\‘š[‹›X\šÙ\‘š[
KÛÛ[Y[š[›NJ‹˜ÛÛ[Y[š[‹˜ÛÛ[Y[š[
KÛÛ[Y[Ý›ÚÙN›NJ‹˜ÛÛ[Y[Ý›ÚÙK‹˜ÛÛ[Y[Ý›ÚÙJKÛÛ[Y[^ÛÛÜŽ›NJ‹˜ÛÛ[Y[^ÛÛÜ‹‹˜ÛÛ[Y[^ÛÛÜŠKÜXÚX[š[›NJ‹œÜXÚX[š[‹œÜXÚX[š[
KÜXÚX[Ý›ÚÙN›NJ‹œÜXÚX[Ý›ÚÙK‹œÜXÚX[Ý›ÚÙJK[S˜[YPÛÛÜŽ›NJ‹œ[S˜[YPÛÛÜ‹‹œ[S˜[YPÛÛÜŠKÚÝÓX\šÙ\œÎœ‹œÚÝÓX\šÙ\œÏÏÛ‹œÚÝÓX\šÙ\œËX\šÙ\”˜Y]\ÎšJ‹›X\šÙ\”˜Y]\Ë‹›X\šÙ\”˜Y]\Ê__KZ[˜Z[›ØYÝ[SÜ[ÛœØ
KÎOUÊOOžÛ]Ù›Û˜[Z[N›ÛÚ^™N›‹\›Z[˜[š[œ‹\›Z[˜[Ý›ÚÙNšK\›Z[˜[^ÛÛÜŽ˜K›Û•\›Z[˜[š[›Ë›Û•\›Z[˜[Ý›ÚÙNœË›Û•\›Z[˜[^ÛÛÜŽ›[™PÛÛÜŽKÝ›ÚÙUÚY™X\šÙ\‘š[™‹ÛÛ[Y[š[œÛÛ[Y[Ý›ÚÙN›KÛÛ[Y[^ÛÛÜŽšÜXÚX[š[™ËÜXÚX[Ý›ÚÙN—Ë[S˜[YPÛÛÜŽŸOYÎJJNÜ™]\›˜ˆœ˜Z[›ØYYXYÜ˜[HÂˆ›ÛY˜[Z[Nˆ	ÝNÂˆ›Û\Ú^™Nˆ	ÛŸ\ÂˆB‚ˆœ˜Z[›ØY]\›Z[˜[™XÝÂˆš[ˆ	ÜŸNÂˆÝ›ÚÙNˆ	Ú_NÂˆÝ›ÚÙK]ÚYˆ	Ù\ÂˆB‚ˆœ˜Z[›ØY]\›Z[˜[^Âˆš[ˆ	Ø_NÂˆ›ÛY˜[Z[Nˆ	ÝNÂˆ›Û\Ú^™Nˆ	ÛŸ\Âˆ^X[˜ÚÜŽˆZYNÂˆÛZ[˜[X˜\Ù[[™NˆZYNÂˆB‚ˆœ˜Z[›ØY[›Û\›Z[˜[™XÝÂˆš[ˆ	ÛßNÂˆÝ›ÚÙNˆ	ÜßNÂˆÝ›ÚÙK]ÚYˆ	Ù\ÂˆB‚ˆœ˜Z[›ØY[›Û\›Z[˜[^Âˆš[ˆ	ÛNÂˆ›ÛY˜[Z[Nˆ	ÝNÂˆ›Û\Ú^™Nˆ	ÛŸ\Âˆ^X[˜ÚÜŽˆZYNÂˆÛZ[˜[X˜\Ù[[™NˆZYNÂˆB‚ˆœ˜Z[›ØY[[™HÂˆÝ›ÚÙNˆ	Ý_NÂˆÝ›ÚÙK]ÚYˆ	Ù\Âˆš[ˆ›Û™NÂˆB‚ˆœ˜Z[›ØY\Ý\Ú\˜ÛKˆœ˜Z[›ØYY[™Ú\˜ÛHÂˆš[ˆ	ÙŸNÂˆB‚ˆœ˜Z[›ØYXÛÛ[Y[[\ÙHÂˆš[ˆ	ÜNÂˆÝ›ÚÙNˆ	Û_NÂˆÝ›ÚÙK]ÚYˆ	Ù\ÂˆB‚ˆœ˜Z[›ØYXÛÛ[Y[^Âˆš[ˆ	ÚNÂˆ›Û\Ý[Nˆ][XÎÂˆ›ÛY˜[Z[Nˆ	ÝNÂˆ›Û\Ú^™Nˆ	ÛŸ\Âˆ^X[˜ÚÜŽˆZYNÂˆÛZ[˜[X˜\Ù[[™NˆZYNÂˆB‚ˆœ˜Z[›ØY\ÜXÚX[™XÝÂˆš[ˆ	ÙßNÂˆÝ›ÚÙNˆ	×ßNÂˆÝ›ÚÙK]ÚYˆ	Ù\ÂˆÝ›ÚÙKY\Ú\œ˜^NˆKÎÂˆB‚ˆœ˜Z[›ØY\ÜXÚX[^Âˆš[ˆ	ÛNÂˆ›ÛY˜[Z[Nˆ	ÝNÂˆ›Û\Ú^™Nˆ	ÛŸ\Âˆ^X[˜ÚÜŽˆZYNÂˆÛZ[˜[X˜\Ù[[™NˆZYNÂˆB‚ˆœ˜Z[›ØY\[K[˜[YHÂˆ›Û]ÙZYÚˆ›ÛÂˆš[ˆ	ÝŸNÂˆ›ÛY˜[Z[Nˆ	ÝNÂˆ›Û\Ú^™Nˆ	ÛŸ\ÂˆB‚ˆœ˜Z[›ØYYÜ›Ý\ÂˆÊˆÜ›Ý\[™ÈÛÛZ[™\‹›ÈÜXÚYšXÈÝ[\È
‹ÂˆB˜KÙ]Ý[\Ø
KŽOXÛ\ÜÞØÛÛœÝXÝÜŠ
^Ý\Ë™X\Ý]XÞÕÊ\Ë]Z[\˜
_[[Ý™UÊK
^Ü™]\›ˆ\Ë™
ÏXH	Ù_H	ÝH\ß[[™UÊK
^Ü™]\›ˆ\Ë™
ÏX	Ù_H	ÝH\ßZÜš^›Û[ÊJ^Ü™]\›ˆ\Ë™
ÏX	Ù_H\ß]™\XØ[ÊJ^Ü™]\›ˆ\Ë™
ÏXˆ	Ù_H\ßX\˜ÕÊK‹‹KKÊ^Ü™]\›ˆ\Ë™
ÏXH	Ù_H	ÝH	ÛŸH	ÊÈH\ŸH	ÊÈHZ_H	Ø_H	ÛßH\ßXZ[

^Ü™]\›ˆ\Ë™š[J
__KXÛ\ÜÞØÛÛœÝXÝÜŠKYÎJ
J^Ý\Ë^ØXÚO[™]ÈX\\ËœÝ™ÏYK\Ë˜ÛÛ™šYÏ]\Ý]XÞÕÊ\Ë˜Z[›ØY™[™\™\˜
_[YX\Ý\™U^
J^ÚYŠ\Ë^ØXÚKš\ÊJJ\™]\›ˆ\Ë^ØXÚK™Ù]
JNÛ]]\ËœÝ™Ë˜\[™
^
K˜]Š›ÛY˜[Z[X\Ë˜ÛÛ™šYË™›Û˜[Z[JK˜]Š›Û\Ú^™X\Ë˜ÛÛ™šYË™›ÛÚ^™JK^
JK]››ÙJ
K™Ù]›Þ

K^ÝÚY›‹ÚYZYÚ›‹šZYÚNÜ™]\›ˆœ™[[Ý™J
K\Ë^ØXÚKœÙ]
KŠKŸ\™[™\•\›Z[˜[
K
^Û]]\Ë›YX\Ý\™U^

K[‹ÚY
Ý\Ë˜ÛÛ™šYËœY[™ÊŒ‹O[‹šZYÚ
Ý\Ë˜ÛÛ™šYËœY[™ÊŒ‹OYK˜\[™
Ø
K˜]ŠÛ\ÜØ˜Z[›ØY]\›Z[˜[
NÜ™]\›ˆK˜\[™
™XÝ
K˜]Š
K˜]ŠX
K˜]ŠÚYŠK˜]ŠZYÚJK˜]ŠžL
K˜]ŠžXL
KK˜\[™
^
K˜]Š‹ÌŠK˜]ŠXKÌŠK^

KÙ[[Y[˜K››ÙJ
K[Y[œÚ[ÛœÎžÝÚYœ‹ZYÚšK\šKÌ‹ÝÛŽšKÌŸ__\™[™\“›Û•\›Z[˜[
K
^Û]]\Ë›YX\Ý\™U^

K[‹ÚY
Ý\Ë˜ÛÛ™šYËœY[™ÊŒ‹O[‹šZYÚ
Ý\Ë˜ÛÛ™šYËœY[™ÊŒ‹OYK˜\[™
Ø
K˜]ŠÛ\ÜØ˜Z[›ØY[›Û\›Z[˜[
NÜ™]\›ˆK˜\[™
™XÝ
K˜]Š
K˜]ŠX
K˜]ŠÚYŠK˜]ŠZYÚJKK˜\[™
^
K˜]Š‹ÌŠK˜]ŠXKÌŠK^

KÙ[[Y[˜K››ÙJ
K[Y[œÚ[ÛœÎžÝÚYœ‹ZYÚšK\šKÌ‹ÝÛŽšKÌŸ__\™[™\”Ù\]Y[˜ÙJK
^Û]]›X\
O\Ëœ™[™\‘^™\ÜÚ[ÛŠK
JKLOLOLÙ›ÜŠ]HÙˆŠ\ŠÏYK™[Y[œÚ[ÛœËÚYOSX]›X^
KK™[Y[œÚ[ÛœË\
KOSX]›X^
KK™[Y[œÚ[ÛœË™ÝÛŠNÜŠÏJ‹›[™ÝLJJ\Ë˜ÛÛ™šYËšÜš^›Û[Ù\\˜][ÛŽÛ]ÏYK˜\[™
Ø
K˜]ŠÛ\ÜØ˜Z[›ØY\Ù\]Y[˜ÙX
KÏLÙ›ÜŠ]OLÙO‹›[™ÝÙJÊÊ^Û][–ÙWKZK]™[Y[œÚ[ÛœË\ÚYŠË››ÙJ
K˜\[™Ú[
™[[Y[
KœÙ]]šX]J˜[œÙ›Ü›X˜[œÛ]J	ÜßK	ÜŸJX
KO‹›[™ÝLJ^Û]O\ÊÝ™[Y[œÚ[ÛœËÚYYJÝ\Ë˜ÛÛ™šYËšÜš^›Û[Ù\\˜][Û‹ZNÛË˜\[™
]
K˜]ŠÛ\ÜØ˜Z[›ØY[[™X
K˜]Š™]ÈŽJ
K›[Ý™UÊKŠK›[™UÊ‹ŠK˜Z[

J_\ÊÏ]™[Y[œÚ[ÛœËÚY
Ý\Ë˜ÛÛ™šYËšÜš^›Û[Ù\\˜][ÛŸ\™]\›žÙ[[Y[›Ë››ÙJ
K[Y[œÚ[ÛœÎžÝÚYœ‹ZYÚšJØK\šKÝÛŽ˜___\™[™\ÚÚXÙJK
^Û]]›X\
O\Ëœ™[™\‘^™\ÜÚ[ÛŠK
JKLOLÙ›ÜŠ]HÙˆŠ\SX]›X^
‹K™[Y[œÚ[ÛœËÚY
KJÏYK™[Y[œÚ[ÛœËšZYÚÚJÏJ‹›[™ÝLJJ\Ë˜ÛÛ™šYË™\XØ[Ù\\˜][ÛŽÛ]O]\Ë˜ÛÛ™šYË˜\˜Ô˜Y]\ËÏXJÏ\ŠÛËYK˜\[™
Ø
K˜]ŠÛ\ÜØ˜Z[›ØYXÚÚXÙX
KOLZKÌŽÙ›ÜŠ]HÙˆŠ^Û]]K]
ÙK™[Y[œÚ[ÛœË\OXJŒŠÊ‹YK™[Y[œÚ[ÛœËÚY
KÌŽÛ››ÙJ
K˜\[™Ú[
K™[[Y[
KœÙ]]šX]J˜[œÙ›Ü›X˜[œÛ]J	Ú_K	ÝJX
NÛ]Ï[™]ÈŽK[™ÛOOYÛË›[Ý™UÊ
K›[™UÊKŠN›Ë›[Ý™UÊ
K˜\˜ÕÊKKLK‹K
ÊØN‹XJJK›[™UÊK‹JØN‹XJJK˜\˜ÕÊKKLKY‹JŒ‹ŠK›[™UÊKŠK˜\[™
]
K˜]ŠÛ\ÜØ˜Z[›ØY[[™X
K˜]ŠË˜Z[

JNÛ][™]ÈŽKOZJÙK™[Y[œÚ[ÛœËÚY\ËXJŒŽÛOOYÜ›[Ý™UÊKŠK›[™UÊË
Nœ›[Ý™UÊKŠK›[™UÊŠK˜\˜ÕÊKKLKY‹ËXKŠÊËXN˜JJK›[™UÊËXK
ÊØN‹XJJK˜\˜ÕÊKKLK‹Ë
K˜\[™
]
K˜]ŠÛ\ÜØ˜Z[›ØY[[™X
K˜]Š˜Z[

JKJÏYK™[Y[œÚ[ÛœËšZYÚ
Ý\Ë˜ÛÛ™šYË™\XØ[Ù\\˜][ÛŸ\™]\›žÙ[[Y[›››ÙJ
K[Y[œÚ[ÛœÎžÝÚYœËZYÚšK\™ÝÛŽšKY__\™[™\“Ü[Û˜[
K
^Û]]\Ëœ™[™\‘^™\ÜÚ[ÛŠK
K]\Ë˜ÛÛ™šYË˜\˜Ô˜Y]\ËO\ŠŒ‹O[‹™[Y[œÚ[ÛœËÚY
ÜŠÏ[‹™[Y[œÚ[ÛœËšZYÚ
ÚKÏYK˜\[™
Ø
K˜]ŠÛ\ÜØ˜Z[›ØY[Ü[Û˜[
K\ŠŒ‹OZNÜË››ÙJ
K˜\[™Ú[
‹™[[Y[
KœÙ]]šX]J˜[œÙ›Ü›X˜[œÛ]J	ÛK	Ý_JX
NÛ]]JÛ‹™[Y[œÚ[ÛœË\[™]ÈŽJ
K›[Ý™UÊ
K›[™UÊŠŒ‹
NÜË˜\[™
]
K˜]ŠÛ\ÜØ˜Z[›ØY[[™X
K˜]Š‹˜Z[

JNÛ][™]ÈŽJ
K›[Ý™UÊ
Û‹™[Y[œÚ[ÛœËÚY
K›[™UÊK
NÜË˜\[™
]
K˜]ŠÛ\ÜØ˜Z[›ØY[[™X
K˜]Š˜Z[

JNÛ]O[™]ÈŽJ
K›[Ý™UÊ
K˜\˜ÕÊ‹‹LKLK‹\ŠK›[™UÊ‹ŠK˜\˜ÕÊ‹‹LKLŠŒ‹
K›[™UÊK\ŠŒ‹
K˜\˜ÕÊ‹‹LKLK\‹ŠK›[™UÊK\‹\ŠK˜\˜ÕÊ‹‹LKLKK
NÜ™]\›ˆË˜\[™
]
K˜]ŠÛ\ÜØ˜Z[›ØY[[™X
K˜]ŠK˜Z[

JKÙ[[Y[œË››ÙJ
K[Y[œÚ[ÛœÎžÝÚY˜KZYÚ›Ë\™ÝÛŽ›ËY__\™[™\”™\]][ÛŠKŠ^Û]]\Ëœ™[™\‘^™\ÜÚ[ÛŠK
KO]\Ë˜ÛÛ™šYË˜\˜Ô˜Y]\ËOZJŒ‹Ï\‹™[Y[œÚ[ÛœËÚY
ÚJÏ[OOL\‹™[Y[œÚ[ÛœËšZYÚ
ØJÊÏØNŒ
KOYK˜\[™
Ø
K˜]ŠÛ\ÜØ˜Z[›ØY\™\]][Û˜
KZJŒ‹\ÏØNŒÝK››ÙJ
K˜\[™Ú[
‹™[[Y[
KœÙ]]šX]J˜[œÙ›Ü›X˜[œÛ]J	ÙK	ÙŸJX
NÛ]YŠÜ‹™[Y[œÚ[ÛœË\ÝK˜\[™
]
K˜]ŠÛ\ÜØ˜Z[›ØY[[™X
K˜]Š™]ÈŽJ
K›[Ý™UÊ
K›[™UÊJŒ‹
K˜Z[

JKK˜\[™
]
K˜]ŠÛ\ÜØ˜Z[›ØY[[™X
K˜]Š™]ÈŽJ
K›[Ý™UÊ
Ü‹™[Y[œÚ[ÛœËÚY
K›[™UÊË
K˜Z[

JNÛ]OYŠÜ‹™[Y[œÚ[ÛœËšZYÚ
ÚK[™]ÈŽJ
K›[Ý™UÊ
Ü‹™[Y[œÚ[ÛœËÚY
K˜\˜ÕÊKKLKL
Ü‹™[Y[œÚ[ÛœËÚY
ÚK
ÚJK›[™UÊ
Ü‹™[Y[œÚ[ÛœËÚY
ÚKJK˜\˜ÕÊKKLKL
Ü‹™[Y[œÚ[ÛœËÚYJÚJK›[™UÊJŒ‹JÚJK˜\˜ÕÊKKLKLKJK›[™UÊK
ÚJK˜\˜ÕÊKKLKLJŒ‹
NÚYŠK˜\[™
]
K˜]ŠÛ\ÜØ˜Z[›ØY[[™X
K˜]Š˜Z[

JKÊ^Û]O[™]ÈŽJ
K›[Ý™UÊ
K˜\˜ÕÊKKLKLKKZJK›[™UÊKJK˜\˜ÕÊKKLKLJŒ‹
K›[™UÊËZJŒ‹
K˜\˜ÕÊKKLKLËZKJK›[™UÊËZKZJK˜\˜ÕÊKKLKLKË
NÝK˜\[™
]
K˜]ŠÛ\ÜØ˜Z[›ØY[[™X
K˜]ŠK˜Z[

J_\™]\›žÙ[[Y[K››ÙJ
K[Y[œÚ[ÛœÎžÝÚY›ËZYÚ›\œÝÛŽ›\__\™[™\”ÜXÚX[
K
^Û]]\Ë›YX\Ý\™U^
È
Ý
ØØ
K[‹ÚY
Ý\Ë˜ÛÛ™šYËœY[™ÊŒ‹O[‹šZYÚ
Ý\Ë˜ÛÛ™šYËœY[™ÊŒ‹OYK˜\[™
Ø
K˜]ŠÛ\ÜØ˜Z[›ØY\ÜXÚX[
NÜ™]\›ˆK˜\[™
™XÝ
K˜]Š
K˜]ŠX
K˜]ŠÚYŠK˜]ŠZYÚJKK˜\[™
^
K˜]Š‹ÌŠK˜]ŠXKÌŠK^
È
Ý
ØØ
KÙ[[Y[˜K››ÙJ
K[Y[œÚ[ÛœÎžÝÚYœ‹ZYÚšK\šKÌ‹ÝÛŽšKÌŸ__\™[™\‘^™\ÜÚ[ÛŠK
^ÜÝÚ]Ú
\J^ØØ\ÙX\›Z[˜[œ™]\›ˆ\Ëœ™[™\•\›Z[˜[
K˜[YJNØØ\ÙX›Û\›Z[˜[œ™]\›ˆ\Ëœ™[™\“›Û•\›Z[˜[
K›˜[YJNØØ\ÙXÙ\]Y[˜ÙXœ™]\›ˆ\Ëœ™[™\”Ù\]Y[˜ÙJK™[[Y[ÊNØØ\ÙXÚÚXÙXœ™]\›ˆ\Ëœ™[™\ÚÚXÙJK˜[\›˜]]™\ÊNØØ\ÙXÜ[Û˜[œ™]\›ˆ\Ëœ™[™\“Ü[Û˜[
K™[[Y[
NØØ\ÙX™\]][Û˜œ™]\›ˆ\Ëœ™[™\”™\]][ÛŠK™[[Y[›Z[ŠNØØ\ÙXÜXÚX[œ™]\›ˆ\Ëœ™[™\”ÜXÚX[
K^
NÙY˜][›ÝÈ\œ›ÜŠ[šÛ›ÝÛˆ›ÙH\Nˆ	Ý\_X
__\™[™\”[JK
^Û]]\ËœÝ™Ë˜\[™
Ø
K˜]ŠÛ\ÜØ˜Z[›ØY\[X
K˜]Š˜[œÙ›Ü›X˜[œÛ]J	ÝJX
KYK›˜[YJØXO]\Ë›YX\Ý\™U^
ŠKÚY
ÌŒOZJÌŒÏ[‹˜\[™
Ø
KÏ]\Ëœ™[™\‘^™\ÜÚ[ÛŠËK™Yš[š][ÛŠKSX]›X^
ŒË™[Y[œÚ[ÛœË\
KO[\Ë™[Y[œÚ[ÛœË\Ü™]\›ˆË˜]Š˜[œÙ›Ü›X˜[œÛ]J	Ø_K	Ý_JX
K‹˜\[™
Ø
K˜]ŠÛ\ÜØ˜Z[›ØY\[K[˜[YKYÜ›Ý\
K˜\[™
^
K˜]ŠÛ\ÜØ˜Z[›ØY\[K[˜[YX
K˜]Š
K˜]ŠX
K^
ŠK‹˜\[™
Ø
K˜]ŠÛ\ÜØ˜Z[›ØY\Ý\
K˜\[™
Ú\˜ÛX
K˜]ŠÞJK˜]ŠÞX
K˜]Š˜\Ë˜ÛÛ™šYË›X\šÙ\”˜Y]\ÊK‹˜\[™
Ø
K˜]ŠÛ\ÜØ˜Z[›ØYY[™
K˜\[™
Ú\˜ÛX
K˜]ŠÞJÜË™[Y[œÚ[ÛœËÚY
ÌL
K˜]ŠÞX
K˜]Š˜\Ë˜ÛÛ™šYË›X\šÙ\”˜Y]\ÊK‹˜\[™
]
K˜]ŠÛ\ÜØ˜Z[›ØY[[™X
K˜]Š™]ÈŽJ
K›[Ý™UÊJÝ\Ë˜ÛÛ™šYË›X\šÙ\”˜Y]\Ë
K›[™UÊK
K˜Z[

JK‹˜\[™
]
K˜]ŠÛ\ÜØ˜Z[›ØY[[™X
K˜]Š™]ÈŽJ
K›[Ý™UÊJÜË™[Y[œÚ[ÛœËÚY
K›[™UÊJÜË™[Y[œÚ[ÛœËÚY
ÌL]\Ë˜ÛÛ™šYË›X\šÙ\”˜Y]\Ë
K˜Z[

JKÚZYÚ“X]›X^
JÜË™[Y[œÚ[ÛœËšZYÚ
Ý\Ë˜ÛÛ™šYËœY[™ÊŒŠKÚY˜JÜË™[Y[œÚ[ÛœËÚY
ÌL
Ý\Ë˜ÛÛ™šYË›X\šÙ\”˜Y]\ß_\™[™\‘XYÜ˜[JJ^Û]]\Ë˜ÛÛ™šYËœY[™ËLÙ›ÜŠ]ˆÙˆJ^Û]O]\Ëœ™[™\”[J‹
NÝ
ÏYKšZYÚ
Ý\Ë˜ÛÛ™šYË™\XØ[Ù\\˜][Û‹SX]›X^
‹KÚY
_\™]\›žÝÚY›ŠÝ\Ë˜ÛÛ™šYËœY[™ÊŒ‹ZYÚ
Ý\Ë˜ÛÛ™šYËœY[™ß__KUÊ
KŠOOžÞÊKšZYÚÚYŠKK˜]ŠšY]Ð›Þ	ÝÚYH	ÝšZYÚX
_KÛÛ™šYÝ\™T˜Z[›ØYÝ™ÔÚ^™X
KNO^Ù˜]Î•Ê
KŠOOžÑË™XYÊÔ˜Z[›ØYH™[™\š[™ÈXYÜ˜[B˜
ÙJNÝž^Û]OU“Ê
NÙK˜]ŠÛ\ÜØ˜Z[›ØYYXYÜ˜[X
NÛ]]]Ê
Kœ˜Z[›ØYË\ÙSX^ÚYÏÈLYŽK™Ù][\Ê
NÚYŠË™XYÊÔ˜Z[›ØYH™[™\š[™È	Ü‹›[™ÝH[\Ø
K‹›[™ÝOOL
^ÑËØ\›ŠÔ˜Z[›ØYH›È[\ÈÈ™[™\˜
K
KÚZYÚŒLÚYŒŒKŠNÜ™]\›ŸP
K™]È
KÎJ
JKœ™[™\‘XYÜ˜[JŠKŠKË™XYÊÔ˜Z[›ØYH™[™\ˆÛÛ\]X
_XØ]Ú
J^Ý›ÝÈË™\œ›ÜŠÔ˜Z[›ØYH™[™\ˆ\œ›ÜŽ˜JK__K˜]Ø
__JJK[
ÙY˜][Š
OO’ÍXYÜ˜[NŠ
OO‘ÍJKKMÍÍÍM[Ê


OOžØŽJ
K’Š
KÊ
KÕ

KžJ
KJ
KŒÊ
KU

K”˜Z[›ØYœ\œÙ\‹“[™Ú][T\œÙ\‹OUÊOOžÜÝÚ]Ú
K‰\J^ØØ\ÙX˜Z[›ØY\›Z[˜[^˜œ™]\›žÝ\N˜\›Z[˜[˜[YN™K˜[Y_NØØ\ÙX˜Z[›ØY›Û•\›Z[˜[^˜œ™]\›žÝ\N˜›Û\›Z[˜[˜[YN™K›˜[Y_NØØ\ÙX˜Z[›ØYÜXÚX[^˜œ™]\›žÝ\N˜ÜXÚX[^™K^NØØ\ÙX˜Z[›ØYÙ\]Y[˜ÙQ^˜žÛ]YK™[[Y[Ë›X\
JNÜ™]\›ˆ›[™ÝOOLOÝÌNžÝ\N˜Ù\]Y[˜ÙX[[Y[Î_XØ\ÙX˜Z[›ØYÚÚXÙQ^˜žÛ]YK˜[\›˜]]™\Ë›X\
JNÜ™]\›ˆ›[™ÝOOLOÝÌNžÝ\N˜ÚÚXÙX[\›˜]]™\Î_XØ\ÙX˜Z[›ØYÜ[Û˜[^˜œ™]\›žÝ\N˜Ü[Û˜[[[Y[žJK™[[Y[
_NØØ\ÙX˜Z[›ØYÛ™SÜ“[Ü™Q^˜œ™]\›žÝ\N˜™\]][Û˜[[Y[žJK™[[Y[
KZ[ŽŒKX^ŒKÌNØØ\ÙX˜Z[›ØY™\›ÓÜ“[Ü™Q^˜œ™]\›žÝ\N˜™\]][Û˜[[Y[žJK™[[Y[
KZ[ŽŒX^ŒKÌNÙY˜][›ÝÈ\œ›ÜŠ[œÝ\ÜY˜Z[›ØY^™\ÜÚ[ÛŽˆ	ÙK‰\_X
__K˜[œÙ›Ü›Q^™\ÜÚ[Û˜
KMUÊOOŠÛ˜[YN™K›˜[YKYš[š][ÛŽžJK™Yš[š][ÛŠ_JK˜[œÙ›Ü›T[X
KÍUÊOOžÙŠKŽJKK]I‰™ŽKœÙ]]JK]JKKœ[\Ë›X\
OO™ŽK˜Y[JM
JJJ_KÜ[]Q˜
KÍ^Ü\œÙ\ŽžÜ\œÙN•ÊOOžÙŽK˜ÛX\Š
KË™XYÊÔ˜Z[›ØY\œÙ\—HÝ\[™È[™Ú][H\œÙX
NÛ]Rœ\œÙJJNÚYŠ›^\‘\œ›ÜœË›[™ÝŒœ\œÙ\‘\œ›ÜœË›[™ÝŒ
]›ÝÈ™]ÈŒÊ
NÛ]]˜[YNÑË™XYÊÔ˜Z[›ØY\œÙ\—H\œÙY[\Î˜‹œ[\Ë›[™Ý
KÍ
ŠKË™XYÊÔ˜Z[›ØY\œÙ\—H\œÙHÛÛ\]X
_K\œÙX
K\œÙ\ŽžÞ^N™Ž__KŽ™ŽK™[™\™\ŽžNKÝ[\Î—Î_KÍQÍJJK[
ÙXYÜ˜[NŠ
OO›ŽJKMÎKM	NŽŽ[Ê


OOžØŽJ
K’Š
KÊ
KÕ

KžJ
KJ
KŒÊ
KM\P

K”˜Z[›ØYX›™‹œ\œÙ\‹“[™Ú][T\œÙ\‹ÎOUÊOOžÛ]YK˜[\›˜]]™\Ë›X\

NÜ™]\›ˆ›[™ÝOOLOÝÌNžÝ\N˜ÚÚXÙX[\›˜]]™\Î_K˜[œÙ›Ü›PÚÚXÙX
KUÊOOžÛ]YK™[[Y[Ë›X\
	
NÜ™]\›ˆ›[™ÝOOLOÝÌNžÝ\N˜Ù\]Y[˜ÙX[[Y[Î_K˜[œÙ›Ü›TÙ\]Y[˜ÙX
KUÊOOžÜÝÚ]Ú
K‰\J^ØØ\ÙXX›™•\›Z[˜[œ™]\›žÝ\N˜\›Z[˜[˜[YN™K˜[Y_NØØ\ÙXX›™“›Û•\›Z[˜[œ™]\›žÝ\N˜›Û\›Z[˜[˜[YN™K›˜[Y_NØØ\ÙXX›™”ÜXÚX[œ™]\›žÝ\N˜ÜXÚX[^™K^NØØ\ÙXX›™‘Ü›Ý\œ™]\›ˆÎJK™[[Y[
NØØ\ÙXX›™“Ü[Û˜[œ™]\›žÝ\N˜Ü[Û˜[[[Y[”ÎJK™[[Y[
_NØØ\ÙXX›™”™\]][Û˜œ™]\›žÝ\N˜™\]][Û˜[[Y[”ÎJK™[[Y[
KZ[ŽŒX^ŒKÌNÙY˜][›ÝÈ\œ›ÜŠ[œÝ\ÜYP“‘ˆš[X\žH›ÙNˆ	ÙK‰\_X
__K˜[œÙ›Ü›Tš[X\žX
KMUÊ
K
OOžÜÝÚ]Ú
‰\J^ØØ\ÙXX›™“Ü[Û˜[ÜÝš^œ™]\›žÝ\N˜Ü[Û˜[[[Y[™_NØØ\ÙXX›™–™\›ÓÜ“[Ü™TÜÝš^œ™]\›žÝ\N˜™\]][Û˜[[Y[™KZ[ŽŒX^ŒKÌNØØ\ÙXX›™“Û™SÜ“[Ü™TÜÝš^œ™]\›žÝ\N˜™\]][Û˜[[Y[™KZ[ŽŒKX^ŒKÌNØØ\ÙXX›™‘^Ù\[Û”ÜÝš^œ™]\›žÝ\N˜Ù\]Y[˜ÙX[[Y[Î–ÙKÝ\N˜\›Z[˜[˜[YN˜XK
™^Ù\
W_NÙY˜][›ÝÈ\œ›ÜŠ[œÝ\ÜYP“‘ˆÜÝš^›ÙNˆ	Ý‰\_X
__K˜[œÙ›Ü›TÜÝš^
K	UÊOO™KœÜÝš^\Ëœ™YXÙJ
K
OO”M
K
K
K˜˜\ÙJJK˜[œÙ›Ü›U\›X
KNUÊOOŠÛ˜[YN™K›˜[YKYš[š][ÛŽ”ÎJK™Yš[š][ÛŠ_JK˜[œÙ›Ü›T[X
KUÊOOžÙŠKŽJKK]I‰™ŽKœÙ]]JK]JKKœ[\Ë›X\
OO™ŽK˜Y[JN
JJJ_KÜ[]Q˜
KŽ^Ü\œÙ\ŽžÜ\œÙN•ÊOOžÙŽK˜ÛX\Š
KË™XYÊÑP“‘ˆ\œÙ\—HÝ\[™È[™Ú][H\œÙX
NÛ]VMœ\œÙJJNÚYŠ›^\‘\œ›ÜœË›[™ÝŒœ\œÙ\‘\œ›ÜœË›[™ÝŒ
]›ÝÈ™]ÈŒÊ
NÛ]]˜[YNÑË™XYÊÑP“‘ˆ\œÙ\—H\œÙY[\Î˜‹œ[\Ë›[™Ý
K
ŠKË™XYÊÑP“‘ˆ\œÙ\—H\œÙHÛÛ\]X
_K\œÙX
K\œÙ\ŽžÞ^N™Ž__KŽ™ŽK™[™\™\ŽžNKÝ[\Î—Î__JJKN[
ÙXYÜ˜[NŠ
OO™ŽJKNÎKÎÎÎNŽ[Ê


OOžØŽJ
K’Š
KÊ
KÕ

KžJ
KJ
KŒÊ
KNI

K”˜Z[›ØYX›™‹œ\œÙ\‹“[™Ú][T\œÙ\‹ÎOUÊOOžÛ]YK˜[\›˜]]™\Ë›X\
Î
NÜ™]\›ˆ›[™ÝOOLOÝÌNžÝ\N˜ÚÚXÙX[\›˜]]™\Î_K˜[œÙ›Ü›P[\›˜][Û˜
KÎUÊOOžÛ]YK™[[Y[Ë›X\
Î
NÜ™]\›ˆ›[™ÝOOLOÝÌNžÝ\N˜Ù\]Y[˜ÙX[[Y[Î_K˜[œÙ›Ü›PÛÛ˜Ø][˜][Û˜
KÎUÊOOžÚYŠKš[˜ÛY\Ê
˜
J^Û]Ý—OYKœÜ]

˜
NÜ™]\›žÛZ[ŽÜ\œÙR[
L
NŒX^›Ü\œÙR[
‹L
NŒKÌ_[]\\œÙR[
KL
NÜ™]\›žÛZ[ŽX^_K\œÙT™\X]
KÎUÊOOžÛ][
Kœš[X\žJNÚYŠYKœ™\X]
\™]\›ˆÛ]ÛZ[Ž›‹X^œŸO\Î
Kœ™\X]
NÜ™]\›ˆOOL	‰œOOLOÞÝ\N˜Ü[Û˜[[[Y[NžÝ\N˜™\]][Û˜[[Y[Z[Ž›‹X^œŸ_K˜[œÙ›Ü›Q[[Y[
KUÊOOžÜÝÚ]Ú
K‰\J^ØØ\ÙXX›™”Ýš[™Ó]\˜[œ™]\›žÝ\N˜\›Z[˜[˜[YN™K˜[Y_NØØ\ÙXX›™“[U˜[œ™]\›žÝ\N˜\›Z[˜[˜[YN™K˜[Y_NØØ\ÙXX›™”[S˜[YXœ™]\›žÝ\N˜›Û\›Z[˜[˜[YN™K›˜[Y_NØØ\ÙXX›™‘Ü›Ý\œ™]\›ˆÎJK™[[Y[
NØØ\ÙXX›™“Ü[Û˜[Ü›Ý\œ™]\›žÝ\N˜Ü[Û˜[[[Y[ÎJK™[[Y[
_NÙY˜][›ÝÈ\œ›ÜŠ[œÝ\ÜYP“‘ˆš[X\žH›ÙNˆ	ÙK‰\_X
__K˜[œÙ›Ü›Tš[X\žX
KNUÊOOŠÛ˜[YN™K›˜[YKYš[š][ÛŽÎJK™Yš[š][ÛŠ_JK˜[œÙ›Ü›T[X
KUÊOOžÙŠKŽJKK]I‰™ŽKœÙ]]JK]JKKœ[\Ë›X\
OO™ŽK˜Y[JN
JJJ_KÜ[]Q˜
KŽ^Ü\œÙ\ŽžÜ\œÙN•ÊOOžÙŽK˜ÛX\Š
KË™XYÊÐP“‘ˆ\œÙ\—HÝ\[™È[™Ú][H\œÙX
NÛ]XNœ\œÙJJNÚYŠ›^\‘\œ›ÜœË›[™ÝŒœ\œÙ\‘\œ›ÜœË›[™ÝŒ
]›ÝÈ™]ÈŒÊ
NÛ]]˜[YNÑË™XYÊÐP“‘ˆ\œÙ\—H\œÙY[\Î˜‹œ[\Ë›[™Ý
K
ŠKË™XYÊÐP“‘ˆ\œÙ\—H\œÙHÛÛ\]X
_K\œÙX
K\œÙ\ŽžÞ^N™Ž__KŽ™ŽK™[™\™\ŽžNKÝ[\Î—Î__JJKN[
ÙXYÜ˜[NŠ
OOÎJKÎÎŽNŽÎÎÎ[Ê


OOžØŽJ
K’Š
KÊ
KÕ

KžJ
KJ
KŒÊ
KZU

K”˜Z[›ØYYËœ\œÙ\‹“[™Ú][T\œÙ\‹ÎUÊOOžÛ]YK˜[\›˜]]™\Ë›X\
Î
NÜ™]\›ˆ›[™ÝOOLOÝÌNžÝ\N˜ÚÚXÙX[\›˜]]™\Î_K˜[œÙ›Ü›SÜ™\™YÚÚXÙX
KÎUÊOOžÛ]YK™[[Y[Ë›X\
Ž
NÜ™]\›ˆ›[™ÝOOLOÝÌNžÝ\N˜Ù\]Y[˜ÙX[[Y[Î_K˜[œÙ›Ü›TÙ\]Y[˜ÙX
KŽUÊOOžÛ]XŽ
KœÝY™š^
NÜ™]\›ˆK›Ü\˜]ÜÞÝ\N˜ÜXÚX[^™K›Ü\˜]ÜOOX	˜Ø	‰ÞN

_X˜IÞN

_XNK˜[œÙ›Ü›T™Yš^
KNUÊOOžÜÝÚ]Ú
K\J^ØØ\ÙX\›Z[˜[œ™]\›˜‰ÙK˜[Y_H˜ØØ\ÙX›Û\›Z[˜[œ™]\›ˆK›˜[YNØØ\ÙXÜXÚX[œ™]\›ˆK^ÙY˜][œ™]\›˜
‹‹ŠX_K›ÙUÓX™[
KŽUÊOOžÛ]^
Kœš[X\žJNÚYŠYK›Ü\˜]ÜŠ\™]\›ˆÜÝÚ]Ú
K›Ü\˜]ÜŠ^ØØ\ÙXØœ™]\›žÝ\N˜Ü[Û˜[[[Y[NØØ\ÙX
˜œ™]\›žÝ\N˜™\]][Û˜[[Y[Z[ŽŒX^ŒKÌNØØ\ÙX
Øœ™]\›žÝ\N˜™\]][Û˜[[Y[Z[ŽŒKX^ŒKÌNÙY˜][›ÝÈ\œ›ÜŠ[œÝ\ÜYQÈÝY™š^Ü\˜]ÜŽˆ	ÙK›Ü\˜]ÜŸX
__K˜[œÙ›Ü›TÝY™š^
KUÊOOžÜÝÚ]Ú
K‰\J^ØØ\ÙXYÓ]\˜[œ™]\›žÝ\N˜\›Z[˜[˜[YN™K˜[Y_NØØ\ÙXYÒY[YšY\˜œ™]\›žÝ\N˜›Û\›Z[˜[˜[YN™K›˜[Y_NØØ\ÙXYÑÜ›Ý\œ™]\›ˆÎ
K™[[Y[
NØØ\ÙXYÐ[žXœ™]\›žÝ\N˜ÜXÚX[^™K™ÝNÙY˜][›ÝÈ\œ›ÜŠ[œÝ\ÜYQÈš[X\žH›ÙNˆ	ÙK‰\_X
__K˜[œÙ›Ü›Tš[X\žX
KÎUÊOOŠÛ˜[YN™K›˜[YKYš[š][ÛŽ™Î
K™Yš[š][ÛŠ_JK˜[œÙ›Ü›T[X
KÎUÊOOžÙŠKŽJKK]I‰™ŽKœÙ]]JK]JKKœ[\Ë›X\
OO™ŽK˜Y[JÎ
JJJ_KÜ[]Q˜
KÎ^Ü\œÙ\ŽžÜ\œÙN•ÊOOžÙŽK˜ÛX\Š
KË™XYÊÔQÈ\œÙ\—HÝ\[™È[™Ú][H\œÙX
NÛ]Zœ\œÙJJNÚYŠ›^\‘\œ›ÜœË›[™ÝŒœ\œÙ\‘\œ›ÜœË›[™ÝŒ
]›ÝÈ™]ÈŒÊ
NÛ]]˜[YNÑË™XYÊÔQÈ\œÙ\—H\œÙY[\Î˜‹œ[\Ë›[™Ý
KÎ
ŠKË™XYÊÔQÈ\œÙ\—H\œÙHÛÛ\]X
_K\œÙX
K\œÙ\ŽžÞ^N™Ž__KŽ™ŽK™[™\™\ŽžNKÝ[\Î—Î__JJNÒÊ
KšÊ
K\J
KÓJ
KZŠ
KZÊ
KZŠ
KJ
KJ
KJ
KÐJ
KÕ

KžJ
KJ
KÙJ
K“Ê
KŠ
KUÙJ
NÝ˜\ˆNXÍ^ÚY‘N]XÝÜŽ•ÊOO‹×—ÊÍÛÛ^ÍÛÛZ[™\ŸÍÛÛ\Û™[Í[˜[ZXßÍ\Þ[Y[Ë\Ý
JK]XÝÜ˜
KØY\Ž•Ê\Þ[˜Ê
OOžÛ]ÙXYÜ˜[N™_OX]ØZ]›ÛZ\ÙKœ™\ÛÛ™J
K[Š

OOŠY

K]]
JNÜ™]\›žÚY‘NXYÜ˜[N™__KØY\˜
_KÎX›ÝØÚ\Î^ÚY“Î]XÝÜŽ•Ê
K
OOË™›ÝØÚ\Ë™Y˜][™[™\™\OOXYÜ™K]Ü˜\\˜Ë™›ÝØÚ\Ë™Y˜][™[™\™\OOX[ØÈLN‹×—Ê™Ü˜\Ë\Ý
JK]XÝÜ˜
KØY\Ž•Ê\Þ[˜Ê
OOžÛ]ÙXYÜ˜[N™_OX]ØZ]›ÛZ\ÙKœ™\ÛÛ™J
K[Š

OOŠÙ

KY
JNÜ™]\›žÚY“ÎXYÜ˜[N™__KØY\˜
_KNX›ÝØÚ\]Œ˜Ž^ÚYN]XÝÜŽ•Ê
K
OOË™›ÝØÚ\Ë™Y˜][™[™\™\OOXYÜ™KYØÈLNŠË™›ÝØÚ\Ë™Y˜][™[™\™\OOX[Ø	‰Š›^[Ý]X[Ø
K×—Ê™Ü˜\Ë\Ý
JI‰Ë™›ÝØÚ\Ë™Y˜][™[™\™\OOXYÜ™K]Ü˜\\˜ÈL‹×—Ê™›ÝØÚ\Ë\Ý
JJK]XÝÜ˜
KØY\Ž•Ê\Þ[˜Ê
OOžÛ]ÙXYÜ˜[N™_OX]ØZ]›ÛZ\ÙKœ™\ÛÛ™J
K[Š

OOŠÙ

KY
JNÜ™]\›žÚYNXYÜ˜[N™__KØY\˜
_KNXÝÚ[[[™XŽ^ÚY“N]XÝÜŽ•ÊOO‹×—ÊœÝÚ[[[™KX™]W‹Ë\Ý
JK]XÝÜ˜
KØY\Ž•Ê\Þ[˜Ê
OOžÛ]ÙXYÜ˜[N™_OX]ØZ]›ÛZ\ÙKœ™\ÛÛ™J
K[Š

OOŠY

KÙ
JNÜ™]\›žÚY“NXYÜ˜[N™__KØY\˜
_KX\˜Ž^ÚY”]XÝÜŽ•ÊOO‹×—Ê™\‘XYÜ˜[KË\Ý
JK]XÝÜ˜
KØY\Ž•Ê\Þ[˜Ê
OOžÛ]ÙXYÜ˜[N™_OX]ØZ]›ÛZ\ÙKœ™\ÛÛ™J
K[Š

OOŠ™

K™
JNÜ™]\›žÚY”XYÜ˜[N™__KØY\˜
_KNXÚ]Ü˜\^ÚY’N]XÝÜŽ•ÊOO‹×—Ê™Ú]Ü˜\Ë\Ý
JK]XÝÜ˜
KØY\Ž•Ê\Þ[˜Ê
OOžÛ]ÙXYÜ˜[N™_OX]ØZ]›ÛZ\ÙKœ™\ÛÛ™J
K[Š

OOŠU]

K’
JNÜ™]\›žÚY’NXYÜ˜[N™__KØY\˜
_KŽXØ[Ž^ÚY”Ž]XÝÜŽ•ÊOO‹×—Ê™Ø[Ë\Ý
JK]XÝÜ˜
KØY\Ž•Ê\Þ[˜Ê
OOžÛ]ÙXYÜ˜[N™_OX]ØZ]›ÛZ\ÙKœ™\ÛÛ™J
K[Š

OOŠ‘Ý

KU]
JNÜ™]\›žÚY”ŽXYÜ˜[N™__KØY\˜
_KŽX[™›ØŽ^ÚYŽ]XÝÜŽ•ÊOO‹×—Êš[™›ËË\Ý
JK]XÝÜ˜
KØY\Ž•Ê\Þ[˜Ê
OOžÛ]ÙXYÜ˜[N™_OX]ØZ]›ÛZ\ÙKœ™\ÛÛ™J
K[Š

OOŠÑÝ

KQÝ
JNÜ™]\›žÚYŽXYÜ˜[N™__KØY\˜
_KXYXN^ÚY’]XÝÜŽ•ÊOO‹×—ÊœYKË\Ý
JK]XÝÜ˜
KØY\Ž•Ê\Þ[˜Ê
OOžÛ]ÙXYÜ˜[N™_OX]ØZ]›ÛZ\ÙKœ™\ÛÛ™J
K[Š

OOŠ‘Ý

KÝ
JNÜ™]\›žÚY’XYÜ˜[N™__KØY\˜
_KÎX]XY˜[Ú\Î^ÚY•Î]XÝÜŽ•ÊOO‹×—Êœ]XY˜[Ú\Ë\Ý
JK]XÝÜ˜
KØY\Ž•Ê\Þ[˜Ê
OOžÛ]ÙXYÜ˜[N™_OX]ØZ]›ÛZ\ÙKœ™\ÛÛ™J
K[Š

OOŠ‘Ý

KQÝ
JNÜ™]\›žÚY•ÎXYÜ˜[N™__KØY\˜
_KÎXXÚ\N^ÚY’Î]XÝÜŽ•ÊOO‹×—ÊžXÚ\
X™]JOËË\Ý
JK]XÝÜ˜
KØY\Ž•Ê\Þ[˜Ê
OOžÛ]ÙXYÜ˜[N™_OX]ØZ]›ÛZ\ÙKœ™\ÛÛ™J
K[Š

OOŠRÝ

K‘Ý
JNÜ™]\›žÚY’ÎXYÜ˜[N™__KØY\˜
_KŽX™\]Z\™[Y[N^ÚY’Ž]XÝÜŽ•ÊOO‹×—Êœ™\]Z\™[Y[
XYÜ˜[JOËË\Ý
JK]XÝÜ˜
KØY\Ž•Ê\Þ[˜Ê
OOžÛ]ÙXYÜ˜[N™_OX]ØZ]›ÛZ\ÙKœ™\ÛÛ™J
K[Š

OOŠ’Ý

KÝ
JNÜ™]\›žÚY’ŽXYÜ˜[N™__KØY\˜
_KXÙ\]Y[˜ÙXŽ^ÚY–]XÝÜŽ•ÊOO‹×—ÊœÙ\]Y[˜ÙQXYÜ˜[KË\Ý
JK]XÝÜ˜
KØY\Ž•Ê\Þ[˜Ê
OOžÛ]ÙXYÜ˜[N™_OX]ØZ]›ÛZ\ÙKœ™\ÛÛ™J
K[Š

OOŠœ]

KRÝ
JNÜ™]\›žÚY–XYÜ˜[N™__KØY\˜
_KNXÛ\ÜØ	^ÚY”N]XÝÜŽ•Ê
K
OOË˜Û\ÜÏË™Y˜][™[™\™\ˆOOXYÜ™K]Ü˜\\˜	‰‹×—Ê˜Û\ÜÑXYÜ˜[KË\Ý
JK]XÝÜ˜
KØY\Ž•Ê\Þ[˜Ê
OOžÛ]ÙXYÜ˜[N™_OX]ØZ]›ÛZ\ÙKœ™\ÛÛ™J
K[Š

OOŠœ]

K\]
JNÜ™]\›žÚY”NXYÜ˜[N™__KØY\˜
_KM]XÛ\ÜÑXYÜ˜[X]^ÚY™M]]XÝÜŽ•Ê
K
OO‹×—Ê˜Û\ÜÑXYÜ˜[KË\Ý
JI‰Ë˜Û\ÜÏË™Y˜][™[™\™\OOXYÜ™K]Ü˜\\˜ÈL‹×—Ê˜Û\ÜÑXYÜ˜[K]Œ‹Ë\Ý
JK]XÝÜ˜
KØY\Ž•Ê\Þ[˜Ê
OOžÛ]ÙXYÜ˜[N™_OX]ØZ]›ÛZ\ÙKœ™\ÛÛ™J
K[Š

OOŠR

K\]
JNÜ™]\›žÚY™M]XYÜ˜[N™__KØY\˜
_K]XÝ]X]^ÚY›]]XÝÜŽ•Ê
K
OOËœÝ]OË™Y˜][™[™\™\ˆOOXYÜ™K]Ü˜\\˜	‰‹×—ÊœÝ]QXYÜ˜[KË\Ý
JK]XÝÜ˜
KØY\Ž•Ê\Þ[˜Ê
OOžÛ]ÙXYÜ˜[N™_OX]ØZ]›ÛZ\ÙKœ™\ÛÛ™J
K[Š

OOŠÖ]

KR
JNÜ™]\›žÚY›]XYÜ˜[N™__KØY\˜
_KM]XÝ]QXYÜ˜[XM]^ÚYšM]]XÝÜŽ•Ê
K
OOˆHJ×—ÊœÝ]QXYÜ˜[K]Œ‹Ë\Ý
J_×—ÊœÝ]QXYÜ˜[KË\Ý
JI‰ËœÝ]OË™Y˜][™[™\™\OOXYÜ™K]Ü˜\\˜
K]XÝÜ˜
KØY\Ž•Ê\Þ[˜Ê
OOžÛ]ÙXYÜ˜[N™_OX]ØZ]›ÛZ\ÙKœ™\ÛÛ™J
K[Š

OOŠ]

K]
JNÜ™]\›žÚYšM]XYÜ˜[N™__KØY\˜
_KÍ]X›Ý\›™^XÍ]^ÚY›Í]]XÝÜŽ•ÊOO‹×—Êš›Ý\›™^KË\Ý
JK]XÝÜ˜
KØY\Ž•Ê\Þ[˜Ê
OOžÛ]ÙXYÜ˜[N™_OX]ØZ]›ÛZ\ÙKœ™\ÛÛ™J
K[Š

OOŠ–]

K–]
JNÜ™]\›žÚY›Í]XYÜ˜[N™__KØY\˜
_KÍ]^Ù˜]Î•Ê
KŠOOžÑË™XYÊ™[™\š[™ÈÝ™È›ÜˆÞ[^\œ›Ü‚˜
NÛ]U“Ê
KO\‹˜\[™
Ø
NÜ‹˜]ŠšY]Ð›ÞLˆLL˜
KÊ‹LLL‹L
KK˜\[™
]
K˜]ŠÛ\ÜØ\œ›Ü‹ZXÛÛ˜
K˜]ŠMLKŒÌLËLŒËŒÌLØÍ‹ŒKM‹ŒH‹ŒKLM‹ŒÍÍHLŒ‹Œ\ËLM‹ŒÍÍKM‹ŒKLŒ‹ŒKLÌ‹Ì‹NKŒÍÍKKŒÍÍKLŒŽLŒŽËLL‹LL‹KLÌ‹Í‹LL‹KMKŒKLM‹M˜ËLKŒŒKKŒŒKL‹ŒÌ‹LËŒÌKŒLKLŒKÌÎKNMŒKMKŒÌLLË‹MÌŒKLLË‹LLKŽËLNL‹‹ŒLÌËLNL‹NLœÎ‹ŒLÌËNLˆNL‹NLˆNL‹N‹ŒLÌÈNL‹LNL˜ÌLÍKMŽMŒÌËLLË‹MÌŒHK‹LKŒÈ‹ÎKL‹ŒHŒLKLËŒÌ[M‹LM˜ÌL‹KLL‹LˆL‹KLÌ‹ÍNMKŒ[LŒŽLŒŽKŒÍÍKNKŒÍÍHÌ‹ŒKLÌKŽNN^›KLŒNKŒÌLËLŽØËML‹ŽLÎNM‹ËŒŒËNM‹MˆŽÍ‹MËŒMM‹LM‹MœËLM‹MËŒMLM‹LM˜ÌMÌMÎMËŒ‹LLŽLŽLLŽŽÍ‹M‹ËŒMM‹MœËMËŒMM‹LM‹Mž˜
KK˜\[™
]
K˜]ŠÛ\ÜØ\œ›Ü‹ZXÛÛ˜
K˜]ŠMNKŒ‹MŽNËM‹ŒKM‹ŒKLM‹ŒÍÍKM‹ŒKLŒ‹ŒKËM‹ŒKM‹ŒÍÍHŒ‹Œ[M‹M˜ÌËŒLKËŒLHËŒŒNKŽLKŒÌLËŽŒMŒNLKMŒÈLKŒÌLËMŽ‹ŒKM‹ŒH‹ŒKLM‹ŒÍÍHLŒ‹Œ[LM‹ŒKLMž˜
KK˜\[™
]
K˜]ŠÛ\ÜØ\œ›Ü‹ZXÛÛ˜
K˜]ŠLÍŒÎMKÍKŒXÌËŒLKËŒLHËŒŒNKŽLKŒÌLËŽŒMŒNLKMŒÈLKŒÌLËMŽ‹ŒKM‹ŒH‹ŒKLM‹ŒÍÍHLŒ‹Œ[LM‹LM˜ËM‹ŒKM‹ŒKLM‹ŒÍÍKM‹ŒKLŒ‹ŒKËM‹ŒKM‹ŒÍÍHŒ‹Œ[MKŽNNKMž˜
KK˜\[™
]
K˜]ŠÛ\ÜØ\œ›Ü‹ZXÛÛ˜
K˜]ŠMÎŽM‹MËŒMM‹LM‹LÌ˜ÌNŽÍ‹MËŒMM‹LM‹LM‹LM‹NŽLM‹ËŒMLM‹MŒÌ˜ÌŽÍˆËŒMM‹MˆM‹Mž˜
KK˜\[™
]
K˜]ŠÛ\ÜØ\œ›Ü‹ZXÛÛ˜
K˜]ŠMM‹M‹NšLÌ˜ËNŽLM‹ËŒMLM‹MˆŽÍˆËŒMM‹MˆM‹MšÌ˜ÎŽM‹MËŒMM‹LMˆNŽÍ‹MËŒMM‹LM‹LM‹LMž˜
KK˜\[™
]
K˜]ŠÛ\ÜØ\œ›Ü‹ZXÛÛ˜
K˜]ŠMÍ‹ŽNÍKŒXÌËŒLKËŒLHËŒŒNKŽLKŒÌLËŽŒMŒNLKMŒÈLKŒÌLËMŽÌ‹LÌ˜Í‹ŒKM‹ŒH‹ŒKLM‹ŒÍÍHLŒ‹Œ\ËLM‹ŒÍÍKM‹ŒKLŒ‹ŒKLÌ‹Ì˜ËM‹ŒLK‹ŒKM‹ŒLKM‹ŒÍÍKLŒKŒ‹Œ^˜
KK˜\[™
^
K˜]ŠÛ\ÜØ\œ›Ü‹]^
K˜]ŠM
K˜]ŠXL
K˜]Š›Û\Ú^™XML
KœÝ[J^X[˜ÚÜ˜ZYX
K^
Þ[^\œ›Üˆ[ˆ^
KK˜\[™
^
K˜]ŠÛ\ÜØ\œ›Ü‹]^
K˜]ŠLL
K˜]ŠX
K˜]Š›Û\Ú^™XL
KœÝ[J^X[˜ÚÜ˜ZYX
K^
Y\›XZY™\œÚ[Ûˆ	ÛŸX
_K˜]Ø
_K]XÍ]M]^ÙŽžßK™[™\™\Ž˜Í]\œÙ\ŽžÜ\œÙN•Ê

OOžßK\œÙX
__K]X›ÝØÚ\Y[Ø]^ÚY™]]XÝÜŽ•Ê
K^ßJOO‹×—Ê™›ÝØÚ\Y[ËË\Ý
J_×—ÊŠ›ÝØÚ\Ü˜\
KË\Ý
JI‰Ë™›ÝØÚ\Ë™Y˜][™[™\™\OOX[ØÊ›^[Ý]X[ØL
NˆLK]XÝÜ˜
KØY\Ž•Ê\Þ[˜Ê
OOžÛ]ÙXYÜ˜[N™_OX]ØZ]›ÛZ\ÙKœ™\ÛÛ™J
K[Š

OOŠÙ

KY
JNÜ™]\›žÚY™]XYÜ˜[N™__KØY\˜
_K]X[Y[[™XM]^ÚYœ]]XÝÜŽ•ÊOO‹×—Ê[Y[[™KË\Ý
JK]XÝÜ˜
KØY\Ž•Ê\Þ[˜Ê
OOžÛ]ÙXYÜ˜[N™_OX]ØZ]›ÛZ\ÙKœ™\ÛÛ™J
K[Š

OOŠV

K–]
JNÜ™]\›žÚYœ]XYÜ˜[N™__KØY\˜
_K]XZ[™X\Í]^ÚYš]]XÝÜŽ•ÊOO‹×—Ê›Z[™X\Ë\Ý
JK]XÝÜ˜
KØY\Ž•Ê\Þ[˜Ê
OOžÛ]ÙXYÜ˜[N™_OX]ØZ]›ÛZ\ÙKœ™\ÛÛ™J
K[Š

OOŠV

KÖ
JNÜ™]\›žÚYš]XYÜ˜[N™__KØY\˜
_KÍ]XØ[˜˜[˜]^ÚY—Í]]XÝÜŽ•ÊOO‹×—ÊšØ[˜˜[‹Ë\Ý
JK]XÝÜ˜
KØY\Ž•Ê\Þ[˜Ê
OOžÛ]ÙXYÜ˜[N™_OX]ØZ]›ÛZ\ÙKœ™\ÛÛ™J
K[Š

OOŠ–

K
JNÜ™]\›žÚY—Í]XYÜ˜[N™__KØY\˜
_KM]XØ[šÙ^X]^ÚYžM]]XÝÜŽ•ÊOO‹×—ÊœØ[šÙ^JX™]JOËË\Ý
JK]XÝÜ˜
KØY\Ž•Ê\Þ[˜Ê
OOžÛ]ÙXYÜ˜[N™_OX]ØZ]›ÛZ\ÙKœ™\ÛÛ™J
K[Š

OOŠ]

KÔ]
JNÜ™]\›žÚYžM]XYÜ˜[N™__KØY\˜
_K]XXÚÙ]Í]^ÚYž]]XÝÜŽ•ÊOO‹×—ÊœXÚÙ]
X™]JOËË\Ý
JK]XÝÜ˜
KØY\Ž•Ê\Þ[˜Ê
OOžÛ]ÙXYÜ˜[N™_OX]ØZ]›ÛZ\ÙKœ™\ÛÛ™J
K[Š

OOŠ]

KÔ]
JNÜ™]\›žÚYž]XYÜ˜[N™__KØY\˜
_KÍ]X˜Y\˜Í]^ÚYÍ]]XÝÜŽ•ÊOO‹×—Êœ˜Y\‹X™]KË\Ý
JK]XÝÜ˜
KØY\Ž•Ê\Þ[˜Ê
OOžÛ]ÙXYÜ˜[N™_OX]ØZ]›ÛZ\ÙKœ™\ÛÛ™J
K[Š

OOŠI

K”]
JNÜ™]\›žÚYÍ]XYÜ˜[N™__KØY\˜
_K]X›ØÚØM]^ÚY•]]XÝÜŽ•ÊOO‹×—Ê˜›ØÚÊX™]JOËË\Ý
JK]XÝÜ˜
KØY\Ž•Ê\Þ[˜Ê
OOžÛ]ÙXYÜ˜[N™_OX]ØZ]›ÛZ\ÙKœ™\ÛÛ™J
K[Š

OOŠL]

KÉ
JNÜ™]\›žÚY•]XYÜ˜[N™__KØY\˜
_K]X™YUšY]ØÍ]^ÚY‘]]XÝÜŽ•ÊOO‹×—Ê™YUšY]ËX™]KË\Ý
JK]XÝÜ˜
KØY\Ž•Ê\Þ[˜Ê
OOžÛ]ÙXYÜ˜[N™_OX]ØZ]›ÛZ\ÙKœ™\ÛÛ™J
K[Š

OOŠL

K]
JNÜ™]\›žÚY‘]XYÜ˜[N™__KØY\˜
_KÍ]X\˜Ú]XÝ\™XM]^ÚYšÍ]]XÝÜŽ•ÊOO‹×—Ê˜\˜Ú]XÝ\™KË\Ý
JK]XÝÜ˜
KØY\Ž•Ê\Þ[˜Ê
OOžÛ]ÙXYÜ˜[N™_OX]ØZ]›ÛZ\ÙKœ™\ÛÛ™J
K[Š

OOŠŒ

KŒ
JNÜ™]\›žÚYšÍ]XYÜ˜[N™__KØY\˜
_K]X]™[[Ù[[™ØM]^ÚYš]]XÝÜŽ•ÊOO‹×—Ê™]™[[Ù[[™ËË\Ý
JK]XÝÜ˜
KØY\Ž•Ê\Þ[˜Ê
OOžÛ]ÙXYÜ˜[N™_OX]ØZ]›ÛZ\ÙKœ™\ÛÛ™J
K[Š

OOŠŒ

KL
JNÜ™]\›žÚYš]XYÜ˜[N™__KØY\˜
_K]X\ÚZØ]ØX]^ÚY“]]XÝÜŽ•ÊOO‹×—Êš\ÚZØ]ØJX™]JO×‹ÚK\Ý
JK]XÝÜ˜
KØY\Ž•Ê\Þ[˜Ê
OOžÛ]ÙXYÜ˜[N™_OX]ØZ]›ÛZ\ÙKœ™\ÛÛ™J
K[Š

OOŠÍ

KŒ
JNÜ™]\›žÚY“]XYÜ˜[N™__KØY\˜
_K]X™[›˜M]^ÚY‘]]XÝÜŽ•ÊOO‹×—Ê™[›‹X™]KË\Ý
JK]XÝÜ˜
KØY\Ž•Ê\Þ[˜Ê
OOžÛ]ÙXYÜ˜[N™_OX]ØZ]›ÛZ\ÙKœ™\ÛÛ™J
K[Š

OOŠÌÝ

KLÝ
JNÜ™]\›žÚY‘]XYÜ˜[N™__KØY\˜
_K]X™Y[X\]^ÚY“]]XÝÜŽ•ÊOO‹×—Ê™Y[X\Ë\Ý
JK]XÝÜ˜
KØY\Ž•Ê\Þ[˜Ê
OOžÛ]ÙXYÜ˜[N™_OX]ØZ]›ÛZ\ÙKœ™\ÛÛ™J
K[Š

OOŠÝ

KÌÝ
JNÜ™]\›žÚY“]XYÜ˜[N™__KØY\˜
_K]XØ\™^X]^ÚYž]]XÝÜŽ•ÊOO‹×—ÊØ\™^KX™]KÚK\Ý
JK]XÝÜ˜
KØY\Ž•Ê\Þ[˜Ê
OOžÛ]ÙXYÜ˜[N™_OX]ØZ]›ÛZ\ÙKœ™\ÛÛ™J
K[Š

OOŠ

KŒÝ
JNÜ™]\›žÚYž]XYÜ˜[N™__KØY\˜
_K]XÞ[™Yš[˜]^ÚY•]]XÝÜŽ•ÊOO‹×—Ê˜Þ[™Yš[‹X™]JÎ–×Î—_	
KË\Ý
JK]XÝÜ˜
KØY\Ž•Ê\Þ[˜Ê
OOžÛ]ÙXYÜ˜[N™_OX]ØZ]›ÛZ\ÙKœ™\ÛÛ™J
K[Š

OOŠM

KM
JNÜ™]\›žÚY•]XYÜ˜[N™__KØY\˜
_KM]X˜Z[›ØYÍ]^ÚY•M]]XÝÜŽ•ÊOO‹×—Êœ˜Z[›ØYX™]KÚK\Ý
JK]XÝÜ˜
KØY\Ž•Ê\Þ[˜Ê
OOžÛ]ÙXYÜ˜[N™_OX]ØZ]›ÛZ\ÙKœ™\ÛÛ™J
K[Š

OOŠM

K
JNÜ™]\›žÚY•M]XYÜ˜[N™__KØY\˜
_KÍ]X˜Z[›ØYX›™˜Í]^ÚY‘Í]]XÝÜŽ•ÊOO‹×—Êœ˜Z[›ØYYX›™‹X™]KÚK\Ý
JK]XÝÜ˜
KØY\Ž•Ê\Þ[˜Ê
OOžÛ]ÙXYÜ˜[N™_OX]ØZ]›ÛZ\ÙKœ™\ÛÛ™J
K[Š

OOŠŽ

K
JNÜ™]\›žÚY‘Í]XYÜ˜[N™__KØY\˜
_KM]X˜Z[›ØYX›™˜]^ÚYœM]]XÝÜŽ•ÊOO‹×—Êœ˜Z[›ØYXX›™‹X™]KÚK\Ý
JK]XÝÜ˜
KØY\Ž•Ê\Þ[˜Ê
OOžÛ]ÙXYÜ˜[N™_OX]ØZ]›ÛZ\ÙKœ™\ÛÛ™J
K[Š

OOŠ

KN
JNÜ™]\›žÚYœM]XYÜ˜[N™__KØY\˜
_KM]X˜Z[›ØYYØ]^ÚY–M]]XÝÜŽ•ÊOO‹×—Êœ˜Z[›ØY\YËX™]KÚK\Ý
JK]XÝÜ˜
KØY\Ž•Ê\Þ[˜Ê
OOžÛ]ÙXYÜ˜[N™_OX]ØZ]›ÛZ\ÙKœ™\ÛÛ™J
K[Š

OOŠ

KN
JNÜ™]\›žÚY–M]XYÜ˜[N™__KØY\˜
_K]HLKÎOUÊ

OOžÖ]
]HLÕ
\œ›Ü˜M]OO™KÓÝÙ\Ø\ÙJ
Kš[J
OOOX\œ›Ü˜
KÕ
KKXÙŽžØÛX\Ž•Ê

OOžßKÛX\˜
_KÝ[\ÎžßK™[™\™\ŽžÙ˜]Î•Ê

OOžßK˜]Ø
_K\œÙ\ŽžÜ\œÙN•Ê

OOžÝ›ÝÈ\œ›ÜŠ‘XYÜ˜[\È™YÚ[›š[™ÈÚ]KKH\™H›Ý˜[YˆYˆ[ÝHÙ\™HžZ[™ÈÈ\ÙHHPSSœ›Û[X]\‹X\ÙH[œÝ\™H][ÝIÝ™HÛÜœ™XÝHÜ[™Y[™ÛÜÙYHPSSœ›Û[X]\ˆÚ][‹Z[™[YKKX›ØÚÜÈŠ_K\œÙX
_K[š]•Ê

OO›[[š]
_KOO™KÓÝÙ\Ø\ÙJ
Kš[TÝ\

KœÝ\ÕÚ]
KKX
JKÝÊ]Í]M]
KÝÊ]]	ŽŽŽNNŽŽŽÎM]M]]Í]Î]Í]NM]M]Í]Í]]]Í]Í]]]M]]]
J_KYXYÜ˜[\Ø
KM]UÊ\Þ[˜Ê
OOžÑË™XYÊØY[™È™YÚ\Ý\™YXYÜ˜[\Ø
NÛ]OJ]ØZ]›ÛZ\ÙK˜[Ù]Y
Øš™XÝ™[šY\ÊÊK›X\
\Þ[˜ÊÙKÙ]XÝÜŽØY\Ž›ŸWJOOžÚYŠŠ]ž^ÜÕ
J_XØ]ÚÝž^Û]ÙXYÜ˜[N™KYœŸOX]ØZ]Š
NÛÕ
‹K
_XØ]Ú

^Ý›ÝÈË™\œ›ÜŠ˜Z[YÈØY^\›˜[XYÜ˜[HÚ]Ù^H	Ù_Kˆ™[[Ýš[™Èœ›ÛH]XÝÜœË˜
K[]HÖÙWK__JJJK™š[\ŠOO™KœÝ]\ÏOOX™Z™XÝY
NÚYŠK›[™ÝŒ
^ÑË™\œ›ÜŠ˜Z[YÈØY	ÙK›[™ÝH^\›˜[XYÜ˜[\Ø
NÙ›ÜŠ]ÙˆJQË™\œ›ÜŠ
NÝ›ÝÈ\œ›ÜŠ˜Z[YÈØY	ÙK›[™ÝH^\›˜[XYÜ˜[\Ø
__KØY™YÚ\Ý\™YXYÜ˜[\Ø
K	]XÜ˜\XÜËYØÝ[Y[ØÝ[Y[Ù[˜Ý[ÛˆMÝ
K
^ÙK˜]Š›ÛX	]
KOOX	‰™K˜]Š\šXK\›ÛY\ØÜš\[Û˜
_UÊMÝÙ]LL^QXYÜ˜[R[™›Ø
NÙ[˜Ý[ÛˆÝ
K‹Š^ÚYŠKš[œÙ\OO]›ÚY
^ÚYŠŠ^Û]XÚ\Y\ØËIÜŸXÙK˜]Š\šXKY\ØÜšX™YžX
KKš[œÙ\
\ØØ™š\œÝXÚ[
K˜]ŠY
K^
Š_ZYŠ
^Û]XÚ\]]KIÜŸXÙK˜]Š\šXK[X™[YžXŠKKš[œÙ\
]X™š\œÝXÚ[
K˜]ŠYŠK^

___UÊÝYÕ‘ØLL^U]Q\ØÜš\[Û˜
NÝ˜\ˆÝXÛ\ÜÈ^ØÛÛœÝXÝÜŠK‹‹J^Ý\Ë\OYK\Ë^]\Ë™[‹\Ëœ\œÙ\\‹\Ëœ™[™\™\Z_\Ý]XÞÕÊ\ËXYÜ˜[X
_\Ý]XÈ\Þ[˜Èœ›ÛU^
^ßJ^Û]]]Ê
KOTÝÊŠNÝRUÙJ
JØ˜Ýž^ÜÕ
J_XØ]ÚÛ]OV‘YJJNÚYŠYJ]›ÝÈ™]ÈÊXYÜ˜[H	Ú_H›Ý›Ý[™˜
NÛ]ÚYXYÜ˜[N›ŸOX]ØZ]J
NÛÕ
Š_[]ÙŽ˜K\œÙ\Ž›Ë™[™\™\ŽœË[š]›O\Õ
JNÜ™]\›ˆËœ\œÙ\‰‰ŠËœ\œÙ\‹ž^OXJKK˜ÛX\ËŠ
KËŠŠK‹]I‰˜KœÙ]XYÜ˜[U]OËŠ‹]JK]ØZ]Ëœ\œÙJ
K™]ÈJKKËÊ_X\Þ[˜È™[™\ŠK
^Ø]ØZ]\Ëœ™[™\™\‹™˜]Ê\Ë^K\Ê_YÙ]\œÙ\Š
^Ü™]\›ˆ\Ëœ\œÙ\ŸYÙ]\J
^Ü™]\›ˆ\Ë\__KÝV×KMÝUÊ

OOžÜÝ™›Ü‘XXÚ
OOžÙJ
_JKÝV×_K]XÚ[˜Ý[ÛœØ
KMÝUÊOO™Kœ™\XÙJ×—Ê‰IJÈ^ÊV×——J×ËÙÛK
Kš[TÝ\

KÛX[\ÛÛ[Y[Ø
NÙ[˜Ý[ÛˆÍÝ
J^Û]YK›X]Ú
ÊNÚYŠ]
\™]\›žÝ^™KY]Y]Nžß_NÛ]]ÌWKPZÊÝÌ—KœÜ]
˜
K›X\
OO™KœÝ\ÕÚ]
ŠOÙKœÛXÙJ‹›[™Ý
N™JKš›Ú[Š˜
NÌ—KÜØÚ[XNšÚßJOÏÞßNÜ]\[ÙˆOXØš™XÝ	‰ˆP\œ˜^Kš\Ð\œ˜^JŠOÜŽžßNÛ]O^ßNÜ™]\›ˆ‹™\Ü^S[ÙI‰ŠK™\Ü^S[ÙO\‹™\Ü^S[ÙKÔÝš[™Ê
JK‹]I‰ŠK]O\‹]KÔÝš[™Ê
JK‹˜ÛÛ™šYÉ‰ŠK˜ÛÛ™šYÏ\‹˜ÛÛ™šYÊKÝ^™KœÛXÙJÌK›[™Ý
KY]Y]Nš__UÊÍÝ^˜XÝœ›ÛX]\˜
NÝ˜\ˆÍÝUÊOO™Kœ™\XÙJ×—ËÙË˜
Kœ™\XÙJÏ
ÊÊJ×—JŠO‹ÙË
KŠOO˜
Ý
Û‹œ™\XÙJÏHŠ×ˆ—JŠH‹ÙËIÉIØ
JØ˜
KÛX[\^
KÍÝUÊOOžÛ]Ý^Y]Y]N›ŸO[ÍÝ
JKÙ\Ü^S[ÙNœ‹]NšKÛÛ™šYÎ˜O^ß_O[ŽÜ™]\›ˆ‰‰ŠK™Ø[^ßKK™Ø[™\Ü^S[ÙO\ŠKÝ]NšKÛÛ™šYÎ˜K^_K›ØÙ\ÜÑœ›ÛX]\˜
KÝUÊOOžÛ]ZPK™]XÝ[š]
JOÏÞßKZPK™]XÝ\™XÝ]™JKÜ˜\
NÜ™]\›ˆ\œ˜^Kš\Ð\œ˜^JŠOÝÜ˜\[‹œÛÛYJ
Ý\N™_JOO™OOOXÜ˜\
N›Ë\OOOXÜ˜\	‰ŠÜ˜\HL
KÝ^žÙJJK\™XÝ]™N_K›ØÙ\ÜÑ\™XÝ]™\Ø
NÙ[˜Ý[ÛˆMÝ
J^Û]XÍÝ
ÍÝ
JJK[Ý
^
KTZÊ˜ÛÛ™šYË‹™\™XÝ]™JNÜ™]\›ˆOXMÝ
‹^
KØÛÙN™K]N]KÛÛ™šYÎœŸ_UÊMÝ™\›ØÙ\ÜÑXYÜ˜[X
NÙ[˜Ý[ÛˆÝ
J^Û][™]È^[˜ÛÙ\Š
K™[˜ÛÙJJKP\œ˜^K™œ›ÛJOO”Ýš[™Ë™œ›ÛPÛÙTÚ[
JJKš›Ú[Š
NÜ™]\›ˆØJŠ_UÊÝÐ˜\ÙM
NÝ˜\ˆÝMYMÝXÜ˜\ŽØVÓX^[][H^Ú^™H[ˆXYÜ˜[H^ÙYYYNÜÝ[HHš[ˆÙ˜XXMÝXØ[™›ÞÝXÛÜÙXÍÝX‹ËÝÝÝËÌË›Ü™ËÌŒÜÝ™ØÍÝX‹ËÝÝÝËÌË›Ü™ËÌNNNKÞ[šØÝX‹ËÝÝÝËÌË›Ü™ËÌNNNKÞ[MÝXL	XÝXL	XÝX›Ü™\ŽŒÛX\™Ú[ŽŒØÍÝXX\™Ú[ŽŒÍÝX[ÝË]Ü[˜]šYØ][Û‹XžK]\Ù\‹XXÝ]˜][Ûˆ[ÝË\Ü\ØÍÝXHšYœ˜[YHˆYÈ\È›ÝÝ\ÜYžH[Ý\ˆœ›ÝÜÙ\‹˜ÝVØ›Ü™ZYÛ›Øš™XÝKMÝVØÛZ[˜[X˜\Ù[[™XNÙ[˜Ý[ÛˆÝ
J^Û]]MÝ
JNÜ™]\›ˆÊ
K‘YJ˜ÛÛ™šYÏÏÞßJKUÊÝ›ØÙ\ÜÐ[™Ù]ÛÛ™šYÜØ
NØ\Þ[˜È[˜Ý[ÛˆÍÝ
K
^ÝÎJ
NÝž^Û]ØÛÙNÛÛ™šYÎ›ŸOQÝ
JNÜ™]\›žÙXYÜ˜[U\NŠ]ØZ]Ý

JK\KÛÛ™šYÎ›Ÿ_XØ]Ú
J^ÚYŠËœÝ\™\ÜÑ\œ›ÜœÊ\™]\›ˆLNÝ›ÝÈ__UÊÍÝ\œÙX
NÝ˜\ˆÍÝUÊ
KV×JOO˜‰Ù_H	ÝH	Ù]ÊÈ	Û‹š›Ú[ŠZ[\Ü[È
_HZ[\Ü[ÈX
_XÜÜÒ[\Ü[Ý[\Ø
KMÝUÊ
K[™]ÈX\
OOžÛ][™]ÈÔÔÔÝ[TÚY]ÚYŠK™›Û˜[Z[HOO]›ÚY	‰›‹š[œÙ\[Jœ›ÛÝÈK[Y\›XZYY›ÛY˜[Z[Nˆ	ÙK™›Û˜[Z[__X‹˜ÜÜÔ[\Ë›[™Ý
KK˜[›Û˜[Z[HOO]›ÚY	‰›‹š[œÙ\[Jœ›ÛÝÈK[Y\›XZYX[Y›ÛY˜[Z[Nˆ	ÙK˜[›Û˜[Z[__X‹˜ÜÜÔ[\Ë›[™Ý
K[œÝ[˜Ù[ÙˆX\
^Û]WÝÊJOÖØˆ
˜Ü[˜N–Ø™XÝÛYÛÛ˜[\ÙXÚ\˜ÛX]NÝ™›Ü‘XXÚ
OOžÜ•ÙJKœÝ[\Ê_‹™›Ü‘XXÚ
OžÛ‹š[œÙ\[JÍÝ
KšYKœÝ[\ÊK‹˜ÜÜÔ[\Ë›[™Ý
_JK•ÙJK^Ý[\Ê_‹š[œÙ\[JÍÝ
KšYÜ[˜
OË^Ý[\ß×JK›X\
OO™Kœ™\XÙJÛÛÜ˜š[
JJK‹˜ÜÜÔ[\Ë›[™Ý
_J_[]XÚYŠK[YPÔÔÈOO]›ÚY
ZYŠ\[Ùˆ‹œ™\XÙTÞ[˜ÏOX[˜Ý[Û˜
^Û][™]ÈÔÔÔÝ[TÚY]Ýœ™\XÙTÞ[˜ÊK[YPÔÔÊKX‘YJ
JØ˜Y[ÙHŠÏX	ÙK[YPÔÔßB˜Ü™]\›ˆŠØ‘YJŠ_KÜ™X]PÜÜÔÝ[\Ø
KÝUÊ
K
OO‘]]
Ý]
	Ù_^ÉÝ_X
KÝ]
ÕÊ[˜Ý[ÛŠ‹‹J^ÚYŠ\OOOX[X	‰\œ˜^Kš\Ð\œ˜^Jœ›ÜÊJ^ÚYŠœ\™[	‰œ\™[\OOOXÙ^Yœ˜[Y\Ø
\™]\›ŽÝœ›ÜÏ]œ›ÜË›X\
OœÝ\ÕÚ]
JOÝ˜	Ù_H	ÝX
_Y[ÙH\KœÝ\ÕÚ]

I‰ŠØYYXXÝ\ÜØ^Y\˜ØÛÜXÛÛZ[™\˜Ý\[™Ë\Ý[XÙ^Yœ˜[Y\ØKš[˜ÛY\Ê\J_
ËØ\›Š™[[Ýš[™È[œÝ\ÜY]\[H	Ý\_Hœ›ÛHÔÔØ
K\OI
J_KY˜[Y\ÜXÙX
K]JJKÛÛ\[PÔÔØ
KMÝUÊ
K‹ŠOOšÝ
‹JMÝ
KŠKË‹‹™K[YU˜\šXX›\Ë[YN™K[YKÛÚÎ™K›ÛÚßKŠJKÜ™X]U\Ù\”Ý[\Ø
KÝUÊ
OXŠOOžÛ]YNÜ™]\›ˆ[‰‰ˆ]	‰Š\‹œ™\XÙJÛX\šÙ\‹Y[™H\›
×
Ë‹ÎOÐKV˜K^‹WJÈËÙËX\šÙ\‹Y[™H\›
Ø
JKXPJŠK\‹œ™\XÙJÏœ‹ÙËœ‹Ï˜
KŸKÛX[•\Ý™ÐÛÙX
KÝUÊ
OX
OO˜Yœ˜[YHÝ[OHÚY‰ÞMÝNÚZYÚ‰ÝËšY]Ð›ÞË˜˜\ÙU˜[ËšZYÚÝšY]Ð›Þ˜˜\ÙU˜[šZYÚ
Ø˜ÝNÉÞÝHˆÜ˜ÏH™]N^Ú[ØÚ\œÙ]UU‹NØ˜\ÙM	ÙÝ
›ÙHÝ[OH‰ÔÍÝH‰Ù_OØ›ÙO˜
_HˆØ[™›ÞH‰ÐÍÝH‚ˆ	ÝÍÝBÚYœ˜[YO˜][ÒQœ˜[YX
KÝUÊ
K‹‹JOOžÛ]OYK˜\[™
]˜
NØK˜]ŠYŠK‰‰˜K˜]ŠÝ[XŠNÛ]ÏXK˜\[™
Ý™Ø
K˜]ŠY
K˜]ŠÚYL	X
K˜]Š[œØÍÝ
NÜ™]\›ˆI‰›Ë˜]Š[œÎž[šØJKË˜\[™
Ø
K_K\[™]”Ý™ÑØ
NÙ[˜Ý[ÛˆMÝ
K
^Ü™]\›ˆK˜\[™
Yœ˜[YX
K˜]ŠY
K˜]ŠÝ[XÚYˆL	NÈZYÚˆL	NØ
K˜]ŠØ[™›Þ
_UÊMÝØ[™›ÞYYœ˜[YX
NÝ˜\ˆÝUÊ
K‹ŠOOžÙK™Ù][[Y[žRY

OËœ™[[Ý™J
KK™Ù][[Y[žRY
ŠOËœ™[[Ý™J
KK™Ù][[Y[žRY
ŠOËœ™[[Ý™J
_K™[[Ý™Q^\Ý[™Ñ[[Y[Ø
KÝUÊ\Þ[˜È[˜Ý[ÛŠKŠ^ÝÎJ
NÛ]QÝ

NÝ\‹˜ÛÙNÛ]O]]Ê
NÑË™XYÊJK›[™ÝŠOË›X^^Ú^™OÏÙÝ
I‰Š\Ý
NÛ]OXÉÙ_XÏXX
ÙKÏXØ
ÛËX
ÙKOXØ
ÛUÊ

OOžÛ]OU•
ÜÎJK››ÙJ
NÙI‰˜™[[Ý™X[ˆI‰™Kœ™[[Ý™J
_K™[[Ý™U[\[[Y[Ø
KU•
ØÝ[Y[˜›ÙJKZKœÙXÝ\š]S]™[OO[MÝOZKœÙXÝ\š]S]™[OOZÝZK™›Û˜[Z[NÛOO]›ÚYÊÝ
ØÝ[Y[KÊKÊU•
MÝ
•
ØÝ[Y[˜›ÙJKÊK››Ù\Ê
VÌK˜ÛÛ[ØÝ[Y[˜›ÙJK‹››ÙJ
KœÝ[K›X\™Ú[X
N™U•
›ÙX
KÝ
‹K
JNŠ‰‰Š‹š[›™\’SX
KÊU•
MÝ
•
ŠKÊK››Ù\Ê
VÌK˜ÛÛ[ØÝ[Y[˜›ÙJK‹››ÙJ
KœÝ[K›X\™Ú[X
N™U•
ŠKÝ
‹K›ÛY˜[Z[Nˆ	ÚXÍÝ
JNÛ]ËÎÝž^ÙÏX]ØZ]Ý™œ›ÛU^
Ý]Nœ‹]_J_XØ]Ú
J^ÚYŠKœÝ\™\ÜÑ\œ›Ü”™[™\š[™Ê]›ÝÈ

KNÙÏX]ØZ]Ý™œ›ÛU^
\œ›Ü˜
KÏY_[]Y‹œÙ[XÝ
JK››ÙJ
KOYË\K]‹™š\œÝÚ[X‹™š\œÝÚ[ÏYËœ™[™\™\‹™Ù]Û\ÜÙ\ÏËŠÊKÏSMÝ
KKËJKÏYØÝ[Y[˜Ü™X]Q[[Y[
Ý[X
NÝËš[›™\’SPË‹š[œÙ\™Y›Ü™JË
NÝž^Ø]ØZ]Ëœ™[™\™\‹™˜]ÊKLKŒM‹ŒÊ_XØ]Ú
Š^Ý›ÝÈKœÝ\™\ÜÑ\œ›Ü”™[™\š[™ÏÙ

N›]™˜]ÊKLKŒM‹Œ
KŸ[]Y‹œÙ[XÝ
	Ý_HÝ™Ø
KOYË™‹™Ù]XØÕ]OËŠ
KYË™‹™Ù]XØÑ\ØÜš\[ÛËŠ
NÕÝ
KK
K‹œÙ[XÝ
ÚYH‰Ù_H—X
KœÙ[XÝ[
›Ü™ZYÛ›Øš™XÝˆ
˜
K˜]Š[œØÝ
NÛ]ÏY‹œÙ[XÝ
JK››ÙJ
Kš[›™\’SÚYŠË™XYÊÛÛ™šYË˜\œ›ÝÓX\šÙ\XœÛÛ]XK˜\œ›ÝÓX\šÙ\XœÛÛ]JKÏSÝ
ËÊK˜\œ›ÝÓX\šÙ\XœÛÛ]JJK
^Û]OY‹œÙ[XÝ
JØÝ™Ø
K››ÙJ
NÓÏTÝ
ËJ_Y[ÙH_
ÏU˜‹œØ[š]^™JËÐQÕQÔÎ•ÝQÐUŽ‘MÝSÒS•QÔUSÓ—ÔÒS•ÎžÙ›Ü™ZYÛ›Øš™XÝˆL_JJNÚYŠMÝ

KÊ]›ÝÈÎÜ™]\›ˆ

KÙXYÜ˜[U\NžKÝ™Î“Ëš[™[˜Ý[ÛœÎ™Ë™‹˜š[™[˜Ý[Ûœß_K™[™\˜
NÙ[˜Ý[ÛˆÝ
O^ßJ^Û]UÐÊßKJNÝË™›Û˜[Z[I‰ˆ][YU˜\šXX›\ÏË™›Û˜[Z[I‰Š[YU˜\šXX›\ß^ßK[YU˜\šXX›\Ë™›Û˜[Z[O]™›Û˜[Z[JKÑYJ
KË[YI‰[YH[ˆPÏÝ[YU˜\šXX›\ÏVPÖÝ[YWK™Ù][YU˜\šXX›\Ê[YU˜\šXX›\ÊN	‰Š[YU˜\šXX›\ÏVPË™Y˜][™Ù][YU˜\šXX›\Ê[YU˜\šXX›\ÊJKžJ
\[ÙˆOXØš™XÝÑÑYJ
N˜ÝÊ
JK›ÙÓ]™[
KÎJ
_UÊÝ[š]X[^™X
NÝ˜\ˆÝUÊ
K^ßJOOžÛ]ØÛÙN›ŸO]MÝ
JNÜ™]\›ˆÝ™œ›ÛU^
‹
_KÙ]XYÜ˜[Qœ›ÛU^
NÙ[˜Ý[ÛˆÝ
K‹Š^ÙMÝ
JKÝ
‹‹˜]ŠY
J_UÊÝYLL^R[™›Ø
NÝ˜\ˆOSØš™XÝ™œ™Y^™JÜ™[™\Ž”Ý\œÙN“ÍÝÙ]XYÜ˜[Qœ›ÛU^Ý[š]X[^™NžÝÙ]ÛÛ™šYÎ]ËÙ]ÛÛ™šYÎ›ËÙ]Ú]PÛÛ™šYÎ˜ÝË\]TÚ]PÛÛ™šYÎœQYK™\Ù]•Ê

OOžÙÊ
_K™\Ù]
KÛØ˜[™\Ù]•Ê

OOžÙÊÊ_KÛØ˜[™\Ù]
KY˜][ÛÛ™šYÎßJNÞžJ]Ê
K›ÙÓ]™[
KÊ]Ê
JNÝ˜\ˆÝUÊ
KŠOOžÑËØ\›ŠJKUÙJJOÊ‰‰›ŠKœÝ‹Kš\Ú
Kœ\Ú
Ë‹‹™KY\ÜØYÙN™KœÝ‹\œ›ÜŽ™_JJNŠ‰‰›ŠJKH[œÝ[˜Ù[Ùˆ\œ›Ü‰‰œ\Ú
ÜÝŽ™K›Y\ÜØYÙKY\ÜØYÙN™K›Y\ÜØYÙK\Ú™K›˜[YK\œ›ÜŽ™_JJ_K[™Q\œ›Ü˜
KMÝUÊ\Þ[˜È[˜Ý[ÛŠO^Ü]Y\žTÙ[XÝÜŽ˜›Y\›XZYJ^Ýž^Ø]ØZ]ÍÝ
J_XØ]Ú

^ÚYŠUÙJ
I‰‘Ë™\œ›ÜŠœÝŠKKœ\œÙQ\œ›Ü‰‰‘Kœ\œÙQ\œ›ÜŠ
KYKœÝ\™\ÜÑ\œ›ÜœÊ]›ÝÈË™\œ›ÜŠ\ÙHHÝ\™\ÜÑ\œ›ÜœÈÜ[ÛˆÈÝ\™\ÜÈ\ÙH\œ›ÜœØ
K_K[˜
KÍÝUÊ\Þ[˜È[˜Ý[ÛŠÜÜÝ™[™\Ø[˜XÚÎ™K]Y\žTÙ[XÝÜŽ›Ù\Î›ŸO^Ü]Y\žTÙ[XÝÜŽ˜›Y\›XZYJ^Û]UK™Ù]ÛÛ™šYÊ
NÑË™XYÊ	ÙOØ˜›ÈPØ[˜XÚÈ[˜Ý[Ûˆ›Ý[™
NÛ]NÚYŠŠZO[ŽÙ[ÙHYŠ
ZOYØÝ[Y[œ]Y\žTÙ[XÝÜ[

NÙ[ÙH›ÝÈ\œ›ÜŠ›Ù\È[™]Y\žTÙ[XÝÜˆ\™H›Ý[™Yš[™Y
NÑË™XYÊ›Ý[™	ÚK›[™ÝHXYÜ˜[\Ø
KËœÝ\Û“ØYOO]›ÚY	‰ŠË™XYÊÝ\ÛˆØYˆ
ÜËœÝ\Û“ØY
KK\]TÚ]PÛÛ™šYÊÜÝ\Û“ØYœËœÝ\Û“ØYJJNÛ]O[™]ÈPK’[š]QÙ[™\˜]ÜŠ‹™]\›Z[š\ÝXÒYË‹™]\›Z[š\ÝXÒQÙYY
KËÏV×NÙ›ÜŠ]Ùˆ\œ˜^K™œ›ÛJJJ^ÚYŠËš[™›Ê™[™\š[™ÈXYÜ˜[Nˆ
ÝšY
K™Ù]]šX]J]K\›ØÙ\ÜÙY
JXÛÛ[YNÝœÙ]]šX]J]K\›ØÙ\ÜÙYYX
NÛ]XY\›XZYIØK›™^

_XÛÏ]š[›™\’SÏQRÙJPK™[]QXÛÙJÊJKš[J
Kœ™\XÙJÏœ—Ê—ÏÏ‹ÙÚKœ‹Ï˜
NÛ]ZPK™]XÝ[š]
ÊNÜ‰‰‘Ë™XYÊ]XÝYX\›H™Z[š]ˆŠNÝž^Û]ÜÝ™Îœ‹š[™[˜Ý[ÛœÎš_OX]ØZ]	Ý
‹Ë
NÝš[›™\’S\‹I‰˜]ØZ]JŠKI‰šJ
_XØ]Ú
J^ÒÝ
KËKœ\œÙQ\œ›ÜŠ__ZYŠË›[™ÝŒ
]›ÝÈÖÌ_K[•›ÝÜÑ\œ›ÜœØ
KÍÝUÊ[˜Ý[ÛŠJ^ÕKš[š]X[^™JJ_K[š]X[^™X
KÍÝUÊ\Þ[˜È[˜Ý[ÛŠKŠ^ÑËØ\›ŠY\›XZYš[š]\È\™XØ]YˆX\ÙH\ÙH[ˆ[œÝXY˜
KI‰‘ÍÝ
JNÛ]^ÜÜÝ™[™\Ø[˜XÚÎ›‹]Y\žTÙ[XÝÜŽ˜›Y\›XZYNÝ\[ÙˆOXÝš[™ØÜ‹œ]Y\žTÙ[XÝÜ]	‰Š[œÝ[˜Ù[ÙˆS[[Y[Ü‹››Ù\ÏVÝNœ‹››Ù\Ï]
K]ØZ]MÝ
Š_K[š]
KMÝUÊ\Þ[˜ÊKÛ^žSØYHLO^ßJOOžÝÎJ
KÝÊ‹‹™JKOOHLI‰˜]ØZ]M]

_K™YÚ\Ý\‘^\›˜[XYÜ˜[\Ø
KÝUÊ[˜Ý[ÛŠ
^ÚYŠKœÝ\Û“ØY
^Û]ÜÝ\Û“ØY™_OUK™Ù]ÛÛ™šYÊ
NÙI‰‘Kœ[Š
K˜Ø]Ú
OO‘Ë™\œ›ÜŠY\›XZY˜Z[YÈ[š]X[^™XJJ__KÛÛ[ØYY
NÝ\[ÙˆØÝ[Y[X	‰Ú[™ÝË˜Y]™[\Ý[™\ŠØYÝLJNÝ˜\ˆMÝUÊ[˜Ý[ÛŠJ^ÑKœ\œÙQ\œ›ÜY_KÙ]\œÙQ\œ›Ü’[™\˜
KNOV×KÝHLKÝUÊ\Þ[˜Ê
OOžÚYŠVÝ
^Ù›ÜŠÝHLÑNK›[™ÝŒÊ^Û]OQNKœÚY

NÚYŠJ]ž^Ø]ØZ]J
_XØ]Ú
J^ÑË™\œ›ÜŠ\œ›Üˆ^XÝ][™È]Y]YXJ__VÝHL__K^XÝ]T]Y]YX
KMÝUÊ\Þ[˜ÊK
OO›™]È›ÛZ\ÙJ
‹ŠOOžÛ]OUÊ

OO›™]È›ÛZ\ÙJ
KJOOžÕKœ\œÙJK
K[ŠOOžÚJJKŠJ_KOOžÑË™\œ›ÜŠ\œ›Üˆ\œÚ[™ØJKKœ\œÙQ\œ›ÜËŠJKJJKŠJ_J_JK\™›Ü›PØ[
NÑNKœ\Ú
JKÝ

K˜Ø]Ú
Š_JK\œÙX
K	ÝUÊ
KŠOO›™]È›ÛZ\ÙJ
‹JOOžÛ]OUÊ

OO›™]È›ÛZ\ÙJ
KÊOOžÕKœ™[™\ŠKŠK[ŠOOžØJJKŠJ_KOOžÑË™\œ›ÜŠ\œ›Üˆ\œÚ[™ØJKKœ\œÙQ\œ›ÜËŠJKÊJKJJ_J_JK\™›Ü›PØ[
NÑNKœ\Ú
JKÝ

K˜Ø]Ú
J_JK™[™\˜
KO^ÜÝ\Û“ØYˆLY\›XZYTN•K\œÙN”MÝ™[™\Ž‰Ý[š]’ÍÝ[Ž•MÝ™YÚ\Ý\‘^\›˜[XYÜ˜[\ÎœMÝ™YÚ\Ý\“^[Ý]ØY\œÎ”[[š]X[^™N‘ÍÝ\œÙQ\œ›ÜŽ›ÚYÛÛ[ØYY’ÝÙ]\œÙQ\œ›Ü’[™\Ž–MÝ]XÝ\N”ÝË™YÚ\Ý\’XÛÛ”XÚÜÎœKÙ]™YÚ\Ý\™YXYÜ˜[\ÓY]Y]N•Ê

OO“Øš™XÝšÙ^\ÊÊK›X\
OOŠÚY™_JJKÙ]™YÚ\Ý\™YXYÜ˜[\ÓY]Y]X
_KN]QK]Y
Ê

K
OOžÝ˜\ˆY[˜Ý[ÛŠJ^Ý˜\ˆKÊÎ—ŸÊ[[™ÊÎXYÙJOËJ×ËWJÊJÏWß	
KÚKL^ßKO^ÛX[X[™K”š\ÛI‰™K”š\ÛK›X[X[\ØX›UÛÜšÙ\“Y\ÜØYÙR[™\Ž™K”š\ÛI‰™K”š\ÛK™\ØX›UÛÜšÙ\“Y\ÜØYÙR[™\‹][žÙ[˜ÛÙN™[˜Ý[ÛˆJ
^Ü™]\›ˆ[œÝ[˜Ù[ÙˆOÛ™]ÈJ\KJ˜ÛÛ[
K˜[X\ÊN\œ˜^Kš\Ð\œ˜^J
OÝ›X\
JNœ™\XÙJÉ‹ÙË	˜[\Ø
Kœ™\XÙJÏÙË	›Ø
Kœ™\XÙJ×LLÙË
_K\N™[˜Ý[ÛŠJ^Ü™]\›ˆØš™XÝœ›ÝÝ\KÔÝš[™Ë˜Ø[
JKœÛXÙJLJ_KØš’Y™[˜Ý[ÛŠJ^Ü™]\›ˆK—×ÚYØš™XÝ™Yš[™T›Ü\JK—×ÚY‹Ý˜[YNŠÊÛŸJKK—×ÚYKÛÛ™N™[˜Ý[ÛˆJŠ^ÛŸ^ßNÝ˜\ˆ‹NÜÝÚ]Ú
K][\J
J^ØØ\ÙXØš™XÝšYŠOZK][›Øš’Y

K–ØWJ\™]\›ˆ–ØWNÙ›ÜŠ˜\ˆÈ[ˆ^ßK–ØWO\‹
]š\ÓÝÛ”›Ü\JÊI‰Š–Û×OYJÛ×KŠJNÜ™]\›ˆŽØØ\ÙX\œ˜^Xœ™]\›ˆOZK][›Øš’Y

K–ØWOÛ–ØWNŠV×K–ØWO\‹™›Ü‘XXÚ
[˜Ý[ÛŠJ^Ü–ÚWOYJŠ_JKŠNÙY˜][œ™]\›ˆ_KÙ][™ÝXYÙN™[˜Ý[ÛŠJ^Ù›ÜŠÙNÊ^Ý˜\ˆ]™^XÊK˜Û\ÜÓ˜[YJNÚYŠŠ\™]\›ˆ–ÌWKÓÝÙ\Ø\ÙJ
NÙOYKœ\™[[[Y[\™]\›˜›Û™XKÙ][™ÝXYÙN™[˜Ý[ÛŠKŠ^ÙK˜Û\ÜÓ˜[YOYK˜Û\ÜÓ˜[YKœ™\XÙJ™YÑ^
ÚX
K
KK˜Û\ÜÓ\Ý˜Y
[™ÝXYÙKX
ÛŠ_KÝ\œ™[ØÜš\™[˜Ý[ÛŠ
^ÚYŠ\[ÙˆØÝ[Y[˜X
\™]\›ˆ[ÚYŠØÝ[Y[˜Ý\œ™[ØÜš\	‰™ØÝ[Y[˜Ý\œ™[ØÜš\YÓ˜[YOOOXÐÔ’T
\™]\›ˆØÝ[Y[˜Ý\œ™[ØÜš\Ýž^Ý›ÝÈ\œ›ÜŠ
_XØ]Ú
Š^Ý˜\ˆOJØ]×Š——J—

ŠŠN–×Ž—JÎ–×Ž—J×
IÚK™^XÊ‹œÝXÚÊ_×JVÌWNÚYŠJ^Ý˜\ˆYØÝ[Y[™Ù][[Y[ÐžUYÓ˜[YJØÜš\
NÙ›ÜŠ˜\ˆˆ[ˆ
ZYŠÛ—KœÜ˜ÏOYJ\™]\›ˆÛ—_\™]\›ˆ[_K\ÐXÝ]™N™[˜Ý[ÛŠKŠ^Ù›ÜŠ˜\ˆX›ËX
ÝÙNÊ^Ý˜\ˆOYK˜Û\ÜÓ\ÝÚYŠK˜ÛÛZ[œÊ
J\™]\›ˆLÚYŠK˜ÛÛZ[œÊŠJ\™]\›ˆLNÙOYKœ\™[[[Y[\™]\›ˆH[Ÿ_K[™ÝXYÙ\ÎžÜZ[Žœ‹Z[^œ‹^œ‹œ‹^[™™[˜Ý[ÛŠK
^Ý˜\ˆZK][˜ÛÛ™JK›[™ÝXYÙ\ÖÙWJNÙ›ÜŠ˜\ˆˆ[ˆ
[–Ü—O]Ü—NÜ™]\›ˆŸK[œÙ\™Y›Ü™N™[˜Ý[ÛŠK‹Š^ÜŸZK›[™ÝXYÙ\ÎÝ˜\ˆO\–ÙWKÏ^ßNÙ›ÜŠ˜\ˆÈ[ˆJZYŠKš\ÓÝÛ”›Ü\JÊJ^ÚYŠÏO]
Y›ÜŠ˜\ˆ[ˆŠ[‹š\ÓÝÛ”›Ü\J
I‰ŠÖÛO[–ÛJNÛ‹š\ÓÝÛ”›Ü\JÊ_
ÖÜ×OXVÜ×J_]˜\ˆO\–ÙWNÜ™]\›ˆ–ÙWO[ËK›[™ÝXYÙ\Ë‘”ÊK›[™ÝXYÙ\Ë[˜Ý[ÛŠŠ^ÛOO]I‰OYI‰Š\ÖÝO[Ê_JKßK”Î™[˜Ý[ÛˆJ‹‹J^Ø_^ßNÝ˜\ˆÏZK][›Øš’YÙ›ÜŠ˜\ˆÈ[ˆ
ZYŠš\ÓÝÛ”›Ü\JÊJ^Û‹˜Ø[
ËÜ×KŸÊNÝ˜\ˆ]Ü×KOZK][\J
NÝOOOXØš™XÝ	‰ˆXVÛÊ
WOÊVÛÊ
WOHLJ‹[JJNOOOX\œ˜^X	‰ˆXVÛÊ
WI‰ŠVÛÊ
WOHLJ‹ËJJ___KYÚ[œÎžßKYÚYÚ[™[˜Ý[ÛŠK
^ÚKšYÚYÚ[[™\ŠØÝ[Y[K
_KYÚYÚ[[™\Ž™[˜Ý[ÛŠKŠ^Ý˜\ˆ^ØØ[˜XÚÎ›‹ÛÛZ[™\Ž™KÙ[XÝÜŽ˜ÛÙVØÛ\ÜÊH›[™ÝXYÙKH—KØÛ\ÜÊH›[™ÝXYÙKH—HÛÙKÛÙVØÛ\ÜÊH›[™ËH—KØÛ\ÜÊH›[™ËH—HÛÙXNÚKšÛÚÜËœ[Š™Y›Ü™KZYÚYÚ[ŠK‹™[[Y[ÏP\œ˜^Kœ›ÝÝ\KœÛXÙK˜\J‹˜ÛÛZ[™\‹œ]Y\žTÙ[XÝÜ[
‹œÙ[XÝÜŠJKKšÛÚÜËœ[Š™Y›Ü™KX[Y[[Y[ËZYÚYÚŠNÙ›ÜŠ˜\ˆOLÎÛÏ\‹™[[Y[ÖØJÊ×NÊZKšYÚYÚ[[Y[
ËOOHL‹˜Ø[˜XÚÊ_KYÚYÚ[[Y[™[˜Ý[ÛŠ‹Š^Ý˜\ˆOZK][™Ù][™ÝXYÙJ
KÏZK›[™ÝXYÙ\ÖØWNÚK][œÙ][™ÝXYÙJJNÝ˜\ˆÏ]œ\™[[[Y[ÜÉ‰œË››ÙS˜[YKÓÝÙ\Ø\ÙJ
OOOX™X	‰šK][œÙ][™ÝXYÙJËJNÝ˜\ˆ^Ù[[Y[[™ÝXYÙN˜KÜ˜[[X\Ž›ËÛÙN^ÛÛ[NÙ[˜Ý[ÛˆJJ^ÛšYÚYÚYÛÙOYKKšÛÚÜËœ[Š™Y›Ü™KZ[œÙ\
K™[[Y[š[›™\’S[šYÚYÚYÛÙKKšÛÚÜËœ[ŠY\‹ZYÚYÚ
KKšÛÚÜËœ[ŠÛÛ\]X
K‰‰œ‹˜Ø[
™[[Y[
_ZYŠKšÛÚÜËœ[Š™Y›Ü™K\Ø[š]KXÚXÚØ
KÏ[™[[Y[œ\™[[[Y[É‰œË››ÙS˜[YKÓÝÙ\Ø\ÙJ
OOOX™X	‰ˆ\Ëš\Ð]šX]JXš[™^
I‰œËœÙ]]šX]JXš[™^
K[˜ÛÙJ^ÚKšÛÚÜËœ[ŠÛÛ\]X
K‰‰œ‹˜Ø[
™[[Y[
NÜ™]\›ŸZYŠKšÛÚÜËœ[Š™Y›Ü™KZYÚYÚ
K[™Ü˜[[X\Š^ÝJK][™[˜ÛÙJ˜ÛÙJJNÜ™]\›ŸZYŠ‰‰™K•ÛÜšÙ\Š^Ý˜\ˆ[™]ÈÛÜšÙ\ŠK™š[[˜[YJNÙ›Û›Y\ÜØYÙOY[˜Ý[ÛŠJ^ÝJK™]J_KœÜÝY\ÜØYÙJ”ÓÓ‹œÝš[™ÚYžJÛ[™ÝXYÙN››[™ÝXYÙKÛÙN›˜ÛÙK[[YYX]PÛÜÙNˆLJJ_Y[ÙHJKšYÚYÚ
˜ÛÙK™Ü˜[[X\‹›[™ÝXYÙJJ_KYÚYÚ™[˜Ý[ÛŠKŠ^Ý˜\ˆ^ØÛÙN™KÜ˜[[X\Ž[™ÝXYÙN›ŸNÚYŠKšÛÚÜËœ[Š™Y›Ü™K]ÚÙ[š^™XŠK\‹™Ü˜[[X\Š]›ÝÈ\œ›ÜŠH[™ÝXYÙH˜
Ü‹›[™ÝXYÙJØˆ\È›ÈÜ˜[[X\‹˜
NÜ™]\›ˆ‹ÚÙ[œÏZKÚÙ[š^™J‹˜ÛÙK‹™Ü˜[[X\ŠKKšÛÚÜËœ[ŠY\‹]ÚÙ[š^™XŠKKœÝš[™ÚYžJK][™[˜ÛÙJ‹ÚÙ[œÊK‹›[™ÝXYÙJ_KÚÙ[š^™N™[˜Ý[ÛŠK
^Ý˜\ˆ]œ™\ÝÚYŠŠ^Ù›ÜŠ˜\ˆˆ[ˆŠ]Ü—O[–Ü—NÙ[]Hœ™\Ý]˜\ˆO[™]ÈÜ™]\›ˆJKKšXYJKÊKKKšXY
KŠJ_KÛÚÜÎžØ[žßKY™[˜Ý[ÛŠK
^Ý˜\ˆZKšÛÚÜË˜[Û–ÙWO[–ÙW_×K–ÙWKœ\Ú

_K[Ž™[˜Ý[ÛŠK
^Ý˜\ˆZKšÛÚÜË˜[ÙWNÚYŠJ[Ÿ[‹›[™Ý
JY›ÜŠ˜\ˆLNØO[–ÜŠÊ×NÊXJ
__KÚÙ[Ž˜_NÙK”š\ÛOZNÙ[˜Ý[ÛˆJK‹Š^Ý\Ë\OYK\Ë˜ÛÛ[]\Ë˜[X\Ï[‹\Ë›[™ÝJŸ
K›[™ÝXKœÝš[™ÚYžOY[˜Ý[ÛˆJŠ^ÚYŠ\[ÙˆOXÝš[™Ø
\™]\›ˆÚYŠ\œ˜^Kš\Ð\œ˜^J
J^Ý˜\ˆXÜ™]\›ˆ™›Ü‘XXÚ
[˜Ý[ÛŠ
^ÜŠÏYJŠ_JKŸ]˜\ˆO^Ý\N\KÛÛ[™J˜ÛÛ[ŠKYÎ˜Ü[˜Û\ÜÙ\Î–ØÚÙ[˜\WK]šX]\ÎžßK[™ÝXYÙN›ŸKÏ]˜[X\ÎÛÉ‰Š\œ˜^Kš\Ð\œ˜^JÊOÐ\œ˜^Kœ›ÝÝ\Kœ\Ú˜\JK˜Û\ÜÙ\ËÊN˜K˜Û\ÜÙ\Ëœ\Ú
ÊJKKšÛÚÜËœ[ŠÜ˜\JNÝ˜\ˆÏXÙ›ÜŠ˜\ˆ[ˆK˜]šX]\Ê\ÊÏX
Û
ØH˜
ÊK˜]šX]\ÖÛ_
Kœ™\XÙJÈ‹ÙË	œ][ÝØ
JØ˜Ü™]\›˜
ØKYÊØÛ\ÜÏH˜
ØK˜Û\ÜÙ\Ëš›Ú[Š
JØ˜
ÜÊØ˜
ØK˜ÛÛ[
ØØ
ØKYÊØ˜NÙ[˜Ý[ÛˆÊK‹Š^ÙK›\Ý[™^]Ý˜\ˆOYK™^XÊŠNÚYŠI‰œ‰‰šVÌWJ^Ý˜\ˆOZVÌWK›[™ÝÚKš[™^
ÏXKVÌOZVÌKœÛXÙJJ_\™]\›ˆ_Y[˜Ý[ÛˆÊK‹‹Š^Ù›ÜŠ˜\ˆ[ˆŠZYŠJ[‹š\ÓÝÛ”›Ü\J
_[–ÜJJ^Ý˜\ˆO[–ÜNÛOP\œ˜^Kš\Ð\œ˜^JJOÛN–ÛWNÙ›ÜŠ˜\ˆLÚK›[™ÝÊÊÚ
^ÚYŠ‰‰™‹˜Ø]\ÙOO\
Ø
Ú
\™]\›ŽÝ˜\ˆÏ[VÚKÏYËš[œÚYKHHYË›ÛÚØ™Z[™OHHYË™Ü™YYKYË˜[X\ÎÚYŠI‰ˆYËœ]\›‹™ÛØ˜[
^Ý˜\ˆYËœ]\›‹ÔÝš[™Ê
K›X]Ú
ÖÚ[\Ý^WJ‰ÊVÌNÙËœ]\›T™YÑ^
Ëœ]\›‹œÛÝ\˜ÙK
ØØ
_Y›ÜŠ˜\ˆÏYËœ]\›ŸËÏ\‹›™^Ï[ÐÈOO]Z[	‰ˆJ‰‰ÏY‹œ™XXÚ
NÝÊÏPË˜[YK›[™ÝÏPË›™^
^Ý˜\ˆPË˜[YNÚYŠ›[™Ý™K›[™Ý
\™]\›ŽÚYŠJ[œÝ[˜Ù[ÙˆJJ^Ý˜\ˆOLKÚYŠJ^ÚYŠ[ÊËËKŠKQš[™^YK›[™Ý
Xœ™XZÎÝ˜\ˆÏQš[™^ÏQš[™^
ÑÌK›[™ÝO]ÎÙ›ÜŠJÏPË˜[YK›[™ÝÓÏPNÊPÏPË›™^JÏPË˜[YK›[™ÝÚYŠKOPË˜[YK›[™ÝÏPKË˜[YH[œÝ[˜Ù[ÙˆJXÛÛ[YNÙ›ÜŠ˜\ˆPÎÚˆOO]Z[	‰ŠOß\[Ùˆ‹˜[YOOXÝš[™Ø
NÚZ‹›™^
QJÊËJÏZ‹˜[YK›[™ÝÑKKKYKœÛXÙJËJKš[™^O]ßY[ÙHYŠ[ÊËŠKQ
XÛÛ[YNÝ˜\ˆÏQš[™^OQÌKUœÛXÙJÊKUœÛXÙJÊÓK›[™Ý
K]ÊÕ›[™ÝÙ‰‰‘™‹œ™XXÚ	‰Š‹œ™XXÚQŠNÝ˜\ˆOPËœ™]ŽÓ‰‰ŠO]JKŠKÊÏS‹›[™Ý
K
KJNÝ˜\ˆ[™]ÈJÏÚKÚÙ[š^™JKÊN“K‹JNÚYŠÏ]JK
K	‰JË
KOŒJ^Ý˜\ˆ^ØØ]\ÙNœ
Ø
Ú™XXÚ‘ŸNÜÊK‹Ëœ™]‹ËŠK‰‰”‹œ™XXÚ™‹œ™XXÚ	‰Š‹œ™XXÚT‹œ™XXÚ
______Y[˜Ý[Ûˆ

^Ý˜\ˆO^Ý˜[YN›[™]Ž›[™^›[K^Ý˜[YN›[™]Ž™K™^›[NÙK›™^]\ËšXYYK\ËZ[]\Ë›[™ÝLY[˜Ý[ÛˆJKŠ^Ý˜\ˆ]›™^O^Ý˜[YN›‹™]Ž™^œŸNÜ™]\›ˆ›™^ZK‹œ™]ZKK›[™Ý
ÊË_Y[˜Ý[Ûˆ
KŠ^Ù›ÜŠ˜\ˆ]›™^OLÚO‰‰œˆOOYKZ[ÚJÊÊ\\‹›™^Ý›™^\‹‹œ™]]K›[™ÝOZ_Y[˜Ý[ÛˆŠJ^Ù›ÜŠ˜\ˆV×KYKšXY›™^ÛˆOOYKZ[Ê]œ\Ú
‹˜[YJK[‹›™^Ü™]\›ˆZYŠYK™ØÝ[Y[
\™]\›ˆK˜Y]™[\Ý[™\‰‰ŠK™\ØX›UÛÜšÙ\“Y\ÜØYÙR[™\ŸK˜Y]™[\Ý[™\ŠY\ÜØYÙX[˜Ý[ÛŠ
^Ý˜\ˆR”ÓÓ‹œ\œÙJ™]JK[‹›[™ÝXYÙKO[‹˜ÛÙKÏ[‹š[[YYX]PÛÜÙNÙKœÜÝY\ÜØYÙJKšYÚYÚ
KK›[™ÝXYÙ\ÖÜ—KŠJKÉ‰™K˜ÛÜÙJ
_KLJJKNÝ˜\ˆZK][˜Ý\œ™[ØÜš\

NÜ	‰ŠK™š[[˜[YO\œÜ˜Ëš\Ð]šX]J]K[X[X[
I‰ŠK›X[X[HL
JNÙ[˜Ý[ÛˆJ
^ÚK›X[X[KšYÚYÚ[

_ZYŠZK›X[X[
^Ý˜\ˆYØÝ[Y[œ™XYTÝ]NÚOOXØY[™ØOOX[\˜XÝ]™X	‰œ	‰œ™Y™\ÙØÝ[Y[˜Y]™[\Ý[™\ŠÓPÛÛ[ØYYJNÚ[™ÝËœ™\]Y\Ý[š[X][Û‘œ˜[YOÝÚ[™ÝËœ™\]Y\Ý[š[X][Û‘œ˜[YJJNÚ[™ÝËœÙ][Y[Ý]
KMŠ_\™]\›ˆ_J\[ÙˆÚ[™ÝÏXÝÚ[™ÝÎ\[ÙˆÛÜšÙ\‘ÛØ˜[ØÛÜOX	‰œÙ[ˆ[œÝ[˜Ù[ÙˆÛÜšÙ\‘ÛØ˜[ØÛÜOÜÙ[ŽžßJNÝOO]›ÚY	‰™^ÜÉ‰Š™^ÜÏ[ŠK\[ÙˆÛØ˜[X	‰ŠÛØ˜[”š\ÛO[ŠK‹›[™ÝXYÙ\Ë›X\šÝ\^ØÛÛ[Y[žÜ]\›Ž‹ÏKKJÎŠÈOKKJV×××JJËKO‹ËÜ™YYNˆLK›ÛÙÎžÜ]\›Ž‹ÏÖ×××JÏ×Ï‹ËÜ™YYNˆLKØÝ\NžÜ]\›Ž‹ÏQÐÕTJÎ–×ˆ‰Ö×W_–×ˆ—JˆŸ	Ö×‰×J‰ÊJÊÎ—ÊÎ–×‰×W_–×ˆ—JˆŸ	Ö×‰×J‰ß
ÈHKKJ_KKJÎ–×‹W_JÈKOŠJJ‹KOŠJ—WÊŠOÏ‹ÚKÜ™YYNˆL[œÚYNžÈš[\›˜[\ÝXœÙ]ŽžÜ]\›Ž‹Ê–×—×J—ÊV×××JÊÏWO‰
KËÛÚØ™Z[™ˆLÜ™YYNˆL[œÚYN›[KÝš[™ÎžÜ]\›Ž‹È–×ˆ—JˆŸ	Ö×‰×J‰ËËÜ™YYNˆLK[˜ÝX][ÛŽ‹×_‰Ö×WKË™ØÝ\K]YÈŽ‹×‘ÐÕTKÚK˜[YN‹Ö×—Ï‰È—JËß_KÙ]NžÜ]\›Ž‹ÏWÐÑUWÖ×××J×WO‹ÚKÜ™YYNˆLKYÎžÜ]\›Ž‹ÏÏÊÈW
V×—Ï—ÏI	WJÊÎ—ÊÎ—Ê–×—Ï—ÏWJÊÎ—ÊWÊŠÎˆ–×ˆ—JˆŸ	Ö×‰×J‰ß×—ÉÈWJÊÏV×Ï—JJ_
ÏV×ËÏ—JJJJÊO×Ê—ÏÏ‹ËÜ™YYNˆL[œÚYNžÝYÎžÜ]\›Ž‹×ÏÖ×—Ï—×JËË[œÚYNžÜ[˜ÝX][ÛŽ‹×ÏËË˜[Y\ÜXÙN‹×–×—Ï—Î—JÎ‹ß_KœÜXÚX[X]ˆŽ–×K˜]‹]˜[YHŽžÜ]\›Ž‹ÏWÊŠÎˆ–×ˆ—JˆŸ	Ö×‰×J‰ß×—ÉÈWJÊKË[œÚYNžÜ[˜ÝX][ÛŽ–ÞÜ]\›Ž‹×KË[X\Î˜]‹Y\]X[ØKÜ]\›Ž‹×ŠÊŠVÈ‰×_È‰×IËÛÚØ™Z[™ˆLW__K[˜ÝX][ÛŽ‹×ÏÏ‹Ë˜]‹[˜[YHŽžÜ]\›Ž‹Ö×—Ï—×JËË[œÚYNžÛ˜[Y\ÜXÙN‹×–×—Ï—Î—JÎ‹ß___K[]N–ÞÜ]\›Ž‹É–×K^—^ÌKNËÚK[X\Î˜˜[YYY[]XKÉˆÞÖ×KY—^ÌKNËÚW_K‹›[™ÝXYÙ\Ë›X\šÝ\YËš[œÚYVØ]‹]˜[YXKš[œÚYK™[]O[‹›[™ÝXYÙ\Ë›X\šÝ\™[]K‹›[™ÝXYÙ\Ë›X\šÝ\™ØÝ\Kš[œÚYVØ[\›˜[\ÝXœÙ]Kš[œÚYO[‹›[™ÝXYÙ\Ë›X\šÝ\‹šÛÚÜË˜Y
Ü˜\[˜Ý[ÛŠJ^ÙK\OOOX[]X	‰ŠK˜]šX]\Ë]OYK˜ÛÛ[œ™\XÙJÉ˜[\ËË	˜
J_JKØš™XÝ™Yš[™T›Ü\J‹›[™ÝXYÙ\Ë›X\šÝ\YË˜Y[›[™Y‹Ý˜[YN™[˜Ý[ÛŠK
^Ý˜\ˆ^ßNÜ–Ø[™ÝXYÙKX
ÝO^Ü]\›Ž‹ÊWÐÑUWÊV×××JÏÊÏWWO‰
KÚKÛÚØ™Z[™ˆL[œÚYN›‹›[™ÝXYÙ\ÖÝ_K‹˜Ù]OK×WÐÑUWßWO‰ÚNÝ˜\ˆO^Èš[˜ÛYYXÙ]HŽžÜ]\›Ž‹ÏWÐÑUWÖ×××J×WO‹ÚK[œÚYNœŸ_NÚVØ[™ÝXYÙKX
ÝO^Ü]\›Ž‹Ö×××JËË[œÚYN›‹›[™ÝXYÙ\ÖÝ_NÝ˜\ˆO^ßNØVÙWO^Ü]\›Ž”™YÑ^

×Ö×—JŠJÎWÐÑUWÊÎ–×—W_JÈWOŠJJ—WOŸ
ÈOWÐÑUWÊV×××JJÊÏO××ÏŠXœ™\XÙJ××ËÙË[˜Ý[ÛŠ
^Ü™]\›ˆ_JKX
KÛÚØ™Z[™ˆLÜ™YYNˆL[œÚYNš_K‹›[™ÝXYÙ\Ëš[œÙ\™Y›Ü™JX\šÝ\Ù]XJ__JKØš™XÝ™Yš[™T›Ü\J‹›[™ÝXYÙ\Ë›X\šÝ\YË˜Y]šX]H‹Ý˜[YN™[˜Ý[ÛŠK
^Û‹›[™ÝXYÙ\Ë›X\šÝ\YËš[œÚYVØÜXÚX[X]˜Kœ\Ú
Ü]\›Ž”™YÑ^

ŸÈ‰××JJÎ˜
ÙJØ
WÊWÊŠÎˆ–×ˆ—JˆŸ	Ö×‰×J‰ß×—ÉÈWJÊÏV×Ï—JJXX
KÛÚØ™Z[™ˆL[œÚYNžÈ˜]‹[˜[YHŽ‹×–×—ÏWJËË˜]‹]˜[YHŽžÜ]\›Ž‹ÏV×××JËË[œÚYNžÝ˜[YNžÜ]\›Ž‹ÊWÊŠÈ‰×_
ÈVÈ‰×JJJWÖ×××JŠÏW‰
KËÛÚØ™Z[™ˆL[X\Î–Ý[™ÝXYÙKX
ÝK[œÚYN›‹›[™ÝXYÙ\ÖÝ_K[˜ÝX][ÛŽ–ÞÜ]\›Ž‹×KË[X\Î˜]‹Y\]X[ØKÈŸ	Ë×____J__JK‹›[™ÝXYÙ\Ëš[[‹›[™ÝXYÙ\Ë›X\šÝ\‹›[™ÝXYÙ\Ë›X][[‹›[™ÝXYÙ\Ë›X\šÝ\‹›[™ÝXYÙ\ËœÝ™Ï[‹›[™ÝXYÙ\Ë›X\šÝ\‹›[™ÝXYÙ\Ëž[[‹›[™ÝXYÙ\Ë™^[™
X\šÝ\ßJK‹›[™ÝXYÙ\ËœÜÛ[[‹›[™ÝXYÙ\Ëž[‹›[™ÝXYÙ\Ë˜]ÛO[‹›[™ÝXYÙ\Ëž[‹›[™ÝXYÙ\ËœœÜÏ[‹›[™ÝXYÙ\Ëž[
[˜Ý[ÛŠJ^Ý˜\ˆKÊÎˆŠÎ—
Î——Ÿ×××J_×ˆ———JJˆŸ	ÊÎ—
Î——Ÿ×××J_×‰×——JJ‰ÊKÎÙK›[™ÝXYÙ\Ë˜ÜÜÏ^ØÛÛ[Y[‹××
–×××J×
—ËË][NžÜ]\›Ž”™YÑ^
×ËWJÎ–×ŽÞ×È‰×_ÊÊÈWÊ_
ÝœÛÝ\˜ÙJØ
JÊÎŽß
ÏWÊ—ÊJX
K[œÚYNžÜ[N‹××ËWJËËœÙ[XÝÜ‹Y[˜Ý[Û‹X\™Ý[Y[ŽžÜ]\›Ž‹ÊœÙ[XÝÜ—Ê—
ÊŠÈV×ÊWJJJÎ–×Š
W×_ÊÊÈV×ÊWJ_

Î–×Š
W_
×Š
WJ—
JJ—
JJÊÏWÊ—
JKËÛÚØ™Z[™ˆL[X\Î˜Ù[XÝÜ˜KÙ^]ÛÜ™žÜ]\›Ž‹ÊŸ×—ËWJJÎ˜[™›ÝÛ›_ÜŠJÈV×ËWJKËÛÚØ™Z[™ˆL__K\›žÜ]\›Ž”™YÑ^
\›

Î˜
ÝœÛÝ\˜ÙJØ
Î–×——Š
H‰×_×××JJŠW
XX
KÜ™YYNˆL[œÚYNžÙ[˜Ý[ÛŽ‹×\›ÚK[˜ÝX][ÛŽ‹×—

IËÝš[™ÎžÜ]\›Ž”™YÑ^
˜
ÝœÛÝ\˜ÙJØ	
K[X\Î˜\›__KÙ[XÝÜŽžÜ]\›Ž”™YÑ^

ŸÞßW×JV×žßW×JÎ–×žßNÈ‰××_ÊÊÈV×Þ×J_
ÝœÛÝ\˜ÙJØ
JŠÏWÊ—ÊX
KÛÚØ™Z[™ˆLKÝš[™ÎžÜ]\›ŽÜ™YYNˆLK›Ü\NžÜ]\›Ž‹ÊŸ×‹W×LWQ‘‘‘—JJÈWÊVËWØK^—LWQ‘‘‘—JÎŠÈWÊVËW×LWQ‘‘‘—JJŠÏWÊŽŠKÚKÛÚØ™Z[™ˆLK[\Ü[‹ÈZ[\Ü[‹ÚK[˜Ý[ÛŽžÜ]\›Ž‹ÊŸ×‹XK^ŒNWJVËXK^ŒNWJÊÏW

KÚKÛÚØ™Z[™ˆLK[˜ÝX][ÛŽ‹ÖÊ
^ßNÎ‹KßKK›[™ÝXYÙ\Ë˜ÜÜË˜][Kš[œÚYKœ™\ÝYK›[™ÝXYÙ\Ë˜ÜÜÎÝ˜\ˆYK›[™ÝXYÙ\Ë›X\šÝ\Û‰‰Š‹YË˜Y[›[™Y
Ý[XÜÜØ
K‹YË˜Y]šX]JÝ[XÜÜØ
J_JJŠK‹›[™ÝXYÙ\Ë˜ÛZÙO^ØÛÛ[Y[–ÞÜ]\›Ž‹ÊŸ×—JW×
–×××JÊÎ—
—ß	
KËÛÚØ™Z[™ˆLÜ™YYNˆLKÜ]\›Ž‹ÊŸ×——JW×ËŠ‹ËÛÚØ™Z[™ˆLÜ™YYNˆLWKÝš[™ÎžÜ]\›Ž‹ÊÈ‰×JJÎ—
Î——Ÿ×××J_
ÈWJV×———JJ—KËÜ™YYNˆLK˜Û\ÜË[˜[YHŽžÜ]\›Ž‹ÊŠÎ˜Û\Üß^[™ß[\[Y[ß[œÝ[˜Ù[ÙŸ[\™˜XÙ_™]ß˜Z]
WÊß˜Ø]ÚÊ×

V×Ë—JËÚKÛÚØ™Z[™ˆL[œÚYNžÜ[˜ÝX][ÛŽ‹ÖË—Kß_KÙ^]ÛÜ™‹×ŠÎ˜œ™XZßØ]ÚÛÛ[Y_ß[Ù_š[˜[_›ÜŸ[˜Ý[ÛŸYŸ[Ÿ[œÝ[˜Ù[ÙŸ™]ß[™]\›Ÿ›Ýßž_Ú[JW‹Ë›ÛÛX[Ž‹×ŠÎ™˜[Ù_YJW‹Ë[˜Ý[ÛŽ‹×—ÊÊÏW

KË[X™\Ž‹×Œ×KY—J×Ÿ
Î——
ÊÎ——
ŠOß——
ÊJÎ™VÊËWO×
ÊOËÚKÜ\˜]ÜŽ‹ÖÏ—OOßÈOWOOÏOßKOß
×
Ïß	‰ßßÏÊ‹ß—‰WKË[˜ÝX][ÛŽ‹ÖÞßV×NÊ
KŽ—KßK‹›[™ÝXYÙ\Ëš˜]˜\ØÜš\[‹›[™ÝXYÙ\Ë™^[™
ÛZÙXÈ˜Û\ÜË[˜[YHŽ–Û‹›[™ÝXYÙ\Ë˜ÛZÙVØÛ\ÜË[˜[YXKÜ]\›Ž‹ÊŸ×‰×LWQ‘‘‘—JJÈWÊV×ÉKV—LWQ‘‘‘—JÎŠÈWÊVÉ×LWQ‘‘‘—JJŠÏWŠÎ˜ÛÛœÝXÝÜŸ›ÝÝ\JJKËÛÚØ™Z[™ˆLWKÙ^]ÛÜ™–ÞÜ]\›Ž‹Ê
Î—ŸJWÊŠXØ]Ú‹ËÛÚØ™Z[™ˆLKÜ]\›Ž‹ÊŸ×‹—_———ÊŠWŠÎ˜\ß\ÜÙ\
ÏWÊ—Ê_\Þ[˜ÊÏWÊŠÎ™[˜Ý[Û—Ÿ
É×LWQ‘‘‘—_	
J_]ØZ]œ™XZßØ\Ù_Û\ÜßÛÛœÝÛÛ[Y_XYÙÙ\ŸY˜][[]_ß[Ù_[[_^Ü^[™ßš[˜[JÏWÊŠÎ—ß	
J_›ÜŸœ›ÛJÏWÊŠÎ–ÉÈ—_	
J_[˜Ý[ÛŸ
Î™Ù]Ù]
JÏWÊŠÎ–È×É×LWQ‘‘‘—_	
J_YŸ[\[Y[ß[\Ü[Ÿ[œÝ[˜Ù[ÙŸ[\™˜XÙ_]™]ß[ÙŸXÚØYÙ_š]˜]_›ÝXÝYX›Xß™]\›ŸÝ]XßÝ\\ŸÝÚ]Ú\ß›Ýßž_\[ÙŸ[™Yš[™Y˜\Ÿ›ÚYÚ[_Ú]ZY[
W‹ËÛÚØ™Z[™ˆLWK[˜Ý[ÛŽ‹ÈÏÊÈWÊV×ÉK^KV—LWQ‘‘‘—JÎŠÈWÊVÉ×LWQ‘‘‘—JJŠÏWÊŠÎ——ÊŠÎ˜\_š[™Ø[
WÊŠO×

KË[X™\ŽžÜ]\›Ž”™YÑ^

Ÿ×—ÉJJÎ“˜SŸ[™š[š]_Ø—VÌWJÊÎ—ÖÌWJÊJ›ßÛÓ×VÌM×JÊÎ—ÖÌM×JÊJ›ßÞV×KQ˜KY—JÊÎ—Ö×KQ˜KY—JÊJ›ß
ÊÎ—×
ÊJ›Ÿ
Î—
ÊÎ—×
ÊJŠÎ—ŠÎ—
ÊÎ—×
ÊJŠOÊOß—
ÊÎ—×
ÊJŠJÎ–ÑYWVÊËWO×
ÊÎ—×
ÊJŠOÊJÈV×ÉJX
KÛÚØ™Z[™ˆLKÜ\˜]ÜŽ‹ËK_
×
ß
—
OßOŸ	‰OßOßÈOWOO_OßÏOßËJÊ‹ÉIŸˆOO—OOßžÌß_×ÏOß×ßßŽ—KßJK‹›[™ÝXYÙ\Ëš˜]˜\ØÜš\ØÛ\ÜË[˜[YXVÌKœ]\›KÊŠÎ˜Û\Üß^[™ß[\[Y[ß[œÝ[˜Ù[ÙŸ[\™˜XÙ_™]ÊWÊÊV×Ë—JËË‹›[™ÝXYÙ\Ëš[œÙ\™Y›Ü™J˜]˜\ØÜš\Ù^]ÛÜ™Ü™YÙ^žÜ]\›Ž”™YÑ^


Î—Ÿ×‰×LWQ‘‘‘‹ˆ‰×JW×_ŠÎœ™]\›ŸZY[
JWÊŠWÊÎŠÎ—ÊÎ–×—W——_ŠJ—_Ÿ×‹××——JJ×ÖÙÚ[^]\×^Ìß_
Î—ÊÎ–×–×W——_ŸÊÎ–×–×W——_ŸÊÎ–×–×W——_ŠJ—JJ—JJ—_Ÿ×‹××——JJ×ÖÙÚ[^]\×^Ìß]–ÙÚ[^]\×^ÌßJJÏJÎ—ß×
ŠÎ–×Š—_
ŠÈWÊJJ—
—ÊJŠÎ‰×—‹ŽÎŸJWW_×ÊJX
KÛÚØ™Z[™ˆLÜ™YYNˆL[œÚYNžÈœ™YÙ^\ÛÝ\˜ÙHŽžÜ]\›Ž‹×ŠÊV×××JÊÏWÖØK^—J‰
KËÛÚØ™Z[™ˆL[X\Î˜[™ÝXYÙK\™YÙ^[œÚYN›‹›[™ÝXYÙ\Ëœ™YÙ^Kœ™YÙ^Y[[Z]\ˆŽ‹×—ßÉËœ™YÙ^Y›YÜÈŽ‹×–ØK^—JÉß_K™[˜Ý[Û‹]˜\šXX›HŽžÜ]\›Ž‹ÈÏÊÈWÊV×ÉK^KV—LWQ‘‘‘—JÎŠÈWÊVÉ×LWQ‘‘‘—JJŠÏWÊ–ÏN—WÊŠÎ˜\Þ[˜×ÊŠOÊÎ—™[˜Ý[Û—Ÿ
Î—

Î–×Š
W_
×Š
WJ—
JJ—
_
ÈWÊV×ÉK^KV—LWQ‘‘‘—JÎŠÈWÊVÉ×LWQ‘‘‘—JJŠWÊOŠJKË[X\Î˜[˜Ý[Û˜K\˜[Y]\Ž–ÞÜ]\›Ž‹Ê[˜Ý[ÛŠÎ—ÊÊÈWÊV×ÉK^KV—LWQ‘‘‘—JÎŠÈWÊVÉ×LWQ‘‘‘—JJŠO×Ê—
ÊŠJÈWÊJÎ–×Š
W×_ÊÊÈV×ÊWJ_
×Š
WJ—
JJÊÏWÊ—
JKËÛÚØ™Z[™ˆL[œÚYN›‹›[™ÝXYÙ\Ëš˜]˜\ØÜš\KÜ]\›Ž‹ÊŸ×‰×LWQ‘‘‘—JJÈWÊV×ÉK^—LWQ‘‘‘—JÎŠÈWÊVÉ×LWQ‘‘‘—JJŠÏWÊOŠKÚKÛÚØ™Z[™ˆL[œÚYN›‹›[™ÝXYÙ\Ëš˜]˜\ØÜš\KÜ]\›Ž‹Ê
ÊŠJÈWÊJÎ–×Š
W×_ÊÊÈV×ÊWJ_
×Š
WJ—
JJÊÏWÊ—
WÊOŠKËÛÚØ™Z[™ˆL[œÚYN›‹›[™ÝXYÙ\Ëš˜]˜\ØÜš\KÜ]\›Ž‹Ê
Î—ŸßŠJÈJÎ˜\ß\Þ[˜ß]ØZ]œ™XZßØ\Ù_Ø]ÚÛ\ÜßÛÛœÝÛÛ[Y_XYÙÙ\ŸY˜][[]_ß[Ù_[[_^Ü^[™ßš[˜[_›ÜŸœ›Û_[˜Ý[ÛŸÙ]YŸ[\[Y[ß[\Ü[Ÿ[œÝ[˜Ù[ÙŸ[\™˜XÙ_]™]ß[ÙŸXÚØYÙ_š]˜]_›ÝXÝYX›Xß™]\›ŸÙ]Ý]XßÝ\\ŸÝÚ]Ú\ß›Ýßž_\[ÙŸ[™Yš[™Y˜\Ÿ›ÚYÚ[_Ú]ZY[
JÈVÉ×LWQ‘‘‘—JJJÎŠÈWÊV×ÉK^KV—LWQ‘‘‘—JÎŠÈWÊVÉ×LWQ‘‘‘—JJ—ÊŠW
ÊŸWÊ—
ÊŠJÈWÊJÎ–×Š
W×_ÊÊÈV×ÊWJ_
×Š
WJ—
JJÊÏWÊ—
WÊ—ÊKËÛÚØ™Z[™ˆL[œÚYN›‹›[™ÝXYÙ\Ëš˜]˜\ØÜš\WKÛÛœÝ[‹×–ÐKV—JÎ–ÐKV—×_ÊJ—‹ßJK‹›[™ÝXYÙ\Ëš[œÙ\™Y›Ü™J˜]˜\ØÜš\Ýš[™ØÚ\Ú˜[™ÎžÜ]\›Ž‹×ˆÈKŠ‹ËÜ™YYNˆL[X\Î˜ÛÛ[Y[K[\]K\Ýš[™ÈŽžÜ]\›Ž‹Ø
Î—×××_	ÊÎ–×žßW_ÊÎ–×žßW_Ö×ŸWJ—JJ—JJ×_
ÈW	ÊV×—JJ˜ËÜ™YYNˆL[œÚYNžÈ[\]K\[˜ÝX][ÛˆŽžÜ]\›Ž‹×˜	Ë[X\Î˜Ýš[™ØK[\œÛ][ÛŽžÜ]\›Ž‹Ê
Î—Ÿ×—JJÎ—ÌŸJJŠW	ÊÎ–×žßW_ÊÎ–×žßW_Ö×ŸWJ—JJ—JJ×KËÛÚØ™Z[™ˆL[œÚYNžÈš[\œÛ][Û‹\[˜ÝX][ÛˆŽžÜ]\›Ž‹×—	ßIË[X\Î˜[˜ÝX][Û˜K™\Ý›‹›[™ÝXYÙ\Ëš˜]˜\ØÜš\_KÝš[™Î‹Ö×××JËß_KœÝš[™Ë\›Ü\HŽžÜ]\›Ž‹Ê
Î—ŸË×JVÈJŠJÈ‰×JJÎ—
Î——Ÿ×××J_
ÈWŠV×———JJ—ŠÏWÊŽŠKÛKÛÚØ™Z[™ˆLÜ™YYNˆL[X\Î˜›Ü\X_JK‹›[™ÝXYÙ\Ëš[œÙ\™Y›Ü™J˜]˜\ØÜš\Ü\˜]Ü˜È›]\˜[\›Ü\HŽžÜ]\›Ž‹Ê
Î—ŸË×JVÈJŠJÈWÊV×ÉK^KV—LWQ‘‘‘—JÎŠÈWÊVÉ×LWQ‘‘‘—JJŠÏWÊŽŠKÛKÛÚØ™Z[™ˆL[X\Î˜›Ü\X_JK‹›[™ÝXYÙ\Ë›X\šÝ\	‰Š‹›[™ÝXYÙ\Ë›X\šÝ\YË˜Y[›[™Y
ØÜš\˜]˜\ØÜš\
K‹›[™ÝXYÙ\Ë›X\šÝ\YË˜Y]šX]JÛŠÎ˜X›Ü›\ŸÚ[™Ù_ÛXÚßÛÛ\ÜÚ][ÛŠÎ™[™Ý\\]J_›ÛXÚß\œ›ÜŸ›ØÝ\ÊÎš[ŸÝ]
OßÙ^JÎ™ÝÛŸ\
_ØY[Ý\ÙJÎ™ÝÛŸ[\ŸX]™_[Ý™_Ý]Ý™\Ÿ\
_™\Ù]™\Ú^™_ØÜ›ÛÙ[XÝÛÝÚ[™Ù_ÝX›Z][›ØYÚY[
X˜]˜\ØÜš\
JK‹›[™ÝXYÙ\ËšœÏ[‹›[™ÝXYÙ\Ëš˜]˜\ØÜš\
[˜Ý[ÛŠ
^ÚYŠOO]›ÚY\[ÙˆØÝ[Y[˜X
\™]\›ŽÑ[[Y[œ›ÝÝ\K›X]Ú\ß
[[Y[œ›ÝÝ\K›X]Ú\ÏQ[[Y[œ›ÝÝ\K›\ÓX]Ú\ÔÙ[XÝÜŸ[[Y[œ›ÝÝ\KÙXšÚ]X]Ú\ÔÙ[XÝÜŠNÝ˜\ˆOXØY[™ø )˜Y[˜Ý[ÛŠK
^Ü™]\›˜8§%ˆ\œ›Üˆ
ÙJØÚ[H™]Ú[™Èš[Nˆ
ÝKX8§%ˆ\œ›ÜŽˆš[HÙ\È›Ý^\ÝÜˆ\È[\XO^ÚœÎ˜˜]˜\ØÜš\N˜]Û˜˜Ž˜XžXÌN˜ÝÙ\œÚ[ÛLN˜ÝÙ\œÚ[Ú˜˜\Ú˜]˜˜]Ú˜Ø^˜]^KOX]K\Ü˜Ë\Ý]\ØÏXØY[™ØÏXØYYX˜Z[YOX™VÙ]K\Ü˜×N››Ý
Ø
ØJØH˜
ÜÊØ—JN››Ý
Ø
ØJØH˜
ÛÊØ—JXÙ[˜Ý[Ûˆ
K‹J^Ý˜\ˆO[™]ÈS™\]Y\ÝØK›Ü[ŠÑUKL
KK›Ûœ™XY\Ý]XÚ[™ÙOY[˜Ý[ÛŠ
^ØKœ™XYTÝ]OOM	‰ŠKœÝ]\Ï	‰˜Kœ™\ÜÛœÙU^ÛŠKœ™\ÜÛœÙU^
N˜KœÝ]\ÏMÚJ
KœÝ]\ËKœÝ]\Õ^
JNšJŠJ_KKœÙ[™
[
_Y[˜Ý[ÛˆŠJ^Ý˜\ˆK×—ÊŠ
ÊWÊŠÎŠ
WÊŠÎŠ
ÊWÊŠOÊOÉË™^XÊ_
NÚYŠ
^Ý˜\ˆS[X™\ŠÌWJK]Ì—KO]Ì×NÜ™]\›ˆÚOÖÛ‹[X™\ŠJWN–Û‹›ÚYN–Û‹—__[‹šÛÚÜË˜Y
™Y›Ü™KZYÚYÚ[[˜Ý[ÛŠJ^ÙKœÙ[XÝÜŠÏX
Ý_JK‹šÛÚÜË˜Y
™Y›Ü™K\Ø[š]KXÚXÚØ[˜Ý[ÛŠ
^Ý˜\ˆ]™[[Y[ÚYŠ‹›X]Ú\ÊJJ^Ý˜ÛÙOX‹œÙ]]šX]JKÊNÝ˜\ˆ\‹˜\[™Ú[
ØÝ[Y[˜Ü™X]Q[[Y[
ÓÑX
JNÜ^ÛÛ[YNÝ˜\ˆO\‹™Ù]]šX]J]K\Ü˜Ø
K]›[™ÝXYÙNÚYŠOOX›Û™X
^Ý˜\ˆÏJ×ŠÊÊIË™^XÊJ_Ë›Û™XJVÌWNÚZVÙ×_ß[‹][œÙ][™ÝXYÙJ
K‹][œÙ][™ÝXYÙJ‹
NÝ˜\ˆÏ[‹œYÚ[œË˜]]ÛØY\Ž×É‰—Ë›ØY[™ÝXYÙ\Ê
K
K[˜Ý[ÛŠJ^Ü‹œÙ]]šX]JKÊNÝ˜\ˆYŠ‹™Ù]]šX]J]K\˜[™ÙX
JNÚYŠ
^Ý˜\ˆOYKœÜ]
×—ß‹ÙÊKÏ]ÌK]ÌWOO[[ÚK›[™ÝÌWNÛÏ	‰ŠÊÏZK›[™Ý
KÏSX]›X^
X]›Z[ŠËLKK›[™Ý
JK	‰Š
ÏZK›[™Ý
KSX]›X^
X]›Z[ŠK›[™Ý
JKOZKœÛXÙJË
Kš›Ú[Š˜
K‹š\Ð]šX]J]K\Ý\
_‹œÙ]]šX]J]K\Ý\Ýš[™ÊÊÌJJ_\^ÛÛ[YK‹šYÚYÚ[[Y[

_K[˜Ý[ÛŠJ^Ü‹œÙ]]šX]JK
K^ÛÛ[Y_J__JK‹œYÚ[œË™š[RYÚYÚ^ÚYÚYÚ™[˜Ý[ÛŠJ^Ù›ÜŠ˜\ˆJ_ØÝ[Y[
Kœ]Y\žTÙ[XÝÜ[
JKLNÚO]ÜŠÊ×NÊ[‹šYÚYÚ[[Y[
J__NÝ˜\ˆHLNÛ‹™š[RYÚYÚY[˜Ý[ÛŠ
^ÜJÛÛœÛÛKØ\›Š”š\ÛK™š[RYÚYÚ\È\™XØ]Yˆ\ÙHš\ÛKœYÚ[œË™š[RYÚYÚšYÚYÚ[œÝXYˆŠKL
K‹œYÚ[œË™š[RYÚYÚšYÚYÚ˜\J\Ë\™Ý[Y[Ê__JJ
_JJJ
KJNÊ[˜Ý[ÛŠJ^Ý˜\ˆXŠÎTÒTÒÔßTÒÐSPTÑTßTÒÐT‘ÐßTÒÐT‘ÕŸTÒÐÓQßTÒÐÓÓTUSÓ—ÐÓÓTUÑTŸTÒÓS‘S“ßTÒÔ‘SPUÒTÒÔÓÕTÑ_TÒÕ‘T”ÒS‘“ßTÒÕ‘T”ÒSÓŸÓÓÔ•T“_ÓÓSS”ßÓÓTÕÓÔ‘”‘PRÔß•T×ÔÑTÔÒSÓ—Ð•T×ÐQ‘TÔßQUS×ÔUTÒÕÔÔÑTÔÒSÓŸT”ÕPÒßTÔV_URQÑTÑTÔÒSÓŸÑWÓS‘ßÓ“ÓQWÒÑVT’S‘×ÐÓÓ•“ÓÓ“ÓQWÒÑVT’S‘×ÔQÔ×ÐQÑS•ÒS‘“ßÔ“ÕTßTÕÓÓ•“ÓTÕ’S_TÕ’STÒV‘_TÕÒV‘_ÓQ_ÔÕSQ_ÔÕT_Q”ßS”ÕSÑ_“ÐŸS‘ßS‘ÕPQÑ_×ÐQ‘TÔß×ÐS×ÒQS•Q’PÐUSÓŸ×ÓQPTÕT‘SQS•×ÓSÓ‘UT–_×ÓSQ_×Ó•SQT’Pß×ÔTTŸ×ÕSTÓ‘_×ÕSQ_TÔÐÓÔÑ_TÔÓÔSŸS‘TßÑÓSQ_×ÐÓÓÔ”ßPPÒT_PRSÒPÒßPS‘UÔ–WÔU“×ÐUÐ”’QÑ_ÓÑÔT”ŸÔS‘Ô’UÔÓÐÒÑUTŸÔÕT_TT”ÒV‘_UTTÕUTßQÌ_ÌŸÌßÍÑS‘Ó_‘T_ÑPÓÓ‘ßÑSS•VÒS’UÑTÔÒSÓŸÑTÔÒSÓ•T_ÑTÔÒSÓ—ÓPSQÑTŸÒSÒSÔßÒ“ÔÒÐUUÔÓÐÒßT“_RQTÕT•ÑU‘S•ßTÕT•ÒS”ÕSÑ_TÕT•Ò“ÐŸTÕT•ÔÑTÔÒSÓŸTÑTŸÒS‘ÕÒQUUÔ’U_×ÐÓÓ‘’Q×ÑT”ß×ÐÕT”‘S•ÑTÒÕÔ×ÑUWÑT”ß×ÑÔ‘QUT—ÑUWÑTŸ×ÓQS•WÔ‘Q’V×Ô•S•SQWÑTŸ×ÔÑPU×ÔÑPUÔU×ÔÑTÔÒSÓ—ÑTÒÕÔ×ÔÑTÔÒSÓ—ÒQ×ÔÑTÔÒSÓ—ÔU×ÔÑTÔÒSÓ—ÕT_×Õ•”ŸSÑQ’QT”ÊW˜^Ü]\›Ž‹ÊŠÈ‰×OÊWÊ×ŠVÈJ×ËŠ‹ËÛÚØ™Z[™ˆL[X\Î˜[˜ÝX][Û˜[œÚYN›[K^Ø˜\Ú›‹[š\›Û›Y[žÜ]\›Ž”™YÑ^
	
Ý
K[X\Î˜ÛÛœÝ[K˜\šXX›N–ÞÜ]\›Ž‹×	×

×××JÏ×
W
KËÜ™YYNˆL[œÚYNžÝ˜\šXX›N–ÞÜ]\›Ž‹Ê—	

×××JÊW
W
KËÛÚØ™Z[™ˆLK×—	

×K[X™\Ž‹×Œ×KQ˜KY—J×Ÿ
Î——
ÊÎ——
ŠOß——
ÊJÎ–ÑYWKO×
ÊOËËÜ\˜]ÜŽ‹ËK_
×
ß
—
OßOßOß	‰ŸÏHJ×J‹ÉO—‰ŸOOßÏßŽ—KË[˜ÝX][ÛŽ‹×

ß
W
OßËß_KÜ]\›Ž‹×	

Î—
×ŠWJ×
_×Š
WJJ×
_×˜JØËÜ™YYNˆL[œÚYNžÝ˜\šXX›N‹×—	
˜
I	ß_KÜ]\›Ž‹×	Ö×ŸWJ×KËÜ™YYNˆL[œÚYNžÛÜ\˜]ÜŽ‹Î–ËOOÊ×OßÈW×_ÈÏß	IOß—ßËË[˜ÝX][ÛŽ‹Ö××WKË[š\›Û›Y[žÜ]\›Ž”™YÑ^

ÊX
Ý
KÛÚØ™Z[™ˆL[X\Î˜ÛÛœÝ[__K×	
Î—ÊßÈÏÊˆP	JK×K[]N‹×
Î–ØX˜ÙQY›œ——_ÏÖÌM×^ÌKß_VÌNXKYKQ—^Î_VÌNXKYKQ—^Í_ÌNXKYKQ—^ÌKŸJKßNÙK›[™ÝXYÙ\Ë˜˜\Ú^ÜÚX˜[™ÎžÜ]\›Ž‹×ˆÈWÊ—ËŠ‹Ë[X\Î˜[\Ü[KÛÛ[Y[žÜ]\›Ž‹ÊŸ×ˆž×	JHËŠ‹ËÛÚØ™Z[™ˆLK™[˜Ý[Û‹[˜[YHŽ–ÞÜ]\›Ž‹Ê™[˜Ý[Û—ÊÊV×ËWJÊÏJÎ—Ê—
Î—Ê—
JO×Ê—ÊKËÛÚØ™Z[™ˆL[X\Î˜[˜Ý[Û˜KÜ]\›Ž‹×–×ËWJÊÏWÊ—
Ê—
WÊ—ÊKË[X\Î˜[˜Ý[Û˜WK™›Ü‹[Ü‹\Ù[XÝŽžÜ]\›Ž‹ÊŠÎ™›ÜŸÙ[XÝ
WÊÊWÊÊÏWÊÚ[—ÊKË[X\Î˜˜\šXX›XÛÚØ™Z[™ˆLK˜\ÜÚYÛ‹[YŽžÜ]\›Ž‹ÊŸ×Îß	—_Ï—W

WÊÊÎ——ÊÊJŠÏW
ÏÏJKË[œÚYNžÙ[š\›Û›Y[žÜ]\›Ž”™YÑ^

Ÿ×Îß	—_Ï—W

X
Ý
KÛÚØ™Z[™ˆL[X\Î˜ÛÛœÝ[_K[X\Î˜˜\šXX›XÛÚØ™Z[™ˆLK\˜[Y]\ŽžÜ]\›Ž‹ÊŸÊK^ÌKŸJÎ—ÊÎ–ÊËWOÊO×ÊÊÎ——ÊÊJŠÏVÏW×_	
KË[X\Î˜˜\šXX›XÛÚØ™Z[™ˆLKÝš[™Î–ÞÜ]\›Ž‹Ê
Î—Ÿ×JOO×ÊŠJÊÊWÖ×××JÊÎ—×ŸŠW‹ËÛÚØ™Z[™ˆLÜ™YYNˆL[œÚYNœŸKÜ]\›Ž‹Ê
Î—Ÿ×JOO×ÊŠJÈ‰×JJÊÊW—Ö×××JÊÎ—×ŸŠWËËÛÚØ™Z[™ˆLÜ™YYNˆL[œÚYNžØ˜\Ú›Ÿ_KÜ]\›Ž‹ÊŸ×—JÎ—
JŠHŠÎ—×××_	
×ŠWJ×
_	
ÈW

_×˜JØ×ˆ—	JJˆ‹ËÛÚØ™Z[™ˆLÜ™YYNˆL[œÚYNœŸKÜ]\›Ž‹ÊŸ×‰JIÖ×‰×J‰ËËÛÚØ™Z[™ˆLÜ™YYNˆLKÜ]\›Ž‹×		ÊÎ–×‰×_×××JJ‰ËËÜ™YYNˆL[œÚYNžÙ[]Nœ‹™[]__WK[š\›Û›Y[žÜ]\›Ž”™YÑ^
	Ø
Ý
K[X\Î˜ÛÛœÝ[K˜\šXX›Nœ‹˜\šXX›K[˜Ý[ÛŽžÜ]\›Ž‹ÊŸ×Îß	—_Ï—W

JÎ˜Y\›ÜÜß\\XØXÚ_\YÙ]\]Y_\Ü[]]Û^\Ü[˜XÚÝ\]Úß˜\Ù[˜[Y_˜\Ú˜ß˜ÛÛœÛÛ_™ßžš\ŸØ[Ø\™ÛßØ]Ù™\ÚßÚÜœÚØÛÛ™šYßÚ[ÙÚÝÛŸÚ›ÛÝÚÜÝ[_ÛX\ŸÛ\ÛÛ[[ŸÛÛ[_ÛÛ\ÜÙ\ŸÜÜ›ÛŸÜ›ÛXŸÜÜ]Ý\›Ý]]_ß™\ØÝY_X›ÛÝÝ˜\ŸY™ŸY™ŒßYß\Ÿ\˜ÛÛÜœß\›˜[Y_\œßY\ÙßØÚÙ\ŸØÚÙ\‹XÛÛ\ÜÙ__YÜ™\Z™XÝ[Ÿ]ÛÛ^[™^XÝ^Ÿ™›Ü›X]™\Úß™ß™Ü™\š[_š[™›]›Û›Ü›X]œ™Y_œØÚß\Ù\ŸØ]ÚßÚ]Ü\YÜ™\Ü›Ý\YÜ›Ý\[Ü›Ý\[ÙÜ›Ý\ßÜX‹[ZØÛÛ™šYßÞš\[XYß\ÝÜž_ÜÝÜÝ˜[Y_ÜXÛÛŸYY˜ÛÛ™šYßY™ÝÛŸY\[\Ü[œÝ[\˜]˜_›Øœß›Ú[ŸÚ[Ú[[\Üß[šßŸØØ]_ÙÛ˜[Y_ÙÜ›Ý]_ÛÚßßŸš[š[š[_›_ßÛÙŸ[žXZÙ_X[ŸXßYY_ZØÛÛ™šYßZÙ\ŸZÙL™œßZÙšY›ßZÙœßZÚ\ÛÙœßZÛ›ÙZÜÝØ\[]Ÿ[Ü™_[ÜÝ[Ý[]ÛÛß]Ÿ]]]Ÿ˜[›ß˜ß™]Ý]šXÙ_››Ù_›Ú\›ÝYžK\Ù[™œ_œÛÛÚÝ\ÜÜ[Ÿ\Y\ÜÝÙ\Ý_]Úß[™ßÚ[œ_ÙX[ŸÙX[‹XÛÛ\ÜÙ_ÜŸš[Ø\š[[Ÿß\ÚŸ][Ý_][ÝXÚXÚß][ÝXÝ˜[_˜\Ÿ˜Ü™X›ÛÝ™[\Þ[˜ß™[˜[Y_™[šXÙ_™]Ÿ›_›Y\Ÿœ_œÞ[˜ßØÜØÜ™Y[ŸÙY™ŸÙYÙ[™XZ[Ù\_Ù\šXÙ_ÙÚÚ[ÚXÚßÚYŸÚ]ÝÛŸÛY\ÛØØ]_ÛÜÜ]ÜÚÝ]Ý˜XÙ_Ý_ÝYßÝ[_Ý\Ü[™ÝØ\ÛŸÞ[˜ßÞ\ØÝXßZ[\ŸY_[Y_[Y[Ý]ÜÝXÚŸ˜XÙ\›Ý]_ÛÜ_[[Ý[[˜[Y_[™^[™[š\_[š]ß[œ˜\Ÿ[œÚ\Ÿ[žš\\]KYÜXŸ\[Y_\Ù\˜Y\Ù\™[\Ù\›[Ù\Ù\œß]YXÛÙ_]Y[˜ÛÙ_Ÿ˜ÜÙß™\Ÿš_š[_š\œÚ›\Ý]ØZ]Ø]ÚØßÙÙ]Ú\™Z\ßÚXÚÚßÚØ[Z_Üš]_\™ÜßË[Ü[ŸX\›ŸY\ß™[š]_š\œÚž\\ŠJÏIÊWÎß	—JKËÛÚØ™Z[™ˆLKÙ^]ÛÜ™žÜ]\›Ž‹ÊŸ×Îß	—_Ï—W

JÎ˜Ø\Ù_ßÛ™_[YŸ[Ù_\ØXßš_›ÜŸ[˜Ý[ÛŸYŸ[ŸÙ[XÝ[Ÿ[[Ú[JJÏIÊWÎß	—JKËÛÚØ™Z[™ˆLKZ[[ŽžÜ]\›Ž‹ÊŸ×Îß	—_Ï—W

JÎ—ŸŸ[X\ßš[™œ™XZßZ[[ŸØ[\ŸÙÛÛ[X[™ÛÛ[Y_XÛ\™_XÚß[˜X›_]˜[^Xß^]^ÜÙ]Üß\Ú[]ØØ[ÙÛÝ]X\š[_š[ŸÙ™XY™XY\œ˜^_™XYÛ›_™]\›ŸÙ]ÚYÚÜÛÝ\˜Ù_\Ý[Y\ß˜\\_\\Ù][[Z][X\Úß[˜[X\ß[œÙ]
JÏIÊWÎß	—JKËÛÚØ™Z[™ˆL[X\Î˜Û\ÜË[˜[YXK›ÛÛX[ŽžÜ]\›Ž‹ÊŸ×Îß	—_Ï—W

JÎ™˜[Ù_YJJÏIÊWÎß	—JKËÛÚØ™Z[™ˆLK™š[KY\ØÜš\ÜˆŽžÜ]\›Ž‹×‰—‹Ë[X\Î˜[\Ü[KÜ\˜]ÜŽžÜ]\›Ž‹×ÏŸ—
Ï_VÏ_—OßOOßÏWOßÉ—OÏŸÏ—IßÏ—VÉWOß	–Ï‰—OßÉŸOËË[œÚYNžÈ™š[KY\ØÜš\ÜˆŽžÜ]\›Ž‹×—Ë[X\Î˜[\Ü[__K[˜ÝX][ÛŽ‹×	×

ß
W
Oß—ŸÞßV×N×KË[X™\ŽžÜ]\›Ž‹ÊŸÊJÎ–ÌKNWW
Ÿ
JÎ–Ë‹W
ÊO×‹ËÛÚØ™Z[™ˆL_K‹š[œÚYOYK›[™ÝXYÙ\Ë˜˜\ÚÙ›ÜŠ˜\ˆOVØÛÛ[Y[[˜Ý[Û‹[˜[YX›Ü‹[Ü‹\Ù[XÝ\ÜÚYÛ‹[Y\˜[Y]\˜Ýš[™Ø[š\›Û›Y[[˜Ý[Û˜Ù^]ÛÜ™Z[[˜›ÛÛX[˜š[KY\ØÜš\Ü˜Ü\˜]Ü˜[˜ÝX][Û˜[X™\˜KO\‹˜\šXX›VÌWKš[œÚYKÏLÛÏK›[™ÝÛÊÊÊXVÚVÛ×WOYK›[™ÝXYÙ\Ë˜˜\ÚÚVÛ×WNÙK›[™ÝXYÙ\ËœÚYK›[™ÝXYÙ\Ë˜˜\ÚK›[™ÝXYÙ\ËœÚ[YK›[™ÝXYÙ\Ë˜˜\ÚJJš\ÛJK
[˜Ý[ÛŠJ^Ý˜\ˆKÊÎˆŠÎ—
Î——Ÿ×××J_×ˆ———JJˆŸ	ÊÎ—
Î——Ÿ×××J_×‰×——JJ‰ÊKÎÙK›[™ÝXYÙ\Ë˜ÜÜÏ^ØÛÛ[Y[‹××
–×××J×
—ËË][NžÜ]\›Ž”™YÑ^
×ËWJÎ–×ŽÞ×È‰×_ÊÊÈWÊ_
ÝœÛÝ\˜ÙJØ
JÊÎŽß
ÏWÊ—ÊJX
K[œÚYNžÜ[N‹××ËWJËËœÙ[XÝÜ‹Y[˜Ý[Û‹X\™Ý[Y[ŽžÜ]\›Ž‹ÊœÙ[XÝÜ—Ê—
ÊŠÈV×ÊWJJJÎ–×Š
W×_ÊÊÈV×ÊWJ_

Î–×Š
W_
×Š
WJ—
JJ—
JJÊÏWÊ—
JKËÛÚØ™Z[™ˆL[X\Î˜Ù[XÝÜ˜KÙ^]ÛÜ™žÜ]\›Ž‹ÊŸ×—ËWJJÎ˜[™›ÝÛ›_ÜŠJÈV×ËWJKËÛÚØ™Z[™ˆL__K\›žÜ]\›Ž”™YÑ^
\›

Î˜
ÝœÛÝ\˜ÙJØ
Î–×——Š
H‰×_×××JJŠW
XX
KÜ™YYNˆL[œÚYNžÙ[˜Ý[ÛŽ‹×\›ÚK[˜ÝX][ÛŽ‹×—

IËÝš[™ÎžÜ]\›Ž”™YÑ^
˜
ÝœÛÝ\˜ÙJØ	
K[X\Î˜\›__KÙ[XÝÜŽžÜ]\›Ž”™YÑ^

ŸÞßW×JV×žßW×JÎ–×žßNÈ‰××_ÊÊÈV×Þ×J_
ÝœÛÝ\˜ÙJØ
JŠÏWÊ—ÊX
KÛÚØ™Z[™ˆLKÝš[™ÎžÜ]\›ŽÜ™YYNˆLK›Ü\NžÜ]\›Ž‹ÊŸ×‹W×LWQ‘‘‘—JJÈWÊVËWØK^—LWQ‘‘‘—JÎŠÈWÊVËW×LWQ‘‘‘—JJŠÏWÊŽŠKÚKÛÚØ™Z[™ˆLK[\Ü[‹ÈZ[\Ü[‹ÚK[˜Ý[ÛŽžÜ]\›Ž‹ÊŸ×‹XK^ŒNWJVËXK^ŒNWJÊÏW

KÚKÛÚØ™Z[™ˆLK[˜ÝX][ÛŽ‹ÖÊ
^ßNÎ‹KßKK›[™ÝXYÙ\Ë˜ÜÜË˜][Kš[œÚYKœ™\ÝYK›[™ÝXYÙ\Ë˜ÜÜÎÝ˜\ˆYK›[™ÝXYÙ\Ë›X\šÝ\Û‰‰Š‹YË˜Y[›[™Y
Ý[XÜÜØ
K‹YË˜Y]šX]JÝ[XÜÜØ
J_JJš\ÛJK
[˜Ý[ÛŠJ^Ý˜\ˆK×ŠÎ˜XœÝ˜XÝ\ÜÙ\›ÛÛX[Ÿœ™XZßž]_Ø\Ù_Ø]ÚÚ\ŸÛ\ÜßÛÛœÝÛÛ[Y_Y˜][ßÝX›_[Ù_[[_^Üß^[™ßš[˜[š[˜[_›Ø]›ÜŸÛÝßYŸ[\[Y[ß[\Ü[œÝ[˜Ù[ÙŸ[[\™˜XÙ_Û™ß[Ù[_˜]]™_™]ß›Û‹\ÙX[Y[Ü[ŸÜ[œßXÚØYÙ_\›Z]ßš]˜]_›ÝXÝY›ÝšY\ßX›Xß™XÛÜ™
ÈWÊ–Ê
^ßV×OI_‹Ž‹ÏÊ×J‹ÉŸ—J_™\]Z\™\ß™]\›ŸÙX[YÚÜÝ]XßÝšXÝœÝ\\ŸÝÚ]ÚÞ[˜Ú›Ûš^™Y\ß›Ýß›ÝÜßß˜[œÚY[˜[œÚ]]™_ž_\Ù\ß˜\Ÿ›ÚY›Û][_Ú[_Ú]ZY[
W‹ËX
Î–ØK^—WÊ—Ê——ÊŠJŠÎ–ÐKV—WÊ—Ê——ÊŠJ˜^Ü]\›Ž”™YÑ^

Ÿ×—Ë—JX
ÛŠØÐKV—JÎ–×ÐKV—J–ØK^—WÊŠO×˜
KÛÚØ™Z[™ˆL[œÚYNžÛ˜[Y\ÜXÙNžÜ]\›Ž‹×–ØK^—WÊŠÎ—Ê——Ê–ØK^—WÊŠJŠÎ—Ê—ŠOËË[œÚYNžÜ[˜ÝX][ÛŽ‹×‹ß_K[˜ÝX][ÛŽ‹×‹ß_NÙK›[™ÝXYÙ\Ëš˜]˜OYK›[™ÝXYÙ\Ë™^[™
ÛZÙXÜÝš[™ÎžÜ]\›Ž‹ÊŸ×—JHŠÎ—Ÿ×ˆ———JJˆ‹ËÛÚØ™Z[™ˆLÜ™YYNˆLK˜Û\ÜË[˜[YHŽ–Ü‹Ü]\›Ž”™YÑ^

Ÿ×—Ë—JX
ÛŠØÐKV—WÊŠÏWÊ×Ê×Ê–ÎËJ
W_ÊŠÎ—Ö×ËJ—WÊŠOÎŽ—Ê›™]×ŠX
KÛÚØ™Z[™ˆL[œÚYNœ‹š[œÚY_KÜ]\›Ž”™YÑ^

ŠÎ˜Û\Üß[[_^[™ß[\[Y[ß[œÝ[˜Ù[ÙŸ[\™˜XÙ_™]ß™XÛÜ™›ÝÜÊWÊÊX
ÛŠØÐKV—WÊ—˜
KÛÚØ™Z[™ˆL[œÚYNœ‹š[œÚY_WKÙ^]ÛÜ™[˜Ý[ÛŽ–ÙK›[™ÝXYÙ\Ë˜ÛZÙK™[˜Ý[Û‹Ü]\›Ž‹ÊŽ—ÊŠVØK^—×WÊ‹ËÛÚØ™Z[™ˆLWK[X™\Ž‹×Œ–ÌWVÌW×J“×ŸŒ
Î—–×KY—Ü
ËWJß×KY—×JÊÎ—–×KY—Ü
ËWJÊOÊWŸ
Î——××JŠÎ—–××JŠOß——××JŠJÎ™VÊËWO×××JŠOÖÙ›OËÚKÜ\˜]ÜŽžÜ]\›Ž‹ÊŸ×‹—JJÎOßÏOßOŸK_
×
ß	‰ŸŽŸÏÎŸ—_ËJÊ‹ÉIŸˆOO—OOÊKÛKÛÚØ™Z[™ˆLKÛÛœÝ[‹×–ÐKV—VÐKV—×J×‹ßJKK›[™ÝXYÙ\Ëš[œÙ\™Y›Ü™J˜]˜XÝš[™ØÈš\K\][ÝY\Ýš[™ÈŽžÜ]\›Ž‹Èˆˆ–ÈJ–×——JÎŠÎˆŸˆŠOÊÎ—Ÿ×ˆ—JJJˆˆˆ‹ËÜ™YYNˆL[X\Î˜Ýš[™ØKÚ\ŽžÜ]\›Ž‹ÉÊÎ—Ÿ×‰×——J^ÌKŸIËËÜ™YYNˆL_JKK›[™ÝXYÙ\Ëš[œÙ\™Y›Ü™J˜]˜XÛ\ÜË[˜[YXØ[››Ý][ÛŽžÜ]\›Ž‹ÊŸ×‹—JPÊÊÎ—Ê——Ê—ÊÊJ‹ËÛÚØ™Z[™ˆL[X\Î˜[˜ÝX][Û˜KÙ[™\šXÜÎžÜ]\›Ž‹Ï
Î–××Ë×_	ŠÈIŠ_
Î–××Ë×_	ŠÈIŠ_
Î–××Ë×_	ŠÈIŠ_
Î–××Ë×_	ŠÈIŠJJŠJŠJŠJ‹Ë[œÚYNžÈ˜Û\ÜË[˜[YHŽœ‹Ù^]ÛÜ™[˜ÝX][ÛŽ‹ÖÏŠ
KŽ—KËÜ\˜]ÜŽ‹ÖÏÉŸKß_K[\Ü–ÞÜ]\›Ž”™YÑ^

š[\ÜÊÊX
ÛŠØ
Î–ÐKV—WÊŸ
ŠJÏWÊŽÊX
KÛÚØ™Z[™ˆL[œÚYNžÛ˜[Y\ÜXÙNœ‹š[œÚYK›˜[Y\ÜXÙK[˜ÝX][ÛŽ‹×‹ËÜ\˜]ÜŽ‹×
‹Ë˜Û\ÜË[˜[YHŽ‹×ÊËß_KÜ]\›Ž”™YÑ^

š[\ÜÊÜÝ]X×ÊÊX
ÛŠØ
Î—Êß
ŠJÏWÊŽÊX
KÛÚØ™Z[™ˆL[X\Î˜Ý]XØ[œÚYNžÛ˜[Y\ÜXÙNœ‹š[œÚYK›˜[Y\ÜXÙKÝ]XÎ‹×—ÊÉË[˜ÝX][ÛŽ‹×‹ËÜ\˜]ÜŽ‹×
‹Ë˜Û\ÜË[˜[YHŽ‹×ÊËß_WK˜[Y\ÜXÙNžÜ]\›Ž”™YÑ^

ŠÎ™^Üß[\Ü
Î—ÊÜÝ]XÊOß[Ù[_Ü[ŸÜ[œßXÚØYÙ_›ÝšY\ß™\]Z\™\ßß˜[œÚ]]™_\Ù\ßÚ]
WÊÊJÈOÙ^]ÛÜ™ŠVØK^—WÊŠÎ—–ØK^—WÊŠJ—Øœ™\XÙJÏÙ^]ÛÜ™‹ÙË[˜Ý[ÛŠ
^Ü™]\›ˆœÛÝ\˜Ù_JJKÛÚØ™Z[™ˆL[œÚYNžÜ[˜ÝX][ÛŽ‹×‹ß__J_JJš\ÛJKš\ÛK›[™ÝXYÙ\Ëš˜]˜\ØÜš\Tš\ÛK›[™ÝXYÙ\Ë™^[™
ÛZÙXÈ˜Û\ÜË[˜[YHŽ–Ôš\ÛK›[™ÝXYÙ\Ë˜ÛZÙVØÛ\ÜË[˜[YXKÜ]\›Ž‹ÊŸ×‰×LWQ‘‘‘—JJÈWÊV×ÉKV—LWQ‘‘‘—JÎŠÈWÊVÉ×LWQ‘‘‘—JJŠÏWŠÎ˜ÛÛœÝXÝÜŸ›ÝÝ\JJKËÛÚØ™Z[™ˆLWKÙ^]ÛÜ™–ÞÜ]\›Ž‹Ê
Î—ŸJWÊŠXØ]Ú‹ËÛÚØ™Z[™ˆLKÜ]\›Ž‹ÊŸ×‹—_———ÊŠWŠÎ˜\ß\ÜÙ\
ÏWÊ—Ê_\Þ[˜ÊÏWÊŠÎ™[˜Ý[Û—Ÿ
É×LWQ‘‘‘—_	
J_]ØZ]œ™XZßØ\Ù_Û\ÜßÛÛœÝÛÛ[Y_XYÙÙ\ŸY˜][[]_ß[Ù_[[_^Ü^[™ßš[˜[JÏWÊŠÎ—ß	
J_›ÜŸœ›ÛJÏWÊŠÎ–ÉÈ—_	
J_[˜Ý[ÛŸ
Î™Ù]Ù]
JÏWÊŠÎ–È×É×LWQ‘‘‘—_	
J_YŸ[\[Y[ß[\Ü[Ÿ[œÝ[˜Ù[ÙŸ[\™˜XÙ_]™]ß[ÙŸXÚØYÙ_š]˜]_›ÝXÝYX›Xß™]\›ŸÝ]XßÝ\\ŸÝÚ]Ú\ß›Ýßž_\[ÙŸ[™Yš[™Y˜\Ÿ›ÚYÚ[_Ú]ZY[
W‹ËÛÚØ™Z[™ˆLWK[˜Ý[ÛŽ‹ÈÏÊÈWÊV×ÉK^KV—LWQ‘‘‘—JÎŠÈWÊVÉ×LWQ‘‘‘—JJŠÏWÊŠÎ——ÊŠÎ˜\_š[™Ø[
WÊŠO×

KË[X™\ŽžÜ]\›Ž”™YÑ^

Ÿ×—ÉJJÎ“˜SŸ[™š[š]_Ø—VÌWJÊÎ—ÖÌWJÊJ›ßÛÓ×VÌM×JÊÎ—ÖÌM×JÊJ›ßÞV×KQ˜KY—JÊÎ—Ö×KQ˜KY—JÊJ›ß
ÊÎ—×
ÊJ›Ÿ
Î—
ÊÎ—×
ÊJŠÎ—ŠÎ—
ÊÎ—×
ÊJŠOÊOß—
ÊÎ—×
ÊJŠJÎ–ÑYWVÊËWO×
ÊÎ—×
ÊJŠOÊJÈV×ÉJX
KÛÚØ™Z[™ˆLKÜ\˜]ÜŽ‹ËK_
×
ß
—
OßOŸ	‰OßOßÈOWOO_OßÏOßËJÊ‹ÉIŸˆOO—OOßžÌß_×ÏOß×ßßŽ—KßJKš\ÛK›[™ÝXYÙ\Ëš˜]˜\ØÜš\ØÛ\ÜË[˜[YXVÌKœ]\›KÊŠÎ˜Û\Üß^[™ß[\[Y[ß[œÝ[˜Ù[ÙŸ[\™˜XÙ_™]ÊWÊÊV×Ë—JËËš\ÛK›[™ÝXYÙ\Ëš[œÙ\™Y›Ü™J˜]˜\ØÜš\Ù^]ÛÜ™Ü™YÙ^žÜ]\›Ž”™YÑ^


Î—Ÿ×‰×LWQ‘‘‘‹ˆ‰×JW×_ŠÎœ™]\›ŸZY[
JWÊŠWÊÎŠÎ—ÊÎ–×—W——_ŠJ—_Ÿ×‹××——JJ×ÖÙÚ[^]\×^Ìß_
Î—ÊÎ–×–×W——_ŸÊÎ–×–×W——_ŸÊÎ–×–×W——_ŠJ—JJ—JJ—_Ÿ×‹××——JJ×ÖÙÚ[^]\×^Ìß]–ÙÚ[^]\×^ÌßJJÏJÎ—ß×
ŠÎ–×Š—_
ŠÈWÊJJ—
—ÊJŠÎ‰×—‹ŽÎŸJWW_×ÊJX
KÛÚØ™Z[™ˆLÜ™YYNˆL[œÚYNžÈœ™YÙ^\ÛÝ\˜ÙHŽžÜ]\›Ž‹×ŠÊV×××JÊÏWÖØK^—J‰
KËÛÚØ™Z[™ˆL[X\Î˜[™ÝXYÙK\™YÙ^[œÚYN”š\ÛK›[™ÝXYÙ\Ëœ™YÙ^Kœ™YÙ^Y[[Z]\ˆŽ‹×—ßÉËœ™YÙ^Y›YÜÈŽ‹×–ØK^—JÉß_K™[˜Ý[Û‹]˜\šXX›HŽžÜ]\›Ž‹ÈÏÊÈWÊV×ÉK^KV—LWQ‘‘‘—JÎŠÈWÊVÉ×LWQ‘‘‘—JJŠÏWÊ–ÏN—WÊŠÎ˜\Þ[˜×ÊŠOÊÎ—™[˜Ý[Û—Ÿ
Î—

Î–×Š
W_
×Š
WJ—
JJ—
_
ÈWÊV×ÉK^KV—LWQ‘‘‘—JÎŠÈWÊVÉ×LWQ‘‘‘—JJŠWÊOŠJKË[X\Î˜[˜Ý[Û˜K\˜[Y]\Ž–ÞÜ]\›Ž‹Ê[˜Ý[ÛŠÎ—ÊÊÈWÊV×ÉK^KV—LWQ‘‘‘—JÎŠÈWÊVÉ×LWQ‘‘‘—JJŠO×Ê—
ÊŠJÈWÊJÎ–×Š
W×_ÊÊÈV×ÊWJ_
×Š
WJ—
JJÊÏWÊ—
JKËÛÚØ™Z[™ˆL[œÚYN”š\ÛK›[™ÝXYÙ\Ëš˜]˜\ØÜš\KÜ]\›Ž‹ÊŸ×‰×LWQ‘‘‘—JJÈWÊV×ÉK^—LWQ‘‘‘—JÎŠÈWÊVÉ×LWQ‘‘‘—JJŠÏWÊOŠKÚKÛÚØ™Z[™ˆL[œÚYN”š\ÛK›[™ÝXYÙ\Ëš˜]˜\ØÜš\KÜ]\›Ž‹Ê
ÊŠJÈWÊJÎ–×Š
W×_ÊÊÈV×ÊWJ_
×Š
WJ—
JJÊÏWÊ—
WÊOŠKËÛÚØ™Z[™ˆL[œÚYN”š\ÛK›[™ÝXYÙ\Ëš˜]˜\ØÜš\KÜ]\›Ž‹Ê
Î—ŸßŠJÈJÎ˜\ß\Þ[˜ß]ØZ]œ™XZßØ\Ù_Ø]ÚÛ\ÜßÛÛœÝÛÛ[Y_XYÙÙ\ŸY˜][[]_ß[Ù_[[_^Ü^[™ßš[˜[_›ÜŸœ›Û_[˜Ý[ÛŸÙ]YŸ[\[Y[ß[\Ü[Ÿ[œÝ[˜Ù[ÙŸ[\™˜XÙ_]™]ß[ÙŸXÚØYÙ_š]˜]_›ÝXÝYX›Xß™]\›ŸÙ]Ý]XßÝ\\ŸÝÚ]Ú\ß›Ýßž_\[ÙŸ[™Yš[™Y˜\Ÿ›ÚYÚ[_Ú]ZY[
JÈVÉ×LWQ‘‘‘—JJJÎŠÈWÊV×ÉK^KV—LWQ‘‘‘—JÎŠÈWÊVÉ×LWQ‘‘‘—JJ—ÊŠW
ÊŸWÊ—
ÊŠJÈWÊJÎ–×Š
W×_ÊÊÈV×ÊWJ_
×Š
WJ—
JJÊÏWÊ—
WÊ—ÊKËÛÚØ™Z[™ˆL[œÚYN”š\ÛK›[™ÝXYÙ\Ëš˜]˜\ØÜš\WKÛÛœÝ[‹×–ÐKV—JÎ–ÐKV—×_ÊJ—‹ßJKš\ÛK›[™ÝXYÙ\Ëš[œÙ\™Y›Ü™J˜]˜\ØÜš\Ýš[™ØÚ\Ú˜[™ÎžÜ]\›Ž‹×ˆÈKŠ‹ËÜ™YYNˆL[X\Î˜ÛÛ[Y[K[\]K\Ýš[™ÈŽžÜ]\›Ž‹Ø
Î—×××_	ÊÎ–×žßW_ÊÎ–×žßW_Ö×ŸWJ—JJ—JJ×_
ÈW	ÊV×—JJ˜ËÜ™YYNˆL[œÚYNžÈ[\]K\[˜ÝX][ÛˆŽžÜ]\›Ž‹×˜	Ë[X\Î˜Ýš[™ØK[\œÛ][ÛŽžÜ]\›Ž‹Ê
Î—Ÿ×—JJÎ—ÌŸJJŠW	ÊÎ–×žßW_ÊÎ–×žßW_Ö×ŸWJ—JJ—JJ×KËÛÚØ™Z[™ˆL[œÚYNžÈš[\œÛ][Û‹\[˜ÝX][ÛˆŽžÜ]\›Ž‹×—	ßIË[X\Î˜[˜ÝX][Û˜K™\Ý”š\ÛK›[™ÝXYÙ\Ëš˜]˜\ØÜš\_KÝš[™Î‹Ö×××JËß_KœÝš[™Ë\›Ü\HŽžÜ]\›Ž‹Ê
Î—ŸË×JVÈJŠJÈ‰×JJÎ—
Î——Ÿ×××J_
ÈWŠV×———JJ—ŠÏWÊŽŠKÛKÛÚØ™Z[™ˆLÜ™YYNˆL[X\Î˜›Ü\X_JKš\ÛK›[™ÝXYÙ\Ëš[œÙ\™Y›Ü™J˜]˜\ØÜš\Ü\˜]Ü˜È›]\˜[\›Ü\HŽžÜ]\›Ž‹Ê
Î—ŸË×JVÈJŠJÈWÊV×ÉK^KV—LWQ‘‘‘—JÎŠÈWÊVÉ×LWQ‘‘‘—JJŠÏWÊŽŠKÛKÛÚØ™Z[™ˆL[X\Î˜›Ü\X_JKš\ÛK›[™ÝXYÙ\Ë›X\šÝ\	‰Šš\ÛK›[™ÝXYÙ\Ë›X\šÝ\YË˜Y[›[™Y
ØÜš\˜]˜\ØÜš\
Kš\ÛK›[™ÝXYÙ\Ë›X\šÝ\YË˜Y]šX]JÛŠÎ˜X›Ü›\ŸÚ[™Ù_ÛXÚßÛÛ\ÜÚ][ÛŠÎ™[™Ý\\]J_›ÛXÚß\œ›ÜŸ›ØÝ\ÊÎš[ŸÝ]
OßÙ^JÎ™ÝÛŸ\
_ØY[Ý\ÙJÎ™ÝÛŸ[\ŸX]™_[Ý™_Ý]Ý™\Ÿ\
_™\Ù]™\Ú^™_ØÜ›ÛÙ[XÝÛÝÚ[™Ù_ÝX›Z][›ØYÚY[
X˜]˜\ØÜš\
JKš\ÛK›[™ÝXYÙ\ËšœÏTš\ÛK›[™ÝXYÙ\Ëš˜]˜\ØÜš\š\ÛK›[™ÝXYÙ\ËšœÛÛ^Ü›Ü\NžÜ]\›Ž‹ÊŸ×—JHŠÎ—Ÿ×————JJˆŠÏWÊŽŠKËÛÚØ™Z[™ˆLÜ™YYNˆLKÝš[™ÎžÜ]\›Ž‹ÊŸ×—JHŠÎ—Ÿ×————JJˆŠÈWÊŽŠKËÛÚØ™Z[™ˆLÜ™YYNˆLKÛÛ[Y[žÜ]\›Ž‹××ËŠŸ×
–×××JÊÎ—
—ß	
KËÜ™YYNˆLK[X™\Ž‹ËO×—
ÊÎ——
ÊOÊÎ™VÊËWO×
ÊO×‹ÚK[˜ÝX][ÛŽ‹ÖÞßV×KKËÜ\˜]ÜŽ‹Î‹Ë›ÛÛX[Ž‹×ŠÎ™˜[Ù_YJW‹Ë[žÜ]\›Ž‹×›[‹Ë[X\Î˜Ù^]ÛÜ™_Kš\ÛK›[™ÝXYÙ\ËÙX›X[šY™\ÝTš\ÛK›[™ÝXYÙ\ËšœÛÛ‹š\ÛK›[™ÝXYÙ\Ëœ]Û^ØÛÛ[Y[žÜ]\›Ž‹ÊŸ×—JHËŠ‹ËÛÚØ™Z[™ˆLÜ™YYNˆLKœÝš[™ËZ[\œÛ][ÛˆŽžÜ]\›Ž‹ÊÎ™ŸœŸ™ŠJÎŠˆˆŸ	ÉÉÊV×××J×_
Ÿ	ÊJÎ—Ÿ
ÈWŠV×———JJ—ŠKÚKÜ™YYNˆL[œÚYNžÚ[\œÛ][ÛŽžÜ]\›Ž‹Ê
Î—Ÿ×ž×JJÎ—×ÊJŠWÊÈWÊJÎ–×žßW_ÊÈWÊJÎ–×žßW_ÊÈWÊJÎ–×žßWJJ×JJ×JJ×KËÛÚØ™Z[™ˆL[œÚYNžÈ™›Ü›X]\ÜXÈŽžÜ]\›Ž‹ÊŠV×ŽŠ
^ßWJÊÏWI
KËÛÚØ™Z[™ˆLK˜ÛÛ™\œÚ[Û‹[Ü[ÛˆŽžÜ]\›Ž‹ÈVÜÜ˜WJÏVÎŸWI
KË[X\Î˜[˜ÝX][Û˜K™\Ý›[_KÝš[™Î‹Ö×××JËß_Kš\K\][ÝY\Ýš[™ÈŽžÜ]\›Ž‹ÊÎ–ÜX—_œŸ˜ŠOÊˆˆŸ	ÉÉÊV×××J×KÚKÜ™YYNˆL[X\Î˜Ýš[™ØKÝš[™ÎžÜ]\›Ž‹ÊÎ–ÜX—_œŸ˜ŠOÊŸ	ÊJÎ—Ÿ
ÈWJV×———JJ—KÚKÜ™YYNˆLK[˜Ý[ÛŽžÜ]\›Ž‹Ê
Î—ŸÊYY–ÈJÊVØK^KV—×WÊŠÏWÊ—

KÙËÛÚØ™Z[™ˆLK˜Û\ÜË[˜[YHŽžÜ]\›Ž‹Ê˜Û\Ü×ÊÊWÊËÚKÛÚØ™Z[™ˆLKXÛÜ˜]ÜŽžÜ]\›Ž‹Ê–×JŠPÊÊÎ——ÊÊJ‹ÛKÛÚØ™Z[™ˆL[X\Î–Ø[››Ý][Û˜[˜ÝX][Û˜K[œÚYNžÜ[˜ÝX][ÛŽ‹×‹ß_KÙ^]ÛÜ™‹×ŠÎ—ÊÏWÊŽŠ_[™\ß\ÜÙ\\Þ[˜ß]ØZ]œ™XZßØ\Ù_Û\ÜßÛÛ[Y_YŸ[[YŸ[Ù_^Ù\^Xßš[˜[_›ÜŸœ›Û_ÛØ˜[YŸ[\Ü[Ÿ\ß[X™_X]Ú›Û›ØØ[›ÝÜŸ\Üßš[˜Z\Ù_™]\›Ÿž_Ú[_Ú]ZY[
W‹ËZ[[Ž‹×ŠÎ—×Ú[\Ü×ßXœß[[ž_\_\ØÚZ_˜\Ù\Ýš[™ßš[Ÿ›ÛÛY™™\Ÿž]X\œ˜^_ž]\ßØ[X›_ÚŸÛ\ÜÛY]ÙÛ\ÛÙ\˜Ù_ÛÛ\[_ÛÛ\^[]ŸXÝ\Ÿ]›[Ù[[Y\˜]_]˜[^XÙš[_š[_š[\Ÿ›Ø]›Ü›X]œ›Þ™[œÙ]Ù]]ŸÛØ˜[ß\Ø]Ÿ\Ú[^Y[œ][[\›Ÿ\Ú[œÝ[˜Ù_\ÜÝX˜Û\Üß]\Ÿ[Ÿ\ÝØØ[ßÛ™ßX\X^Y[[Üž]šY]ßZ[Ÿ™^Øš™XÝØÝÜ[ŸÜ™Ýß›Ü\_˜[™Ù_˜]×Ú[œ]™YXÙ_™[ØY™\Ÿ™]™\œÙY›Ý[™Ù]Ù]]ŸÛXÙ_ÛÜYÝ]XÛY]ÙÝŸÝ[_Ý\\Ÿ\_\_[šXÚŸ[šXÛÙ_˜\œß˜[™Ù_š\
W‹Ë›ÛÛX[Ž‹×ŠÎ‘˜[Ù_›Û™_YJW‹Ë[X™\Ž‹×Œ
Î˜ŠÎ—ÏÖÌWJJßÊÎ—ÏÖÌM×JJß
Î—ÏÖØKYŒNWJJÊWŸ
Î——
ÊÎ—×
ÊJŠÎ—ŠÎ—
ÊÎ—×
ÊJŠOÊOß——
ÊÎ—×
ÊJŠJÎ™VÊËWO×
ÊÎ—×
ÊJŠOÚÊÈWÊKÚKÜ\˜]ÜŽ‹ÖËJÉOWOOßO__
—
ÏOß×ÏÏOßÏO—Oß–ÏO—OßÉŸŸ—KË[˜ÝX][ÛŽ‹ÖÞßV×NÊ
KŽ—KßKš\ÛK›[™ÝXYÙ\Ëœ]Û–ØÝš[™ËZ[\œÛ][Û˜Kš[œÚYKš[\œÛ][Û‹š[œÚYKœ™\ÝTš\ÛK›[™ÝXYÙ\Ëœ]Û‹š\ÛK›[™ÝXYÙ\ËœOTš\ÛK›[™ÝXYÙ\Ëœ]Û‹š\ÛK›[™ÝXYÙ\ËœÜ[^ØÛÛ[Y[žÜ]\›Ž‹ÊŸ×—JJÎ—×
–×××J×
—ß
Î‹K_×ßÊKŠŠKËÛÚØ™Z[™ˆLK˜\šXX›N–ÞÜ]\›Ž‹Ð
È‰ØJJÎ—×××_
ÈWJV×—JJ×KËÜ™YYNˆLKÐ×Ë‰JË×KÝš[™ÎžÜ]\›Ž‹ÊŸ×JJŸ	ÊJÎ—×××_
ÈWŠV×—_—ŠJ—‹ËÜ™YYNˆLÛÚØ™Z[™ˆLKY[YšY\ŽžÜ]\›Ž‹ÊŸ×JX
Î—×××_×˜_
J˜ËÜ™YYNˆLÛÚØ™Z[™ˆL[œÚYNžÜ[˜ÝX][ÛŽ‹×˜	ß_K[˜Ý[ÛŽ‹×ŠÎU‘ßÓÕS•’T”Õ“Ô“PUTÕÐTÑ_SŸPVRQRSŸSÑ“Õß“ÕS‘ÕS_PÐTÑJJÏWÊ—

KÚKÙ^]ÛÜ™‹×ŠÎPÕSÓŸQQ•TŸSÓÔ’U_SSTŸSSV‘_S–_T_TßTÐßUUÔ’VUSÓŸUU×ÒSÔ‘SQS•PÒÕT‘Ÿ‘QÒSŸ‘T’ÑSVQŸ’QÒS•’ST–_’U“ÐŸ“ÓÓ“ÓÓPSŸ”‘PRß”“ÕÔÑ_•‘Q_•Sß–_ÐSÐTÐÐQQßÐTÑ_ÒRSŸÒTŠÎPÕTŸÑU
OßÒPÒÊÎ”ÒS•
OßÓÔÑ_ÓTÕT‘QÓÐSTÐÑ_ÓÓU_ÓÓSS”ÏßÓÓSQS•ÓÓSRU
Î•Q
OßÓÓTU_ÓÓ“‘PÕÓÓ”ÒTÕS•ÓÓ”ÕRS•ÓÓ•RS”ÊÎ•P“JOßÓÓ•S•Q_ÓÓ•‘T•Ô‘PU_Ô“ÔÔßÕT”‘S•
Î—ÑU_ÕSQ_ÕSQTÕSTÕTÑTŠOßÕT”ÓÔŸÖPÓ_UJÎTÑTÏÊOßUJÎ•SQJOßV_ÐßPSÐÐU_PßPÒSPSPÓT‘_QUSQ’S‘TŸSVQQSU_SSRUT”ÏßS–_TÐßTÐÔ’P‘_UT“RS’TÕPßTÐP“_TÐÐT‘TÒßTÕSÕTÕSÕ“ÕßTÕ’P•UQßÕP“_“ÔSSV_ST
Î‘’SJOßTPÐU_SÑJÎ’QŠOßSP“_SÓÔÑQS‘S‘ÒS‘_S•S_T”““T”“Ô”ßTÐÐTQßVÑTVPÊÎ•UJOßVTÕßVUVRSŸVS‘Q‘UÒ’QSß’S_’SPÕÔŸ’T”Õ’VQ“ÐU“ÓÕÒS‘ß“ÔŠÎˆPPÒ“ÕÊOß“ÔÑ_“Ô‘RQÓŸ”‘QUV
Î•P“JOß”“Ó_•S•SÕSÓŸÑSÓQU–JÎÓÓPÕSÓŠOßÓÐSÓÕßÔS•Ô“ÕTS‘TŸTÒU’S‘ßÓÐÒßÕTŸQS•UJÎÓÓÒS”ÑT•
OßQŸQÓ“Ô‘_STÔ•S‘VS‘’S_S“‘TŸS““ÑŸS“ÕUS”ÑT•S•S•QÑTŸS•T”ÑPÕS•T•SS•ßS•“ÒÑTŸTÓÓUSÓŸUTU_“ÒSŸÑVTÏßÒSS‘ÕPQÑ_TÕPU‘_Q•U‘SSRUS‘S“ßS‘TßS‘TÕ’S‘ßÐQÐÐSÐÒßÓ‘ÊÎ“ÐŸV
_ÓÔPUÒ
Î‘Q
OßQQUSJÎ“ÐŸS•V
_QT‘Ñ_RQRS•RS•U_SÑ_SÑQ’QTßSÑQ–_SÓ•USJÎ“S‘TÕ’S‘ßÒS•ÓQÓÓŠ_USÓSUTSÒTŸ‘V“ß“ÓÓTÕT‘Q•SQŸ•SQT’PßÑ‘ßÑ‘”ÑUÏßÓŸÔSŠÎ‘UTÓÕTÑ_UQT–_“ÕÔÑU
OßÔSRV‘_ÔSÓŠÎSJOßÔ‘TŸÕU
Î‘TŸ’SJOßÕ‘TŸT•PST•USÓŸTÑS•U“ÕSŸÒS•ÓQÓÓŸ‘PÑQS‘ß‘PÒTÒSÓŸ‘TT‘_‘UŸ’SPT–_’S•’U’SQÑTß“ÐÊÎ‘QT‘JOßP“PßT‘Ñ_URPÒßRTÑT”“ÔŸ‘PQÏß‘PS‘PÓÓ‘’QÕT‘_‘Q‘T‘SÑTß‘SPTÑ_‘SSQ_‘TPU
ÎP“JOß‘TPÑ_‘TPÐUSÓŸ‘TURT‘_‘TÒQÓS‘TÕÔ‘_‘TÕ’PÕ‘UT“ŠÎ’S‘ßÊOß‘U“ÒÑ_’QÒ“ÓPÒß“ÕUS‘_“ÕÊÎÓÕS•ÕRQÓÓÊOß•‘Q_•S_ÐU‘JÎ”ÒS•
OßÐÒSP_ÑPÓÓ‘ÑSPÕÑT’PS
Î’VP“JOßÑTÔÒSÓŠÎ—ÕTÑTŠOßÑU
Î•TÑTŠOßÒT‘_ÒÕßÒUÕÓŸÒST_ÓPSS•ÓTÒÕÓÓQ_ÓÓSQ_ÔSÕT•
Î’S‘ÊOßÕUTÕPÔßÕUTßÕ’TQÖTÕSWÕTÑTŸP“TÏßP“TÔPÑ_ST
Î“ÔT–_P“JOßT“RSUQV
Î”ÒV‘JOßSŸSQJÎ”ÕST
OßS–JÎ“ÐŸS•V
_ÔßSŠÎ”ÐPÕSÓ”ÏÊOß’QÑÑTŸ•SÐU_ÑTUPSTTÏßS“ÕS‘QSÓÓSRUQS‘Q’S‘QS’SÓŸS’TUQ_S“ÐÒßS”U“ÕS”ÒQÓ‘QTUJÎ•V
OßTÐQÑ_TÑ_TÑTŸTÒS‘ßSQTÏßTŠÎ’ST–_ÒTŸÒTPÕTŸRS‘Ê_’QUßÐRU“ÔŸÐT“’S‘ÔßÒSŸÒT‘_ÒS_ÒU
Îˆ“ÓTSŠOßÓÔ’ßÔ’UJÎ•V
OßQPTŠW‹ÚK›ÛÛX[Ž‹×ŠÎ‘SÑ_•S•QJW‹ÚK[X™\Ž‹×Œ×KY—J×Ÿ—
ÊÎ——
ŠOß——
×‹ÚKÜ\˜]ÜŽ‹ÖËJÊ—ÏIWŸ—_	‰ßßOOß
ÎOßŠOß–ÏWOßŠÎS‘‘UÑQSŸUŸSRÑ_SŸTßRÑ_“ÕÔŸ‘QÑV“RÑ_ÓÕS‘ÈRÑ_ÔŠW‹ÚK[˜ÝX][ÛŽ‹ÖÎÖ×J
X—KßK
[˜Ý[ÛŠJ^ÙK›[™ÝXYÙ\Ë\\ØÜš\YK›[™ÝXYÙ\Ë™^[™
˜]˜\ØÜš\È˜Û\ÜË[˜[YHŽžÜ]\›Ž‹ÊŠÎ˜Û\Üß^[™ß[\[Y[ß[œÝ[˜Ù[ÙŸ[\™˜XÙ_™]ß\JWÊÊJÈZÙ^[Ù—ŠJÈWÊV×ÉK^KV—LWQ‘‘‘—JÎŠÈWÊVÉ×LWQ‘‘‘—JJŠÎ—Ê
Î–×—_
Î–×—_×—JŠJŠJŠOËËÛÚØ™Z[™ˆLÜ™YYNˆL[œÚYN›[KZ[[Ž‹×ŠÎ\œ˜^_[˜Ý[ÛŸ›ÛZ\Ù_[ž_›ÛÛX[ŸÛÛœÛÛ_™]™\Ÿ[X™\ŸÝš[™ßÞ[X›Û[šÛ›ÝÛŠW‹ßJKK›[™ÝXYÙ\Ë\\ØÜš\šÙ^]ÛÜ™œ\Ú
×ŠÎ˜XœÝ˜XÝXÛ\™_\ßÙ^[ÙŸ™XYÛ›_™\]Z\™JW‹Ë×ŠÎ˜\ÜÙ\ß[™™\Ÿ[\™˜XÙ_[Ù[_˜[Y\ÜXÙ_\JWŠÏWÊŠÎ–Þ×ÉK^KV—LWQ‘‘‘—_	
JKË×\WŠÏWÊŠÎ–×Ê—_	
JKÊK[]HK›[™ÝXYÙ\Ë\\ØÜš\œ\˜[Y]\‹[]HK›[™ÝXYÙ\Ë\\ØÜš\Ø]\˜[\›Ü\XNÝ˜\ˆYK›[™ÝXYÙ\Ë™^[™
\\ØÜš\ßJNÙ[]HØÛ\ÜË[˜[YXKK›[™ÝXYÙ\Ë\\ØÜš\ØÛ\ÜË[˜[YXKš[œÚYO]K›[™ÝXYÙ\Ëš[œÙ\™Y›Ü™J\\ØÜš\[˜Ý[Û˜ÙXÛÜ˜]ÜŽžÜ]\›Ž‹ÐÉ×LWQ‘‘‘—JËË[œÚYNžØ]žÜ]\›Ž‹×Ë[X\Î˜Ü\˜]Ü˜K[˜Ý[ÛŽ‹×–×××JËß_K™Ù[™\šXËY[˜Ý[ÛˆŽžÜ]\›Ž‹ÈÏÊÈWÊV×ÉK^KV—LWQ‘‘‘—JÎŠÈWÊVÉ×LWQ‘‘‘—JJ—Ê
Î–×—_
Î–×—_×—JŠJŠJŠÏWÊ—

KËÜ™YYNˆL[œÚYNžÙ[˜Ý[ÛŽ‹×ˆÏÊÈWÊV×ÉK^KV—LWQ‘‘‘—JÎŠÈWÊVÉ×LWQ‘‘‘—JJ‹ËÙ[™\šXÎžÜ]\›Ž‹Ï×××JËË[X\Î˜Û\ÜË[˜[YX[œÚYN___JKK›[™ÝXYÙ\ËÏYK›[™ÝXYÙ\Ë\\ØÜš\JJš\ÛJK
[˜Ý[ÛŠJ^Ý˜\ˆKÖÊ‰—V×—Ö×^ßKJËËKÈJÎ××IHÎËÏÎ	JÉˆ_Š‰Ê
V×WJÏŸ
Î–ØK^KV—WJˆJOÖ××IHÎËÏÎ	JÉŸŠ‰Ê
WJÊOËËX
Î˜
Û‹œÛÝ\˜ÙJØ
Î–ÈWJØ
ÝœÛÝ\˜ÙJØ
Oß
ÝœÛÝ\˜ÙJØ
Î–ÈWJØ
Û‹œÛÝ\˜ÙJØ
OÊXOX
Î–×—×WKWYˆHˆÉI‰Ê‹NÐ×WßWÙ‹W‹WY—YWY™™—Y™™™WY™™™—_ÏÎ‹WORSŠJÎ–ÈJŠÎŠÈVÈÎ—JORSŸRSŠJJ˜œ™\XÙJÏRS‹ÙË[˜Ý[ÛŠ
^Ü™]\›˜×—×WKWY‹×^ßWÙ‹W‹WY—YWY™™—Y™™™WY™™™—XJKOXŠÎ–×ˆ———_ŠJˆŸ	ÊÎ–×‰×——_ŠJ‰ØÙ[˜Ý[ÛˆÊK
^ÝJ
Kœ™\XÙJÛKÙË
JØXÝ˜\ˆX
Î—KÞ×WÊŠÎ—Ï›Ü–ÈJÊOÊJÎ˜[YOŠJÏVÈJŠÎ‰__
Î–×——WÊŠOÈÊJXœ™\XÙJÏ›Ü‹ÙË[˜Ý[ÛŠ
^Ü™]\›ˆŸJKœ™\XÙJÏ˜[YO‹ÙË[˜Ý[ÛŠ
^Ü™]\›ˆ_JNÜ™]\›ˆ™YÑ^
‹
_YK›[™ÝXYÙ\ËžX[[^ÜØØ[\ŽžÜ]\›Ž”™YÑ^

×N—WÊŠÎ—Ï›Ü–ÈJÊOÖß—JVÈJŠÎŠ
Î—×ŸŠVÈJÊWÖ×———JŠÎ—–×———JÊJŠXœ™\XÙJÏ›Ü‹ÙË[˜Ý[ÛŠ
^Ü™]\›ˆŸJJKÛÚØ™Z[™ˆL[X\Î˜Ýš[™ØKÛÛ[Y[‹ÈËŠ‹ËÙ^NžÜ]\›Ž”™YÑ^


Î—ŸÎ—KÞ×—×JVÈJŠÎ›Ü–ÈJÊOÊOÙ^OŠÏWÊŽ—ÊXœ™\XÙJÏ›Ü‹ÙË[˜Ý[ÛŠ
^Ü™]\›ˆŸJKœ™\XÙJÏÙ^O‹ÙË[˜Ý[ÛŠ
^Ü™]\›˜
Î˜
ÚJØ
ØJØ
XJJKÛÚØ™Z[™ˆLÜ™YYNˆL[X\Î˜][XK\™XÝ]™NžÜ]\›Ž‹Ê–ÈJŠIKŠËÛKÛÚØ™Z[™ˆL[X\Î˜[\Ü[K]][YNžÜ]\›Ž›ÊÍKWËWÊÎ–Ý_ÈJÊWÎ—ÌŸN—ÌŸJÎ——
ŠOÊÎ–ÈJŠÎ–ŸËJ×WÊÎŽ—ÌŸJOÊJOßÍKWÌŸKWÌŸ_Î—ÌŸJÎŽ—ÌŸJÎ——
ŠOÊOØ
KÛÚØ™Z[™ˆL[X\Î˜[X™\˜K›ÛÛX[ŽžÜ]\›Ž›Ê˜[Ù_YXX
KÛÚØ™Z[™ˆL[X\Î˜[\Ü[K[žÜ]\›Ž›Ê[˜X
KÛÚØ™Z[™ˆL[X\Î˜[\Ü[KÝš[™ÎžÜ]\›Ž›ÊJKÛÚØ™Z[™ˆLÜ™YYNˆLK[X™\ŽžÜ]\›Ž›ÊÊËWOÊÎŒ×KY—JßÖÌM×Jß
Î—
ÊÎ——
ŠOß—
ÊJÎ™VÊËWO×
ÊOßš[™Ÿ›˜[ŠXX
KÛÚØ™Z[™ˆLKYÎ›‹[\Ü[[˜ÝX][ÛŽ‹ËKK_Î–×^ßWK×_——‹ßKK›[™ÝXYÙ\Ëž[[YK›[™ÝXYÙ\ËžX[[JJš\ÛJNÝ˜\ˆŽ]\Ê
OOžÝ˜\ˆTÞ[X›Û™›ÜŠ™XXÝ˜[œÚ][Û˜[™[[Y[
KTÞ[X›Û™›ÜŠ™XXÝœÜ[
KTÞ[X›Û™›ÜŠ™XXÝ™œ˜YÛY[
KOTÞ[X›Û™›ÜŠ™XXÝœÝšXÝÛ[ÙX
KOTÞ[X›Û™›ÜŠ™XXÝœ›Ùš[\˜
KÏTÞ[X›Û™›ÜŠ™XXÝ˜ÛÛœÝ[Y\˜
KÏTÞ[X›Û™›ÜŠ™XXÝ˜ÛÛ^
KTÞ[X›Û™›ÜŠ™XXÝ™›ÜØ\™Ü™Y˜
KOTÞ[X›Û™›ÜŠ™XXÝœÝ\Ü[œÙX
KTÞ[X›Û™›ÜŠ™XXÝ›Y[[Ø
KTÞ[X›Û™›ÜŠ™XXÝ›^žX
KTÞ[X›Û™›ÜŠ™XXÝ˜XÝ]š]X
KOTÞ[X›Û™›ÜŠ™XXÝšY]×Ý˜[œÚ][Û˜
KTÞ[X›Ûš]\˜]ÜŽÙ[˜Ý[ÛˆÊJ^Ü™]\›ˆ\[ÙˆHOXØš™XÝYOÛ[ŠOZ	‰™VÚ_VØ]\˜]Ü˜K\[ÙˆOOX[˜Ý[Û˜ÙN›[
_]˜\ˆÏ^Ú\Ó[Ý[Y™[˜Ý[ÛŠ
^Ü™]\›ˆL_K[œ]Y]YQ›Ü˜ÙU\]N™[˜Ý[ÛŠ
^ßK[œ]Y]YT™\XÙTÝ]N™[˜Ý[ÛŠ
^ßK[œ]Y]YTÙ]Ý]N™[˜Ý[ÛŠ
^ß_KSØš™XÝ˜\ÜÚYÛ‹O^ßNÙ[˜Ý[ÛˆŠKŠ^Ý\Ëœ›ÜÏYK\Ë˜ÛÛ^]\Ëœ™YœÏ^K\Ë\]\[ŸßX‹œ›ÝÝ\Kš\Ô™XXÝÛÛ\Û™[^ßK‹œ›ÝÝ\KœÙ]Ý]OY[˜Ý[ÛŠK
^ÚYŠ\[ÙˆHOXØš™XÝ	‰\[ÙˆHOX[˜Ý[Û˜	‰™HO[[
]›ÝÈ\œ›ÜŠZÙ\È[ˆØš™XÝÙˆÝ]H˜\šXX›\ÈÈ\]HÜˆH[˜Ý[ÛˆÚXÚ™]\›œÈ[ˆØš™XÝÙˆÝ]H˜\šXX›\Ë˜
NÝ\Ë\]\‹™[œ]Y]YTÙ]Ý]J\ËKÙ]Ý]X
_K‹œ›ÝÝ\K™›Ü˜ÙU\]OY[˜Ý[ÛŠJ^Ý\Ë\]\‹™[œ]Y]YQ›Ü˜ÙU\]J\ËK›Ü˜ÙU\]X
_NÙ[˜Ý[Ûˆ

^ß^œ›ÝÝ\OX‹œ›ÝÝ\NÙ[˜Ý[ÛˆÊKŠ^Ý\Ëœ›ÜÏYK\Ë˜ÛÛ^]\Ëœ™YœÏ^K\Ë\]\[Ÿß]˜\ˆÏTËœ›ÝÝ\O[™]ÈÐË˜ÛÛœÝXÝÜTËŠË‹œ›ÝÝ\JKËš\Ô\™T™XXÝÛÛ\Û™[HLÝ˜\ˆÏP\œ˜^Kš\Ð\œ˜^NÙ[˜Ý[Ûˆ

^ß]˜\ˆO^Ò›[N›[›[Î›[KSØš™XÝœ›ÝÝ\Kš\ÓÝÛ”›Ü\NÙ[˜Ý[ÛˆÊK‹Š^Ý˜\ˆO\‹œ™YŽÜ™]\›žÉ	\[ÙŽ\N™KÙ^N›‹™YŽšOOO]›ÚYÛ[šK›ÜÎœŸ_Y[˜Ý[ÛˆÊK
^Ü™]\›ˆÊK\KKœ›ÜÊ_Y[˜Ý[ÛˆJJ^Ü™]\›ˆ\[ÙˆOOXØš™XÝ	‰ˆHYI‰™K‰	\[ÙOO]Y[˜Ý[ÛˆŠJ^Ý˜\ˆ^ÈHŽ˜LŽˆŽ˜L˜NÜ™]\›˜	
ÙKœ™\XÙJÖÏN—KÙË[˜Ý[ÛŠJ^Ü™]\›ˆÙW_J_]˜\ˆOK×ÊËÙÎÙ[˜Ý[ÛˆŠK
^Ü™]\›ˆ\[ÙˆOOXØš™XÝ	‰™I‰™KšÙ^HO[[ÚŠ
ÙKšÙ^JNÔÝš[™ÊÍŠ_Y[˜Ý[Ûˆ
J^ÜÝÚ]Ú
KœÝ]\Ê^ØØ\ÙX[š[Yœ™]\›ˆK˜[YNØØ\ÙX™Z™XÝY›ÝÈKœ™X\ÛÛŽÙY˜][œÝÚ]Ú
\[ÙˆKœÝ]\ÏOXÝš[™ØÙK[Š
NŠKœÝ]\ÏX[™[™ØK[Š[˜Ý[ÛŠ
^ÙKœÝ]\ÏOOX[™[™Ø	‰ŠKœÝ]\ÏX[š[YK˜[YO]
_K[˜Ý[ÛŠ
^ÙKœÝ]\ÏOOX[™[™Ø	‰ŠKœÝ]\ÏX™Z™XÝYKœ™X\ÛÛ]
_JJKKœÝ]\Ê^ØØ\ÙX[š[Yœ™]\›ˆK˜[YNØØ\ÙX™Z™XÝY›ÝÈKœ™X\ÛÛŸ_]›ÝÈ_Y[˜Ý[ÛˆŠK‹KKÊ^Ý˜\ˆÏ]\[ÙˆNÊÏOOX[™Yš[™YÏOOX›ÛÛX[˜
I‰ŠO[[
NÝ˜\ˆHLNÚYŠOOO[[
[HLÙ[ÙHÝÚ]Ú
Ê^ØØ\ÙXšYÚ[˜Ø\ÙXÝš[™Ø˜Ø\ÙX[X™\˜›HLØœ™XZÎØØ\ÙXØš™XÝœÝÚ]Ú
K‰	\[ÙŠ^ØØ\ÙH˜Ø\ÙHŽ›HLØœ™XZÎØØ\ÙHŽœ™]\›ˆYK—Ú[š]Š
K—Ü^[ØY
K‹KKÊ__ZYŠ
\™]\›ˆÏ[ÊJKXOOOXØ˜
ÓŠK
N˜KÊÊOÊOXO[[	‰ŠO[œ™\XÙJK		‹Ø
JØØ
KŠË‹K[˜Ý[ÛŠJ^Ü™]\›ˆ_JJN›ÈO[[	‰ŠJÊI‰ŠÏZÊËJÊËšÙ^OO[[I‰™KšÙ^OOO[ËšÙ^OØŠ
ÛËšÙ^JKœ™\XÙJK		‹Ø
JØØ
JÛ
JK‹œ\Ú
ÊJKNÛLÝ˜\ˆOXOOOXØ˜˜JØ˜ÚYŠÊJJY›ÜŠ˜\ˆLÙK›[™ÝÙ
ÊÊXOYVÙKÏ]JÓŠK
K
ÏQŠK‹KËÊNÙ[ÙHYŠYÊJK\[ÙˆOX[˜Ý[Û˜
Y›ÜŠOY˜Ø[
JKLÈJOYK›™^

JK™Û™NÊXOXK˜[YKÏ]JÓŠK
ÊÊK
ÏQŠK‹KËÊNÙ[ÙHYŠÏOOXØš™XÝ
^ÚYŠ\[ÙˆK[OX[˜Ý[Û˜
\™]\›ˆŠ
JK‹KKÊNÝ›ÝÈTÝš[™ÊJK\œ›ÜŠØš™XÝÈ\™H›Ý˜[Y\ÈH™XXÝÚ[
›Ý[™ˆ
ÊOOXÛØš™XÝØš™XÝXØØš™XÝÚ]Ù^\ÈØ
ÓØš™XÝšÙ^\ÊJKš›Ú[Š
JØXœŠJØ
KˆYˆ[ÝHYX[È™[™\ˆHÛÛXÝ[ÛˆÙˆÚ[™[‹\ÙH[ˆ\œ˜^H[œÝXY˜
_\™]\›ˆY[˜Ý[ÛˆJKŠ^ÚYŠOO[[
\™]\›ˆNÝ˜\ˆV×KOLÜ™]\›ˆŠK‹[˜Ý[ÛŠJ^Ü™]\›ˆ˜Ø[
‹KJÊÊ_JKŸY[˜Ý[Ûˆ
J^ÚYŠK—ÜÝ]\ÏOOKLJ^Ý˜\ˆYK—Ü™\Ý[]

NÛ‹[Š[˜Ý[ÛŠ
^ÊK—ÜÝ]\ÏOOLK—ÜÝ]\ÏOOKLJI‰ŠK—ÜÝ]\ÏLKK—Ü™\Ý[]‹œÝ]\ÏOO]›ÚY	‰Š‹œÝ]\ÏX[š[Y‹˜[YO]
J_K[˜Ý[ÛŠ
^ÊK—ÜÝ]\ÏOOLK—ÜÝ]\ÏOOKLJI‰ŠK—ÜÝ]\ÏL‹K—Ü™\Ý[]‹œÝ]\ÏOO]›ÚY	‰Š‹œÝ]\ÏX™Z™XÝY‹œ™X\ÛÛ]
J_JKK—ÜÝ]\ÏOOKLI‰ŠK—ÜÝ]\ÏLK—Ü™\Ý[[Š_ZYŠK—ÜÝ]\ÏOOLJ\™]\›ˆK—Ü™\Ý[™Y˜][Ý›ÝÈK—Ü™\Ý[]˜\ˆ]\[Ùˆ™\Ü\œ›ÜOX[˜Ý[Û˜Ü™\Ü\œ›ÜŽ™[˜Ý[ÛŠJ^ÚYŠ\[ÙˆÚ[™ÝÏOXØš™XÝ	‰\[ÙˆÚ[™ÝË‘\œ›Ü‘]™[OX[˜Ý[Û˜
^Ý˜\ˆ[™]ÈÚ[™ÝË‘\œ›Ü‘]™[
\œ›Ü˜ØX˜›\ÎˆLØ[˜Ù[X›NˆLY\ÜØYÙN\[ÙˆOOXØš™XÝ	‰™I‰\[ÙˆK›Y\ÜØYÙOOXÝš[™ØÔÝš[™ÊK›Y\ÜØYÙJN”Ýš[™ÊJK\œ›ÜŽ™_JNÚYŠ]Ú[™ÝË™\Ü]Ú]™[

J\™]\›ŸY[ÙHYŠ\[Ùˆ›ØÙ\ÜÏOXØš™XÝ	‰\[Ùˆ›ØÙ\ÜË™[Z]OX[˜Ý[Û˜
^Ü›ØÙ\ÜË™[Z]
[˜Ø]YÚ^Ù\[Û˜JNÜ™]\›ŸXÛÛœÛÛK™\œ›ÜŠJ_NÙ[˜Ý[ÛˆYJJ^Ý˜\ˆQK•^ßNÛ‹\\Ï]OO[[Û[\\ËK•[ŽÝž^Ý˜\ˆYJ
KOQK”ÎÚHOO[[	‰šJ‹ŠK\[ÙˆOXØš™XÝ	‰œ‰‰\[Ùˆ‹[OX[˜Ý[Û˜	‰œ‹[ŠŠ_XØ]Ú
J^ÔŠJ_Yš[˜[^ÝOO[[	‰›‹\\ÈOO[[	‰Š\\Ï[‹\\ÊKK•]_Y[˜Ý[ÛˆJJ^Ý˜\ˆQK•ÚYŠOO[[
^Ý˜\ˆ]\\ÎÛOO[[Ý\\ÏVÙWN›‹š[™^ÙŠJOOOKLI‰›‹œ\Ú
J_Y[ÙHYJK˜š[™
[JJ_]˜\ˆ™O^ÛX\’K›Ü‘XXÚ™[˜Ý[ÛŠKŠ^ÒJK[˜Ý[ÛŠ
^Ý˜\J\Ë\™Ý[Y[Ê_KŠ_KÛÝ[™[˜Ý[ÛŠJ^Ý˜\ˆLÜ™]\›ˆJK[˜Ý[ÛŠ
^Ý
ÊßJKKÐ\œ˜^N™[˜Ý[ÛŠJ^Ü™]\›ˆJK[˜Ý[ÛŠJ^Ü™]\›ˆ_J_×_KÛ›N™[˜Ý[ÛŠJ^ÚYŠPJJJ]›ÝÈ\œ›ÜŠ™XXÝÚ[™[‹›Û›H^XÝYÈ™XÙZ]™HHÚ[™ÛH™XXÝ[[Y[Ú[˜
NÜ™]\›ˆ__NÙKXÝ]š]O\KÚ[™[[™KKÛÛ\Û™[X‹K‘œ˜YÛY[\‹K”›Ùš[\XKK”\™PÛÛ\Û™[TËK”ÝšXÝ[ÙOZKK”Ý\Ü[œÙO]KK•šY]Õ˜[œÚ][Û[KK—×ÐÓQS•ÒS•T“S×Ñ×Ó“ÕÕTÑWÓÔ—ÕÐT“—ÕTÑT”×ÕVWÐÐS““ÕÕTÔQOQKK—×ÐÓÓTST—Ô•S•SQO^××Ü›Ý××Î›[Î™[˜Ý[ÛŠJ^Ü™]\›ˆK’\ÙSY[[ÐØXÚJJ__KK˜Y˜[œÚ][Û•\O]KK˜ØXÚOY[˜Ý[ÛŠJ^Ü™]\›ˆ[˜Ý[ÛŠ
^Ü™]\›ˆK˜\J[\™Ý[Y[Ê__KK˜ØXÚTÚYÛ˜[Y[˜Ý[ÛŠ
^Ü™]\›ˆ[KK˜ÛÛ™Q[[Y[Y[˜Ý[ÛŠKŠ^ÚYŠOO[[
]›ÝÈ\œ›ÜŠH\™Ý[Y[]\Ý™HH™XXÝ[[Y[][ÝH\ÜÙY
ÙJØ˜
NÝ˜\ˆ]ŠßKKœ›ÜÊKOYKšÙ^NÚYŠO[[
Y›ÜŠH[ˆšÙ^HOO]›ÚY	‰ŠOX
ÝšÙ^JK
HQ˜Ø[
J_OOOXÙ^XOOOX×ÜÙ[˜OOOX×ÜÛÝ\˜ÙXOOOX™Y˜	‰œ™YOO]›ÚY
–ØWO]ØWJNÝ˜\ˆOX\™Ý[Y[Ë›[™ÝLŽÚYŠOOOLJ\‹˜Ú[™[[ŽÙ[ÙHYŠOJ^Ù›ÜŠ˜\ˆÏP\œ˜^JJKÏLÜÏNÜÊÊÊ[ÖÜ×OX\™Ý[Y[ÖÜÊÌ—NÜ‹˜Ú[™[[ß\™]\›ˆÊK\KKŠ_KK˜Ü™X]PÛÛ^Y[˜Ý[ÛŠJ^Ü™]\›ˆO^É	\[ÙŽœËØÝ\œ™[˜[YN™KØÝ\œ™[˜[YLŽ™KÝ™XYÛÝ[Œ›ÝšY\Ž›[ÛÛœÝ[Y\Ž›[KK”›ÝšY\YKKÛÛœÝ[Y\^É	\[ÙŽ›ËØÛÛ^™_K_KK˜Ü™X]Q[[Y[Y[˜Ý[ÛŠKŠ^Ý˜\ˆ‹O^ßKO[[ÚYŠO[[
Y›ÜŠˆ[ˆšÙ^HOO]›ÚY	‰ŠOX
ÝšÙ^JK
Q˜Ø[
ŠI‰œˆOOXÙ^X	‰œˆOOX×ÜÙ[˜	‰œˆOOX×ÜÛÝ\˜ÙX	‰ŠVÜ—O]Ü—JNÝ˜\ˆÏX\™Ý[Y[Ë›[™ÝLŽÚYŠÏOOLJZK˜Ú[™[[ŽÙ[ÙHYŠOÊ^Ù›ÜŠ˜\ˆÏP\œ˜^JÊKLÛÎÛ
ÊÊ\ÖÛOX\™Ý[Y[ÖÛ
Ì—NÚK˜Ú[™[\ßZYŠI‰™K™Y˜][›ÜÊY›ÜŠˆ[ˆÏYK™Y˜][›ÜËÊZVÜ—OOO]›ÚY	‰ŠVÜ—O[ÖÜ—JNÜ™]\›ˆÊKKJ_KK˜Ü™X]T™YY[˜Ý[ÛŠ
^Ü™]\›žØÝ\œ™[›[_KK™›ÜØ\™™YY[˜Ý[ÛŠJ^Ü™]\›žÉ	\[ÙŽ›™[™\Ž™__KKš\Õ˜[Y[[Y[PKK›^žOY[˜Ý[ÛŠJ^Ü™]\›žÉ	\[ÙŽ™‹Ü^[ØYž×ÜÝ]\Î‹LKÜ™\Ý[™_KÚ[š]“_KK›Y[[ÏY[˜Ý[ÛŠK
^Ü™]\›žÉ	\[ÙŽ™\N™KÛÛ\\™NOO]›ÚYÛ[_KKœÝ\˜[œÚ][ÛYYKK[œÝX›WÝ\ÙPØXÚT™Yœ™\ÚY[˜Ý[ÛŠ
^Ü™]\›ˆK’\ÙPØXÚT™Yœ™\Ú

_KK\ÙOY[˜Ý[ÛŠJ^Ü™]\›ˆK’\ÙJJ_KK\ÙPXÝ[Û”Ý]OY[˜Ý[ÛŠKŠ^Ü™]\›ˆK’\ÙPXÝ[Û”Ý]JKŠ_KK\ÙPØ[˜XÚÏY[˜Ý[ÛŠK
^Ü™]\›ˆK’\ÙPØ[˜XÚÊK
_KK\ÙPÛÛ^Y[˜Ý[ÛŠJ^Ü™]\›ˆK’\ÙPÛÛ^
J_KK\ÙQXYÕ˜[YOY[˜Ý[ÛŠ
^ßKK\ÙQY™\œ™Y˜[YOY[˜Ý[ÛŠK
^Ü™]\›ˆK’\ÙQY™\œ™Y˜[YJK
_KK\ÙQY™™XÝY[˜Ý[ÛŠK
^Ü™]\›ˆK’\ÙQY™™XÝ
K
_KK\ÙQY™™XÝ]™[Y[˜Ý[ÛŠJ^Ü™]\›ˆK’\ÙQY™™XÝ]™[
J_KK\ÙRYY[˜Ý[ÛŠ
^Ü™]\›ˆK’\ÙRY

_KK\ÙR[\\˜]]™R[™OY[˜Ý[ÛŠKŠ^Ü™]\›ˆK’\ÙR[\\˜]]™R[™JKŠ_KK\ÙR[œÙ\[Û‘Y™™XÝY[˜Ý[ÛŠK
^Ü™]\›ˆK’\ÙR[œÙ\[Û‘Y™™XÝ
K
_KK\ÙS^[Ý]Y™™XÝY[˜Ý[ÛŠK
^Ü™]\›ˆK’\ÙS^[Ý]Y™™XÝ
K
_KK\ÙSY[[ÏY[˜Ý[ÛŠK
^Ü™]\›ˆK’\ÙSY[[ÊK
_KK\ÙSÜ[Z\ÝXÏY[˜Ý[ÛŠK
^Ü™]\›ˆK’\ÙSÜ[Z\ÝXÊK
_KK\ÙT™YXÙ\Y[˜Ý[ÛŠKŠ^Ü™]\›ˆK’\ÙT™YXÙ\ŠKŠ_KK\ÙT™YY[˜Ý[ÛŠJ^Ü™]\›ˆK’\ÙT™YŠJ_KK\ÙTÝ]OY[˜Ý[ÛŠJ^Ü™]\›ˆK’\ÙTÝ]JJ_KK\ÙTÞ[˜Ñ^\›˜[ÝÜ™OY[˜Ý[ÛŠKŠ^Ü™]\›ˆK’\ÙTÞ[˜Ñ^\›˜[ÝÜ™JKŠ_KK\ÙU˜[œÚ][ÛY[˜Ý[ÛŠ
^Ü™]\›ˆK’\ÙU˜[œÚ][ÛŠ
_KK™\œÚ[ÛXNKŒËŒJJKŽ]\Ê

K
OOžÝ™^ÜÏ[Ž]

_JJKN]\Ê
OOžÝ˜\ˆ\Ž]

NÙ[˜Ý[ÛˆŠJ^Ý˜\ˆXÎ‹ËÜ™XXÝ™]‹Ù\œ›ÜœËØ
ÙNÚYŠO\™Ý[Y[Ë›[™Ý
^Ý
ÏXØ\™ÜÖ×OX
Ù[˜ÛÙUT’PÛÛ\Û™[
\™Ý[Y[ÖÌWJNÙ›ÜŠ˜\ˆLŽÛ\™Ý[Y[Ë›[™ÝÛŠÊÊ]
ÏX	˜\™ÜÖ×OX
Ù[˜ÛÙUT’PÛÛ\Û™[
\™Ý[Y[ÖÛ—J_\™]\›˜Z[šYšYY™XXÝ\œ›ÜˆØ
ÙJØÈš\Ú]
Ý
Ø›ÜˆH[Y\ÜØYÙHÜˆ\ÙHH›Û‹[Z[šYšYY]ˆ[š\›Û›Y[›Üˆ[\œ›ÜœÈ[™Y][Û˜[[[Ø\›š[™ÜË˜Y[˜Ý[ÛˆŠ
^ß]˜\ˆO^ÙžÙŽœ‹Ž™[˜Ý[ÛŠ
^Ý›ÝÈ\œ›ÜŠŠLŒŠJ_Kœ‹Îœ‹œ‹Nœ‹œ‹Îœ‹NœŸKŒš[™ÓS›ÙN›[KOTÞ[X›Û™›ÜŠ™XXÝœÜ[
KÏTÞ[X›Û™›ÜŠ™XXÝœ™XÛÝ™\˜X›X
KÏTÞ[X›Û™›ÜŠ™XXÝ›Ü[Z\ÝX×ÚÙ^X
NÙ[˜Ý[Ûˆ
KŠ^Ý˜\ˆLÏ\™Ý[Y[Ë›[™Ý	‰˜\™Ý[Y[ÖÌ×HOO]›ÚYØ\™Ý[Y[ÖÌ×N›[Ü™]\›žÉ	\[ÙŽ˜KÙ^NœO[[Û[œOO\ÏÜÎ˜
Ü‹Ú[™[Ž™KÛÛZ[™\’[™›Î[\[Y[][ÛŽ›Ÿ_]˜\ˆO]—×ÐÓQS•ÒS•T“S×Ñ×Ó“ÕÕTÑWÓÔ—ÕÐT“—ÕTÑT”×ÕVWÐÐS““ÕÕTÔQNÙ[˜Ý[Ûˆ
K
^ÚYŠOOOX›Û
\™]\›˜ÚYŠ\[ÙˆOXÝš[™Ø
\™]\›ˆOOX\ÙKXÜ™Y[X[ØÝ˜YK—×ÑÓWÒS•T“S×Ñ×Ó“ÕÕTÑWÓÔ—ÕÐT“—ÕTÑT”×ÕVWÐÐS““ÕÕTÔQOZKK˜œ›ÝÜÙ\Y[˜Ý[ÛŠJ^Ü™]\›žÉ	\[ÙŽ›ËÜ™X\ÛÛŽ™__KK˜Ü™X]TÜ[Y[˜Ý[ÛŠK
^Ý˜\ˆL\™Ý[Y[Ë›[™Ý	‰˜\™Ý[Y[ÖÌ—HOO]›ÚYØ\™Ý[Y[ÖÌ—N›[ÚYŠ]››ÙU\HOOLI‰››ÙU\HOONI‰››ÙU\HOOLLJ]›ÝÈ\œ›ÜŠŠŽNJJNÜ™]\›ˆ
K[Š_KK™›\ÚÞ[˜ÏY[˜Ý[ÛŠJ^Ý˜\ˆ]K•ZKœÝž^ÚYŠK•[[KœL‹J\™]\›ˆJ
_Yš[˜[^ÝK•]Kœ[‹K™™Š
__KKœ™XÛÛ›™XÝY[˜Ý[ÛŠK
^Ý\[ÙˆOOXÝš[™Ø	‰ŠÊ]˜Ü›ÜÜÓÜšYÚ[‹]\[ÙˆOXÝš[™ØÝOOX\ÙKXÜ™Y[X[ØÝ˜›ÚY
N[[K™ÊK
J_KKœ™Y™]Ú”ÏY[˜Ý[ÛŠJ^Ý\[ÙˆOOXÝš[™Ø	‰šK™‘
J_KKœ™Z[š]Y[˜Ý[ÛŠK
^ÚYŠ\[ÙˆOOXÝš[™Ø	‰	‰\[Ùˆ˜\ÏOXÝš[™Ø
^Ý˜\ˆ]˜\ËY
‹˜Ü›ÜÜÓÜšYÚ[ŠKO]\[Ùˆš[YÜš]OOXÝš[™ØÝš[YÜš]N›ÚYÏ]\[Ùˆ™™]Úš[Üš]OOXÝš[™ØÝ™™]Úš[Üš]N›ÚYÛOOXÝ[XÚK™”ÊK\[Ùˆœ™XÙY[˜ÙOOXÝš[™ØÝœ™XÙY[˜ÙN›ÚYØÜ›ÜÜÓÜšYÚ[Žœ‹[YÜš]N˜K™]Úš[Üš]N›ßJN›OOXØÜš\	‰šK™–
KØÜ›ÜÜÓÜšYÚ[Žœ‹[YÜš]N˜K™]Úš[Üš]N›Ë›Û˜ÙN\[Ùˆ››Û˜ÙOOXÝš[™ØÝ››Û˜ÙN›ÚYJ__KKœ™Z[š][Ù[OY[˜Ý[ÛŠK
^ÚYŠ\[ÙˆOOXÝš[™Ø
ZYŠ\[ÙˆOXØš™XÝ	‰
^ÚYŠ˜\ÏO[[˜\ÏOOXØÜš\
^Ý˜\ˆY
˜\Ë˜Ü›ÜÜÓÜšYÚ[ŠNÚK™“JKØÜ›ÜÜÓÜšYÚ[Ž›‹[YÜš]N\[Ùˆš[YÜš]OOXÝš[™ØÝš[YÜš]N›ÚY›Û˜ÙN\[Ùˆ››Û˜ÙOOXÝš[™ØÝ››Û˜ÙN›ÚY™]Úš[Üš]N\[Ùˆ™™]Úš[Üš]OOXÝš[™ØÝ™™]Úš[Üš]N›ÚYJ__Y[ÙHÏÚK™“JJ_KKœ™[ØYY[˜Ý[ÛŠK
^ÚYŠ\[ÙˆOOXÝš[™Ø	‰\[ÙˆOXØš™XÝ	‰	‰\[Ùˆ˜\ÏOXÝš[™Ø
^Ý˜\ˆ]˜\ËY
‹˜Ü›ÜÜÓÜšYÚ[ŠNÚK™“
K‹ØÜ›ÜÜÓÜšYÚ[Žœ‹[YÜš]N\[Ùˆš[YÜš]OOXÝš[™ØÝš[YÜš]N›ÚY›Û˜ÙN\[Ùˆ››Û˜ÙOOXÝš[™ØÝ››Û˜ÙN›ÚY\N\[Ùˆ\OOXÝš[™ØÝ\N›ÚY™]Úš[Üš]N\[Ùˆ™™]Úš[Üš]OOXÝš[™ØÝ™™]Úš[Üš]N›ÚY™Y™\œ™\”ÛXÞN\[Ùˆœ™Y™\œ™\”ÛXÞOOXÝš[™ØÝœ™Y™\œ™\”ÛXÞN›ÚY[XYÙTÜ˜ÔÙ]\[Ùˆš[XYÙTÜ˜ÔÙ]OXÝš[™ØÝš[XYÙTÜ˜ÔÙ]›ÚY[XYÙTÚ^™\Î\[Ùˆš[XYÙTÚ^™\ÏOXÝš[™ØÝš[XYÙTÚ^™\Î›ÚYYYXN\[Ùˆ›YYXOOXÝš[™ØÝ›YYXN›ÚYJ__KKœ™[ØY[Ù[OY[˜Ý[ÛŠK
^ÚYŠ\[ÙˆOOXÝš[™Ø
ZYŠ
^Ý˜\ˆY
˜\Ë˜Ü›ÜÜÓÜšYÚ[ŠNÚK™›JKØ\Î\[Ùˆ˜\ÏOXÝš[™Ø	‰˜\ÈOOXØÜš\Ý˜\Î›ÚYÜ›ÜÜÓÜšYÚ[Ž›‹[YÜš]N\[Ùˆš[YÜš]OOXÝš[™ØÝš[YÜš]N›ÚY›Û˜ÙN\[Ùˆ››Û˜ÙOOXÝš[™ØÝ››Û˜ÙN›ÚY™]Úš[Üš]N\[Ùˆ™™]Úš[Üš]OOXÝš[™ØÝ™™]Úš[Üš]N›ÚYJ_Y[ÙHK™›JJ_KKœ™\]Y\Ý›Ü›T™\Ù]Y[˜Ý[ÛŠJ^ÚK™œŠJ_KK[œÝX›WØ˜]ÚY\]\ÏY[˜Ý[ÛŠK
^Ü™]\›ˆJ
_KK\ÙQ›Ü›TÝ]OY[˜Ý[ÛŠKŠ^Ü™]\›ˆK’\ÙQ›Ü›TÝ]JKŠ_KK\ÙQ›Ü›TÝ]\ÏY[˜Ý[ÛŠ
^Ü™]\›ˆK’\ÙRÜÝ˜[œÚ][Û”Ý]\Ê
_KK™\œÚ[ÛXNKŒËŒJJKN]\Ê

K
OOžÙ[˜Ý[ÛˆŠ
^ÚYŠJ\[Ùˆ×Ô‘PPÕÑU•ÓÓ×ÑÓÐSÒÓÒ××Ï˜X\[Ùˆ×Ô‘PPÕÑU•ÓÓ×ÑÓÐSÒÓÒ××Ë˜ÚXÚÑÑHOX[˜Ý[Û˜
J]ž^××Ô‘PPÕÑU•ÓÓ×ÑÓÐSÒÓÒ××Ë˜ÚXÚÑÑJŠ_XØ]Ú
J^ØÛÛœÛÛK™\œ›ÜŠJ__[Š
K™^ÜÏZN]

_JJKÎ]\Ê
OOžÙ[˜Ý[Ûˆ
K
^Ý˜\ˆYK›[™ÝÙKœ\Ú

NØN™›ÜŠÌŽÊ^Ý˜\ˆ[‹LOŒKOYVÜ—NÚYŠJK
JYVÜ—O]VÛ—OXK\ŽÙ[ÙHœ™XZÈ__Y[˜Ý[ÛˆŠJ^Ü™]\›ˆK›[™ÝOOLÛ[™VÌ_Y[˜Ý[ÛˆŠJ^ÚYŠK›[™ÝOOL
\™]\›ˆ[Ý˜\ˆYVÌKYKœÜ

NÚYŠˆOO]
^ÙVÌO[ŽØN™›ÜŠ˜\ˆLOYK›[™ÝÏXOŒNÜÎÊ^Ý˜\ˆÏLŠŠŠÌJKLKYVÜ×KO\ÊÌKYVÝWNÚYŠšJŠJ]OI‰ŒšJ
OÊVÜ—OYVÝWO[‹]JNŠVÜ—O[VÜ×O[‹\ÊNÙ[ÙHYŠOI‰ŒšJŠJYVÜ—OYVÝWO[‹]NÙ[ÙHœ™XZÈ__\™]\›ˆY[˜Ý[ÛˆJK
^Ý˜\ˆYKœÛÜ[™^]œÛÜ[™^Ü™]\›ˆOOLÙKšY]šY›ŸZYŠK[œÝX›WÛ›ÝÏ]›ÚY\[Ùˆ\™›Ü›X[˜ÙOOXØš™XÝ	‰\[Ùˆ\™›Ü›X[˜ÙK››ÝÏOX[˜Ý[Û˜
^Ý˜\ˆO\\™›Ü›X[˜ÙNÙK[œÝX›WÛ›ÝÏY[˜Ý[ÛŠ
^Ü™]\›ˆK››ÝÊ
__Y[Ù^Ý˜\ˆÏQ]KÏ[Ë››ÝÊ
NÙK[œÝX›WÛ›ÝÏY[˜Ý[ÛŠ
^Ü™]\›ˆË››ÝÊ
K\ß_]˜\ˆV×KOV×KLK[[LËOHLKHLKÏHLKÏHLK]\[ÙˆÙ][Y[Ý]OX[˜Ý[Û˜ÜÙ][Y[Ý]›[O]\[ÙˆÛX\•[Y[Ý]OX[˜Ý[Û˜ØÛX\•[Y[Ý]›[]\[ÙˆÙ][[YYX]OXÜÙ][[YYX]N›[Ù[˜Ý[Ûˆ
J^Ù›ÜŠ˜\ˆO[ŠJNÚHOO[[Ê^ÚYŠK˜Ø[˜XÚÏOO[[
\ŠJNÙ[ÙHYŠKœÝ\[YOYJ\ŠJKKœÛÜ[™^ZK™^\˜][Û•[YK
JNÙ[ÙHœ™XZÎÚO[ŠJ__Y[˜Ý[ÛˆÊJ^ÚYŠÏHLK
JKZ
ZYŠŠ
HOO[[
ZHLß
ÏHLÊ
JNÙ[Ù^Ý˜\ˆ[ŠJNÝOO[[	‰“JËœÝ\[YKYJ__]˜\ˆÏHLKÏKLKMKOKLNÙ[˜Ý[Ûˆ

^Ü™]\›ˆÏÈLˆJK[œÝX›WÛ›ÝÊ
KQO
_Y[˜Ý[ÛˆÊ
^ÚYŠÏHLKÊ^Ý˜\ˆYK[œÝX›WÛ›ÝÊ
NÑO]Ý˜\ˆOHLÝž^ØNžÚHLKÉ‰ŠÏHLKJÊKÏKLJKOHLÝ˜\ˆO\Ýž^ØŽžÙ›ÜŠ

K[Š
NÙˆOO[[	‰ˆJ‹™^\˜][Û•[YO	‰‘

JNÊ^Ý˜\ˆÏY‹˜Ø[˜XÚÎÚYŠ\[ÙˆÏOX[˜Ý[Û˜
^Ù‹˜Ø[˜XÚÏ[[Y‹œš[Üš]S]™[Ý˜\ˆÏ[Ê‹™^\˜][Û•[YO]
NÚYŠYK[œÝX›WÛ›ÝÊ
K\[ÙˆÏOX[˜Ý[Û˜
^Ù‹˜Ø[˜XÚÏ\Ë

KOHLØœ™XZÈŸYOO[Š
I‰œŠ
K

_Y[ÙHŠ
NÙ[Š
_ZYŠˆOO[[
ZOHLÙ[Ù^Ý˜\ˆ[ŠJNÙOO[[	‰“JËœÝ\[YK]
KOHL__Xœ™XZÈ_Yš[˜[^Ù[[XKOHL_ZO]›ÚY_Yš[˜[^ÚOÚÊ
NÏHL___]˜\ˆÎÚYŠ\[ÙˆOX[˜Ý[Û˜
ZÏY[˜Ý[ÛŠ
^ØŠÊ_NÙ[ÙHYŠ\[ÙˆY\ÜØYÙPÚ[›™[X
^Ý˜\ˆO[™]ÈY\ÜØYÙPÚ[›™[PKœÜŽÐKœÜK›Û›Y\ÜØYÙOSËÏY[˜Ý[ÛŠ
^Ú‹œÜÝY\ÜØYÙJ[
__Y[ÙHÏY[˜Ý[ÛŠ
^ÝŠË
_NÙ[˜Ý[ÛˆJŠ^ÝÏ]Š[˜Ý[ÛŠ
^Ý
K[œÝX›WÛ›ÝÊ
J_KŠ_YK[œÝX›WÒYTš[Üš]OMKK[œÝX›WÒ[[YYX]Tš[Üš]OLKK[œÝX›WÓÝÔš[Üš]OMK[œÝX›WÓ›Ü›X[š[Üš]OLËK[œÝX›WÔ›Ùš[[™Ï[[K[œÝX›WÕ\Ù\›ØÚÚ[™Ôš[Üš]OL‹K[œÝX›WØØ[˜Ù[Ø[˜XÚÏY[˜Ý[ÛŠJ^ÙK˜Ø[˜XÚÏ[[KK[œÝX›WÙ›Ü˜ÙQœ˜[YT˜]OY[˜Ý[ÛŠJ^Ì™_LOOØÛÛœÛÛK™\œ›ÜŠ›Ü˜ÙQœ˜[YT˜]HZÙ\ÈHÜÚ]]™H[™]ÙY[ˆ[™LK›Ü˜Ú[™Èœ˜[YH˜]\ÈYÚ\ˆ[ˆLHœÈ\È›ÝÝ\ÜY
N•LOÓX]™›ÛÜŠYLËÙJN_KK[œÝX›WÙÙ]Ý\œ™[š[Üš]S]™[Y[˜Ý[ÛŠ
^Ü™]\›ˆKK[œÝX›WÛ™^Y[˜Ý[ÛŠJ^ÜÝÚ]Ú

^ØØ\ÙHN˜Ø\ÙHŽ˜Ø\ÙHÎ˜\ˆLÎØœ™XZÎÙY˜][\]˜\ˆ\Ü]Ýž^Ü™]\›ˆJ
_Yš[˜[^Ü[Ÿ_KK[œÝX›WÜ™\]Y\ÝZ[Y[˜Ý[ÛŠ
^×ÏHLKK[œÝX›WÜ[•Ú]š[Üš]OY[˜Ý[ÛŠK
^ÜÝÚ]Ú
J^ØØ\ÙHN˜Ø\ÙHŽ˜Ø\ÙHÎ˜Ø\ÙH˜Ø\ÙHN˜œ™XZÎÙY˜][™OLß]˜\ˆ\ÜYNÝž^Ü™]\›ˆ

_Yš[˜[^Ü[Ÿ_KK[œÝX›WÜØÚY[PØ[˜XÚÏY[˜Ý[ÛŠ‹KJ^Ý˜\ˆÏYK[œÝX›WÛ›ÝÊ
NÜÝÚ]Ú
\[ÙˆOOXØš™XÝ	‰˜OÊOXK™[^KO]\[ÙˆOOX[X™\˜	‰ŒOÛÊØN›ÊN˜O[ËŠ^ØØ\ÙHN˜\ˆÏKLNØœ™XZÎØØ\ÙHŽœÏLLØœ™XZÎØØ\ÙHNœÏLLÌÍÍNŒÎØœ™XZÎØØ\ÙHœÏLYMØœ™XZÎÙY˜][œÏMYLß\™]\›ˆÏXJÜË^ÚY™
ÊËØ[˜XÚÎšKš[Üš]S]™[œ‹Ý\[YN˜K^\˜][Û•[YNœËÛÜ[™^‹L_KO›ÏÊ‹œÛÜ[™^XK
KŠKŠ
OOO[[	‰œOO[ŠJI‰ŠÏÊJÊKÏKLJN™ÏHLJËK[ÊJJNŠ‹œÛÜ[™^\Ë
ŠK_
HLß
ÏHLÊ
JJJKŸKK[œÝX›WÜÚÝ[ZY[QK[œÝX›WÝÜ˜\Ø[˜XÚÏY[˜Ý[ÛŠJ^Ý˜\ˆ\Ü™]\›ˆ[˜Ý[ÛŠ
^Ý˜\ˆ\Ü]Ýž^Ü™]\›ˆK˜\J\Ë\™Ý[Y[Ê_Yš[˜[^Ü[Ÿ___JJKÎ]\Ê

K
OOžÝ™^ÜÏ[Î]

_JJKÎ]\Ê
OOžÝ˜\ˆ\Î]

K\Ž]

KXN]

NÙ[˜Ý[ÛˆJJ^Ý˜\ˆXÎ‹ËÜ™XXÝ™]‹Ù\œ›ÜœËØ
ÙNÚYŠO\™Ý[Y[Ë›[™Ý
^Ý
ÏXØ\™ÜÖ×OX
Ù[˜ÛÙUT’PÛÛ\Û™[
\™Ý[Y[ÖÌWJNÙ›ÜŠ˜\ˆLŽÛ\™Ý[Y[Ë›[™ÝÛŠÊÊ]
ÏX	˜\™ÜÖ×OX
Ù[˜ÛÙUT’PÛÛ\Û™[
\™Ý[Y[ÖÛ—J_\™]\›˜Z[šYšYY™XXÝ\œ›ÜˆØ
ÙJØÈš\Ú]
Ý
Ø›ÜˆH[Y\ÜØYÙHÜˆ\ÙHH›Û‹[Z[šYšYY]ˆ[š\›Û›Y[›Üˆ[\œ›ÜœÈ[™Y][Û˜[[[Ø\›š[™ÜË˜Y[˜Ý[ÛˆJJ^Ü™]\›ˆJY_K››ÙU\HOOLI‰™K››ÙU\HOONI‰™K››ÙU\HOOLLJ_Y[˜Ý[ÛˆÊJ^Ù›ÜŠ˜\ˆYK]Û‰‰ˆ[‹˜[\›˜]NÊ][‹™›YÜÉN	‰ŠO]œ™]\›ŠK]œ™]\›ŽÙ›ÜŠÝœ™]\›ŽÊ]]œ™]\›ŽÜ™]\›ˆYÏOOLÏÙN›[Y[˜Ý[ÛˆÊJ^ÚYŠKYÏOOLLÊ^Ý˜\ˆYK›Y[[Ú^™YÝ]NÚYŠOO[[	‰ŠOYK˜[\›˜]KHOO[[	‰ŠYK›Y[[Ú^™YÝ]JJKOO[[
\™]\›ˆ™ZY˜]Y\™]\›ˆ[Y[˜Ý[Ûˆ
J^ÚYŠKYÏOOLÌJ^Ý˜\ˆYK›Y[[Ú^™YÝ]NÚYŠOO[[	‰ŠOYK˜[\›˜]KHOO[[	‰ŠYK›Y[[Ú^™YÝ]JJKOO[[
\™]\›ˆ™ZY˜]Y\™]\›ˆ[Y[˜Ý[ÛˆJJ^ÚYŠÊJHOOYJ]›ÝÈ\œ›ÜŠJN
J_Y[˜Ý[Ûˆ
J^Ý˜\ˆYK˜[\›˜]NÚYŠ]
^ÚYŠ[ÊJKOO[[
]›ÝÈ\œ›ÜŠJN
JNÜ™]\›ˆOOYOÙN›[Y›ÜŠ˜\ˆYK]ÎÊ^Ý˜\ˆO[‹œ™]\›ŽÚYŠOOO[[
Xœ™XZÎÝ˜\ˆÏXK˜[\›˜]NÚYŠÏOO[[
^ÚYŠXKœ™]\›‹ˆOO[[
^Û\ŽØÛÛ[Y_Xœ™XZßZYŠK˜Ú[OO\Ë˜Ú[
^Ù›ÜŠÏXK˜Ú[ÜÎÊ^ÚYŠÏOO[Š\™]\›ˆJJKNÚYŠÏOO\Š\™]\›ˆJJKÜÏ\ËœÚX›[™ß]›ÝÈ\œ›ÜŠJN
J_ZYŠ‹œ™]\›ˆOO\‹œ™]\›Š[XK\ÎÙ[Ù^Ù›ÜŠ˜\ˆHLKXK˜Ú[ÙÊ^ÚYŠOO[Š^ÛHLXK\ÎØœ™XZßZYŠOO\Š^ÛHLXK\ÎØœ™XZßYYœÚX›[™ßZYŠ[
^Ù›ÜŠ\Ë˜Ú[ÙÊ^ÚYŠOO[Š^ÛHL\ËXNØœ™XZßZYŠOO\Š^ÛHL\ËXNØœ™XZßYYœÚX›[™ßZYŠ[
]›ÝÈ\œ›ÜŠJNJJ__ZYŠ‹˜[\›˜]HOO\Š]›ÝÈ\œ›ÜŠJNL
J_ZYŠ‹YÈOOLÊ]›ÝÈ\œ›ÜŠJN
JNÜ™]\›ˆ‹œÝ]S›ÙK˜Ý\œ™[OO[ÙNY[˜Ý[ÛˆŠJ^Ý˜\ˆYKYÎÚYŠOOM_OOLŸOOLßOOMŠ\™]\›ˆNÙ›ÜŠOYK˜Ú[ÙHOO[[Ê^ÚYŠYŠJKOO[[
\™]\›ˆÙOYKœÚX›[™ß\™]\›ˆ[Y[˜Ý[Ûˆ
K‹‹KJ^Ù›ÜŠÙHOO[[Ê^ÚYŠ
KYÏOOM_KYÏOOLßKYÏOOMŠI‰›ŠK‹KJ_
KYÈOOLŒŸK›Y[[Ú^™YÝ]OOO[[
I‰ŠKYÈOOMI‰™KYÈOOLÊI‰œ
K˜Ú[‹‹KJJ\™]\›ˆLÙOYKœÚX›[™ß\™]\›ˆL_Y[˜Ý[ÛˆJJ^Ù›ÜŠOYKœ™]\›ŽÙHOO[[Ê^ÚYŠKYÏOOLßKYÏOOM_KYÏOOLÊ\™]\›ˆNÙOYKœ™]\›Ÿ\™]\›ˆ[Y[˜Ý[Ûˆ
J^Ý˜\ˆHLNÙ›ÜŠOYKœ™]\›ŽÙHOO[[	‰ŠKYÏOOM	‰ŠHL
KJKYÏOOLßKYÏOOM_KYÏOOLÊJNÊYOYKœ™]\›ŽÜ™]\›ˆY[˜Ý[ÛˆÊJ^Ý˜\ˆVÛ[[K[JJNÜ™]\›ˆOO[[ÊK‹˜Ú[Ù›Ý[™Ù[ŽˆL_JKY[˜Ý[ÛˆÊK‹Š^Ù›ÜŠÛˆOO[[Ê^ÚYŠOO]
\‹™›Ý[™Ù[HLÙ[ÙHYŠ‹YÏOOM_‹YÏOOLß‹YÏOOMŠ^ÚYŠ‹™›Ý[™Ù[Š\™]\›ˆVÌWO[‹LÙVÌO[ŸY[ÙHYŠ
‹YÈOOLŒŸ‹›Y[[Ú^™YÝ]OOO[[
I‰—ÊK‹˜Ú[ŠJ\™]\›ˆLÛ[‹œÚX›[™ß\™]\›ˆL_Y[˜Ý[ÛˆŠJ^ÜÝÚ]Ú
KYÊ^ØØ\ÙHN˜Ø\ÙHÎ˜Ø\ÙHŽœ™]\›ˆKœÝ]S›ÙNØØ\ÙHÎœ™]\›ˆKœÝ]S›ÙK˜ÛÛZ[™\’[™›ÎÙY˜][›ÝÈ\œ›ÜŠJMNJJ__]˜\ˆO[[[[Ù[˜Ý[Ûˆ
KŠ^Ü™]\›ˆOOO[ÈL™OOO]ÊOYKL
NˆL_Y[˜Ý[ÛˆÊKŠ^Ü™]\›ˆOOO[ÊYKLJN™OOO]ÊˆOO[[	‰ŠOYJKL
NˆL_Y[˜Ý[ÛˆÊJ^ÚYŠOOO[[
\™]\›ˆ[ÙÈOYOOO[[Û[™Kœ™]\›ŽÝÚ[JI‰™KYÈOOMI‰™KYÈOOLÉ‰™KYÈOOLÊNÜ™]\›ˆ_[Y[˜Ý[ÛˆÊKŠ^Ù›ÜŠ˜\ˆLOYNÚNÚO[ŠJJ\ŠÊÎÚOLÙ›ÜŠ˜\ˆO]ØNØO[ŠJJZJÊÎÙ›ÜŠÌ‹ZNÊYO[ŠJK‹KNÙ›ÜŠÌK\ŽÊ][Š
KKKNÙ›ÜŠÜ‹KNÊ^ÚYŠOOO]OO[[	‰™OOO]˜[\›˜]J\™]\›ˆNÙO[ŠJK[Š
_\™]\›ˆ[]˜\ˆSØš™XÝ˜\ÜÚYÛ‹OTÞ[X›Û™›ÜŠ™XXÝ™[[Y[
KTÞ[X›Û™›ÜŠ™XXÝ˜[œÚ][Û˜[™[[Y[
KÏTÞ[X›Û™›ÜŠ™XXÝœÜ[
KÏTÞ[X›Û™›ÜŠ™XXÝ™œ˜YÛY[
KOTÞ[X›Û™›ÜŠ™XXÝœÝšXÝÛ[ÙX
KTÞ[X›Û™›ÜŠ™XXÝœ›Ùš[\˜
KOTÞ[X›Û™›ÜŠ™XXÝ˜ÛÛœÝ[Y\˜
KTÞ[X›Û™›ÜŠ™XXÝ˜ÛÛ^
KTÞ[X›Û™›ÜŠ™XXÝ™›ÜØ\™Ü™Y˜
KTÞ[X›Û™›ÜŠ™XXÝœÝ\Ü[œÙX
KOTÞ[X›Û™›ÜŠ™XXÝœÝ\Ü[œÙWÛ\Ý
KTÞ[X›Û™›ÜŠ™XXÝ›Y[[Ø
KTÞ[X›Û™›ÜŠ™XXÝ›^žX
KYOTÞ[X›Û™›ÜŠ™XXÝ˜XÝ]š]X
KOTÞ[X›Û™›ÜŠ™XXÝ›YØXÞWÚY[˜
K™OTÞ[X›Û™›ÜŠ™XXÝ›Y[[×ØØXÚWÜÙ[[™[
K™OTÞ[X›Û™›ÜŠ™XXÝšY]×Ý˜[œÚ][Û˜
KYOTÞ[X›Û™›ÜŠ™XXÝœ™XÛÝ™\˜X›X
KYOTÞ[X›Ûš]\˜]ÜŽÙ[˜Ý[ÛˆŠJ^Ü™]\›ˆ\[ÙˆHOXØš™XÝYOÛ[ŠOXYI‰™VØYW_VØ]\˜]Ü˜K\[ÙˆOOX[˜Ý[Û˜ÙN›[
_]˜\ˆÙOTÞ[X›Û™›ÜŠ™XXÝ˜ÛY[œ™Y™\™[˜ÙX
NÙ[˜Ý[ÛˆÙJJ^ÚYŠOO[[
\™]\›ˆ[ÚYŠ\[ÙˆOOX[˜Ý[Û˜
\™]\›ˆK‰	\[ÙOO[ÙOÛ[™K™\Ü^S˜[Y_K›˜[Y_[ÚYŠ\[ÙˆOOXÝš[™Ø
\™]\›ˆNÜÝÚ]Ú
J^ØØ\ÙHÎœ™]\›˜œ˜YÛY[ØØ\ÙHŽœ™]\›˜›Ùš[\˜ØØ\ÙHNœ™]\›˜ÝšXÝ[ÙXØØ\ÙHŽœ™]\›˜Ý\Ü[œÙXØØ\ÙHNœ™]\›˜Ý\Ü[œÙS\ÝØØ\ÙHYNœ™]\›˜XÝ]š]XØØ\ÙH™Nœ™]\›˜šY]Õ˜[œÚ][Û˜ZYŠ\[ÙˆOOXØš™XÝ
\ÝÚ]Ú
K‰	\[ÙŠ^ØØ\ÙHÎœ™]\›˜Ü[ØØ\ÙHŽœ™]\›ˆK™\Ü^S˜[Y_ÛÛ^ØØ\ÙHNœ™]\›ŠK—ØÛÛ^™\Ü^S˜[Y_ÛÛ^
JØÛÛœÝ[Y\˜ØØ\ÙH˜\ˆYKœ™[™\ŽÜ™]\›ˆOYK™\Ü^S˜[YK_JO]™\Ü^S˜[Y_›˜[Y_OOOXØ›ÜØ\™™Y˜˜›ÜØ\™™YŠ
ÙJØ
X
KNØØ\ÙHœ™]\›ˆYK™\Ü^S˜[Y_[OO[[ÜÙJK\J_Y[[ØØØ\ÙHŽYK—Ü^[ØYOYK—Ú[š]Ýž^Ü™]\›ˆÙJJ
J_XØ]Úß_\™]\›ˆ[]˜\ˆÙOP\œ˜^Kš\Ð\œ˜^KO[‹—×ÐÓQS•ÒS•T“S×Ñ×Ó“ÕÕTÑWÓÔ—ÕÐT“—ÕTÑT”×ÕVWÐÐS““ÕÕTÔQKYO\‹—×ÑÓWÒS•T“S×Ñ×Ó“ÕÕTÑWÓÔ—ÕÐT“—ÕTÑT”×ÕVWÐÐS““ÕÕTÔQKO^Ü[™[™ÎˆLK]N›[Y]Ù›[XÝ[ÛŽ›[K™OV×KOKLNÙ[˜Ý[ÛˆYJJ^Ü™]\›žØÝ\œ™[™__Y[˜Ý[ÛˆJJ^Ìœ_
K˜Ý\œ™[Y™VÜWK™VÜWO[[KKJ_Y[˜Ý[ÛˆÙJK
^ÜJÊË™VÜWOYK˜Ý\œ™[K˜Ý\œ™[]]˜\ˆÙO[YJ[
K™O[YJ[
KYO[YJ[
K™O[YJ[
NÙ[˜Ý[ÛˆJK
^ÜÝÚ]Ú
ÙJYK
KÙJ™KJKÙJÙK[
K››ÙU\J^ØØ\ÙHN˜Ø\ÙHLN™OJO]™ØÝ[Y[[[Y[
I‰ŠOYK›˜[Y\ÜXÙUT’JOÛÙŠJNŒØœ™XZÎÙY˜][šYŠO]YÓ˜[YK]›˜[Y\ÜXÙUT’J][ÙŠ
KOYÝJJNÙ[ÙHÝÚ]Ú
J^ØØ\ÙXÝ™Ø™OLNØœ™XZÎØØ\ÙXX]™OLŽØœ™XZÎÙY˜][™OL_ZJÙJKÙJÙKJ_Y[˜Ý[ÛˆÙJ
^ÚJÙJKJ™JKJYJ_Y[˜Ý[ÛˆÙJJ^Ý˜\ˆYK›Y[[Ú^™YÝ]NÝOO[[	‰Š—ØÝ\œ™[˜[YO]›Y[[Ú^™YÝ]KÙJ™KJJKWÙK˜Ý\œ™[Ý˜\ˆYÝJK\JNÝOO[‰‰ŠÙJ™KJKÙJÙKŠJ_Y[˜Ý[ÛˆÙJJ^Ý™K˜Ý\œ™[OOYI‰ŠJÙJKJ™JJK™K˜Ý\œ™[OOYI‰ŠJ™JK—ØÝ\œ™[˜[YOYJ_]˜\ˆKYNÙ[˜Ý[ÛˆJJ^ÚYŠOOO]›ÚY
]ž^Ý›ÝÈ\œ›ÜŠ
_XØ]Ú
J^Ý˜\ˆYKœÝXÚËš[J
K›X]Ú
×Š
Š]
OÊKÊNÕO]	‰ÌW_YOKLOKœÝXÚËš[™^ÙŠˆ]
OØ
[›Ûž[[Ý\ÏŠX‹LOKœÝXÚËš[™^ÙŠ
OØ[šÛ›ÝÛŽŒŒ˜\™]\›˜˜
ÕJÙJÑY_]˜\ˆÙOHLNÙ[˜Ý[ÛˆÙJK
^ÚYŠY_ÙJ\™]\›˜ÓÙOHLÝ˜\ˆQ\œ›Ü‹œ™\\™TÝXÚÕ˜XÙNÑ\œ›Ü‹œ™\\™TÝXÚÕ˜XÙO]›ÚYÝž^Ý˜\ˆ^Ñ]\›Z[™PÛÛ\Û™[œ˜[YT›ÛÝ™[˜Ý[ÛŠ
^Ýž^ÚYŠ
^Ý˜\ˆY[˜Ý[ÛŠ
^Ý›ÝÈ\œ›ÜŠ
_NÚYŠØš™XÝ™Yš[™T›Ü\J‹œ›ÝÝ\Kœ›ÜÈ‹ÜÙ]™[˜Ý[ÛŠ
^Ý›ÝÈ\œ›ÜŠ
__JK\[Ùˆ™Y›XÝOXØš™XÝ	‰”™Y›XÝ˜ÛÛœÝXÝ
^Ýž^Ô™Y›XÝ˜ÛÛœÝXÝ
‹×J_XØ]Ú
J^Ý˜\ˆY_T™Y›XÝ˜ÛÛœÝXÝ
K×KŠ_Y[Ù^Ýž^Û‹˜Ø[

_XØ]Ú
J^ÜY_[HLNÝž^Ý˜\ˆOSØš™XÝ™Ù]ÝÛ”›Ü\Q\ØÜš\ÜŠKœ›ÝÝ\K›ÜØ
NÓØš™XÝ™Yš[™T›Ü\JKœ›ÝÝ\Kœ›ÜÈ‹ØÛÛ™šYÝ\˜X›NˆLÙ]™[˜Ý[ÛŠ
^Ý›ÝÈ\œ›ÜŠ
__JKHL™]È_Yš[˜[^Û‰‰ŠOOO]›ÚYÙ[]HKœ›ÝÝ\Kœ›ÜÎ“Øš™XÝ™Yš[™T›Ü\JKœ›ÝÝ\Kœ›ÜÈ‹JJ___Y[Ù^Ýž^Ý›ÝÈ\œ›ÜŠ
_XØ]Ú
J^ÜY_JYJ
JI‰\[Ùˆ‹˜Ø]ÚOX[˜Ý[Û˜	‰›‹˜Ø]Ú
[˜Ý[ÛŠ
^ßJ__XØ]Ú
J^ÚYŠI‰œ‰‰\[ÙˆKœÝXÚÏOXÝš[™Ø
\™]\›–ÙKœÝXÚË‹œÝXÚ×_\™]\›–Û[[__NÜ‹‘]\›Z[™PÛÛ\Û™[œ˜[YT›ÛÝ™\Ü^S˜[YOX]\›Z[™PÛÛ\Û™[œ˜[YT›ÛÝÝ˜\ˆOSØš™XÝ™Ù]ÝÛ”›Ü\Q\ØÜš\ÜŠ‹‘]\›Z[™PÛÛ\Û™[œ˜[YT›ÛÝ˜[YX
NÚI‰šK˜ÛÛ™šYÝ\˜X›I‰“Øš™XÝ™Yš[™T›Ü\J‹‘]\›Z[™PÛÛ\Û™[œ˜[YT›ÛÝ›˜[YH‹Ý˜[YN˜]\›Z[™PÛÛ\Û™[œ˜[YT›ÛÝJNÝ˜\ˆO\‹‘]\›Z[™PÛÛ\Û™[œ˜[YT›ÛÝ

KÏXVÌKÏXVÌWNÚYŠÉ‰œÊ^Ý˜\ˆ[ËœÜ]
˜
KO\ËœÜ]
˜
NÙ›ÜŠO\LÜ›[™Ý	‰ˆ[Ü—Kš[˜ÛY\Ê]\›Z[™PÛÛ\Û™[œ˜[YT›ÛÝ
NÊ\ŠÊÎÙ›ÜŠÚOK›[™Ý	‰ˆ]VÚWKš[˜ÛY\Ê]\›Z[™PÛÛ\Û™[œ˜[YT›ÛÝ
NÊZJÊÎÚYŠOO[›[™ÝOOO]K›[™Ý
Y›ÜŠ[›[™ÝLKO]K›[™ÝLNÌO\‰‰ŒZI‰›Ü—HOO]VÚWNÊZKKNÙ›ÜŠÌO\‰‰ŒZNÜ‹KKKKJZYŠÜ—HOO]VÚWJ^ÚYŠˆOOL_HOOLJYÈYŠ‹KKKKKš_Ü—HOO]VÚWJ^Ý˜\ˆX˜
ÛÜ—Kœ™\XÙJ]™]È]
NÜ™]\›ˆK™\Ü^S˜[YI‰™š[˜ÛY\Ê[›Ûž[[Ý\Ï˜
I‰ŠYœ™\XÙJ[›Ûž[[Ý\Ï˜K™\Ü^S˜[YJJK]Ú[JO\‰‰ŒZJNØœ™XZß__Yš[˜[^ÓÙOHLK\œ›Ü‹œ™\\™TÝXÚÕ˜XÙO[Ÿ\™]\›ŠYOÙK™\Ü^S˜[Y_K›˜[YN˜
OÑJŠN˜Y[˜Ý[ÛˆYJK
^ÜÝÚ]Ú
KYÊ^ØØ\ÙHŽ˜Ø\ÙHÎ˜Ø\ÙHNœ™]\›ˆJK\JNØØ\ÙHMŽœ™]\›ˆJ^žX
NØØ\ÙHLÎœ™]\›ˆK˜Ú[OO]	‰OO[[ÑJÝ\Ü[œÙH˜[˜XÚØ
N‘JÝ\Ü[œÙX
NØØ\ÙHNNœ™]\›ˆJÝ\Ü[œÙS\Ý
NØØ\ÙH˜Ø\ÙHMNœ™]\›ˆÙJK\KLJNØØ\ÙHLNœ™]\›ˆÙJK\Kœ™[™\‹LJNØØ\ÙHNœ™]\›ˆÙJK\KL
NØØ\ÙHÌNœ™]\›ˆJXÝ]š]X
NØØ\ÙHÌœ™]\›ˆJšY]Õ˜[œÚ][Û˜
NÙY˜][œ™]\›˜_Y[˜Ý[Ûˆ™JJ^Ýž^Ý˜\ˆX[[ÙÈ
ÏPYJKŠKYKOYKœ™]\›ŽÝÚ[JJNÜ™]\›ˆXØ]Ú
J^Ü™]\›˜‘\œ›ÜˆÙ[™\˜][™ÈÝXÚÎˆ
ÙK›Y\ÜØYÙJØ˜
ÙKœÝXÚß_]˜\ˆYOSØš™XÝœ›ÝÝ\Kš\ÓÝÛ”›Ü\K™O][œÝX›WÜØÚY[PØ[˜XÚËO][œÝX›WØØ[˜Ù[Ø[˜XÚË™O][œÝX›WÜÚÝ[ZY[YO][œÝX›WÜ™\]Y\ÝZ[O][œÝX›WÛ›ÝË™O][œÝX›WÙÙ]Ý\œ™[š[Üš]S]™[™O][œÝX›WÒ[[YYX]Tš[Üš]K™O][œÝX›WÕ\Ù\›ØÚÚ[™Ôš[Üš]K™O][œÝX›WÓ›Ü›X[š[Üš]KO][œÝX›WÓÝÔš[Üš]KYO][œÝX›WÒYTš[Üš]KÙO]›ÙËÙO][œÝX›WÜÙ]\ØX›VZY[˜[YKÙO[[YO[[Ù[˜Ý[Ûˆ™JJ^ÚYŠ\[ÙˆÙOOX[˜Ý[Û˜	‰‘ÙJJKYI‰\[ÙˆYKœÙ]ÝšXÝ[ÙOOX[˜Ý[Û˜
]ž^ÜYKœÙ]ÝšXÝ[ÙJÙKJ_XØ]Úß_]˜\ˆYOSX]˜ÛŒÌÓX]˜ÛŒÌŽ”YKOSX]›ÙË™OSX]“ŒŽÙ[˜Ý[ÛˆYJJ^Ü™]\›ˆOLOOOLÌÌŽŒÌKJJJKÖ™_
_]˜\ˆ	OLM‹]LŒŒMMNMÌÙ[˜Ý[Ûˆ
J^Ý˜\ˆYIŽÚYŠOOL
\™]\›ˆÜÝÚ]Ú
I‹YJ^ØØ\ÙHNœ™]\›ˆNØØ\ÙHŽœ™]\›ˆŽØØ\ÙHœ™]\›ˆØØ\ÙHœ™]\›ˆØØ\ÙHMŽœ™]\›ˆMŽØØ\ÙHÌŽœ™]\›ˆÌŽØØ\ÙHœ™]\›ˆØØ\ÙHLŽœ™]\›ˆLŽØØ\ÙHMŽ˜Ø\ÙHLLŽ˜Ø\ÙHL˜Ø\ÙHŒ˜Ø\ÙHMŽ˜Ø\ÙHNLŽ˜Ø\ÙHMŒÎ˜Ø\ÙHÌÍŽ˜Ø\ÙHMLÍŽ˜Ø\ÙHLÌLÌŽœ™]\›ˆI‹YNØØ\ÙHŒŒM˜Ø\ÙHLŽ˜Ø\ÙHLMÍŽ˜Ø\ÙHŒMÌMLŽœ™]\›ˆIŒÎLÌŒMŒØØ\ÙHNMÌ˜Ø\ÙHÎŒ˜Ø\ÙHMÍÍÌŒMŽ˜Ø\ÙHÌÍMMÌŽœ™]\›ˆIŒŽLMMŒØØ\ÙHÌLœ™]\›ˆÌLØØ\ÙHLÍŒMÍÌŽœ™]\›ˆLÍŒMÍÌŽØØ\ÙHŽÍMMŽœ™]\›ˆŽÍMMŽØØ\ÙHLÍŽÌLLŽœ™]\›ˆLÍŽÌLLŽØØ\ÙHLÌÍÍNœ™]\›ˆÙY˜][œ™]\›ˆ__Y[˜Ý[Ûˆ
KŠ^Ý˜\ˆYKœ[™[™Ó[™\ÎÚYŠOOL
\™]\›ˆÝ˜\ˆOLOYKœÝ\Ü[™Y[™\ËÏYKœ[™ÙY[™\ÎÙOYKØ\›S[™\ÎÝ˜\ˆÏ\‰ŒLÍŒMÍÌÎÜ™]\›ˆÏOOLÊÏ\‰Ÿ˜KÏOOLÛÏOOLÛŸ
\‰Ÿ™KˆOOL	‰ŠO[
ŠJJNšO[
ÊNšO[
ÊJNŠ\ÉŸ˜KOOLÊÉ\ËÏOOLÛŸ
\ÉŸ™KˆOOL	‰ŠO[
ŠJJNšO[
ÊJNšO[
ŠJKOOOLÌOOL	‰OOZI‰Š	˜JOOOL	‰ŠOZI‹ZK]	‹]O[ŸOOOLÌ‰‰›‰NM
OÝš_Y[˜Ý[Ûˆ]
K
^Ü™]\›ŠKœ[™[™Ó[™\ÉŸŠKœÝ\Ü[™Y[™\ÉŸ™Kœ[™ÙY[™\ÊI
OOOLY[˜Ý[Ûˆ]
K
^Ý	Ž	‰Š]	ŒÌŠNÝ˜\ˆYK™[[™ÛY[™\ÎÚYŠˆOOL
Y›ÜŠOYK™[[™Û[Y[Ë‰]ÌŽÊ^Ý˜\ˆLÌKVYJŠKOLOŽÝYVÜ—K‰_š_\™]\›ˆY[˜Ý[ÛˆÝ
K
^ÜÝÚ]Ú
J^ØØ\ÙHN˜Ø\ÙHŽ˜Ø\ÙH˜Ø\ÙH˜Ø\ÙHœ™]\›ˆ
ÌLØØ\ÙHMŽ˜Ø\ÙHÌŽ˜Ø\ÙHLŽ˜Ø\ÙHMŽ˜Ø\ÙHLLŽ˜Ø\ÙHL˜Ø\ÙHŒ˜Ø\ÙHMŽ˜Ø\ÙHNLŽ˜Ø\ÙHMŒÎ˜Ø\ÙHÌÍŽ˜Ø\ÙHMLÍŽ˜Ø\ÙHLÌLÌŽ˜Ø\ÙHŒŒM˜Ø\ÙHLŽ˜Ø\ÙHLMÍŽ˜Ø\ÙHŒMÌMLŽœ™]\›ˆ
ÍYLÎØØ\ÙHNMÌ˜Ø\ÙHÎŒ˜Ø\ÙHMÍÍÌŒMŽ˜Ø\ÙHÌÍMMÌŽœ™]\›‹LNØØ\ÙHÌL˜Ø\ÙHLÍŒMÍÌŽ˜Ø\ÙHŽÍMMŽ˜Ø\ÙHLÍŽÌLLŽ˜Ø\ÙHLÌÍÍNœ™]\›‹LNÙY˜][œ™]\›‹L__Y[˜Ý[ÛˆÝ

^Ý˜\ˆO]Ü™]\›ˆLKJ	ŒŽLMMŒ
I‰ŠMNMÌ
K_Y[˜Ý[ÛˆÝ
J^Ù›ÜŠ˜\ˆV×KLÌÌO›ŽÛŠÊÊ]œ\Ú
JNÜ™]\›ˆY[˜Ý[Ûˆ
K
^ÙKœ[™[™Ó[™\ß]OOLŽÍMM‰‰ŠKœÝ\Ü[™Y[™\ÏLKœ[™ÙY[™\ÏLKØ\›S[™\ÏL
_Y[˜Ý[Ûˆ]
K‹‹KJ^Ý˜\ˆÏYKœ[™[™Ó[™\ÎÙKœ[™[™Ó[™\Ï[‹KœÝ\Ü[™Y[™\ÏLKœ[™ÙY[™\ÏLKØ\›S[™\ÏLK™^\™Y[™\É[‹K™[[™ÛY[™\É[‹K™\œ›Ü”™XÛÝ™\žQ\ØX›Y[™\É[‹KœÚ[Ý\Ü[™ÛÝ[\LÝ˜\ˆÏYK™[[™Û[Y[ËYK™^\˜][Û•[Y\ËOYKšY[•\]\ÎÙ›ÜŠ[ÉŸ›ŽÌŽÊ^Ý˜\ˆLÌKVYJŠKLOÜÖÙOLÙOKLNÝ˜\ˆ]VÙNÚYŠOO[[
Y›ÜŠVÙO[[LÙ›[™ÝÙ
ÊÊ^Ý˜\ˆO\ÙNÛHOO[[	‰ŠK›[™IKMLÍŽÌLLÊ_[‰_™Ÿ\ˆOOL	‰™
K‹
KHOOL	‰šOOOL	‰™KYÈOOL	‰ŠKœÝ\Ü[™Y[™\ßXIŸŠÉŸ
J_Y[˜Ý[Ûˆ
KŠ^ÙKœ[™[™Ó[™\ß]KœÝ\Ü[™Y[™\É_Ý˜\ˆLÌKVYJ
NÙK™[[™ÛY[™\ß]K™[[™Û[Y[ÖÜ—OYK™[[™Û[Y[ÖÜ—_LÌÍÍN‰ŒŒNLÌY[˜Ý[Ûˆ
K
^Ý˜\ˆYK™[[™ÛY[™\ß]Ù›ÜŠOYK™[[™Û[Y[ÎÛŽÊ^Ý˜\ˆLÌKVYJŠKOLOŽÚIVÜ—I	‰ŠVÜ—_]
K‰_š__Y[˜Ý[Ûˆ
K
^Ý˜\ˆ]	‹]Ü™]\›ˆ[‰ÌN›]
ŠK
‰ŠKœÝ\Ü[™Y[™\ß
JOOOLÛŽŒY[˜Ý[Ûˆ]
J^ÜÝÚ]Ú
J^ØØ\ÙHŽ™OLNØœ™XZÎØØ\ÙH™OMØœ™XZÎØØ\ÙHÌŽ™OLMŽØœ™XZÎØØ\ÙHMŽ˜Ø\ÙHLLŽ˜Ø\ÙHL˜Ø\ÙHŒ˜Ø\ÙHMŽ˜Ø\ÙHNLŽ˜Ø\ÙHMŒÎ˜Ø\ÙHÌÍŽ˜Ø\ÙHMLÍŽ˜Ø\ÙHLÌLÌŽ˜Ø\ÙHŒŒM˜Ø\ÙHLŽ˜Ø\ÙHLMÍŽ˜Ø\ÙHŒMÌMLŽ˜Ø\ÙHNMÌ˜Ø\ÙHÎŒ˜Ø\ÙHMÍÍÌŒMŽ˜Ø\ÙHÌÍMMÌŽ™OLLŽØœ™XZÎØØ\ÙHŽÍMMŽ™OLLÍŒMÍÌŽØœ™XZÎÙY˜][™OL\™]\›ˆ_Y[˜Ý[Ûˆ
J^Ü™]\›ˆIKYKOÎOÙIŒLÍŒMÍÌÏÌÌŽŒŽÍMMŽŽŒŸY[˜Ý[ÛˆÝ

^Ý˜\ˆO]YKœÜ™]\›ˆOOOLÊO]Ú[™ÝË™]™[OOO]›ÚYÌÌŽ™JK\JJN™_Y[˜Ý[ÛˆÝ
K
^Ý˜\ˆ]YKœÝž^Ü™]\›ˆYKœYK

_Yš[˜[^ÝYKœ[Ÿ_]˜\ˆSX]œ˜[™ÛJ
KÔÝš[™ÊÍŠKœÛXÙJŠK]X×Ü™XXÝšX™\‰
ÝX×Ü™XXÝ›ÜÉ
ÝX×Ü™XXÝÛÛZ[™\‰
ÝÝX×Ü™XXÝ]™[É
ÝÝX×Ü™XXÝ\Ý[™\œÉ
ÝÝX×Ü™XXÝ[™\É
ÝX×Ü™XXÝ™\ÛÝ\˜Ù\É
Ý]X×Ü™XXÝX\šÙ\‰
ÝX×Ü™XXÝØY	
ÝÙ[˜Ý[ÛˆÝ
J^Ù[]HVÞ]K[]HVØK[]HVÐÝK[]HVÝÝ_Y[˜Ý[ÛˆÝ
J^Ý˜\ˆÚYŠYVÞ]J\™]\›ˆÙ›ÜŠ˜\ˆYKœ\™[›ÙNÛŽÊ^ÚYŠ[–Þ_–Þ]J^ÚYŠ]˜[\›˜]K˜Ú[OO[[ˆOO[[	‰›‹˜Ú[OO[[
Y›ÜŠOP™ŠJNÙHOO[[Ê^ÚYŠYVÞ]J\™]\›ˆŽÙOP™ŠJ_\™]\›ˆYO[‹YKœ\™[›Ù_\™]\›ˆ[Y[˜Ý[Ûˆ]
J^ÚYŠOYVÞ]_VÞJ^Ý˜\ˆYKYÎÚYŠOOM_OOMŸOOLLßOOLÌ_OOLŸOOLßOOLÊ\™]\›ˆ_\™]\›ˆ[Y[˜Ý[Ûˆ
J^Ý˜\ˆYKYÎÚYŠOOM_OOLŸOOLßOOMŠ\™]\›ˆKœÝ]S›ÙNÝ›ÝÈ\œ›ÜŠJÌÊJ_Y[˜Ý[Ûˆ]
J^Ý˜\ˆYVÕNÜ™]\›ˆYVÕO^ÚÚ\ÝX›TÝ[\Î›™]ÈX\Ú\ÝX›TØÜš\Î›™]ÈX\KY[˜Ý[Ûˆ
J^ÙVÑ]OHLY[˜Ý[Ûˆ
J^ÙVÑO]›ÚY]˜\ˆ[™]ÈÙ]]^ßNÙ[˜Ý[Ûˆ
K
^Ô
K
K
JØØ\\™X
_Y[˜Ý[Ûˆ
K
^Ù›ÜŠ]ÙWO]OLÙO›[™ÝÙJÊÊQ˜Y
ÙWJ_]˜\ˆT™YÑ^
–ÎKV—ØK^—LÌWL—LWL—LŽWL‘‘—LÍÌWLÍÑLÍÑ‹WLQ‘‘—LŒËWLŒLŒÌWLŒN—LÌWL‘‘Q—LÌKWQÑ‘—QŽLWQ‘Ñ—Q‘ŒWQ‘‘‘VÎKV—ØK^—LÌWL—LWL—LŽWL‘‘—LÍÌWLÍÑLÍÑ‹WLQ‘‘—LŒËWLŒLŒÌWLŒN—LÌWL‘‘Q—LÌKWQÑ‘—QŽLWQ‘Ñ—Q‘ŒWQ‘‘‘KŒNWL×LÌWLÍ‘—LŒÑ‹WLŒJ‰
K^ßK^ßNÙ[˜Ý[Ûˆ
J^Ü™]\›ˆYK˜Ø[
JOÈL“YK˜Ø[
JOÈLNž\Ý
JOÕÙWOHLŠÙWOHLLJ_]˜\ˆ]HLNÙ[˜Ý[ÛˆÝ

^Ý˜\ˆOU]Ü™]\›ˆ]HLK_Y[˜Ý[ÛˆÝ
KŠ^ÚYŠ

JZYŠOO[[
YKœ™[[Ý™P]šX]J
NÙ[Ù^ÜÝÚ]Ú
\[ÙˆŠ^ØØ\ÙX[™Yš[™Y˜Ø\ÙX[˜Ý[Û˜˜Ø\ÙXÞ[X›Û™Kœ™[[Ý™P]šX]J
NÜ™]\›ŽØØ\ÙX›ÛÛX[˜˜\ˆ]ÓÝÙ\Ø\ÙJ
KœÛXÙJJNÚYŠˆOOX]KX	‰œˆOOX\šXKX
^ÙKœ™[[Ý™P]šX]J
NÜ™]\›Ÿ_YKœÙ]]šX]JŠ__Y[˜Ý[ÛˆÝ
KŠ^ÚYŠOO[[
YKœ™[[Ý™P]šX]J
NÙ[Ù^ÜÝÚ]Ú
\[ÙˆŠ^ØØ\ÙX[™Yš[™Y˜Ø\ÙX[˜Ý[Û˜˜Ø\ÙXÞ[X›Û˜Ø\ÙX›ÛÛX[˜™Kœ™[[Ý™P]šX]J
NÜ™]\›ŸYKœÙ]]šX]JŠ__Y[˜Ý[Ûˆ]
K‹Š^ÚYŠOO[[
YKœ™[[Ý™P]šX]JŠNÙ[Ù^ÜÝÚ]Ú
\[ÙˆŠ^ØØ\ÙX[™Yš[™Y˜Ø\ÙX[˜Ý[Û˜˜Ø\ÙXÞ[X›Û˜Ø\ÙX›ÛÛX[˜™Kœ™[[Ý™P]šX]JŠNÜ™]\›ŸYKœÙ]]šX]S”Ê‹Š__Y[˜Ý[Ûˆ
J^ÜÝÚ]Ú
\[ÙˆJ^ØØ\ÙXšYÚ[˜Ø\ÙX›ÛÛX[˜˜Ø\ÙX[X™\˜˜Ø\ÙXÝš[™Ø˜Ø\ÙX[™Yš[™Yœ™]\›ˆNØØ\ÙXØš™XÝœ™]\›ˆNÙY˜][œ™]\›˜_Y[˜Ý[Ûˆ]
J^Ý˜\ˆYK\NÜ™]\›ŠOYK››ÙS˜[YJI‰™KÓÝÙ\Ø\ÙJ
OOOX[œ]	‰ŠOOXÚXÚØ›ÞOOX˜Y[Ø
_Y[˜Ý[Ûˆ
KŠ^Ý˜\ˆSØš™XÝ™Ù]ÝÛ”›Ü\Q\ØÜš\ÜŠK˜ÛÛœÝXÝÜ‹œ›ÝÝ\K
NÚYŠYKš\ÓÝÛ”›Ü\J
I‰œˆOO]›ÚY	‰\[Ùˆ‹™Ù]OX[˜Ý[Û˜	‰\[Ùˆ‹œÙ]OX[˜Ý[Û˜
^Ý˜\ˆO\‹™Ù]O\‹œÙ]Ü™]\›ˆØš™XÝ™Yš[™T›Ü\JKØÛÛ™šYÝ\˜X›NˆLÙ]™[˜Ý[ÛŠ
^Ü™]\›ˆK˜Ø[
\Ê_KÙ]™[˜Ý[ÛŠJ^ÛX
ÙKK˜Ø[
\ËJ__JKØš™XÝ™Yš[™T›Ü\JKÙ[[Y\˜X›Nœ‹™[[Y\˜X›_JKÙÙ]˜[YN™[˜Ý[ÛŠ
^Ü™]\›ˆŸKÙ]˜[YN™[˜Ý[ÛŠJ^ÛX
Ù_KÝÜ˜XÚÚ[™Î™[˜Ý[ÛŠ
^ÙK—Ý˜[YU˜XÚÙ\[[[]HVÝ____Y[˜Ý[Ûˆ
J^ÚYŠYK—Ý˜[YU˜XÚÙ\Š^Ý˜\ˆV]
JOØÚXÚÙY˜˜[YXÙK—Ý˜[YU˜XÚÙ\V
K
ÙVÝJ__Y[˜Ý[Ûˆ]
J^ÚYŠYJ\™]\›ˆLNÝ˜\ˆYK—Ý˜[YU˜XÚÙ\ŽÚYŠ]
\™]\›ˆLÝ˜\ˆ]™Ù]˜[YJ
KXÜ™]\›ˆI‰ŠV]
JOÙK˜ÚXÚÙYØYX˜˜[ÙX™K˜[YJKO\‹OOO[ÈLNŠœÙ]˜[YJJKL
_]˜\ˆ	KÖ×ˆ—KÙÎÙ[˜Ý[Ûˆ[ŠJ^Ü™]\›ˆKœ™\XÙJ	[˜Ý[ÛŠJ^Ü™]\›˜
ÙK˜Ú\ÛÙP]

KÔÝš[™ÊMŠJØJ_Y[˜Ý[ÛˆŠK‹‹KKËÊ^ÙK›˜[YOXÈO[[	‰\[ÙˆÈOX[˜Ý[Û˜	‰\[ÙˆÈOXÞ[X›Û	‰\[ÙˆÈOX›ÛÛX[˜ÙK\O[Î™Kœ™[[Ý™P]šX]J\X
KO[[ÛÈOOXÝX›Z]	‰›ÈOOX™\Ù]Kœ™[[Ý™P]šX]J˜[YX
N›ÏOOX[X™\˜ÊOOL	‰™K˜[YOOOXK˜[YHO]
I‰ŠK˜[YOX
Ò

JN™K˜[YHOOX
Ò

I‰ŠK˜[YOX
Ò

JKO[[ÛO[[ÜˆO[[	‰™Kœ™[[Ý™P]šX]J˜[YX
Nœ›ŠK
ŠJN›ÏOOX[X™\˜	‰™K˜[YOO]Ü›ŠK
K˜[YJJNœ›ŠK

JKOO[[	‰˜HO[[	‰ŠK™Y˜][ÚXÚÙYHHXJKHO[[	‰ŠK˜ÚXÚÙYZI‰\[ÙˆHOX[˜Ý[Û˜	‰\[ÙˆHOXÞ[X›Û
KÈO[[	‰\[ÙˆÈOX[˜Ý[Û˜	‰\[ÙˆÈOXÞ[X›Û	‰\[ÙˆÈOX›ÛÛX[˜ÙK›˜[YOX
Ò
ÊN™Kœ™[[Ý™P]šX]J˜[YX
_Y[˜Ý[Ûˆ›ŠK‹‹KKËÊ^ÚYŠHO[[	‰\[ÙˆHOX[˜Ý[Û˜	‰\[ÙˆHOXÞ[X›Û	‰\[ÙˆHOX›ÛÛX[˜	‰ŠK\OXJKO[[ˆO[[
^ÚYŠJHOOXÝX›Z]	‰˜HOOX™\Ù]O[[
J^Ö
JNÜ™]\›Ÿ[[O[[Ø˜
Ò
ŠK]O[[ÛŽ˜
Ò

KßOOYK˜[Y_
K˜[YO]
KK™Y˜][˜[YO]\ÏÏZK]\[ÙˆˆOX[˜Ý[Û˜	‰\[ÙˆˆOXÞ[X›Û	‰ˆH\‹K˜ÚXÚÙY\ÏÙK˜ÚXÚÙYˆH\‹K™Y˜][ÚXÚÙYHH\‹ÈO[[	‰\[ÙˆÈOX[˜Ý[Û˜	‰\[ÙˆÈOXÞ[X›Û	‰\[ÙˆÈOX›ÛÛX[˜	‰ŠK›˜[YO[ÊK
J_Y[˜Ý[Ûˆ›ŠK
^ÙK™Y˜][˜[YHOOX
Ý	‰ŠK™Y˜][˜[YOX
Ý
_Y[˜Ý[Ûˆ[ŠK‹Š^ÚYŠOYK›Ü[ÛœË
^Ý^ßNÙ›ÜŠ˜\ˆOLÚO‹›[™ÝÚJÊÊ]Ø	
Û–ÚWWOHLÙ›ÜŠLÛK›[™ÝÛŠÊÊZO]š\ÓÝÛ”›Ü\J	
ÙVÛ—K˜[YJKVÛ—KœÙ[XÝYOOZI‰ŠVÛ—KœÙ[XÝYZJKI‰œ‰‰ŠVÛ—K™Y˜][Ù[XÝYHL
_Y[Ù^Ù›ÜŠX
Ò
ŠK[[OLÚOK›[™ÝÚJÊÊ^ÚYŠVÚWK˜[YOOO[Š^ÙVÚWKœÙ[XÝYHL‰‰ŠVÚWK™Y˜][Ù[XÝYHL
NÜ™]\›Ÿ]OO[[VÚWK™\ØX›Y
YVÚWJ_]OO[[	‰ŠœÙ[XÝYHL
__Y[˜Ý[ÛˆÛŠKŠ^ÚYŠO[[	‰ŠX
Ò

KOOYK˜[YI‰ŠK˜[YO]
KO[[
J^ÙK™Y˜][˜[YHOO]	‰ŠK™Y˜][˜[YO]
NÜ™]\›ŸYK™Y˜][˜[YO[O[[Ø˜
Ò
Š_Y[˜Ý[ÛˆÛŠK‹Š^ÚYŠO[[
^ÚYŠˆO[[
^ÚYŠˆO[[
]›ÝÈ\œ›ÜŠJLŠJNÚYŠÙJŠJ^ÚYŠO‹›[™Ý
]›ÝÈ\œ›ÜŠJLÊJNÜ\–Ì_[\Ÿ[ÏÏX[Ÿ[R

KK™Y˜][˜[YO[‹YK^ÛÛ[OO[‰‰œˆOOX	‰œˆOO[[	‰ŠK˜[YO\ŠK
J_Y[˜Ý[ÛˆÛŠK
^ÚYŠ
^Ý˜\ˆYK™š\œÝÚ[ÚYŠ‰‰›OOYK›\ÝÚ[	‰›‹››ÙU\OOOLÊ^Û‹››ÙU˜[YO]Ü™]\›Ÿ_YK^ÛÛ[]]˜\ˆYYO[™]ÈÙ]
[š[X][Û’]\˜][ÛÛÝ[\ÜXÝ˜][È›Ü™\’[XYÙSÝ]Ù]›Ü™\’[XYÙTÛXÙH›Ü™\’[XYÙUÚY›Þ›^›Þ›^Ü›Ý\›ÞÜ™[˜[Ü›Ý\ÛÛ[[ÛÝ[ÛÛ[[œÈ›^›^Ü›ÝÈ›^ÜÚ]]™H›^Úš[šÈ›^™YØ]]™H›^Ü™\ˆÜšY\™XHÜšY›ÝÈÜšY›ÝÑ[™ÜšY›ÝÔÜ[ˆÜšY›ÝÔÝ\ÜšYÛÛ[[ˆÜšYÛÛ[[‘[™ÜšYÛÛ[[”Ü[ˆÜšYÛÛ[[”Ý\›ÛÙZYÚ[™PÛ[\[™RZYÚÜXÚ]HÜ™\ˆÜœ[œÈØØ[HX”Ú^™HÚYÝÜÈ’[™^›ÛÛHš[ÜXÚ]H›ÛÙÜXÚ]HÝÜÜXÚ]HÝ›ÚÙQ\Ú\œ˜^HÝ›ÚÙQ\ÚÙ™œÙ]Ý›ÚÙSZ]\›[Z]Ý›ÚÙSÜXÚ]HÝ›ÚÙUÚY[Þ[š[X][Û’]\˜][ÛÛÝ[[Þ›Þ›^[Þ›Þ›^Ü›Ý\[Þ“[™PÛ[\\Ð[š[X][Û’]\˜][ÛÛÝ[\Ñ›^\Ö›ÛÛH\Ñ›^Ü›ÝÈ\Ñ›^™YØ]]™H\Ñ›^Ü™\ˆ\Ñ›^ÜÚ]]™H\Ñ›^Úš[šÈ\ÑÜšYÛÛ[[ˆ\ÑÜšYÛÛ[[”Ü[ˆ\ÑÜšY›ÝÈ\ÑÜšY›ÝÔÜ[ˆÙXšÚ][š[X][Û’]\˜][ÛÛÝ[ÙXšÚ]›Þ›^ÙX’Ú]›Þ›^Ü›Ý\ÙXšÚ]›ÞÜ™[˜[Ü›Ý\ÙXšÚ]ÛÛ[[ÛÝ[ÙXšÚ]ÛÛ[[œÈÙXšÚ]›^ÙXšÚ]›^Ü›ÝÈÙXšÚ]›^ÜÚ]]™HÙXšÚ]›^Úš[šÈÙXšÚ][™PÛ[\œÜ]

JNÙ[˜Ý[ÛˆYJKŠ^Ý˜\ˆ]š[™^ÙŠKX
OOOLÛO[[\[ÙˆOX›ÛÛX[˜OOXÜÙKœÙ]›Ü\J
NOOX›Ø]ÙK˜ÜÜÑ›Ø]X™VÝOXœÙKœÙ]›Ü\JŠN\[ÙˆˆOX[X™\˜OOLYYKš\Ê
OÝOOX›Ø]ÙK˜ÜÜÑ›Ø][Ž™VÝOJ
ÛŠKš[J
N™VÝO[ŠØY[˜Ý[ÛˆŠKŠ^ÚYŠO[[	‰\[ÙˆOXØš™XÝ
]›ÝÈ\œ›ÜŠJŒŠJNÚYŠOYKœÝ[KˆO[[
^Ù›ÜŠ˜\ˆˆ[ˆŠH[‹š\ÓÝÛ”›Ü\JŠ_O[[	‰š\ÓÝÛ”›Ü\JŠ_
‹š[™^ÙŠKX
OOOLÙKœÙ]›Ü\J‹
NœOOX›Ø]ÙK˜ÜÜÑ›Ø]X™VÜ—OX]HL
NÙ›ÜŠ˜\ˆH[ˆ
\]ØWKš\ÓÝÛ”›Ü\JJI‰›–ØWHOO\‰‰ŠYJKKŠK]HL
_Y[ÙH›ÜŠ˜\ˆÈ[ˆ
]š\ÓÝÛ”›Ü\JÊI‰YJKËÛ×J_Y[˜Ý[Ûˆ[ŠJ^ÚYŠKš[™^ÙŠX
OOOKLJ\™]\›ˆLNÜÝÚ]Ú
J^ØØ\ÙX[››Ý][Û‹^[˜Ø\ÙXÛÛÜ‹\›Ùš[X˜Ø\ÙX›ÛY˜XÙX˜Ø\ÙX›ÛY˜XÙK\Ü˜Ø˜Ø\ÙX›ÛY˜XÙK]\šX˜Ø\ÙX›ÛY˜XÙKY›Ü›X]˜Ø\ÙX›ÛY˜XÙK[˜[YX˜Ø\ÙXZ\ÜÚ[™ËYÛ\œ™]\›ˆLNÙY˜][œ™]\›ˆL_]˜\ˆ[™]ÈX\
ÖØXØÙ\Ú\œÙ]XØÙ\XÚ\œÙ]KØ[›Ü˜›Ü˜KØ\]Z]˜Y\]Z]˜KØÜ›ÜÜÓÜšYÚ[˜Ü›ÜÜÛÜšYÚ[˜KØXØÙ[ZYÚXØÙ[ZZYÚKØ[YÛ›Y[˜\Ù[[™X[YÛ›Y[X˜\Ù[[™XKØ\˜XšXÑ›Ü›X\˜XšXËY›Ü›XKØ˜\Ù[[™TÚY˜\Ù[[™K\ÚYKØØ\ZYÚØ\ZZYÚKØÛ\]Û\\]KØÛ\[XÛ\\[XKØÛÛÜ’[\œÛ][Û˜ÛÛÜ‹Z[\œÛ][Û˜KØÛÛÜ’[\œÛ][Û‘š[\œØÛÛÜ‹Z[\œÛ][Û‹Yš[\œØKØÛÛÜ”›Ùš[XÛÛÜ‹\›Ùš[XKØÛÛÜ”™[™\š[™ØÛÛÜ‹\™[™\š[™ØKØÛZ[˜[˜\Ù[[™XÛZ[˜[X˜\Ù[[™XKØ[˜X›P˜XÚÙÜ›Ý[™[˜X›KX˜XÚÙÜ›Ý[™KØš[ÜXÚ]Xš[[ÜXÚ]XKØš[[Xš[\[XKØ›ÛÙÛÛÜ˜›ÛÙXÛÛÜ˜KØ›ÛÙÜXÚ]X›ÛÙ[ÜXÚ]XKØ›Û˜[Z[X›ÛY˜[Z[XKØ›ÛÚ^™X›Û\Ú^™XKØ›ÛÚ^™PY\Ý›Û\Ú^™KXY\ÝKØ›ÛÝ™]Ú›Û\Ý™]ÚKØ›ÛÝ[X›Û\Ý[XKØ›Û˜\šX[›Û]˜\šX[KØ›ÛÙZYÚ›Û]ÙZYÚKØÛ\˜[YXÛ\[˜[YXKØÛ\ÜšY[][Û’Üš^›Û[Û\[ÜšY[][Û‹ZÜš^›Û[KØÛ\ÜšY[][Û•™\XØ[Û\[ÜšY[][Û‹]™\XØ[KØÜš^Y–Üš^‹XY‹^KØÜš^“ÜšYÚ[–Üš^‹[ÜšYÚ[‹^KØ[XYÙT™[™\š[™Ø[XYÙK\™[™\š[™ØKØ]\”ÜXÚ[™Ø]\‹\ÜXÚ[™ØKØYÚ[™ÐÛÛÜ˜YÚ[™ËXÛÛÜ˜KØX\šÙ\‘[™X\šÙ\‹Y[™KØX\šÙ\“ZYX\šÙ\‹[ZYKØX\šÙ\”Ý\X\šÙ\‹\Ý\KØX\ÚÕ\XX\ÚË]\XKØÝ™\›[™TÜÚ][Û˜Ý™\›[™K\ÜÚ][Û˜KØÝ™\›[™UXÚÛ™\ÜØÝ™\›[™K]XÚÛ™\ÜØKØZ[Ü™\˜Z[[Ü™\˜KØ[›ÜÙKLX[›ÜÙKLXKØÚ[\‘]™[ØÚ[\‹Y]™[ØKØ™[™\š[™Ò[[™[™\š[™ËZ[[KØÚ\T™[™\š[™ØÚ\K\™[™\š[™ØKØÝÜÛÛÜ˜ÝÜXÛÛÜ˜KØÝÜÜXÚ]XÝÜ[ÜXÚ]XKØÝšZÙ]›ÝYÚÜÚ][Û˜ÝšZÙ]›ÝYÚ\ÜÚ][Û˜KØÝšZÙ]›ÝYÚXÚÛ™\ÜØÝšZÙ]›ÝYÚ]XÚÛ™\ÜØKØÝ›ÚÙQ\Ú\œ˜^XÝ›ÚÙKY\Ú\œ˜^XKØÝ›ÚÙQ\ÚÙ™œÙ]Ý›ÚÙKY\ÚÙ™œÙ]KØÝ›ÚÙS[™XØ\Ý›ÚÙK[[™XØ\KØÝ›ÚÙS[™Z›Ú[˜Ý›ÚÙK[[™Z›Ú[˜KØÝ›ÚÙSZ]\›[Z]Ý›ÚÙK[Z]\›[Z]KØÝ›ÚÙSÜXÚ]XÝ›ÚÙK[ÜXÚ]XKØÝ›ÚÙUÚYÝ›ÚÙK]ÚYKØ^[˜ÚÜ˜^X[˜ÚÜ˜KØ^XÛÜ˜][Û˜^YXÛÜ˜][Û˜KØ^™[™\š[™Ø^\™[™\š[™ØKØ˜[œÙ›Ü›SÜšYÚ[˜˜[œÙ›Ü›K[ÜšYÚ[˜KØ[™\›[™TÜÚ][Û˜[™\›[™K\ÜÚ][Û˜KØ[™\›[™UXÚÛ™\ÜØ[™\›[™K]XÚÛ™\ÜØKØ[šXÛÙPšYX[šXÛÙKXšYXKØ[šXÛÙT˜[™ÙX[šXÛÙK\˜[™ÙXKØ[š]Ô\‘[X[š]Ë\\‹Y[XKØ[X™]XØ‹X[X™]XØKØ’[™Ú[™Ø‹Z[™Ú[™ØKØ’Y[ÙÜ˜\XØ‹ZY[ÙÜ˜\XØKØ“X][X]XØ[‹[X][X]XØ[KØ™XÝÜ‘Y™™XÝ™XÝÜ‹YY™™XÝKØ™\Y–X™\XY‹^XKØ™\ÜšYÚ[–™\[ÜšYÚ[‹^KØ™\ÜšYÚ[–X™\[ÜšYÚ[‹^XKØÛÜ™ÜXÚ[™ØÛÜ™\ÜXÚ[™ØKØÜš][™Ó[ÙXÜš][™Ë[[ÙXKØ[œÖ[šØ[œÎž[šØKØZYÚZZYÚWJK›K×–×LWLQˆJš–×——J˜V×——J–×——J˜V×——JœÖ×——J˜Ö×——Jœ–×——JšV×——Jœ×——J×——JŽ‹ÚNÙ[˜Ý[ÛˆŠJ^Ü™]\›ˆ›‹\Ý

ÙJOØ˜]˜\ØÜš\›ÝÈ™]È\œ›ÜŠ	Ô™XXÝ\È›ØÚÙYH˜]˜\ØÜš\ˆT“\ÈHÙXÝ\š]H™XØ]][Û‹‰ÊX™_Y[˜Ý[Ûˆ[Š
^ß]˜\ˆ[[Ù[˜Ý[ÛˆÛŠJ^Ü™]\›ˆOYK\™Ù]KœÜ˜Ñ[[Y[Ú[™ÝËK˜ÛÜœ™\ÜÛ™[™Õ\ÙQ[[Y[	‰ŠOYK˜ÛÜœ™\ÜÛ™[™Õ\ÙQ[[Y[
KK››ÙU\OOOLÏÙKœ\™[›ÙN™_]˜\ˆÛ[[›[[Ù[˜Ý[Ûˆ[ŠJ^Ý˜\ˆP]
JNÚYŠ	‰ŠO]œÝ]S›ÙJJ^Ý˜\ˆYVØ_[ØNœÝÚ]Ú
O]œÝ]S›ÙK\J^ØØ\ÙX[œ]šYŠŠK‹˜[YK‹™Y˜][˜[YK‹™Y˜][˜[YK‹˜ÚXÚÙY‹™Y˜][ÚXÚÙY‹\K‹›˜[YJK[‹›˜[YK‹\OOOX˜Y[Ø	‰O[[
^Ù›ÜŠYNÛ‹œ\™[›ÙNÊ[[‹œ\™[›ÙNÙ›ÜŠ[‹œ]Y\žTÙ[XÝÜ[
[œ]Û˜[YOH˜
Ù[Š
Ý
JØ—VÝ\OHœ˜Y[È—X
KLÝ‹›[™ÝÝ
ÊÊ^Ý˜\ˆ[–ÝNÚYŠˆOOYI‰œ‹™›Ü›OOOYK™›Ü›J^Ý˜\ˆO\–Ø_[ÚYŠXJ]›ÝÈ\œ›ÜŠJL
JNÝŠ‹K˜[YKK™Y˜][˜[YKK™Y˜][˜[YKK˜ÚXÚÙYK™Y˜][ÚXÚÙYK\KK›˜[YJ__Y›ÜŠLÝ‹›[™ÝÝ
ÊÊ\[–ÝK‹™›Ü›OOOYK™›Ü›I‰”]
Š_Xœ™XZÈNØØ\ÙX^\™XX›ÛŠK‹˜[YK‹™Y˜][˜[YJNØœ™XZÈNØØ\ÙXÙ[XÝ[‹˜[YKO[[	‰˜[ŠKH[‹›][\KLJ___]˜\ˆ›HLNÙ[˜Ý[ÛˆŠKŠ^ÚYŠ›Š\™]\›ˆJŠNØ›HLÝž^Ü™]\›ˆJ
_Yš[˜[^ÚYŠ›HLK
ÛˆOO[[›ˆOO[[
I‰Š]J
KÛ‰‰ŠWÛ‹O]›‹›WÛ[[[Š
KJJJY›ÜŠLÝK›[™ÝÝ
ÊÊ^[ŠVÝJ__Y[˜Ý[ÛˆÛŠK
^Ý˜\ˆYKœÝ]S›ÙNÚYŠOO[[
\™]\›ˆ[Ý˜\ˆ[–Ø_[ÚYŠOO[[
\™]\›ˆ[Û\–ÝNØNœÝÚ]Ú

^ØØ\ÙXÛÛXÚØ˜Ø\ÙXÛÛXÚÐØ\\™X˜Ø\ÙXÛ‘ÝX›PÛXÚØ˜Ø\ÙXÛ‘ÝX›PÛXÚÐØ\\™X˜Ø\ÙXÛ“[Ý\ÙQÝÛ˜˜Ø\ÙXÛ“[Ý\ÙQÝÛØ\\™X˜Ø\ÙXÛ“[Ý\ÙS[Ý™X˜Ø\ÙXÛ“[Ý\ÙS[Ý™PØ\\™X˜Ø\ÙXÛ“[Ý\ÙU\˜Ø\ÙXÛ“[Ý\ÙU\Ø\\™X˜Ø\ÙXÛ“[Ý\ÙQ[\˜ŠH\‹™\ØX›Y
_
OYK\KHJOOOX]Û˜OOOX[œ]OOOXÙ[XÝOOOX^\™XX
JKOH\ŽØœ™XZÈNÙY˜][™OHL_ZYŠJ\™]\›ˆ[ÚYŠ‰‰\[ÙˆˆOX[˜Ý[Û˜
]›ÝÈ\œ›ÜŠJŒÌK\[ÙˆŠJNÜ™]\›ˆŸ]˜\ˆÛHJ\[ÙˆÚ[™ÝÏ˜XÚ[™ÝË™ØÝ[Y[OO]›ÚYÚ[™ÝË™ØÝ[Y[˜Ü™X]Q[[Y[OO]›ÚY
KÛHLNÚYŠÛŠ]ž^Ý˜\ˆ^ßNÓØš™XÝ™Yš[™T›Ü\J‹œ\ÜÚ]™H‹ÙÙ]™[˜Ý[ÛŠ
^ÝÛHL_JKÚ[™ÝË˜Y]™[\Ý[™\Š\Ý‹ŠKÚ[™ÝËœ™[[Ý™Q]™[\Ý[™\Š\Ý‹Š_XØ]ÚÝÛHL_]˜\ˆ[[[[[Û[[Ù[˜Ý[ÛˆÛŠ
^ÚYŠÛŠ\™]\›ˆÛŽÝ˜\ˆKQ‹]›[™Ý‹OX˜[YX[ˆ[Ñ[‹˜[YN‘[‹^ÛÛ[OZK›[™ÝÙ›ÜŠOLÙO‰‰ÙWOOOZVÙWNÙJÊÊNÝ˜\ˆÏ[‹YNÙ›ÜŠLNÜ[É‰Û‹\—OOOZVØK\—NÜŠÊÊNÜ™]\›ˆÛZKœÛXÙJKOÌK\Ž›ÚY
_Y[˜Ý[Ûˆ[ŠJ^Ý˜\ˆYKšÙ^PÛÙNÜ™]\›˜Ú\ÛÙX[ˆOÊOYK˜Ú\ÛÙKOOOL	‰OOLLÉ‰ŠOLLÊJN™O]OOOLL	‰ŠOLLÊKÌY_OOOLLÏÙNŒY[˜Ý[Ûˆ›Š
^Ü™]\›ˆLY[˜Ý[Ûˆ™YJ
^Ü™]\›ˆL_Y[˜Ý[Ûˆ[ŠJ^Ù[˜Ý[Ûˆ
‹‹KJ^Ù›ÜŠ˜\ˆÈ[ˆ\Ë—Ü™XXÝ˜[YO]\Ë—Ý\™Ù][œÝ\‹\Ë\O[‹\Ë›˜]]™Q]™[ZK\Ë\™Ù]XK\Ë˜Ý\œ™[\™Ù][[JYKš\ÓÝÛ”›Ü\JÊI‰ŠYVÛ×K\ÖÛ×O]Ý
JNšVÛ×JNÜ™]\›ˆ\Ëš\ÑY˜][™]™[YJK™Y˜][™]™[YO[[ÈLOOOZKœ™]\›•˜[YNšK™Y˜][™]™[Y
OÚ›Ž›™YK\Ëš\Ô›ÜYØ][Û”ÝÜY[™YK\ß\™]\›ˆ
œ›ÝÝ\KÜ™]™[Y˜][™[˜Ý[ÛŠ
^Ý\Ë™Y˜][™]™[YHLÝ˜\ˆO]\Ë›˜]]™Q]™[ÙI‰ŠKœ™]™[Y˜][ÙKœ™]™[Y˜][

N\[ÙˆKœ™]\›•˜[YHOX[šÛ›ÝÛ˜	‰ŠKœ™]\›•˜[YOHLJK\Ëš\ÑY˜][™]™[YZ›Š_KÝÜ›ÜYØ][ÛŽ™[˜Ý[ÛŠ
^Ý˜\ˆO]\Ë›˜]]™Q]™[ÙI‰ŠKœÝÜ›ÜYØ][ÛÙKœÝÜ›ÜYØ][ÛŠ
N\[ÙˆK˜Ø[˜Ù[X˜›HOX[šÛ›ÝÛ˜	‰ŠK˜Ø[˜Ù[X˜›OHL
K\Ëš\Ô›ÜYØ][Û”ÝÜYZ›Š_K\œÚ\Ý™[˜Ý[ÛŠ
^ßK\Ô\œÚ\Ý[š›ŸJK]˜\ˆ›^Ù]™[\ÙNŒX˜›\ÎŒØ[˜Ù[X›NŒ[YTÝ[\™[˜Ý[ÛŠJ^Ü™]\›ˆK[YTÝ[\]K››ÝÊ
_KY˜][™]™[YŒ\Õ\ÝYŒKS[Š›ŠK›U
ßK›‹ÝšY]ÎŒ]Z[ŒJK™YOS[Š›ŠK[‹‹›‹›U
ßK›‹ÜØÜ™Y[–ŒØÜ™Y[–NŒÛY[ŒÛY[NŒYÙVŒYÙVNŒÝ›Ù^NŒÚYÙ^NŒ[Ù^NŒY]RÙ^NŒÙ][ÙYšY\”Ý]Nœ[‹]ÛŽŒ]ÛœÎŒ™[]Y\™Ù]™[˜Ý[ÛŠJ^Ü™]\›ˆKœ™[]Y\™Ù]OO]›ÚYÙK™œ›ÛQ[[Y[OOYKœÜ˜Ñ[[Y[ÙKÑ[[Y[™K™œ›ÛQ[[Y[™Kœ™[]Y\™Ù]K[Ý™[Y[™[˜Ý[ÛŠJ^Ü™]\›˜[Ý™[Y[[ˆOÙK›[Ý™[Y[ŠHOOT›‰‰Š›‰‰™K\OOOX[Ý\Ù[[Ý™XÊ[YKœØÜ™Y[–T›‹œØÜ™Y[–YKœØÜ™Y[–KT›‹œØÜ™Y[–JN“R[L›YJK[Š_K[Ý™[Y[N™[˜Ý[ÛŠJ^Ü™]\›˜[Ý™[Y[X[ˆOÙK›[Ý™[Y[N“Ÿ_JK›S[Š›ŠKYYOS[Š
ßK›‹Ù]U˜[œÙ™\ŽŒJJK›S[Š
ßK›‹Ü™[]Y\™Ù]ŒJJKYYOS[Š
ßK›‹Ø[š[X][Û“˜[YNŒ[\ÙY[YNŒÙ]YÑ[[Y[ŒJJKS[Š
ßK›‹ØÛ\›Ø\™]N™[˜Ý[ÛŠJ^Ü™]\›˜Û\›Ø\™]X[ˆOÙK˜Û\›Ø\™]NÚ[™ÝË˜Û\›Ø\™]__JJK[S[Š
ßK›‹Ù]NŒJJKÛ^Ñ\ØÎ˜\ØØ\XÜXÙX˜\Ž˜Y˜\œ›ÝÓY\˜\œ›ÝÕ\šYÚ˜\œ›ÝÔšYÚÝÛŽ˜\œ›ÝÑÝÛ˜[˜[]XÚ[Ž˜ÔØY[N˜ÛÛ^Y[X\Î˜ÛÛ^Y[XØÜ›Û˜ØÜ›ÛØÚØ[Þ”š[X›RÙ^N˜[šY[YšYYKÙYO^Î˜˜XÚÜÜXÙXN˜X˜LŽ˜ÛX\˜LÎ˜[\˜MŽ˜ÚYMÎ˜ÛÛ›ÛN˜[NN˜]\ÙXŒ˜Ø\ÓØÚØÎ˜\ØØ\XÌŽ˜ÌÎ˜YÙU\Í˜YÙQÝÛ˜ÍN˜[™ÍŽ˜ÛYXÍÎ˜\œ›ÝÓYÎ˜\œ›ÝÕ\ÎN˜\œ›ÝÔšYÚ˜\œ›ÝÑÝÛ˜N˜[œÙ\Ž˜[]XLLŽ˜ŒXLLÎ˜Œ˜LM˜ŒØLMN˜LMŽ˜XLMÎ˜˜LN˜ØLNN˜ŽLŒ˜ŽXLŒN˜ŒLLŒŽ˜ŒLXLŒÎ˜ŒL˜M˜[SØÚØMN˜ØÜ›ÛØÚØŒ˜Y]XKÛ^Ð[˜[Ù^XÛÛ›Û˜Ý›Ù^XY]N˜Y]RÙ^XÚY˜ÚYÙ^XNÙ[˜Ý[ÛˆÛŠJ^Ý˜\ˆ]\Ë›˜]]™Q]™[Ü™]\›ˆ™Ù][ÙYšY\”Ý]OÝ™Ù][ÙYšY\”Ý]JJNŠOQÛ–ÙWJOÈH]ÙWNˆL_Y[˜Ý[Ûˆ[Š
^Ü™]\›ˆÛŸ]˜\ˆ›S[Š
ßK›‹ÚÙ^N™[˜Ý[ÛŠJ^ÚYŠKšÙ^J^Ý˜\ˆUÛ–ÙKšÙ^W_KšÙ^NÚYŠOOX[šY[YšYY
\™]\›ˆ\™]\›ˆK\OOOXÙ^\™\ÜØÊOP[ŠJKOOOLLÏØ[\˜”Ýš[™Ë™œ›ÛPÚ\ÛÙJJJN™K\OOOXÙ^YÝÛ˜K\OOOXÙ^]\ÛÙYVÙKšÙ^PÛÙW_[šY[YšYY˜KÛÙNŒØØ][ÛŽŒÝ›Ù^NŒÚYÙ^NŒ[Ù^NŒY]RÙ^NŒ™\X]ŒØØ[NŒÙ][ÙYšY\”Ý]Nœ[‹Ú\ÛÙN™[˜Ý[ÛŠJ^Ü™]\›ˆK\OOOXÙ^\™\ÜØÐ[ŠJNŒKÙ^PÛÙN™[˜Ý[ÛŠJ^Ü™]\›ˆK\OOOXÙ^YÝÛ˜K\OOOXÙ^]\ÙKšÙ^PÛÙNŒKÚXÚ™[˜Ý[ÛŠJ^Ü™]\›ˆK\OOOXÙ^\™\ÜØÐ[ŠJN™K\OOOXÙ^YÝÛ˜K\OOOXÙ^]\ÙKšÙ^PÛÙNŒ_JJK[S[Š
ßK›‹ÜÚ[\’YŒÚYŒZYÚŒ™\ÜÝ\™NŒ[™Ù[X[™\ÜÝ\™NŒ[Œ[NŒÚ\ÝŒÚ[\•\NŒ\Ôš[X\žNŒJJKS[Š
ßK›‹ÜÝX›Z]\ŽŒJJKÙYOS[Š
ßK›‹ÝÝXÚ\ÎŒ\™Ù]ÝXÚ\ÎŒÚ[™ÙYÝXÚ\ÎŒ[Ù^NŒY]RÙ^NŒÝ›Ù^NŒÚYÙ^NŒÙ][ÙYšY\”Ý]Nœ[ŸJJK›S[Š
ßK›‹Ü›Ü\S˜[YNŒ[\ÙY[YNŒÙ]YÑ[[Y[ŒJJK[S[Š
ßK›‹Ù[V™[˜Ý[ÛŠJ^Ü™]\›˜[V[ˆOÙK™[V˜ÚY[[V[ˆOËYKÚY[[VŒK[VN™[˜Ý[ÛŠJ^Ü™]\›˜[VX[ˆOÙK™[VN˜ÚY[[VX[ˆOËYKÚY[[VN˜ÚY[[X[ˆOËYKÚY[[NŒK[VŽŒ[S[ÙNŒJJK	S[Š
ßK›‹Û™]ÔÝ]NŒÛÝ]NŒÛÝ\˜ÙNŒJJK\VÎKLËËÌ—KPÛ‰‰˜ÛÛ\ÜÚ][Û‘]™[[ˆÚ[™ÝËœ[[ÐÛ‰‰˜ØÝ[Y[[ÙX[ˆØÝ[Y[	‰ŠœYØÝ[Y[™ØÝ[Y[[ÙJNÝ˜\ˆÙYOPÛ‰‰˜^]™[[ˆÚ[™ÝÉ‰ˆ[œ‹œPÛ‰‰Š]Ÿœ‰‰Žœ‰‰ŒLO[œŠK\X\HLNÙ[˜Ý[ÛˆÜŠK
^ÜÝÚ]Ú
J^ØØ\ÙXÙ^]\œ™]\›ˆ\‹š[™^ÙŠšÙ^PÛÙJHOOKLNØØ\ÙXÙ^YÝÛ˜œ™]\›ˆšÙ^PÛÙHOOLŒŽNØØ\ÙXÙ^\™\ÜØ˜Ø\ÙX[Ý\ÙYÝÛ˜˜Ø\ÙX›ØÝ\ÛÝ]œ™]\›ˆLÙY˜][œ™]\›ˆL__Y[˜Ý[ÛˆÜŠJ^Ü™]\›ˆOYK™]Z[\[ÙˆOOXØš™XÝ	‰˜]X[ˆOÙK™]N›[]˜\ˆÜHLNÙ[˜Ý[ÛˆŠK
^ÜÝÚ]Ú
J^ØØ\ÙXÛÛ\ÜÚ][Û™[™œ™]\›ˆÜŠ
NØØ\ÙXÙ^\™\ÜØœ™]\›ˆÚXÚOOLÌÊ\HL\ŠN›[ØØ\ÙX^[œ]œ™]\›ˆO]™]KOOOZ\‰‰˜\Û[™NÙY˜][œ™]\›ˆ[_Y[˜Ý[Ûˆ\ŠK
^ÚYŠÜŠ\™]\›ˆOOOXÛÛ\ÜÚ][Û™[™]‰‰›ÜŠK
OÊOZÛŠ
KÛQQ[[[ÜHLKJN›[ÜÝÚ]Ú
J^ØØ\ÙX\ÝXœ™]\›ˆ[ØØ\ÙXÙ^\™\ÜØšYŠJ˜Ý›Ù^_˜[Ù^_›Y]RÙ^J_˜Ý›Ù^I‰˜[Ù^J^ÚYŠ˜Ú\‰‰ŒO˜Ú\‹›[™Ý
\™]\›ˆ˜Ú\ŽÚYŠÚXÚ
\™]\›ˆÝš[™Ë™œ›ÛPÚ\ÛÙJÚXÚ
_\™]\›ˆ[ØØ\ÙXÛÛ\ÜÚ][Û™[™œ™]\›ˆœ‰‰›ØØ[HOOXÛØÛ[™]NÙY˜][œ™]\›ˆ[_]˜\ˆ^ØÛÛÜŽˆL]NˆL]][YNˆL™]][YK[ØØ[ŽˆL[XZ[ˆL[ÛˆL[X™\ŽˆL\ÜÝÛÜ™ˆL˜[™ÙNˆLÙX\˜ÚˆL[ˆL^ˆL[YNˆL\›ˆLÙYZÎˆLNÙ[˜Ý[ÛˆœŠJ^Ý˜\ˆYI‰™K››ÙS˜[YI‰™K››ÙS˜[YKÓÝÙ\Ø\ÙJ
NÜ™]\›ˆOOX[œ]ÈHY–ÙK\WNOOX^\™XXY[˜Ý[ÛˆŠK‹Š^×ÛÝ›Ý›‹œ\Ú
ŠN›VÜ—N—Û\‹R™
ÛÚ[™ÙX
K›[™Ý	‰Š[™]ÈŠÛÚ[™ÙXÚ[™ÙX[‹ŠKKœ\Ú
Ù]™[›‹\Ý[™\œÎJJ_]˜\ˆ\[[[[Ù[˜Ý[ÛˆYJJ^Õ™
K
_Y[˜Ý[ÛˆÜŠJ^ÚYŠ]

JJJ\™]\›ˆ_Y[˜Ý[ÛˆÜŠK
^ÚYŠOOOXÚ[™ÙX
\™]\›ˆ]˜\ˆYYOHLNÚYŠÛŠ^Ý˜\ˆœŽÚYŠÛŠ^Ý˜\ˆ\XÛš[œ][ˆØÝ[Y[ÚYŠ^\Š^Ý˜\ˆYOYØÝ[Y[˜Ü™X]Q[[Y[
]˜
NÙYKœÙ]]šX]JÛš[œ]™]\›ŽØ
K\]\[ÙˆYK›Ûš[œ]OX[˜Ý[Û˜]œ^\ŸY[ÙHœHLNÝYYO]œ‰‰ŠYØÝ[Y[™ØÝ[Y[[Ù_OØÝ[Y[™ØÝ[Y[[ÙJ_Y[˜Ý[Ûˆ™YJ
^Û\‰‰Š\‹™]XÚ]™[
Ûœ›Ü\XÚ[™ÙXœŠK[\[[
_Y[˜Ý[ÛˆœŠJ^ÚYŠKœ›Ü\S˜[YOOOX˜[YX	‰™ÜŠŠJ^Ý˜\ˆV×NÜŠ‹KÛŠJJKŠYK
__Y[˜Ý[ÛˆŠKŠ^ÙOOOX›ØÝ\Ú[˜Ê™YJ
K\][‹\‹˜]XÚ]™[
Ûœ›Ü\XÚ[™ÙXœŠJN™OOOX›ØÝ\ÛÝ]	‰™™YJ
_Y[˜Ý[ÛˆYJJ^ÚYŠOOOXÙ[XÝ[Û˜Ú[™ÙXOOOXÙ^]\OOOXÙ^YÝÛ˜
\™]\›ˆÜŠŠ_Y[˜Ý[ÛˆÜŠK
^ÚYŠOOOXÛXÚØ
\™]\›ˆÜŠ
_Y[˜Ý[ÛˆÜŠK
^ÚYŠOOOX[œ]OOOXÚ[™ÙX
\™]\›ˆÜŠ
_Y[˜Ý[ÛˆYYJK
^Ü™]\›ˆOOO]	‰ŠHOOLKÙOOLKÝ
_HOOYI‰OO]]˜\ˆÜ]\[ÙˆØš™XÝš\ÏOX[˜Ý[Û˜ÓØš™XÝš\Î›YYNÙ[˜Ý[ÛˆŠK
^ÚYŠÜŠK
J\™]\›ˆLÚYŠ\[ÙˆHOXØš™XÝY_\[ÙˆOXØš™XÝ]
\™]\›ˆLNÝ˜\ˆSØš™XÝšÙ^\ÊJKSØš™XÝšÙ^\Ê
NÚYŠ‹›[™ÝOO\‹›[™Ý
\™]\›ˆLNÙ›ÜŠLÜ‹›[™ÝÜŠÊÊ^Ý˜\ˆO[–Ü—NÚYŠSYK˜Ø[
J_]ÜŠVÚWKÚWJJ\™]\›ˆL_\™]\›ˆLY[˜Ý[Ûˆ\ŠJ^ÚYŠ_]\[ÙˆØÝ[Y[XÙØÝ[Y[›ÚYOOO]›ÚY
\™]\›ˆ[Ýž^Ü™]\›ˆK˜XÝ]™Q[[Y[K˜›Ù_XØ]ÚÜ™]\›ˆK˜›Ù__Y[˜Ý[ÛˆŠJ^Ù›ÜŠÙI‰™K™š\œÝÚ[ÊYOYK™š\œÝÚ[Ü™]\›ˆ_Y[˜Ý[ÛˆÜŠK
^Ý˜\ˆQŠJNÙOLÙ›ÜŠ˜\ˆŽÛŽÊ^ÚYŠ‹››ÙU\OOOLÊ^ÚYŠYJÛ‹^ÛÛ[›[™ÝO]	‰œ]
\™]\›žÛ›ÙN›‹Ù™œÙ]Y_NÙO\ŸXNžÙ›ÜŠÛŽÊ^ÚYŠ‹›™^ÚX›[™Ê^Û[‹›™^ÚX›[™ÎØœ™XZÈ_[[‹œ\™[›Ù_[]›ÚY[QŠŠ__Y[˜Ý[ÛˆÜŠK
^Ü™]\›ˆI‰ÙOOO]ÈL™I‰™K››ÙU\OOOLÏÈLN	‰››ÙU\OOOLÏÚÜŠKœ\™[›ÙJN˜ÛÛZ[œØ[ˆOÙK˜ÛÛZ[œÊ
N™K˜ÛÛ\\™QØÝ[Y[ÜÚ][ÛÈHJK˜ÛÛ\\™QØÝ[Y[ÜÚ][ÛŠ
IŒMŠNˆLNˆL_Y[˜Ý[Ûˆ\ŠJ^ÙOYHO[[	‰™K›ÝÛ™\‘ØÝ[Y[O[[	‰™K›ÝÛ™\‘ØÝ[Y[™Y˜][šY]ÈO[[ÙK›ÝÛ™\‘ØÝ[Y[™Y˜][šY]ÎÚ[™ÝÎÙ›ÜŠ˜\ˆQ\ŠK™ØÝ[Y[
NÝ[œÝ[˜Ù[ÙˆK’SQœ˜[YQ[[Y[Ê^Ýž^Ý˜\ˆ]\[Ùˆ˜ÛÛ[Ú[™ÝË›ØØ][Û‹š™YOXÝš[™ØXØ]ÚÛHL_ZYŠŠYO]˜ÛÛ[Ú[™ÝÎÙ[ÙHœ™XZÎÝQ\ŠK™ØÝ[Y[
_\™]\›ˆY[˜Ý[ÛˆœŠJ^Ý˜\ˆYI‰™K››ÙS˜[YI‰™K››ÙS˜[YKÓÝÙ\Ø\ÙJ
NÜ™]\›ˆ	‰ŠOOX[œ]	‰ŠK\OOOX^K\OOOXÙX\˜ÚK\OOOX[K\OOOX\›K\OOOX\ÜÝÛÜ™
_OOX^\™XXK˜ÛÛ[Y]X›OOOXYX
_]˜\ˆ\PÛ‰‰˜ØÝ[Y[[ÙX[ˆØÝ[Y[	‰ŒLOYØÝ[Y[™ØÝ[Y[[ÙKœ[[[[œ[[\HLNÙ[˜Ý[ÛˆŠKŠ^Ý˜\ˆ[‹Ú[™ÝÏOO[Û‹™ØÝ[Y[›‹››ÙU\OOONOÛŽ›‹›ÝÛ™\‘ØÝ[Y[Ò\ŸœO[[œˆOOQ\ŠŠ_
Sœ‹Ù[XÝ[Û”Ý\[ˆ‰‰šœŠŠOÜ^ÜÝ\œ‹œÙ[XÝ[Û”Ý\[™œ‹œÙ[XÝ[Û‘[™NŠJ‹›ÝÛ™\‘ØÝ[Y[	‰œ‹›ÝÛ™\‘ØÝ[Y[™Y˜][šY]ßÚ[™ÝÊK™Ù]Ù[XÝ[ÛŠ
K^Ø[˜ÚÜ“›ÙNœ‹˜[˜ÚÜ“›ÙK[˜ÚÜ“Ù™œÙ]œ‹˜[˜ÚÜ“Ù™œÙ]›ØÝ\Ó›ÙNœ‹™›ØÝ\Ó›ÙK›ØÝ\ÓÙ™œÙ]œ‹™›ØÝ\ÓÙ™œÙ]JKœ‰‰•Šœ‹Š_
œ\‹R™
‹Û”Ù[XÝ
K‹›[™Ý	‰Š[™]ÈŠÛ”Ù[XÝÙ[XÝ[ŠKKœ\Ú
Ù]™[\Ý[™\œÎœŸJK\™Ù]SœŠJJ_Y[˜Ý[ÛˆœŠK
^Ý˜\ˆ^ßNÜ™]\›ˆ–ÙKÓÝÙ\Ø\ÙJ
WO]ÓÝÙ\Ø\ÙJ
K–ØÙXšÚ]
ÙWOXÙXšÚ]
Ý–Ø[Þ˜
ÙWOX[Þ˜
ÝŸ]˜\ˆœ^Ø[š[X][Û™[™”œŠ[š[X][Û˜[š[X][Û‘[™
K[š[X][Ûš]\˜][ÛŽ”œŠ[š[X][Û˜[š[X][Û’]\˜][Û˜
K[š[X][ÛœÝ\”œŠ[š[X][Û˜[š[X][Û”Ý\
K˜[œÚ][Ûœ[Ž”œŠ˜[œÚ][Û˜˜[œÚ][Û”[˜
K˜[œÚ][ÛœÝ\”œŠ˜[œÚ][Û˜˜[œÚ][Û”Ý\
K˜[œÚ][Û˜Ø[˜Ù[”œŠ˜[œÚ][Û˜˜[œÚ][ÛØ[˜Ù[
K˜[œÚ][Û™[™”œŠ˜[œÚ][Û˜˜[œÚ][Û‘[™
_Kœ^ßKœ^ßNÐÛ‰‰ŠœYØÝ[Y[˜Ü™X]Q[[Y[
]˜
KœÝ[K[š[X][Û‘]™[[ˆÚ[™Ýß
[]Hœ‹˜[š[X][Û™[™˜[š[X][Û‹[]Hœ‹˜[š[X][Ûš]\˜][Û‹˜[š[X][Û‹[]Hœ‹˜[š[X][ÛœÝ\˜[š[X][ÛŠK˜[œÚ][Û‘]™[[ˆÚ[™Ýß[]Hœ‹˜[œÚ][Û™[™˜[œÚ][ÛŠNÙ[˜Ý[ÛˆŠJ^ÚYŠœ–ÙWJ\™]\›ˆœ–ÙWNÚYŠ^œ–ÙWJ\™]\›ˆNÝ˜\ˆ^œ–ÙWKŽÙ›ÜŠˆ[ˆ
ZYŠš\ÓÝÛ”›Ü\JŠI‰›ˆ[ˆœŠ\™]\›ˆœ–ÙWO]Û—NÜ™]\›ˆ_]˜\ˆ\RŠ[š[X][Û™[™
KÜRŠ[š[X][Ûš]\˜][Û˜
KÜRŠ[š[X][ÛœÝ\
KYORŠ˜[œÚ][Ûœ[˜
KÜRŠ˜[œÚ][ÛœÝ\
K\RŠ˜[œÚ][Û˜Ø[˜Ù[
KœRŠ˜[œÚ][Û™[™
KÙYO[™]ÈX\\XX›Ü]^ÛXÚÈ™Y›Ü™UÙÙÛHØ[˜Ù[Ø[”^HØ[”^U›ÝYÚÛXÚÈÛÜÙHÛÛ^Y[HÛÜHÝ]˜YÈ˜YÑ[™˜YÑ[\ˆ˜YÑ^]˜YÓX]™H˜YÓÝ™\ˆ˜YÔÝ\›Ü\˜][ÛÚ[™ÙH[\YY[˜Üž\Y[™Y\œ›Üˆ[ØÜ™Y[Ú[™ÙH[ØÜ™Y[‘\œ›ÜˆÛÝÚ[\Ø\\™H[œ][˜[YÙ^QÝÛˆÙ^T™\ÜÈÙ^U\ØYØYY]HØYYY]Y]HØYÝ\ÜÝÚ[\Ø\\™H[Ý\ÙQÝÛˆ[Ý\ÙS[Ý™H[Ý\ÙSÝ][Ý\ÙSÝ™\ˆ[Ý\ÙU\\ÝH]\ÙH^H^Z[™ÈÚ[\Ø[˜Ù[Ú[\‘ÝÛˆÚ[\“[Ý™HÚ[\“Ý]Ú[\“Ý™\ˆÚ[\•\›ÙÜ™\ÜÈ˜]PÚ[™ÙH™\Ù]™\Ú^™HÙYZÙYÙYZÚ[™ÈÝ[YÝX›Z]Ý\Ü[™[YU\]HÝXÚØ[˜Ù[ÝXÚ[™ÝXÚÝ\›Û[YPÚ[™ÙHØÜ›ÛÙÙÛHÝXÚ[Ý™HØZ][™ÈÚY[œÜ]

NÖ\‹œ\Ú
ØÜ›Û[™
NÙ[˜Ý[ÛˆŠK
^ÙÙYKœÙ]
K
K
ÙWJ_]˜\ˆÙYOLÙ[˜Ý[ÛˆœŠK
^ÚYŠK›˜[YHO[[	‰™K›˜[YHOOX]]Ø
\™]\›ˆK›˜[YNÚYŠ˜]]Ó˜[YHOO[[
\™]\›ˆ˜]]Ó˜[YNÙOZKšY[YšY\”™Yš^Ý˜\ˆWÙYJÊÎÜ™]\›ˆOXØ
ÙJØØ
Û‹ÔÝš[™ÊÌŠJØØ˜]]Ó˜[YOY_Y[˜Ý[Ûˆ\ŠJ^ÚYŠOO[[\[ÙˆOOXÝš[™Ø
\™]\›ˆNÝ˜\ˆ[[^NÚYŠˆOO[[
Y›ÜŠ˜\ˆLÜ‹›[™ÝÜŠÊÊ^Ý˜\ˆOYVÛ–Ü—WNÚYŠHO[[
^ÚYŠOOOX›Û™X
\™]\›˜›Û™XÝ]O[[ÚN
Ê
ÚJ__\™]\›ˆÏÙK™Y˜][Y[˜Ý[Ûˆ	ŠK
^Ü™]\›ˆOT\ŠJKT\Š
KO[[ÙOOOX]]ØÛ[™NOOX]]ØÛ[]˜\ˆZO]\[Ùˆ™\Ü\œ›ÜOX[˜Ý[Û˜Ü™\Ü\œ›ÜŽ™[˜Ý[ÛŠJ^ÚYŠ\[ÙˆÚ[™ÝÏOXØš™XÝ	‰\[ÙˆÚ[™ÝË‘\œ›Ü‘]™[OX[˜Ý[Û˜
^Ý˜\ˆ[™]ÈÚ[™ÝË‘\œ›Ü‘]™[
\œ›Ü˜ØX˜›\ÎˆLØ[˜Ù[X›NˆLY\ÜØYÙN\[ÙˆOOXØš™XÝ	‰™I‰\[ÙˆK›Y\ÜØYÙOOXÝš[™ØÔÝš[™ÊK›Y\ÜØYÙJN”Ýš[™ÊJK\œ›ÜŽ™_JNÚYŠ]Ú[™ÝË™\Ü]Ú]™[

J\™]\›ŸY[ÙHYŠ\[Ùˆ›ØÙ\ÜÏOXØš™XÝ	‰\[Ùˆ›ØÙ\ÜË™[Z]OX[˜Ý[Û˜
^Ü›ØÙ\ÜË™[Z]
[˜Ø]YÚ^Ù\[Û˜JNÜ™]\›ŸXÛÛœÛÛK™\œ›ÜŠJ_KOV×KšOLšOLÙ[˜Ý[ÛˆZJ
^Ù›ÜŠ˜\ˆO[šK\šO[šOLÝNÊ^Ý˜\ˆ]VÝNÝVÝ
Ê×O[[Ý˜\ˆ]VÝNÝVÝ
Ê×O[[Ý˜\ˆO]VÝNÝVÝ
Ê×O[[Ý˜\ˆO]VÝNÚYŠVÝ
Ê×O[[ˆOO[[	‰šHOO[[
^Ý˜\ˆÏ\‹œ[™[™ÎÛÏOO[[ÚK›™^ZNŠK›™^[Ë›™^Ë›™^ZJK‹œ[™[™ÏZ_XHOOL	‰˜ÚJ‹KJ__Y[˜Ý[ÛˆZJK‹Š^ÝVÛšJÊ×OYKVÛšJÊ×O]VÛšJÊ×O[‹VÛšJÊ×O\‹š_\‹K›[™\ß\‹OYK˜[\›˜]KHOO[[	‰ŠK›[™\ß\Š_Y[˜Ý[ÛˆÚJK‹Š^Ü™]\›ˆZJK‹ŠKJJ_Y[˜Ý[ÛˆÚJK
^Ü™]\›ˆZJK[[
KJJ_Y[˜Ý[ÛˆÚJKŠ^ÙK›[™\ß[ŽÝ˜\ˆYK˜[\›˜]NÜˆOO[[	‰Š‹›[™\ß[ŠNÙ›ÜŠ˜\ˆOHLKOYKœ™]\›ŽØHOO[[ÊXK˜Ú[[™\ß[‹XK˜[\›˜]KˆOO[[	‰Š‹˜Ú[[™\ß[ŠKKYÏOOLŒ‰‰ŠOXKœÝ]S›ÙKOOO[[K—Ýš\ÚXš[]IŒ_
OHL
JKOXKOXKœ™]\›ŽÜ™]\›ˆKYÏOOLÏÊOYKœÝ]S›ÙKI‰OO[[	‰ŠOLÌKVYJŠKOXKšY[•\]\ËYVÚWKOO[[ÙVÚWOVÝNœ‹œ\Ú

K›[™O[ŸLÍŽÌLLŠKJN›[Y[˜Ý[ÛˆJJ^ÚYŠLJ]›ÝÈOLO[[\œ›ÜŠJNJJNÙ›ÜŠ˜\ˆYKœ™]\›ŽÝOO[[ÊYO]YKœ™]\›ŽÜ™]\›ˆKYÏOOLÏÙKœÝ]S›ÙN›[]˜\ˆZO^ßNÙ[˜Ý[Ûˆ™YJK‹Š^Ý\ËYÏYK\ËšÙ^O[‹\ËœÚX›[™Ï]\Ë˜Ú[]\Ëœ™]\›]\ËœÝ]S›ÙO]\Ë\O]\Ë™[[Y[\O[[\Ëš[™^L\Ëœ™YÛX[\]\Ëœ™Y[[\Ëœ[™[™Ô›ÜÏ]\Ë™\[™[˜ÚY\Ï]\Ë›Y[[Ú^™YÝ]O]\Ë\]T]Y]YO]\Ë›Y[[Ú^™Y›ÜÏ[[\Ë›[ÙO\‹\ËœÝX™YQ›YÜÏ]\Ë™›YÜÏL\Ë™[][ÛœÏ[[\Ë˜Ú[[™\Ï]\Ë›[™\ÏL\Ë˜[\›˜]O[[Y[˜Ý[ÛˆJK‹Š^Ü™]\›ˆ™]È™YJK‹Š_Y[˜Ý[ÛˆšJJ^Ü™]\›ˆOYKœ›ÝÝ\KJY_YKš\Ô™XXÝÛÛ\Û™[
_Y[˜Ý[ÛˆJK
^Ý˜\ˆYK˜[\›˜]NÜ™]\›ˆOO[[ÊYJKYËKšÙ^KK›[ÙJK‹™[[Y[\OYK™[[Y[\K‹\OYK\K‹œÝ]S›ÙOYKœÝ]S›ÙK‹˜[\›˜]OYKK˜[\›˜]O[ŠNŠ‹œ[™[™Ô›ÜÏ]‹\OYK\K‹™›YÜÏL‹œÝX™YQ›YÜÏL‹™[][ÛœÏ[[
K‹™›YÜÏYK™›YÜÉŒLŒŽLLMÍ‹‹˜Ú[[™\ÏYK˜Ú[[™\Ë‹›[™\ÏYK›[™\Ë‹˜Ú[YK˜Ú[‹›Y[[Ú^™Y›ÜÏYK›Y[[Ú^™Y›ÜË‹›Y[[Ú^™YÝ]OYK›Y[[Ú^™YÝ]K‹\]T]Y]YOYK\]T]Y]YKYK™\[™[˜ÚY\Ë‹™\[™[˜ÚY\Ï]OO[[Û[žÛ[™\Î›[™\Ëš\œÝÛÛ^™š\œÝÛÛ^K‹œÚX›[™ÏYKœÚX›[™Ë‹š[™^YKš[™^‹œ™YYKœ™Y‹‹œ™YÛX[\YKœ™YÛX[\ŸY[˜Ý[ÛˆYYJK
^ÙK™›YÜÉLLŒŽLLMÎÝ˜\ˆYK˜[\›˜]NÜ™]\›ˆOO[[ÊK˜Ú[[™\ÏLK›[™\Ï]K˜Ú[[[KœÝX™YQ›YÜÏLK›Y[[Ú^™Y›ÜÏ[[K›Y[[Ú^™YÝ]O[[K\]T]Y]YO[[K™\[™[˜ÚY\Ï[[KœÝ]S›ÙO[[
NŠK˜Ú[[™\Ï[‹˜Ú[[™\ËK›[™\Ï[‹›[™\ËK˜Ú[[‹˜Ú[KœÝX™YQ›YÜÏLK™[][ÛœÏ[[K›Y[[Ú^™Y›ÜÏ[‹›Y[[Ú^™Y›ÜËK›Y[[Ú^™YÝ]O[‹›Y[[Ú^™YÝ]KK\]T]Y]YO[‹\]T]Y]YKK\O[‹\K[‹™\[™[˜ÚY\ËK™\[™[˜ÚY\Ï]OO[[Û[žÛ[™\Î›[™\Ëš\œÝÛÛ^™š\œÝÛÛ^JK_Y[˜Ý[ÛˆZJK‹‹KÊ^Ý˜\ˆÏLÚYŠYK\[ÙˆOX[˜Ý[Û˜
YšJŠI‰ŠÏLJNÙ[ÙHYŠ\[ÙˆOXÝš[™Ø
\Ï\
K‹ÙK˜Ý\œ™[
OÌŽ™OOOX[OOOXXYOOOX›ÙXÌÎNÙ[ÙHNœÝÚ]Ú
Š^ØØ\ÙHYNœ™]\›ˆOYJÌK‹JKK™[[Y[\OYYKK›[™\Ï[ËNØØ\ÙHÎœ™]\›ˆJ‹˜Ú[™[‹KË
NØØ\ÙHNœÏN_LØœ™XZÎØØ\ÙHŽœ™]\›ˆOYJL‹‹_ŠKK™[[Y[\OZ‹K›[™\Ï[ËNØØ\ÙHŽœ™]\›ˆOYJLË‹JKK™[[Y[\OQ‹K›[™\Ï[ËNØØ\ÙHNœ™]\›ˆOYJNK‹JKK™[[Y[\ORKK›[™\Ï[ËNØØ\ÙHN˜Ø\ÙH™Nœ™]\›ˆOX_Ì‹OYJÌ‹JKK™[[Y[\O\™KK›[™\Ï[ËKœÝ]S›ÙO^Ø]]Ó˜[YN›[Z\™Y›[ÛÛ™\Î›[™YŽ›[KNÙY˜][šYŠ\[ÙˆOXØš™XÝ	‰œŠ\ÝÚ]Ú
‹‰	\[ÙŠ^ØØ\ÙHŽœÏLLØœ™XZÈNØØ\ÙHNœÏNNØœ™XZÈNØØ\ÙHœÏLLNØœ™XZÈNØØ\ÙHœÏLMØœ™XZÈNØØ\ÙHŽœÏLM‹[[Øœ™XZÈ_\ÏLŽKQ\œ›ÜŠJLÌOOO[[Ø[\[ÙˆK
JK[[\™]\›ˆYJË‹JK™[[Y[\OYK\O\‹›[™\Ï[ËY[˜Ý[ÛˆJK‹Š^Ü™]\›ˆOYJËK‹
KK›[™\Ï[‹_Y[˜Ý[ÛˆÚJKŠ^Ü™]\›ˆOYJ‹K[
KK›[™\Ï[‹_Y[˜Ý[ÛˆÚJJ^Ý˜\ˆYJN[[
NÜ™]\›ˆœÝ]S›ÙOYKY[˜Ý[ÛˆšJKŠ^Ü™]\›ˆYJK˜Ú[™[OO[[Ö×N™K˜Ú[™[‹KšÙ^K
K›[™\Ï[‹œÝ]S›ÙO^ØÛÛZ[™\’[™›Î™K˜ÛÛZ[™\’[™›Ë[™[™ÐÚ[™[Ž›[[\[Y[][ÛŽ™Kš[\[Y[][ÛŸK]˜\ˆZO[™]ÈÙXZÓX\Ù[˜Ý[ÛˆšJK
^ÚYŠ\[ÙˆOOXØš™XÝ	‰™J^Ý˜\ˆ^ZK™Ù]
JNÜ™]\›ˆOO]›ÚYÊ^Ý˜[YN™KÛÝ\˜ÙNÝXÚÎš™J
_KZKœÙ]
K
K
N›Ÿ\™]\›žÝ˜[YN™KÛÝ\˜ÙNÝXÚÎš™J
__]˜\ˆOV×KÚOLÚO[[ÚOLOV×KZOLO[[ÚOLKÚOXÙ[˜Ý[ÛˆZJK
^ÞVÔÚJÊ×O]ÚKVÔÚJÊ×OPÚKÚOYKÚO]Y[˜Ý[ÛˆšJKŠ^ÕVÑZJÊ×OSÚKVÑZJÊ×OZÚKVÑZJÊ×OQKOYNÝ˜\ˆSÚNÙOZÚNÝ˜\ˆOLÌ‹VYJŠKLNÜ‰_ŠOJKŠÏLNÝ˜\ˆOLÌ‹VYJ
JÚNÚYŠÌJ^Ý˜\ˆÏZKZIMNØOJ‰ŠOÊKLJKÔÝš[™ÊÌŠK[ËKO[ËÚOLOÌ‹VYJ
JÚ__‹ÚOXJÙ_Y[ÙHÚOLO__‹ÚOY_Y[˜Ý[ÛˆZJJ^ÙKœ™]\›ˆOO[[	‰ŠZJKJKšJKK
J_Y[˜Ý[ÛˆšJJ^Ù›ÜŠÙOOOPÚNÊPÚO^VËKTÚWKVÔÚWO[[ÚO^VËKTÚWKVÔÚWO[[Ù›ÜŠÙOOOQNÊQOUVËKQZWKVÑZWO[[ÚOUVËKQZWKVÑZWO[[ÚOUVËKQZWKVÑZWO[[Y[˜Ý[ÛˆJK
^ÕVÑZJÊ×OSÚKVÑZJÊ×OZÚKVÑZJÊ×OQKÚO]šYÚO]›Ý™\™›ÝËOY_]˜\ˆšO[[ZO[[OHLKšO[[šOHLKšOQ\œ›ÜŠJLNJJNÙ[˜Ý[ÛˆšJJ^Ý›ÝÈZJšJ\œ›ÜŠJNO\™Ý[Y[Ë›[™Ý	‰˜\™Ý[Y[ÖÌWHOO]›ÚY	‰˜\™Ý[Y[ÖÌWOØ^˜S
JKJJKš_Y[˜Ý[ÛˆJJ^Ý˜\ˆYKœÝ]S›ÙKYK\KYK›Y[[Ú^™Y›ÜÎÜÝÚ]Ú
Þ]OYKØO\‹Š^ØØ\ÙXX[ÙØ’
Ø[˜Ù[
K
ÛÜÙX
NØœ™XZÎØØ\ÙXYœ˜[YX˜Ø\ÙXØš™XÝ˜Ø\ÙX[X™Y’
ØY
NØœ™XZÎØØ\ÙXšY[Ø˜Ø\ÙX]Y[Ø™›ÜŠLÛ™›[™ÝÛŠÊÊR
™Û—K
NØœ™XZÎØØ\ÙXÛÝ\˜ÙX’
\œ›Ü˜
NØœ™XZÎØØ\ÙX[YØ˜Ø\ÙX[XYÙX˜Ø\ÙX[šØ’
\œ›Ü˜
K
ØY
NØœ™XZÎØØ\ÙX]Z[Ø’
ÙÙÛX
NØœ™XZÎØØ\ÙX[œ]’
[˜[Y
K›Š‹˜[YK‹™Y˜][˜[YK‹˜ÚXÚÙY‹™Y˜][ÚXÚÙY‹\K‹›˜[YKL
NØœ™XZÎØØ\ÙXÙ[XÝ’
[˜[Y
NØœ™XZÎØØ\ÙX^\™XX’
[˜[Y
KÛŠ‹˜[YK‹™Y˜][˜[YK‹˜Ú[™[Š_[\‹˜Ú[™[‹\[ÙˆˆOXÝš[™Ø	‰\[ÙˆˆOX[X™\˜	‰\[ÙˆˆOXšYÚ[^ÛÛ[OOX
ÛŸLOO\‹œÝ\™\ÜÒY˜][Û•Ø\›š[™ß™
^ÛÛ[ŠOÊ‹œÜÝ™\ˆO[[	‰Š
™Y›Ü™]ÙÙÛX
K
ÙÙÛX
JK‹›Û”ØÜ›ÛO[[	‰’
ØÜ›Û
K‹›Û”ØÜ›Û[™O[[	‰’
ØÜ›Û[™
K‹›ÛÛXÚÈO[[	‰Š›Û˜ÛXÚÏ[[ŠKHL
NHLKšJKL
_Y[˜Ý[ÛˆZJJ^Ù›ÜŠšOYKœ™]\›ŽÑšNÊ\ÝÚ]Ú
šKYÊ^ØØ\ÙHN˜Ø\ÙHÌN˜Ø\ÙHLÎžšOHLNÜ™]\›ŽØØ\ÙHÎ˜Ø\ÙHÎžšOHLÜ™]\›ŽÙY˜][‘šOQšKœ™]\›Ÿ_Y[˜Ý[ÛˆÚJJ^ÚYŠHOOQšJ\™]\›ˆLNÚYŠSJ\™]\›ˆZJJKOHLLNÝ˜\ˆYKYËŽÚYŠ
]OOLÉ‰OOLÊI‰Š
]OOMJI‰ŠYK\KHJˆOOX›Ü›X	‰›ˆOOX]Û˜
_ÙŠK\KK›Y[[Ú^™Y›ÜÊJKH[ŠK‰‰’ZI‰•šJJKZJJKOOLLÊ^ÚYŠOYK›Y[[Ú^™YÝ]KOYOOO[[Û[™K™ZY˜]YYJ]›ÝÈ\œ›ÜŠJÌMÊJNÒZO^™ŠJ_Y[ÙHYŠOOLÌJ^ÚYŠOYK›Y[[Ú^™YÝ]KOYOOO[[Û[™K™ZY˜]YYJ]›ÝÈ\œ›ÜŠJÌMÊJNÒZO^™ŠJ_Y[ÙHOOLÏÊRZKYŠK\JOÊOT™‹™[[ZOYJN’ZO]
N’ZOQšOÓŠKœÝ]S›ÙK›™^ÚX›[™ÊN›[Ü™]\›ˆLY[˜Ý[ÛˆÚJ
^ÒZOQšO[[OHL_Y[˜Ý[ÛˆÚJ
^Ý˜\ˆOTšNÜ™]\›ˆHOO[[	‰ŠÝOOO[[ÐÝOYNÝKœ\Ú˜\JÝKJKšO[[
K_Y[˜Ý[ÛˆZJJ^ÔšOOO[[ÔšOVÙWN”šKœ\Ú
J_]˜\ˆšO[YJ[
KZO[[O[[Ù[˜Ý[ÛˆšJKŠ^ÙÙJšK—ØÝ\œ™[˜[YJK—ØÝ\œ™[˜[YO[ŸY[˜Ý[ÛˆZJJ^ÙK—ØÝ\œ™[˜[YORšK˜Ý\œ™[JšJ_Y[˜Ý[Ûˆ	JKŠ^Ù›ÜŠÙHOO[[Ê^Ý˜\ˆYK˜[\›˜]NÚYŠ
K˜Ú[[™\É
OOO]ÜˆOO[[	‰Š‹˜Ú[[™\É
HOO]	‰Š‹˜Ú[[™\ß]
NŠK˜Ú[[™\ß]ˆOO[[	‰Š‹˜Ú[[™\ß]
JKOOO[ŠXœ™XZÎÙOYKœ™]\›Ÿ_Y[˜Ý[ÛˆXJK‹Š^Ý˜\ˆOYK˜Ú[Ù›ÜŠHOO[[	‰ŠKœ™]\›YJNØHOO[[Ê^Ý˜\ˆÏXK™\[™[˜ÚY\ÎÚYŠÈOO[[
^Ý˜\ˆÏXK˜Ú[ÛÏ[Ë™š\œÝÛÛ^ØN™›ÜŠÛÈOO[[Ê^Ý˜\ˆ[ÎÛÏXNÙ›ÜŠ˜\ˆOLÝO›[™ÝÝJÊÊZYŠ˜ÛÛ^OO]ÝWJ^ÛË›[™\ß[‹[Ë˜[\›˜]KOO[[	‰Š›[™\ß[ŠK	JËœ™]\›‹‹JKŸ
Ï[[
NØœ™XZÈ_[Ï[›™^_Y[ÙHYŠKYÏOOLN
^ÚYŠÏXKœ™]\›‹ÏOO[[
]›ÝÈ\œ›ÜŠJÍJJNÜË›[™\ß[‹Ï\Ë˜[\›˜]KÈOO[[	‰ŠË›[™\ß[ŠK	JË‹JKÏ[[Y[ÙHKYÏOOLLÉ‰˜K›Y[[Ú^™YÝ]HOO[[	‰˜K›Y[[Ú^™YÝ]K™ZY˜]YOO[[ÊK›[™\ß[‹ÏXK˜[\›˜]KÈOO[[	‰ŠË›[™\ß[ŠK	JKœ™]\›‹‹JKÏXK˜Ú[Ï\ÏOO[[Û[œËœÚX›[™ÊNœÏXK˜Ú[ÚYŠÈOO[[
\Ëœ™]\›XNÙ[ÙH›ÜŠÏXNÜÈOO[[Ê^ÚYŠÏOOYJ^ÜÏ[[Øœ™XZßZYŠO\ËœÚX›[™ËHOO[[
^ØKœ™]\›\Ëœ™]\›‹ÏXNØœ™XZß\Ï\Ëœ™]\›ŸXO\ß_Y[˜Ý[ÛˆJK‹Š^ÙO[[Ù›ÜŠ˜\ˆO]ÏHLNØHOO[[Ê^ÚYŠ[Ê^ÚYŠK™›YÜÉLŽ
[ÏHLÙ[ÙHYŠK™›YÜÉŒŒŒM
Xœ™XZßZYŠKYÏOOLL
^Ý˜\ˆÏXK˜[\›˜]NÚYŠÏOO[[
]›ÝÈ\œ›ÜŠJÎÊJNÚYŠÏ\Ë›Y[[Ú^™Y›ÜËÈOO[[
^Ý˜\ˆXK\NÝÜŠKœ[™[™Ô›ÜË˜[YKË˜[YJ_
OOO[[ÙOVÛN™Kœ\Ú

J__Y[ÙHYŠOOOX™K˜Ý\œ™[
^ÚYŠÏXK˜[\›˜]KÏOO[[
]›ÝÈ\œ›ÜŠJÎÊJNÜË›Y[[Ú^™YÝ]K›Y[[Ú^™YÝ]HOOXK›Y[[Ú^™YÝ]K›Y[[Ú^™YÝ]I‰ŠOOO[[ÙOVÕN™Kœ\Ú

J_XOXKœ™]\›Ÿ\™]\›ˆHOO[[	‰™XJK‹ŠK™›YÜßLŒŒMHOO[[Y[˜Ý[Ûˆ˜JJ^Ù›ÜŠOYK™š\œÝÛÛ^ÙHOO[[Ê^ÚYŠ]ÜŠK˜ÛÛ^—ØÝ\œ™[˜[YKK›Y[[Ú^™Y˜[YJJ\™]\›ˆLÙOYK›™^\™]\›ˆL_Y[˜Ý[Ûˆ˜JJ^ÖZOYKO[[OYK™\[™[˜ÚY\ËHOO[[	‰ŠK™š\œÝÛÛ^[[
_Y[˜Ý[ÛˆXJJ^Ü™]\›ˆØJZKJ_Y[˜Ý[ÛˆXJK
^Ü™]\›ˆZOOO[[	‰œ˜JJKØJK
_Y[˜Ý[ÛˆØJK
^Ý˜\ˆ]—ØÝ\œ™[˜[YNÚYŠ^ØÛÛ^Y[[Ú^™Y˜[YN›‹™^›[KOOO[[
^ÚYŠOOO[[
]›ÝÈ\œ›ÜŠJÌ
JNÖO]K™\[™[˜ÚY\Ï^Û[™\ÎŒš\œÝÛÛ^KK™›YÜßMLŽY[ÙHOVK›™^]Ü™]\›ˆŸ]˜\ˆ™YO]\[ÙˆX›ÜÛÛ›Û\XÐX›ÜÛÛ›Û\Ž™[˜Ý[ÛŠ
^Ý˜\ˆOV×K]\ËœÚYÛ˜[^ØX›ÜYˆLKY]™[\Ý[™\Ž™[˜Ý[ÛŠŠ^ÙKœ\Ú
Š__NÝ\Ë˜X›ÜY[˜Ý[ÛŠ
^Ý˜X›ÜYHLK™›Ü‘XXÚ
[˜Ý[ÛŠJ^Ü™]\›ˆJ
_J__KØO][œÝX›WÜØÚY[PØ[˜XÚËØO][œÝX›WÓ›Ü›X[š[Üš]KO^É	\[ÙŽ“‹ÛÛœÝ[Y\Ž›[›ÝšY\Ž›[ØÝ\œ™[˜[YN›[ØÝ\œ™[˜[YLŽ›[Ý™XYÛÝ[ŒNÙ[˜Ý[ÛˆXJ
^Ü™]\›žØÛÛ›Û\Ž›™]È™YK]N›™]ÈX\™YÛÝ[Œ_Y[˜Ý[ÛˆJJ^ÙKœ™YÛÝ[KKKœ™YÛÝ[OOL	‰œØJØK[˜Ý[ÛŠ
^ÙK˜ÛÛ›Û\‹˜X›Ü

_J_Y[˜Ý[Ûˆ˜JK
^ÚYŠKœ[™[™Ó[™\ÉNM
^Ý˜\ˆYK˜[œÚ][Û•\\ÎÙ›ÜŠOO[[	‰ŠYK˜[œÚ][Û•\\ÏV×JKOLÙO›[™ÝÙJÊÊ^Ý˜\ˆ]ÙWNÛ‹š[™^ÙŠŠOOOKLI‰›‹œ\Ú
Š___]˜\ˆO[[Ù[˜Ý[ÛˆXJJ^Ý˜\ˆYK˜[œÚ][Û•\\ÎÜ™]\›ˆK˜[œÚ][Û•\\Ï[[]˜\ˆO[[ØOLØOL˜O[[Ù[˜Ý[ÛˆYJK
^ÚYŠOOO[[
^Ý˜\ˆZOV×NÙØOLØOQ™

K˜O^ÜÝ]\Î˜[™[™Ø˜[YN›ÚY[Ž™[˜Ý[ÛŠJ^Û‹œ\Ú
J___\™]\›ˆØJÊË[ŠÙYKÙYJKY[˜Ý[ÛˆÙYJ
^ÚYŠKYØOOOL	‰ŠO[[HOO[[
J^Ý˜HOO[[	‰Š˜KœÝ]\ÏX[š[Y
NÝ˜\ˆOZNÚO[[ØOL˜O[[Ù›ÜŠ˜\ˆLÝK›[™ÝÝ
ÊÊJVÝJJ
__Y[˜Ý[ÛˆXJK
^Ý˜\ˆV×K^ÜÝ]\Î˜[™[™Ø˜[YN›[™X\ÛÛŽ›[[Ž™[˜Ý[ÛŠJ^Û‹œ\Ú
J__NÜ™]\›ˆK[Š[˜Ý[ÛŠ
^Ü‹œÝ]\ÏX[š[Y‹˜[YO]Ù›ÜŠ˜\ˆOLÙO‹›[™ÝÙJÊÊJ–ÙWJJ
_K[˜Ý[ÛŠJ^Ù›ÜŠ‹œÝ]\ÏX™Z™XÝY‹œ™X\ÛÛYKOLÙO‹›[™ÝÙJÊÊJ–ÙWJJ›ÚY
_JKŸ]˜\ˆ˜O[K”ÎÛK”ÏY[˜Ý[ÛŠK
^ÚYŠ]OSJ
K\[ÙˆOXØš™XÝ	‰	‰\[Ùˆ[OX[˜Ý[Û˜	‰žYJK
KHOO[[
Y›ÜŠ˜\ˆPÙÛˆOO[[ÊY˜J‹JK[‹›™^ÚYŠYK\\ËˆOO[[
^Ù›ÜŠ˜\ˆPÙÜˆOO[[ÊY˜J‹ŠK\‹›™^ÚYŠØHOOL
^Ü\KOO[[	‰Š\OV×JNÙ›ÜŠ˜\ˆOLÚO‹›[™ÝÚJÊÊ^Ý˜\ˆO[–ÚWNÜ‹š[™^ÙŠJOOOKLI‰œ‹œ\Ú
J___X˜HOO[[	‰˜˜JK
_NÝ˜\ˆO[YJ[
NÙ[˜Ý[ÛˆØJ
^Ý˜\ˆO^K˜Ý\œ™[Ü™]\›ˆOOO[[ÜÝKœÛÛYØXÚN™_Y[˜Ý[ÛˆØJK
^ÝOO[[ÙÙJKK˜Ý\œ™[
N™ÙJKœÛÛ
_Y[˜Ý[ÛˆØJ
^Ý˜\ˆOTØJ
NÜ™]\›ˆOOO[[Û[žÜ\™[›K—ØÝ\œ™[˜[YKÛÛ™__]˜\ˆOQ\œ›ÜŠJŒ
JKXOQ\œ›ÜŠJÍ
JKOQ\œ›ÜŠJMŠJKØO^Ý[Ž™[˜Ý[ÛŠ
^ß_NÙ[˜Ý[ÛˆØJJ^Ü™]\›ˆOYKœÝ]\ËOOOX[š[YOOOX™Z™XÝYY[˜Ý[ÛˆXJKŠ^ÜÝÚ]Ú
YVÛ—KOO]›ÚYÙKœ\Ú

N›ˆOO]	‰Š[Š[‹[ŠK[ŠKœÝ]\Ê^ØØ\ÙX[š[Yœ™]\›ˆ˜[YNØØ\ÙX™Z™XÝY›ÝÈO]œ™X\ÛÛ‹JJKOOO]›ÚY	‰ˆJ™X\ÛÛ˜[ˆ
OÑ\œ›ÜŠJŒ
JN™NÙY˜][šYŠ\[ÙˆœÝ]\ÏOXÝš[™Ø
][Š[‹[ŠNÙ[Ù^ÚYŠO\ÝKHOO[[	‰ŒLKœÚ[Ý\Ü[™ÛÝ[\Š]›ÝÈ\œ›ÜŠJŠJNÙO]KœÝ]\ÏX[™[™ØK[Š[˜Ý[ÛŠJ^ÚYŠœÝ]\ÏOOX[™[™Ø
^Ý˜\ˆ]Û‹œÝ]\ÏX[š[Y‹˜[YOY__K[˜Ý[ÛŠJ^ÚYŠœÝ]\ÏOOX[™[™Ø
^Ý˜\ˆ]Û‹œÝ]\ÏX™Z™XÝY‹œ™X\ÛÛY__J_\ÝÚ]Ú
œÝ]\Ê^ØØ\ÙX[š[Yœ™]\›ˆ˜[YNØØ\ÙX™Z™XÝY›ÝÈO]œ™X\ÛÛ‹JJK_]›ÝÈXO]__Y[˜Ý[Ûˆ˜JJ^Ýž^Ý˜\ˆYK—Ú[š]Ü™]\›ˆ
K—Ü^[ØY
_XØ]Ú
J^Ý›ÝÈ\[ÙˆOOXØš™XÝ	‰™I‰\[ÙˆK[OX[˜Ý[Û˜ÊXOYKJN™__]˜\ˆXO[[Ù[˜Ý[Ûˆ˜J
^ÚYŠXOOO[[
]›ÝÈ\œ›ÜŠJNJJNÝ˜\ˆOSXNÜ™]\›ˆXO[[_Y[˜Ý[ÛˆJJ^ÚYŠOOOU_OOOQJ]›ÝÈ\œ›ÜŠJÊJ_]˜\ˆ˜O[[XOLÙ[˜Ý[ÛˆJJ^Ý˜\ˆRXNÜ™]\›ˆXJÏLK˜OOO[[	‰Š˜OV×JKXJ˜KK
_Y[˜Ý[Ûˆ˜JK
^Ý]œ›ÜËœ™Y‹Kœ™Y]OO]›ÚYÛ[Y[˜Ý[Ûˆ˜JK
^Ý›ÝÈ‰	\[ÙOOQOÑ\œ›ÜŠJLJJNŠOSØš™XÝœ›ÝÝ\KÔÝš[™Ë˜Ø[

K\œ›ÜŠJÌKOOOXÛØš™XÝØš™XÝXØØš™XÝÚ]Ù^\ÈØ
ÓØš™XÝšÙ^\Ê
Kš›Ú[Š
JØX™JJJ_Y[˜Ý[ÛˆÙYJJ^Ù[˜Ý[Ûˆ
Š^ÚYŠJ^Ý˜\ˆ]™[][ÛœÎÜOO[[Ê™[][ÛœÏVÛ—K™›YÜßLMŠNœ‹œ\Ú
Š__Y[˜Ý[ÛˆŠ‹Š^ÚYŠYJ\™]\›ˆ[Ù›ÜŠÜˆOO[[Ê]
‹ŠK\‹œÚX›[™ÎÜ™]\›ˆ[Y[˜Ý[ÛˆŠJ^Ù›ÜŠ˜\ˆ[™]ÈX\ÙHOO[[ÊYKšÙ^OOO[[ÝœÙ]
Kš[™^JNœÙ]
KšÙ^KJKOYKœÚX›[™ÎÜ™]\›ˆY[˜Ý[ÛˆJK
^Ü™]\›ˆO\JK
KKš[™^LKœÚX›[™Ï[[_Y[˜Ý[ÛˆÊ‹Š^Ü™]\›ˆš[™^\‹OÊ]˜[\›˜]KOO[[Ê™›YÜßLLÍŒMÍÌÌŠNŠ\‹š[™^Ê™›YÜßL‹ŠNœŠJNŠ™›YÜßLLMÍ‹Š_Y[˜Ý[ÛˆÊ
^Ü™]\›ˆI‰˜[\›˜]OOO[[	‰Š™›YÜßLLÍŒMÍÌÌ
KY[˜Ý[Ûˆ
K‹Š^Ü™]\›ˆOO[[YÈOOMÊYÚJ‹K›[ÙKŠKœ™]\›YK
NŠXJŠKœ™]\›YK
_Y[˜Ý[ÛˆJK‹Š^Ý˜\ˆO[‹\NÜ™]\›ˆOOOZÏÊOYŠK‹œ›ÜË˜Ú[™[‹‹‹šÙ^JK˜JKŠKJNOO[[	‰Š™[[Y[\OOOZ_\[ÙˆOOXØš™XÝ	‰šI‰šK‰	\[ÙOOT‰‰š˜JJOOO]\JOÊXJ‹œ›ÜÊK˜JŠKœ™]\›YK
NŠ[ZJ‹\K‹šÙ^K‹œ›ÜË[K›[ÙKŠK˜JŠKœ™]\›YK
_Y[˜Ý[Ûˆ
K‹Š^Ü™]\›ˆOO[[YÈOOMœÝ]S›ÙK˜ÛÛZ[™\’[™›ÈOO[‹˜ÛÛZ[™\’[™›ßœÝ]S›ÙKš[\[Y[][ÛˆOO[‹š[\[Y[][ÛÊ]šJ‹K›[ÙKŠKœ™]\›YK
NŠXJ‹˜Ú[™[Ÿ×JKœ™]\›YK
_Y[˜Ý[ÛˆŠK‹‹J^Ü™]\›ˆOO[[YÈOOMÏÊZJ‹K›[ÙK‹JKœ™]\›YK
NŠXJŠKœ™]\›YK
_Y[˜Ý[Ûˆ
KŠ^ÚYŠ\[ÙˆOXÝš[™Ø	‰OOX\[ÙˆOX[X™\˜\[ÙˆOXšYÚ[
\™]\›ˆYÚJ
ÝK›[ÙKŠKœ™]\›YKÚYŠ\[ÙˆOXØš™XÝ	‰
^ÜÝÚ]Ú
‰	\[ÙŠ^ØØ\ÙHœ™]\›ˆ[ZJ\KšÙ^Kœ›ÜË[K›[ÙKŠK˜J‹
K‹œ™]\›YKŽØØ\ÙHÎœ™]\›ˆ]šJK›[ÙKŠKœ™]\›YKØØ\ÙHŽœ™]\›ˆZ˜J
K
KŠ_ZYŠÙJ
_Š
J\™]\›ˆZJK›[ÙK‹[
Kœ™]\›YKÚYŠ\[Ùˆ[OX[˜Ý[Û˜
\™]\›ˆ
KJ
KŠNÚYŠ‰	\[ÙOOSŠ\™]\›ˆ
KXJK
KŠNÞ˜JK
_\™]\›ˆ[Y[˜Ý[ÛˆJK‹Š^Ý˜\ˆO]OO[[Û[šÙ^NÚYŠ\[ÙˆOXÝš[™Ø	‰›ˆOOX\[ÙˆOX[X™\˜\[ÙˆOXšYÚ[
\™]\›ˆOOO[[Û
K
Û‹ŠN›[ÚYŠ\[ÙˆOXØš™XÝ	‰›Š^ÜÝÚ]Ú
‹‰	\[ÙŠ^ØØ\ÙHœ™]\›ˆ‹šÙ^OOOZOÝJK‹ŠN›[ØØ\ÙHÎœ™]\›ˆ‹šÙ^OOOZOÙ
K‹ŠN›[ØØ\ÙHŽœ™]\›ˆZ˜JŠKJK‹Š_ZYŠÙJŠ_ŠŠJ\™]\›ˆOOO[[ÙŠK‹‹[
N›[ÚYŠ\[Ùˆ‹[OX[˜Ý[Û˜
\™]\›ˆJKJŠKŠNÚYŠ‹‰	\[ÙOOSŠ\™]\›ˆJKXJKŠKŠNÞ˜JKŠ_\™]\›ˆ[Y[˜Ý[Ûˆ
K‹‹J^ÚYŠ\[ÙˆOXÝš[™Ø	‰œˆOOX\[ÙˆOX[X™\˜\[ÙˆOXšYÚ[
\™]\›ˆOYK™Ù]
Š_[
K
Ü‹JNÚYŠ\[ÙˆOXØš™XÝ	‰œŠ^ÜÝÚ]Ú
‹‰	\[ÙŠ^ØØ\ÙHœ™]\›ˆOYK™Ù]
‹šÙ^OOO[[ÛŽœ‹šÙ^J_[JK‹JNØØ\ÙHÎœ™]\›ˆOYK™Ù]
‹šÙ^OOO[[ÛŽœ‹šÙ^J_[
K‹JNØØ\ÙHŽœ™]\›ˆZ˜JŠK
K‹‹J_ZYŠÙJŠ_ŠŠJ\™]\›ˆOYK™Ù]
Š_[ŠK‹K[
NÚYŠ\[Ùˆ‹[OX[˜Ý[Û˜
\™]\›ˆ
K‹JŠKJNÚYŠ‹‰	\[ÙOOSŠ\™]\›ˆ
K‹XJŠKJNÞ˜JŠ_\™]\›ˆ[Y[˜Ý[ÛˆÊKKË
^Ù›ÜŠ˜\ˆO[[[[XKÏXOLÏ[[ÙˆOO[[	‰™ÏË›[™ÝÙÊÊÊ^Ù‹š[™^™ÏÊÏY‹[[
N—ÏY‹œÚX›[™ÎÝ˜\ˆ[JK‹ÖÙ×K
NÚYŠOO[[
^ÙOO[[	‰ŠWÊNØœ™XZßYI‰™‰‰‹˜[\›˜]OOO[[	‰
KŠKO[Ê‹KÊKOO[[ÝO]Ž™œÚX›[™Ï]‹]‹WßZYŠÏOO\Ë›[™Ý
\™]\›ˆŠKŠKI‰ZJKÊKNÚYŠOO[[
^Ù›ÜŠÙÏË›[™ÝÙÊÊÊY\
KÖÙ×K
KˆOO[[	‰ŠO[Ê‹KÊKOO[[ÝOYŽ™œÚX›[™ÏY‹YŠNÜ™]\›ˆI‰ZJKÊK_Y›ÜŠ\ŠŠNÙÏË›[™ÝÙÊÊÊWÏZ
‹KËÖÙ×K
KÈOO[[	‰ŠI‰ŠWË˜[\›˜]KˆOO[[	‰™‹™[]J‹šÙ^OOO[[ÙÎ‹šÙ^JJKO[ÊËKÊKOO[[ÝOWÎ™œÚX›[™ÏWËWÊNÜ™]\›ˆI‰™‹™›Ü‘XXÚ
[˜Ý[ÛŠJ^Ü™]\›ˆ
KJ_JKI‰ZJKÊK_Y[˜Ý[ÛˆÊKËJ^ÚYŠO[[
]›ÝÈ\œ›ÜŠJMLJJNÙ›ÜŠ˜\ˆ[[[[Ï\ËÏ\ÏL[[O[›™^

NÙÈOO[[	‰ˆ^K™Û™N×ÊÊËO[›™^

J^ÙËš[™^—ÏÊYËÏ[[
NYËœÚX›[™ÎÝ˜\ˆ[JKËK˜[YKJNÚYŠOO[[
^ÙÏOO[[	‰ŠÏ]ŠNØœ™XZßYI‰™É‰˜‹˜[\›˜]OOO[[	‰
KÊKÏ[Ê‹ËÊKOO[[ÙXŽ™‹œÚX›[™ÏX‹X‹Ï]ŸZYŠK™Û™J\™]\›ˆŠKÊKI‰ZJKÊKÚYŠÏOO[[
^Ù›ÜŠÈ^K™Û™N×ÊÊËO[›™^

J^O\
KK˜[YKJKHOO[[	‰ŠÏ[ÊKËÊKOO[[Ù^N™‹œÚX›[™Ï^K^JNÜ™]\›ˆI‰ZJKÊKY›ÜŠÏ\ŠÊNÈ^K™Û™N×ÊÊËO[›™^

J^OZ
ËKËK˜[YKJKHOO[[	‰ŠI‰Š^K˜[\›˜]KˆOO[[	‰™Ë™[]J‹šÙ^OOO[[×Î‹šÙ^JJKÏ[ÊKËÊKOO[[Ù^N™‹œÚX›[™Ï^K^JNÜ™]\›ˆI‰™Ë™›Ü‘XXÚ
[˜Ý[ÛŠJ^Ü™]\›ˆ
KJ_JKI‰ZJKÊKY[˜Ý[ÛˆŠK‹Ë
^ÚYŠ\[ÙˆÏOXØš™XÝ	‰›É‰›Ë\OOOZÉ‰›ËšÙ^OOO[[	‰›Ëœ›ÜËœ™YOO]›ÚY	‰ŠÏ[Ëœ›ÜË˜Ú[™[ŠK\[ÙˆÏOXØš™XÝ	‰›Ê^ÜÝÚ]Ú
Ë‰	\[ÙŠ^ØØ\ÙH˜NžÙ›ÜŠ˜\ˆO[ËšÙ^NÜˆOO[[Ê^ÚYŠ‹šÙ^OOO]J^ÚYŠO[Ë\KOOOZÊ^ÚYŠ‹YÏOOMÊ^ÛŠK‹œÚX›[™ÊKXJ‹Ëœ›ÜË˜Ú[™[ŠK˜JÊKœ™]\›YKO[Øœ™XZÈ__Y[ÙHYŠ‹™[[Y[\OOO]_\[ÙˆOOXØš™XÝ	‰I‰K‰	\[ÙOOT‰‰š˜JJOOO\‹\J^ÛŠK‹œÚX›[™ÊKXJ‹Ëœ›ÜÊK˜JÊKœ™]\›YKO[Øœ™XZÈ_[ŠKŠNØœ™XZßY[ÙH
KŠNÜ\‹œÚX›[™ß[Ë\OOOZÏÊZJËœ›ÜË˜Ú[™[‹K›[ÙKËšÙ^JK˜JÊKœ™]\›YKO[
NŠ[ZJË\KËšÙ^KËœ›ÜË[K›[ÙK
K˜JÊKœ™]\›YKO[
_\™]\›ˆÊJNØØ\ÙHÎ˜NžÙ›ÜŠO[ËšÙ^NÜˆOO[[Ê^ÚYŠ‹šÙ^OOO]JZYŠ‹YÏOOM	‰œ‹œÝ]S›ÙK˜ÛÛZ[™\’[™›ÏOO[Ë˜ÛÛZ[™\’[™›É‰œ‹œÝ]S›ÙKš[\[Y[][ÛOO[Ëš[\[Y[][ÛŠ^ÛŠK‹œÚX›[™ÊKXJ‹Ë˜Ú[™[Ÿ×JKœ™]\›YKO[Øœ™XZÈ_Y[Ù^ÛŠKŠNØœ™XZßY[ÙH
KŠNÜ\‹œÚX›[™ß[]šJËK›[ÙK
Kœ™]\›YKO[\™]\›ˆÊJNØØ\ÙHŽœ™]\›ˆÏZ˜JÊKŠK‹Ë
_ZYŠÙJÊJ\™]\›ˆÊK‹Ë
NÚYŠŠÊJ^ÚYŠO^ŠÊK\[ÙˆHOX[˜Ý[Û˜
]›ÝÈ\œ›ÜŠJML
JNÜ™]\›ˆÏ]K˜Ø[
ÊKÊK‹Ë
_ZYŠ\[ÙˆË[OX[˜Ý[Û˜
\™]\›ˆŠK‹JÊK
NÚYŠË‰	\[ÙOOSŠ\™]\›ˆŠK‹XJKÊK
NÞ˜JKÊ_\™]\›ˆ\[ÙˆÏOXÝš[™Ø	‰›ÈOOX\[ÙˆÏOX[X™\˜\[ÙˆÏOXšYÚ[ÊÏX
ÛËˆOO[[	‰œ‹YÏOOMÊŠK‹œÚX›[™ÊKXJ‹ÊKœ™]\›YKO[
NŠŠKŠKYÚJËK›[ÙK
Kœ™]\›YKO[
KÊJJN›ŠKŠ_\™]\›ˆ[˜Ý[ÛŠK‹Š^Ýž^ÒXOLÝ˜\ˆO]ŠK‹ŠNÜ™]\›ˆ˜O[[_XØ]Ú

^ÚYŠOOU_OOQJ]›ÝÈÝ˜\ˆOYJŽK[K›[ÙJNÜ™]\›ˆK›[™\Ï\‹Kœ™]\›YK___]˜\ˆ˜OPÙYJL
K˜OPÙYJLJKOHLNÙ[˜Ý[ÛˆXJJ^ÙK\]T]Y]YO^Ø˜\ÙTÝ]N™K›Y[[Ú^™YÝ]Kš\œÝ˜\ÙU\]N›[\Ý˜\ÙU\]N›[Ú\™YžÜ[™[™Î›[[™\ÎŒY[Ø[˜XÚÜÎ›[KØ[˜XÚÜÎ›[_Y[˜Ý[ÛˆØJK
^ÙOYK\]T]Y]YK\]T]Y]YOOOYI‰Š\]T]Y]YO^Ø˜\ÙTÝ]N™K˜˜\ÙTÝ]Kš\œÝ˜\ÙU\]N™K™š\œÝ˜\ÙU\]K\Ý˜\ÙU\]N™K›\Ý˜\ÙU\]KÚ\™Y™KœÚ\™YØ[˜XÚÜÎ›[J_Y[˜Ý[ÛˆØJJ^Ü™]\›žÛ[™N™KYÎŒ^[ØY›[Ø[˜XÚÎ›[™^›[_Y[˜Ý[ÛˆØJKŠ^Ý˜\ˆYK\]T]Y]YNÚYŠOO[[
\™]\›ˆ[ÚYŠ\‹œÚ\™YÝIŒŠ^Ý˜\ˆO\‹œ[™[™ÎÜ™]\›ˆOOO[[Ý›™^]Š›™^ZK›™^K›™^]
K‹œ[™[™Ï][JJKÚJK[ŠK\™]\›ˆZJK‹ŠKJJ_Y[˜Ý[ÛˆXJKŠ^ÚYŠ]\]T]Y]YKOO[[	‰Š]œÚ\™Y‰NM
J^Ý˜\ˆ]›[™\ÎÜ‰YKœ[™[™Ó[™\ËŸ\‹›[™\Ï[‹
KŠ__Y[˜Ý[Ûˆ˜JK
^Ý˜\ˆYK\]T]Y]YKYK˜[\›˜]NÚYŠˆOO[[	‰Š\‹\]T]Y]YKOO\ŠJ^Ý˜\ˆO[[O[[ÚYŠ[‹™š\œÝ˜\ÙU\]KˆOO[[
^ÙÞÝ˜\ˆÏ^Û[™N›‹›[™KYÎ›‹YË^[ØY›‹œ^[ØYØ[˜XÚÎ›[™^›[NØOOO[[ÚOXO[Î˜OXK›™^[Ë[‹›™^]Ú[JˆOO[[
NØOOO[[ÚOXO]˜OXK›™^]Y[ÙHOXO]Û^Ø˜\ÙTÝ]Nœ‹˜˜\ÙTÝ]Kš\œÝ˜\ÙU\]NšK\Ý˜\ÙU\]N˜KÚ\™Yœ‹œÚ\™YØ[˜XÚÜÎœ‹˜Ø[˜XÚÜßKK\]T]Y]YO[ŽÜ™]\›ŸYO[‹›\Ý˜\ÙU\]KOOO[[Û‹™š\œÝ˜\ÙU\]O]™K›™^]‹›\Ý˜\ÙU\]O]]˜\ˆXOHLNÙ[˜Ý[ÛˆJ
^ÚYŠXJ^Ý˜\ˆO]˜NÚYŠHOO[[
]›ÝÈ__Y[˜Ý[Ûˆ˜JK‹Š^ÖXOHLNÝ˜\ˆOYK\]T]Y]YNÒOHLNÝ˜\ˆOZK™š\œÝ˜\ÙU\]KÏZK›\Ý˜\ÙU\]KÏZKœÚ\™Yœ[™[™ÎÚYŠÈOO[[
^ÚKœÚ\™Yœ[™[™Ï[[Ý˜\ˆ\ËO[›™^Û›™^[[ÏOO[[ØO]N›Ë›™^]KÏ[Ý˜\ˆYK˜[\›˜]NÙOO[[	‰ŠY\]T]Y]YKÏY›\Ý˜\ÙU\]KÈOO[É‰ŠÏOO[[Ù™š\œÝ˜\ÙU\]O]NœË›™^]K›\Ý˜\ÙU\]O[
J_ZYŠHOO[[
^Ý˜\ˆZK˜˜\ÙTÝ]NÛÏL]O[[[ÏXNÙÞÝ˜\ˆ\Ë›[™I‹MLÍŽÌLLËO\OO\Ë›[™NÚYŠOÊIœ
OOO\Š‰œ
OOO\
^ÜOOL	‰œOOWØI‰ŠXOHL
KOO[[	‰ŠY›™^^Û[™NŒYÎœËYË^[ØYœËœ^[ØYØ[˜XÚÎ›[™^›[JNØNžÝ˜\ˆYKÏ\ÎÜ]Ý˜\ˆÏ[ŽÜÝÚ]Ú
ËYÊ^ØØ\ÙHNšYŠYËœ^[ØY\[ÙˆOX[˜Ý[Û˜
^ÙZ˜Ø[
Ë‹
NØœ™XZÈ_YZØœ™XZÈNØØ\ÙHÎš™›YÜÏZ™›YÜÉ‹MMLÍßLŽØØ\ÙHšYŠYËœ^[ØY]\[ÙˆOX[˜Ý[Û˜Ú˜Ø[
Ë‹
NšO[[
Xœ™XZÈNÙU
ßK‹
NØœ™XZÈNØØ\ÙHŽ’OHL_\\Ë˜Ø[˜XÚËOO[[	‰ŠK™›YÜßMI‰ŠK™›YÜßNNLŠKOZK˜Ø[˜XÚÜËOOO[[ÚK˜Ø[˜XÚÜÏVÜN›Kœ\Ú

J_Y[ÙHO^Û[™NœYÎœËYË^[ØYœËœ^[ØYØ[˜XÚÎœË˜Ø[˜XÚË™^›[KOO[[ÊOY[KYŠN™Y›™^[Kß\ÚYŠÏ\Ë›™^ÏOO[[
^ÚYŠÏZKœÚ\™Yœ[™[™ËÏOO[[
Xœ™XZÎÛO\ËÏ[K›™^K›™^[[K›\Ý˜\ÙU\]O[KKœÚ\™Yœ[™[™Ï[[_]Ú[JJNÙOO[[	‰ŠYŠKK˜˜\ÙTÝ]O[K™š\œÝ˜\ÙU\]O]KK›\Ý˜\ÙU\]OYOOO[[	‰ŠKœÚ\™Y›[™\ÏL
KÝ_[ËK›[™\Ï[ËK›Y[[Ú^™YÝ]OYŸ_Y[˜Ý[ÛˆÙYJK
^ÚYŠ\[ÙˆHOX[˜Ý[Û˜
]›ÝÈ\œ›ÜŠJNLKJJNÙK˜Ø[

_Y[˜Ý[ÛˆYJK
^Ý˜\ˆYK˜Ø[˜XÚÜÎÚYŠˆOO[[
Y›ÜŠK˜Ø[˜XÚÜÏ[[OLÙO‹›[™ÝÙJÊÊ]ÙYJ–ÙWK
_]˜\ˆXO[YJ[
K	O[YJ
NÙ[˜Ý[ÛˆYYJK
^ÙOZKÙJ	KJKÙJXK
KOY_˜˜\ÙS[™\ßY[˜Ý[Ûˆ[Ê
^ÙÙJ	KJKÙJXKXK˜Ý\œ™[
_Y[˜Ý[ÛˆÊ
^ÚOIK˜Ý\œ™[JXJKJ	J_]˜\ˆ›Ï[YJ[
K›Ï[[Ù[˜Ý[Ûˆ[ÊJ^Ý˜\ˆYK˜[\›˜]NÙÙJËË˜Ý\œ™[	ŒJKÙJ›ËJK›ÏOO[[	‰ŠOO[[XK˜Ý\œ™[OO[[›Y[[Ú^™YÝ]HOO[[
I‰Š›ÏYJ_Y[˜Ý[Ûˆ[ÊJ^ÙÙJËË˜Ý\œ™[
KÙJ›ËJK›ÏOO[[	‰Š›ÏYJ_Y[˜Ý[ÛˆÛÊJ^ÙKYÏOOLŒÊÙJËË˜Ý\œ™[
KÙJ›ËJK›ÏOO[[	‰Š›ÏYJJNœÛÊ
_Y[˜Ý[ÛˆÛÊ
^ÙÙJËË˜Ý\œ™[
KÙJ›Ë›Ë˜Ý\œ™[
_Y[˜Ý[ÛˆÛÊJ^ÚJ›ÊK›ÏOOYI‰Š›Ï[[
KJÊ_]˜\ˆÏ[YJ
NÙ[˜Ý[Ûˆ[ÊK
^ÙÙJ›Ë›Ë˜Ý\œ™[
KÙJË
_Y[˜Ý[Ûˆ›ÊJ^ÚJÊKJ›ÊK›ÏOOYI‰Š›Ï[[
_Y[˜Ý[ÛˆÊJ^Ù›ÜŠ˜\ˆYNÝOO[[Ê^ÚYŠYÏOOLLÊ^Ý˜\ˆ]›Y[[Ú^™YÝ]NÚYŠˆOO[[	‰Š[‹™ZY˜]YOO[[™ŠŠ_YŠŠJJ\™]\›ˆY[ÙHYŠYÏOOLNI‰›Y[[Ú^™Y›ÜËœ™]™X[Ü™\ˆOOX[™\[™[
^ÚYŠ™›YÜÉŒLŽ
\™]\›ˆY[ÙHYŠ˜Ú[OO[[
^Ý˜Ú[œ™]\›]]˜Ú[ØÛÛ[Y_ZYŠOOYJXœ™XZÎÙ›ÜŠÝœÚX›[™ÏOO[[Ê^ÚYŠœ™]\›OO[[œ™]\›OOYJ\™]\›ˆ[Ý]œ™]\›Ÿ]œÚX›[™Ëœ™]\›]œ™]\›‹]œÚX›[™ß\™]\›ˆ[]˜\ˆ[ÏLÏ[[ÛÏ[[ÛÏ[[›ÏHLK[ÏHLK›ÏHLKÏLÛÏLÛÏ[[ÛÏLÙ[˜Ý[ÛˆÊ
^Ý›ÝÈ\œ›ÜŠJÌŒJJ_Y[˜Ý[Ûˆ[ÊK
^ÚYŠOO[[
\™]\›ˆLNÙ›ÜŠ˜\ˆLÛ›[™Ý	‰›K›[™ÝÛŠÊÊZYŠ]ÜŠVÛ—KÛ—JJ\™]\›ˆLNÜ™]\›ˆLY[˜Ý[ÛˆÊK‹‹KJ^Ü™]\›ˆ[ÏXKÏ]›Y[[Ú^™YÝ]O[[\]T]Y]YO[[›[™\ÏLK’YOOO[[K›Y[[Ú^™YÝ]OOO[[ÔÎ‘œË›ÏHLKO[Š‹JK›ÏHLK[É‰ŠOZÛÊ‹‹JJKÛÊJK_Y[˜Ý[ÛˆÛÊJ^ÛK’SœÎÝ˜\ˆYÛÈOO[[	‰™ÛË›™^OO[[ÚYŠ[ÏLÛÏYÛÏZÏ[[›ÏHLKÛÏLÛÏ[[
]›ÝÈ\œ›ÜŠJÌ
JNÙOOO[[\ß
OYK™\[™[˜ÚY\ËHOO[[	‰›˜JJI‰Š\ÏHL
J_Y[˜Ý[ÛˆÛÊK‹Š^ÚÏYNÝ˜\ˆOLÙÞÚYŠ[É‰ŠÛÏ[[
KÛÏL[ÏHLKOXJ]›ÝÈ\œ›ÜŠJÌJJNÚYŠJÏLKÛÏYÛÏ[[K\]T]Y]YHO[[
^Ý˜\ˆÏYK\]T]Y]YNÛË›\ÝY™™XÝ[[Ë™]™[Ï[[ËœÝÜ™\Ï[[Ë›Y[[ÐØXÚHO[[	‰ŠË›Y[[ÐØXÚKš[™^L
_[K’R\ËÏ]
‹Š_]Ú[J[ÊNÜ™]\›ˆßY[˜Ý[ÛˆYJ
^Ý˜\ˆO[K’YK\ÙTÝ]J
VÌNÜ™]\›ˆ]\[Ùˆ[OX[˜Ý[Û˜Ò[Ê
NOYK\ÙTÝ]J
VÌK
ÛÏOO[[Û[™ÛË›Y[[Ú^™YÝ]JHOOYI‰ŠË™›YÜßLL
KY[˜Ý[Ûˆ[Ê
^Ý˜\ˆO^ÈOOLÜ™]\›ˆÏL_Y[˜Ý[Ûˆ›ÊKŠ^Ý\]T]Y]YOYK\]T]Y]YK™›YÜÉKLŒLËK›[™\É_›ŸY[˜Ý[Ûˆ[ÊJ^ÚYŠ›Ê^Ù›ÜŠOYK›Y[[Ú^™YÝ]NÙHOO[[Ê^Ý˜\ˆYKœ]Y]YNÝOO[[	‰Šœ[™[™Ï[[
KOYK›™^]›ÏHL_[[ÏLÛÏYÛÏZÏ[[[ÏHLKÛÏ^ÏLÛÏ[[Y[˜Ý[Ûˆ›Ê
^Ý˜\ˆO^ÛY[[Ú^™YÝ]N›[˜\ÙTÝ]N›[˜\ÙT]Y]YN›[]Y]YN›[™^›[NÜ™]\›ˆÛÏOO[[ÚË›Y[[Ú^™YÝ]OWÛÏYN—ÛÏWÛË›™^YKÛßY[˜Ý[ÛˆÊ
^ÚYŠÛÏOO[[
^Ý˜\ˆOZË˜[\›˜]NÙOYOOO[[Û[™K›Y[[Ú^™YÝ]_Y[ÙHOYÛË›™^Ý˜\ˆWÛÏOO[[ÚË›Y[[Ú^™YÝ]N—ÛË›™^ÚYŠOO[[
WÛÏ]ÛÏYNÙ[Ù^ÚYŠOOO[[
]›ÝÈË˜[\›˜]OOO[[Ñ\œ›ÜŠJÊJN‘\œ›ÜŠJÌL
JNÙÛÏYKO^ÛY[[Ú^™YÝ]N™ÛË›Y[[Ú^™YÝ]K˜\ÙTÝ]N™ÛË˜˜\ÙTÝ]K˜\ÙT]Y]YN™ÛË˜˜\ÙT]Y]YK]Y]YN™ÛËœ]Y]YK™^›[KÛÏOO[[ÚË›Y[[Ú^™YÝ]OWÛÏYN—ÛÏWÛË›™^Y_\™]\›ˆÛßY[˜Ý[Ûˆ›Ê
^Ü™]\›žÛ\ÝY™™XÝ›[]™[Î›[ÝÜ™\Î›[Y[[ÐØXÚN›[_Y[˜Ý[Ûˆ[ÊJ^Ý˜\ˆTÛÎÜ™]\›ˆÛÊÏLKÛÏOO[[	‰ŠÛÏV×JKOPXJÛËK
KZË
ÛÏOO[[Ý›Y[[Ú^™YÝ]N—ÛË›™^
OOO[[	‰Š]˜[\›˜]KK’]OO[[›Y[[Ú^™YÝ]OOO[[ÔÎ‘œÊK_Y[˜Ý[ÛˆÊJ^ÚYŠ\[ÙˆOOXØš™XÝ	‰™J^ÚYŠ\[ÙˆK[OX[˜Ý[Û˜
\™]\›ˆ[ÊJNÚYŠK‰	\[ÙOOZYJ\™]\›ŽÚYŠK‰	\[ÙOOSŠ\™]\›ˆXJJ_]›ÝÈ\œ›ÜŠJÎÝš[™ÊJJJ_Y[˜Ý[Ûˆ›ÊJ^Ý˜\ˆ[[ZË\]T]Y]YNÚYŠˆOO[[	‰Š[‹›Y[[ÐØXÚJKO[[
^Ý˜\ˆZË˜[\›˜]NÜˆOO[[	‰Š\‹\]T]Y]YKˆOO[[	‰Š\‹›Y[[ÐØXÚKˆO[[	‰Š^Ù]Nœ‹™]K›X\
[˜Ý[ÛŠJ^Ü™]\›ˆKœÛXÙJ
_JK[™^ŒJJJ_ZYŠÏÏ^Ù]N–×K[™^ŒKOO[[	‰ŠQ›Ê
KË\]T]Y]YO[ŠK‹›Y[[ÐØXÚO]]™]VÝš[™^KOO]›ÚY
Y›ÜŠ]™]VÝš[™^OP\œ˜^JJKLÜNÜŠÊÊ[–Ü—O[™NÜ™]\›ˆš[™^
ÊËŸY[˜Ý[Ûˆ›ÊK
^Ü™]\›ˆ\[ÙˆOX[˜Ý[Û˜Ý
JNY[˜Ý[Ûˆ›ÊJ^Ü™]\›ˆ›ÊÊ
KÛËJ_Y[˜Ý[Ûˆ›ÊKŠ^Ý˜\ˆYKœ]Y]YNÚYŠOO[[
]›ÝÈ\œ›ÜŠJÌLJJNÜ‹›\Ý™[™\™Y™YXÙ\[ŽÝ˜\ˆOYK˜˜\ÙT]Y]YKÏ\‹œ[™[™ÎÚYŠÈOO[[
^ÚYŠHOO[[
^Ý˜\ˆÏXK›™^ØK›™^[Ë›™^Ë›™^\ß]˜˜\ÙT]Y]YOXO[Ë‹œ[™[™Ï[[ZYŠÏYK˜˜\ÙTÝ]KOOO[[
YK›Y[[Ú^™YÝ]O[ÎÙ[Ù^ÝXK›™^Ý˜\ˆ\Ï[[O[[]HLNÙÞÝ˜\ˆY›[™I‹MLÍŽÌLLÎÚYŠOOY›[™OÊ[Éœ
OOO\ŠIœ
OOO\
^Ý˜\ˆOYœ™]™\[™NÚYŠOOOL
]HOO[[	‰ŠO]K›™^^Û[™NŒ™]™\[™NŒÙ\Ý\™N›[XÝ[ÛŽ™˜XÝ[Û‹\ÑXYÙ\”Ý]N™š\ÑXYÙ\”Ý]KXYÙ\”Ý]N™™XYÙ\”Ý]K™^›[JKOOWØI‰ŠHL
NÙ[ÙHYŠ
[É›JOOO[J^ÙY›™^OOOWØI‰ŠHL
NØÛÛ[Y_Y[ÙH^Û[™NŒ™]™\[™N™œ™]™\[™KÙ\Ý\™N›[XÝ[ÛŽ™˜XÝ[Û‹\ÑXYÙ\”Ý]N™š\ÑXYÙ\”Ý]KXYÙ\”Ý]N™™XYÙ\”Ý]K™^›[KOOO[[Ê]O\Ï[ÊNO]K›™^\Ë›[™\ß[KÝ_[NÜY˜XÝ[Û‹›É‰›ŠË
KÏYš\ÑXYÙ\”Ý]OÙ™XYÙ\”Ý]N›ŠË
_Y[ÙHO^Û[™Nœ™]™\[™N™œ™]™\[™KÙ\Ý\™N™™Ù\Ý\™KXÝ[ÛŽ™˜XÝ[Û‹\ÑXYÙ\”Ý]N™š\ÑXYÙ\”Ý]KXYÙ\”Ý]N™™XYÙ\”Ý]K™^›[KOOO[[Ê]O[KÏ[ÊNO]K›™^[KË›[™\ß\Ý_\ÙY›™^]Ú[JOO[[	‰™OO]
NÚYŠOOO[[ÜÏ[ÎK›™^[]ÜŠËK›Y[[Ú^™YÝ]JI‰Š\ÏHL‰‰Š]˜KˆOO[[
JJ]›ÝÈŽÙK›Y[[Ú^™YÝ]O[ËK˜˜\ÙTÝ]O\ËK˜˜\ÙT]Y]YO]K‹›\Ý™[™\™YÝ]O[ß\™]\›ˆOOO[[	‰Š‹›[™\ÏL
KÙK›Y[[Ú^™YÝ]K‹™\Ü]Ú_Y[˜Ý[ÛˆÊJ^Ý˜\ˆTÊ
K]œ]Y]YNÚYŠOO[[
]›ÝÈ\œ›ÜŠJÌLJJNÛ‹›\Ý™[™\™Y™YXÙ\YNÝ˜\ˆ[‹™\Ü]ÚO[‹œ[™[™ËÏ]›Y[[Ú^™YÝ]NÚYŠHOO[[
^Û‹œ[™[™Ï[[Ý˜\ˆÏXOXK›™^ÙÈÏYJËË˜XÝ[ÛŠKÏ\Ë›™^ÝÚ[JÈOOXJNÝÜŠË›Y[[Ú^™YÝ]J_
\ÏHL
K›Y[[Ú^™YÝ]O[Ë˜˜\ÙT]Y]YOOO[[	‰Š˜˜\ÙTÝ]O[ÊK‹›\Ý™[™\™YÝ]O[ß\™]\›–ÛË—_Y[˜Ý[Ûˆ[ÊKŠ^Ý˜\ˆZËOTÊ
KÏSNÚYŠÊ^ÚYŠOO]›ÚY
]›ÝÈ\œ›ÜŠJÊJNÛ[Š
_Y[ÙH]

NÝ˜\ˆÏH]ÜŠ
ÛßJK›Y[[Ú^™YÝ]KŠNÚYŠÉ‰ŠK›Y[[Ú^™YÝ]O[‹\ÏHL
KOXKœ]Y]YKÜÊÛË˜š[™
[‹KJKÙWJKOXK™Ù]Û˜\ÚÝOO]ßÛÈOO[[	‰ŠÛË›Y[[Ú^™YÝ]KYÉŒJHOLœÊOÎNŽÙ\Ý›ÞN›ÚYKÛË˜š[™
[‹K‹
K[
KJ^ÚYŠ‹™›YÜßLŒÝOOO[[
]›ÝÈ\œ›ÜŠJÍJJNÛß[ÉŒLßÛÊ‹Š_\™]\›ˆŸY[˜Ý[ÛˆÛÊKŠ^ÙK™›YÜßLMŒÎO^ÙÙ]Û˜\ÚÝ˜[YN›ŸKZË\]T]Y]YKOO[[ÊQ›Ê
KË\]T]Y]YO]œÝÜ™\ÏVÙWJNŠ]œÝÜ™\ËOO[[ÝœÝÜ™\ÏVÙWN›‹œ\Ú
JJ_Y[˜Ý[ÛˆÛÊK‹Š^Ý˜[YO[‹™Ù]Û˜\ÚÝ\‹[Ê
I‰’›ÊJ_Y[˜Ý[ÛˆÛÊKŠ^Ü™]\›ˆŠ[˜Ý[ÛŠ
^Ü[Ê
I‰’›ÊJ_J_Y[˜Ý[Ûˆ[ÊJ^Ý˜\ˆYK™Ù]Û˜\ÚÝÙOYK˜[YNÝž^Ý˜\ˆ]

NÜ™]\›ˆ]ÜŠKŠ_XØ]ÚÜ™]\›ˆL_Y[˜Ý[Ûˆ›ÊJ^Ý˜\ˆ\ÚJKŠNÝOO[[	‰•ÝJKŠ_Y[˜Ý[Ûˆ[ÊJ^Ý˜\ˆS›Ê
NÚYŠ\[ÙˆOOX[˜Ý[Û˜
^Ý˜\ˆYNÚYŠO[Š
K›Ê^Ò™JL
NÝž^ÛŠ
_Yš[˜[^Ò™JLJ___\™]\›ˆ›Y[[Ú^™YÝ]O]˜˜\ÙTÝ]OYKœ]Y]YO^Ü[™[™Î›[[™\ÎŒ\Ü]Ú›[\Ý™[™\™Y™YXÙ\Žž›Ë\Ý™[™\™YÝ]N™_KY[˜Ý[ÛˆÙYJK‹Š^Ü™]\›ˆK˜˜\ÙTÝ]O[‹›ÊKÛË\[ÙˆOX[˜Ý[Û˜ÜŽž›Ê_Y[˜Ý[ÛˆÊK‹‹J^ÚYŠ\ÊJJ]›ÝÈ\œ›ÜŠJJJNÚYŠO]˜XÝ[Û‹HOO[[
^Ý˜\ˆÏ^Ü^[ØY˜KXÝ[ÛŽ™K™^›[\Õ˜[œÚ][ÛŽˆLÝ]\Î˜[™[™Ø˜[YN›[™X\ÛÛŽ›[\Ý[™\œÎ–×K[Ž™[˜Ý[ÛŠJ^ÛË›\Ý[™\œËœ\Ú
J__NÛK•OO[[ÛËš\Õ˜[œÚ][ÛHLN›ŠL
KŠÊK]œ[™[™ËOO[[ÊË›™^]œ[™[™Ï[Ë›ÊÊJNŠË›™^[‹›™^œ[™[™Ï[‹›™^[Ê__Y[˜Ý[Ûˆ›ÊK
^Ý˜\ˆ]˜XÝ[Û‹]œ^[ØYOYKœÝ]NÚYŠš\Õ˜[œÚ][ÛŠ^Ý˜\ˆO[K•Ï^ßNÛË\\ÏXOOO[[Û[˜K\\ËK•[ÎÝž^Ý˜\ˆÏ[ŠKŠK[K”ÎÛOO[[	‰›
ËÊKÙYJKÊ_XØ]Ú
Š^ÉÊKŠ_Yš[˜[^ØHOO[[	‰›Ë\\ÈOO[[	‰ŠK\\Ï[Ë\\ÊKK•X__Y[ÙHž^ØO[ŠKŠKÙYJKJ_XØ]Ú
Š^ÉÊKŠ__Y[˜Ý[ÛˆÙYJKŠ^Ý\[ÙˆOXØš™XÝ	‰›‰‰\[Ùˆ‹[OX[˜Ý[Û˜Û‹[Š[˜Ý[ÛŠŠ^Ô[ÊKŠ_K[˜Ý[ÛŠŠ^Ü™]\›ˆ	ÊKŠ_JN”[ÊKŠ_Y[˜Ý[Ûˆ[ÊKŠ^ÝœÝ]\ÏX[š[Y˜[YO[‹\Ê
KKœÝ]O[‹YKœ[™[™ËOO[[	‰Š]›™^OO]ÙKœ[™[™Ï[[Š[‹›™^›™^[‹›ÊKŠJJ_Y[˜Ý[Ûˆ	ÊKŠ^Ý˜\ˆYKœ[™[™ÎÚYŠKœ[™[™Ï[[ˆOO[[
^Ü\‹›™^ÙÈœÝ]\ÏX™Z™XÝYœ™X\ÛÛ[‹\Ê
K]›™^ÝÚ[JOO\Š_YK˜XÝ[Û[[Y[˜Ý[Ûˆ\ÊJ^ÙOYK›\Ý[™\œÎÙ›ÜŠ˜\ˆLÝK›[™ÝÝ
ÊÊJVÝJJ
_Y[˜Ý[ÛˆÊK
^Ü™]\›ˆY[˜Ý[ÛˆœÊK
^ÚYŠJ^Ý˜\ˆ\ÝK™›Ü›TÝ]NÚYŠˆOO[[
^ØNžÝ˜\ˆZÎÚYŠJ^ÚYŠZJ^ØŽžÙ›ÜŠ˜\ˆORZKO^šNÚK››ÙU\HOONÊ^ÚYŠXJ^ÚO[[Øœ™XZÈŸZYŠOSŠK›™^ÚX›[™ÊKOOO[[
^ÚO[[Øœ™XZÈŸ_XOZK™]KOXOOOXˆXOOOX˜ÚN›[ZYŠJ^ÒZOSŠK›™^ÚX›[™ÊKZK™]OOOXˆXØœ™XZÈ__UšJŠ_\HL_\‰‰Š[–ÌJ__\™]\›ˆS›Ê
K‹›Y[[Ú^™YÝ]O[‹˜˜\ÙTÝ]O]^Ü[™[™Î›[[™\ÎŒ\Ü]Ú›[\Ý™[™\™Y™YXÙ\ŽË\Ý™[™\™YÝ]NK‹œ]Y]YO\‹QË˜š[™
[ËŠK‹™\Ü]Ú[‹V[ÊLJKOZÜË˜š[™
[ËLK‹œ]Y]YJKS›Ê
KO^ÜÝ]N\Ü]Ú›[XÝ[ÛŽ™K[™[™Î›[K‹œ]Y]YOZKVË˜š[™
[ËKKŠKK™\Ü]Ú[‹‹›Y[[Ú^™YÝ]OYKÝ‹LW_Y[˜Ý[ÛˆYYJJ^Ü™]\›ˆ™YJÊ
KÛËJ_Y[˜Ý[Ûˆ™YJKŠ^ÚYŠU›ÊKÊVÌKOP›Ê›ÊVÌK\[ÙˆOXØš™XÝ	‰	‰\[Ùˆ[OX[˜Ý[Û˜
]ž^Ý˜\ˆR[Ê
_XØ]Ú
J^Ý›ÝÈOOOUOÑN™_Y[ÙH]ÝTÊ
NÝ˜\ˆO]œ]Y]YKOZK™\Ü]ÚÜ™]\›ˆˆOO]›Y[[Ú^™YÝ]I‰ŠË™›YÜßLŒœÊKÙ\Ý›ÞN›ÚYKYYK˜š[™
[KŠK[
JKÜ‹KW_Y[˜Ý[ÛˆYYJK
^ÙK˜XÝ[Û]Y[˜Ý[Ûˆ™YJJ^Ý˜\ˆTÊ
KYÛÎÚYŠˆOO[[
\™]\›ˆ™YJ‹JNÔÊ
K]›Y[[Ú^™YÝ]KTÊ
NÝ˜\ˆ[‹œ]Y]YK™\Ü]ÚÜ™]\›ˆ‹›Y[[Ú^™YÝ]OYKÝ‹LW_Y[˜Ý[ÛˆœÊK‹Š^Ü™]\›ˆO^ÝYÎ™KÜ™X]N›‹\Îœ‹[œÝ™^›[KZË\]T]Y]YKOO[[	‰ŠQ›Ê
KË\]T]Y]YO]
K]›\ÝY™™XÝOO[[Ý›\ÝY™™XÝYK›™^YNŠ[‹›™^‹›™^YKK›™^\‹›\ÝY™™XÝYJK_Y[˜Ý[Ûˆ\Ê
^Ü™]\›ˆÊ
K›Y[[Ú^™YÝ]_Y[˜Ý[Ûˆ\ÊK‹Š^Ý˜\ˆOS›Ê
NÚË™›YÜßYKK›Y[[Ú^™YÝ]O\œÊ_Ù\Ý›ÞN›ÚYK‹OO]›ÚYÛ[œŠ_Y[˜Ý[ÛˆÜÊK‹Š^Ý˜\ˆOTÊ
NÜ\OO]›ÚYÛ[œŽÝ˜\ˆOZK›Y[[Ú^™YÝ]Kš[œÝÙÛÈOO[[	‰œˆOO[[	‰‘[Ê‹ÛË›Y[[Ú^™YÝ]K™\ÊOÚK›Y[[Ú^™YÝ]O\œÊK‹ŠNŠË™›YÜßYKK›Y[[Ú^™YÝ]O\œÊ_K‹ŠJ_Y[˜Ý[ÛˆÜÊK
^Ø\ÊÎLM‹K
_Y[˜Ý[ÛˆÜÊK
^ÛÜÊŒK
_Y[˜Ý[ÛˆÊJ^ÚË™›YÜßMÝ˜\ˆZË\]T]Y]YNÚYŠOO[[
]Q›Ê
KË\]T]Y]YO]™]™[ÏVÙWNÙ[Ù^Ý˜\ˆ]™]™[ÎÛOO[[Ý™]™[ÏVÙWN›‹œ\Ú
J__Y[˜Ý[Ûˆ\ÊJ^Ý˜\ˆTÊ
K›Y[[Ú^™YÝ]NÜ™]\›ˆÊÜ™YŽ™^[\™_JK[˜Ý[ÛŠ
^ÚYŠÝIŒŠ]›ÝÈ\œ›ÜŠJ
JNÜ™]\›ˆš[\˜\J›ÚY\™Ý[Y[Ê__Y[˜Ý[ÛˆÊK
^Ü™]\›ˆÜÊ‹K
_Y[˜Ý[ÛˆœÊK
^Ü™]\›ˆÜÊK
_Y[˜Ý[ÛˆÊK
^ÚYŠ\[ÙˆOX[˜Ý[Û˜
^ÙOYJ
NÝ˜\ˆ]
JNÜ™]\›ˆ[˜Ý[ÛŠ
^Ý\[ÙˆOX[˜Ý[Û˜ÛŠ
N
[
__ZYŠO[[
\™]\›ˆOYJ
K˜Ý\œ™[YK[˜Ý[ÛŠ
^Ý˜Ý\œ™[[[_Y[˜Ý[Ûˆ\ÊKŠ^Û[O[[Û[›‹˜ÛÛ˜Ø]
ÙWJKÜÊË˜š[™
[JKŠ_Y[˜Ý[ÛˆÊ
^ßY[˜Ý[ÛˆÜÊK
^Ý˜\ˆTÊ
NÝ]OO]›ÚYÛ[Ý˜\ˆ[‹›Y[[Ú^™YÝ]NÜ™]\›ˆOO[[	‰‘[Ê–ÌWJOÜ–ÌNŠ‹›Y[[Ú^™YÝ]OVÙKKJ_Y[˜Ý[ÛˆYJK
^Ý˜\ˆTÊ
NÝ]OO]›ÚYÛ[Ý˜\ˆ[‹›Y[[Ú^™YÝ]NÚYŠOO[[	‰‘[Ê–ÌWJJ\™]\›ˆ–ÌNÚYŠYJ
K›Ê^Ò™JL
NÝž^ÙJ
_Yš[˜[^Ò™JLJ__\™]\›ˆ‹›Y[[Ú^™YÝ]OVÜ‹KŸY[˜Ý[ÛˆÜÊKŠ^Ü™]\›ˆOO]›ÚY[ÉŒLÌÍÍN	‰ˆJIŒŒNLÌ
OÙK›Y[[Ú^™YÝ]O]ŠK›Y[[Ú^™YÝ]O[‹OTYYJ
KË›[™\ßYKÝ_YKŠ_Y[˜Ý[Ûˆ™YJK‹Š^Ü™]\›ˆÜŠ‹
OÛŽ”XK˜Ý\œ™[OO[[ÈJ[ÉŒLŠ_[ÉŒLÌÍÍN	‰ˆJIŒŒNLÌ
OÊ\ÏHLK›Y[[Ú^™YÝ]O[ŠNŠOTYYJ
KË›[™\ßYKÝ_YK
NŠOWÜÊK‹ŠKÜŠK
_
\ÏHL
KJ_Y[˜Ý[ÛˆYYJK‹‹J^Ý˜\ˆO]YKœÝYKœXHOOL	‰Ž˜OØNŽÝ˜\ˆÏ[K•Ï^ßNÜË\\Ï[ÏOO[[Û[›Ë\\ËK•\ËÜÊKLKŠNÝž^Ý˜\ˆZJ
KO[K”ÎÝHOO[[	‰JË
K\[ÙˆOXØš™XÝ	‰›	‰\[Ùˆ[OX[˜Ý[Û˜ÓÜÊKXJŠKJJJN“ÜÊK‹JJJ_XØ]Ú
Š^ÓÜÊKÝ[Ž™[˜Ý[ÛŠ
^ßKÝ]\Î˜™Z™XÝY™X\ÛÛŽ›ŸKJ
J_Yš[˜[^ÝYKœXKÈOO[[	‰œË\\ÈOO[[	‰ŠË\\Ï\Ë\\ÊKK•[ß_Y[˜Ý[ÛˆœÊ
^ßY[˜Ý[Ûˆ\ÊK‹Š^ÚYŠKYÈOOMJ]›ÝÈ\œ›ÜŠJÍŠJNÝ˜\ˆOXœÊJKœ]Y]YNÒYYJKKKOO[[ÝœÎ™[˜Ý[ÛŠ
^Ü™]\›ˆÊJKŠŠ_J_Y[˜Ý[ÛˆœÊJ^Ý˜\ˆYK›Y[[Ú^™YÝ]NÚYŠOO[[
\™]\›ˆÝ^ÛY[[Ú^™YÝ]N™K˜\ÙTÝ]N™K˜\ÙT]Y]YN›[]Y]YNžÜ[™[™Î›[[™\ÎŒ\Ü]Ú›[\Ý™[™\™Y™YXÙ\Žž›Ë\Ý™[™\™YÝ]N™_K™^›[NÝ˜\ˆ^ßNÜ™]\›ˆ›™^^ÛY[[Ú^™YÝ]N›‹˜\ÙTÝ]N›‹˜\ÙT]Y]YN›[]Y]YNžÜ[™[™Î›[[™\ÎŒ\Ü]Ú›[\Ý™[™\™Y™YXÙ\Žž›Ë\Ý™[™\™YÝ]N›ŸK™^›[KK›Y[[Ú^™YÝ]O]OYK˜[\›˜]KHOO[[	‰ŠK›Y[[Ú^™YÝ]O]
KY[˜Ý[ÛˆÊJ^Ý˜\ˆXœÊJNÝ›™^OO[[	‰ŠYK˜[\›˜]K›Y[[Ú^™YÝ]JKÜÊK›™^œ]Y]YKßKJ
J_Y[˜Ý[ÛˆÜÊ
^Ü™]\›ˆXJ
_Y[˜Ý[ÛˆÜÊ
^Ü™]\›ˆÊ
K›Y[[Ú^™YÝ]_Y[˜Ý[ÛˆÜÊ
^Ü™]\›ˆÊ
K›Y[[Ú^™YÝ]_Y[˜Ý[ÛˆÊJ^Ù›ÜŠ˜\ˆYKœ™]\›ŽÝOO[[Ê^ÜÝÚ]Ú
YÊ^ØØ\ÙH˜Ø\ÙHÎ˜\ˆRJ
NÙOQØJŠNÝ˜\ˆRØJKŠNÜˆOO[[	‰ŠÝJ‹ŠKXJ‹ŠJK^ØØXÚNXJ
_KKœ^[ØY]Ü™]\›Ÿ]]œ™]\›Ÿ_Y[˜Ý[Ûˆ\ÊKŠ^Ý˜\ˆRJ
NÛ^Û[™Nœ‹™]™\[™NŒÙ\Ý\™N›[XÝ[ÛŽ›‹\ÑXYÙ\”Ý]NˆLKXYÙ\”Ý]N›[™^›[K\ÊJOÚœÊŠNŠ[ÚJK‹ŠKˆOO[[	‰ŠÝJ‹KŠK\Ê‹ŠJJ_Y[˜Ý[ÛˆÊKŠ^ÓÜÊK‹J
J_Y[˜Ý[ÛˆÜÊK‹Š^Ý˜\ˆO^Û[™Nœ‹™]™\[™NŒÙ\Ý\™N›[XÝ[ÛŽ›‹\ÑXYÙ\”Ý]NˆLKXYÙ\”Ý]N›[™^›[NÚYŠ\ÊJJZœÊJNÙ[Ù^Ý˜\ˆOYK˜[\›˜]NÚYŠK›[™\ÏOOL	‰ŠOOO[[K›[™\ÏOOL
I‰ŠO]›\Ý™[™\™Y™YXÙ\‹HOO[[
J]ž^Ý˜\ˆÏ]›\Ý™[™\™YÝ]KÏXJËŠNÚYŠKš\ÑXYÙ\”Ý]OHLK™XYÙ\”Ý]O\ËÜŠËÊJ\™]\›ˆZJKK
KÝOOO[[	‰šZJ
KL_XØ]ÚßZYŠ[ÚJKKŠKˆOO[[
\™]\›ˆÝJ‹KŠK\Ê‹ŠKL\™]\›ˆL_Y[˜Ý[ÛˆÜÊK‹Š^ÚYŠ^Û[™NŒ‹™]™\[™N‘™

KÙ\Ý\™N›[XÝ[ÛŽœ‹\ÑXYÙ\”Ý]NˆLKXYÙ\”Ý]N›[™^›[K\ÊJJ^ÚYŠ
]›ÝÈ\œ›ÜŠJÎJJ_Y[ÙH[ÚJK‹‹ŠKOO[[	‰•ÝJKŠ_Y[˜Ý[Ûˆ\ÊJ^Ý˜\ˆYK˜[\›˜]NÜ™]\›ˆOOOZßOO[[	‰OOZßY[˜Ý[ÛˆœÊK
^Þ[Ï]›ÏHLÝ˜\ˆYKœ[™[™ÎÛOO[[Ý›™^]Š›™^[‹›™^‹›™^]
KKœ[™[™Ï]Y[˜Ý[Ûˆ\ÊKŠ^ÚYŠ‰NM
^Ý˜\ˆ]›[™\ÎÜ‰YKœ[™[™Ó[™\ËŸ\‹›[™\Ï[‹
KŠ__]˜\ˆœÏ^Ü™XYÛÛ^šXK\ÙN“Ë\ÙPØ[˜XÚÎ•Ë\ÙPÛÛ^•Ë\ÙQY™™XÝ•Ë\ÙR[\\˜]]™R[™N•Ë\ÙS^[Ý]Y™™XÝ•Ë\ÙR[œÙ\[Û‘Y™™XÝ•Ë\ÙSY[[Î•Ë\ÙT™YXÙ\Ž•Ë\ÙT™YŽ•Ë\ÙTÝ]N•Ë\ÙQXYÕ˜[YN•Ë\ÙQY™\œ™Y˜[YN•Ë\ÙU˜[œÚ][ÛŽ•Ë\ÙTÞ[˜Ñ^\›˜[ÝÜ™N•Ë\ÙRY•Ë\ÙRÜÝ˜[œÚ][Û”Ý]\Î•Ë\ÙQ›Ü›TÝ]N•Ë\ÙPXÝ[Û”Ý]N•Ë\ÙSÜ[Z\ÝXÎ•Ë\ÙSY[[ÐØXÚN•Ë\ÙPØXÚT™Yœ™\Ú•Ë\ÙQY™™XÝ]™[•ßKÏ^Ü™XYÛÛ^šXK\ÙN“Ë\ÙPØ[˜XÚÎ™[˜Ý[ÛŠK
^Ü™]\›ˆ›Ê
K›Y[[Ú^™YÝ]OVÙKOO]›ÚYÛ[K_K\ÙPÛÛ^šXK\ÙQY™™XÝœÜË\ÙR[\\˜]]™R[™N™[˜Ý[ÛŠKŠ^Û[O[[Û[›‹˜ÛÛ˜Ø]
ÙWJK\ÊNMÌË˜š[™
[JKŠ_K\ÙS^[Ý]Y™™XÝ™[˜Ý[ÛŠK
^Ü™]\›ˆ\ÊNMÌK
_K\ÙR[œÙ\[Û‘Y™™XÝ™[˜Ý[ÛŠK
^Ø\Ê‹K
_K\ÙSY[[Î™[˜Ý[ÛŠK
^Ý˜\ˆS›Ê
NÝ]OO]›ÚYÛ[Ý˜\ˆYJ
NÚYŠ›Ê^Ò™JL
NÝž^ÙJ
_Yš[˜[^Ò™JLJ__\™]\›ˆ‹›Y[[Ú^™YÝ]OVÜ‹KŸK\ÙT™YXÙ\Ž™[˜Ý[ÛŠKŠ^Ý˜\ˆS›Ê
NÚYŠˆOO]›ÚY
^Ý˜\ˆO[Š
NÚYŠ›Ê^Ò™JL
NÝž^ÛŠ
_Yš[˜[^Ò™JLJ___Y[ÙHO]Ü™]\›ˆ‹›Y[[Ú^™YÝ]O\‹˜˜\ÙTÝ]OZKO^Ü[™[™Î›[[™\ÎŒ\Ü]Ú›[\Ý™[™\™Y™YXÙ\Ž™K\Ý™[™\™YÝ]Nš_K‹œ]Y]YOYKOYK™\Ü]ÚQ\Ë˜š[™
[ËJKÜ‹›Y[[Ú^™YÝ]KW_K\ÙT™YŽ™[˜Ý[ÛŠJ^Ý˜\ˆS›Ê
NÜ™]\›ˆO^ØÝ\œ™[™_K›Y[[Ú^™YÝ]OY_K\ÙTÝ]N™[˜Ý[ÛŠJ^ÙOV[ÊJNÝ˜\ˆYKœ]Y]YKQË˜š[™
[Ë
NÜ™]\›ˆ™\Ü]Ú[‹ÙK›Y[[Ú^™YÝ]K—_K\ÙQXYÕ˜[YNšË\ÙQY™\œ™Y˜[YN™[˜Ý[ÛŠK
^Ü™]\›ˆÜÊ›Ê
KK
_K\ÙU˜[œÚ][ÛŽ™[˜Ý[ÛŠ
^Ý˜\ˆOV[ÊLJNÜ™]\›ˆORYYK˜š[™
[ËKœ]Y]YKLLJK›Ê
K›Y[[Ú^™YÝ]OYKÈLKW_K\ÙTÞ[˜Ñ^\›˜[ÝÜ™N™[˜Ý[ÛŠKŠ^Ý˜\ˆZËOS›Ê
NÚYŠJ^ÚYŠOO]›ÚY
]›ÝÈ\œ›ÜŠJÊJNÛ[Š
_Y[Ù^ÚYŠ]

KÝOOO[[
]›ÝÈ\œ›ÜŠJÍJJNÛIŒLßÛÊ‹Š_XK›Y[[Ú^™YÝ]O[ŽÝ˜\ˆÏ^Ý˜[YN›‹Ù]Û˜\ÚÝNÜ™]\›ˆKœ]Y]YO[ËÜÊÛË˜š[™
[‹ËJKÙWJK‹™›YÜßLŒœÊKÙ\Ý›ÞN›ÚYKÛË˜š[™
[‹Ë‹
K[
KŸK\ÙRY™[˜Ý[ÛŠ
^Ý˜\ˆOS›Ê
K\ÝKšY[YšY\”™Yš^ÚYŠJ^Ý˜\ˆZÚKSÚNÛJ‰ŸŠOÌ‹VYJŠKLJJKÔÝš[™ÊÌŠJÛ‹XØ
Ý
Ø—Ø
Û‹^ÊÊË‰‰Š
ÏX
Û‹ÔÝš[™ÊÌŠJK
ÏXØY[ÙH]ÛÊÊËXØ
Ý
Ø—Ø
Û‹ÔÝš[™ÊÌŠJØØÜ™]\›ˆK›Y[[Ú^™YÝ]O]K\ÙRÜÝ˜[œÚ][Û”Ý]\Î”ÜË\ÙQ›Ü›TÝ]N›œË\ÙPXÝ[Û”Ý]N›œË\ÙSÜ[Z\ÝXÎ™[˜Ý[ÛŠJ^Ý˜\ˆS›Ê
NÝ›Y[[Ú^™YÝ]O]˜˜\ÙTÝ]OYNÝ˜\ˆ^Ü[™[™Î›[[™\ÎŒ\Ü]Ú›[\Ý™[™\™Y™YXÙ\Ž›[\Ý™[™\™YÝ]N›[NÜ™]\›ˆœ]Y]YO[‹ZÜË˜š[™
[ËLŠK‹™\Ü]Ú]ÙK_K\ÙSY[[ÐØXÚN”›Ë\ÙPØXÚT™Yœ™\Ú™[˜Ý[ÛŠ
^Ü™]\›ˆ›Ê
K›Y[[Ú^™YÝ]OUË˜š[™
[Ê_K\ÙQY™™XÝ]™[™[˜Ý[ÛŠJ^Ý˜\ˆS›Ê
K^Ú[\™_NÜ™]\›ˆ›Y[[Ú^™YÝ]O[‹[˜Ý[ÛŠ
^ÚYŠÝIŒŠ]›ÝÈ\œ›ÜŠJ
JNÜ™]\›ˆ‹š[\˜\J›ÚY\™Ý[Y[Ê___KœÏ^Ü™XYÛÛ^šXK\ÙN“Ë\ÙPØ[˜XÚÎ™ÜË\ÙPÛÛ^šXK\ÙQY™™XÝ˜ÜË\ÙR[\\˜]]™R[™N›\Ë\ÙR[œÙ\[Û‘Y™™XÝ™Ë\ÙS^[Ý]Y™™XÝ™œË\ÙSY[[Î”YK\ÙT™YXÙ\Ž›Ë\ÙT™YŽš\Ë\ÙTÝ]N™[˜Ý[ÛŠ
^Ü™]\›ˆ›Ê›Ê_K\ÙQXYÕ˜[YNšË\ÙQY™\œ™Y˜[YN™[˜Ý[ÛŠK
^Ü™]\›ˆ™YJÊ
KÛË›Y[[Ú^™YÝ]KK
_K\ÙU˜[œÚ][ÛŽ™[˜Ý[ÛŠ
^Ý˜\ˆOP›Ê›ÊVÌKTÊ
K›Y[[Ú^™YÝ]NÜ™]\›–Ý\[ÙˆOOX›ÛÛX[˜ÙN’[ÊJK_K\ÙTÞ[˜Ñ^\›˜[ÝÜ™N•[Ë\ÙRYÜË\ÙRÜÝ˜[œÚ][Û”Ý]\Î”ÜË\ÙQ›Ü›TÝ]NYYK\ÙPXÝ[Û”Ý]NYYK\ÙSÜ[Z\ÝXÎ™[˜Ý[ÛŠK
^Ü™]\›ˆÙYJÊ
KÛËK
_K\ÙSY[[ÐØXÚN”›Ë\ÙPØXÚT™Yœ™\ÚÜË\ÙQY™™XÝ]™[\ßK\Ï^Ü™XYÛÛ^šXK\ÙN“Ë\ÙPØ[˜XÚÎ™ÜË\ÙPÛÛ^šXK\ÙQY™™XÝ˜ÜË\ÙR[\\˜]]™R[™N›\Ë\ÙR[œÙ\[Û‘Y™™XÝ™Ë\ÙS^[Ý]Y™™XÝ™œË\ÙSY[[Î”YK\ÙT™YXÙ\Ž’Ë\ÙT™YŽš\Ë\ÙTÝ]N™[˜Ý[ÛŠ
^Ü™]\›ˆÊ›Ê_K\ÙQXYÕ˜[YNšË\ÙQY™\œ™Y˜[YN™[˜Ý[ÛŠK
^Ý˜\ˆTÊ
NÜ™]\›ˆÛÏOO[[×ÜÊ‹K
N‘™YJ‹ÛË›Y[[Ú^™YÝ]KK
_K\ÙU˜[œÚ][ÛŽ™[˜Ý[ÛŠ
^Ý˜\ˆORÊ›ÊVÌKTÊ
K›Y[[Ú^™YÝ]NÜ™]\›–Ý\[ÙˆOOX›ÛÛX[˜ÙN’[ÊJK_K\ÙTÞ[˜Ñ^\›˜[ÝÜ™N•[Ë\ÙRYÜË\ÙRÜÝ˜[œÚ][Û”Ý]\Î”ÜË\ÙQ›Ü›TÝ]N“™YK\ÙPXÝ[Û”Ý]N“™YK\ÙSÜ[Z\ÝXÎ™[˜Ý[ÛŠK
^Ý˜\ˆTÊ
NÜ™]\›ˆÛÏOO[[Ê‹˜˜\ÙTÝ]OYKÙK‹œ]Y]YK™\Ü]ÚJN“ÙYJ‹ÛËK
_K\ÙSY[[ÐØXÚN”›Ë\ÙPØXÚT™Yœ™\ÚÜË\ÙQY™™XÝ]™[\ßNÙ[˜Ý[ÛˆÊK‹Š^ÝYK›Y[[Ú^™YÝ]K[Š‹
K[O[[Ý•
ßKŠKK›Y[[Ú^™YÝ]O[‹K›[™\ÏOOL	‰ŠK\]T]Y]YK˜˜\ÙTÝ]O[Š_]˜\ˆœÏ^Ù[œ]Y]YTÙ]Ý]N™[˜Ý[ÛŠKŠ^ÙOYK—Ü™XXÝ[\›˜[ÎÝ˜\ˆRJ
KOQØJŠNÚKœ^[ØY]ˆO[[	‰ŠK˜Ø[˜XÚÏ[ŠKRØJKKŠKOO[[	‰ŠÝJKŠKXJKŠJ_K[œ]Y]YT™\XÙTÝ]N™[˜Ý[ÛŠKŠ^ÙOYK—Ü™XXÝ[\›˜[ÎÝ˜\ˆRJ
KOQØJŠNÚKYÏLKKœ^[ØY]ˆO[[	‰ŠK˜Ø[˜XÚÏ[ŠKRØJKKŠKOO[[	‰ŠÝJKŠKXJKŠJ_K[œ]Y]YQ›Ü˜ÙU\]N™[˜Ý[ÛŠK
^ÙOYK—Ü™XXÝ[\›˜[ÎÝ˜\ˆRJ
KQØJŠNÜ‹YÏL‹O[[	‰Š‹˜Ø[˜XÚÏ]
KRØJK‹ŠKOO[[	‰ŠÝJKŠKXJKŠJ__NÙ[˜Ý[ÛˆœÊK‹‹KKÊ^Ü™]\›ˆOYKœÝ]S›ÙK\[ÙˆKœÚÝ[ÛÛ\Û™[\]OOX[˜Ý[Û˜ÙKœÚÝ[ÛÛ\Û™[\]J‹KÊNœ›ÝÝ\I‰œ›ÝÝ\Kš\Ô\™T™XXÝÛÛ\Û™[ÈUŠ‹Š_UŠKJNˆLY[˜Ý[ÛˆœÊK‹Š^ÙO]œÝ]K\[Ùˆ˜ÛÛ\Û™[Ú[™XÙZ]™T›ÜÏOX[˜Ý[Û˜	‰˜ÛÛ\Û™[Ú[™XÙZ]™T›ÜÊ‹ŠK\[Ùˆ•S”ÐQ‘WØÛÛ\Û™[Ú[™XÙZ]™T›ÜÏOX[˜Ý[Û˜	‰•S”ÐQ‘WØÛÛ\Û™[Ú[™XÙZ]™T›ÜÊ‹ŠKœÝ]HOOYI‰”œË™[œ]Y]YT™\XÙTÝ]JœÝ]K[
_Y[˜Ý[ÛˆœÊK
^Ý˜\ˆ]ÚYŠ™Y˜[ˆ
Y›ÜŠ˜\ˆˆ[ˆ^ßK
\ˆOOX™Y˜	‰Š–Ü—O]Ü—JNÚYŠOYK™Y˜][›ÜÊY›ÜŠ˜\ˆH[ˆOO]	‰ŠU
ßKŠJKJ[–ÚWOOO]›ÚY	‰Š–ÚWOYVÚWJNÜ™]\›ˆŸY[˜Ý[ÛˆÊJ^ÙZJJ_Y[˜Ý[Ûˆ\ÊJ^ØÛÛœÛÛK™\œ›ÜŠJ_Y[˜Ý[ÛˆYJJ^ÙZJJ_Y[˜Ý[ÛˆÜÊK
^Ýž^Ý˜\ˆYK›Û•[˜Ø]YÚ\œ›ÜŽÛŠ˜[YKØÛÛ\Û™[ÝXÚÎœÝXÚßJ_XØ]Ú
J^ÜÙ][Y[Ý]
[˜Ý[ÛŠ
^Ý›ÝÈ_J__Y[˜Ý[ÛˆÜÊKŠ^Ýž^Ý˜\ˆYK›ÛØ]YÚ\œ›ÜŽÜŠ‹˜[YKØÛÛ\Û™[ÝXÚÎ›‹œÝXÚË\œ›Ü›Ý[™\žNYÏOOLOÝœÝ]S›ÙN›[J_XØ]Ú
J^ÜÙ][Y[Ý]
[˜Ý[ÛŠ
^Ý›ÝÈ_J__Y[˜Ý[ÛˆÜÊKŠ^Ü™]\›ˆQØJŠK‹YÏLË‹œ^[ØY^Ù[[Y[›[K‹˜Ø[˜XÚÏY[˜Ý[ÛŠ
^ÕÜÊK
_KŸY[˜Ý[Ûˆ\ÊJ^Ü™]\›ˆOQØJJKKYÏLË_Y[˜Ý[Ûˆ™YJK‹Š^Ý˜\ˆO[‹\K™Ù]\š]™YÝ]Qœ›ÛQ\œ›ÜŽÚYŠ\[ÙˆOOX[˜Ý[Û˜
^Ý˜\ˆO\‹˜[YNÙKœ^[ØYY[˜Ý[ÛŠ
^Ü™]\›ˆJJ_KK˜Ø[˜XÚÏY[˜Ý[ÛŠ
^ÑÜÊ‹Š__]˜\ˆÏ[‹œÝ]S›ÙNÛÈOO[[	‰\[ÙˆË˜ÛÛ\Û™[YØ]ÚOX[˜Ý[Û˜	‰ŠK˜Ø[˜XÚÏY[˜Ý[ÛŠ
^ÑÜÊ‹ŠK\[ÙˆHOX[˜Ý[Û˜	‰ŠÝOOO[[ÚÝO[™]ÈÙ]
Ý\×JNšÝK˜Y
\ÊJNÝ˜\ˆO\‹œÝXÚÎÝ\Ë˜ÛÛ\Û™[YØ]Ú
‹˜[YKØÛÛ\Û™[ÝXÚÎ™OOO[[Ø™_J_J_Y[˜Ý[Ûˆ™YJK‹‹J^ÚYŠ‹™›YÜßLÌÍŽ\[ÙˆOXØš™XÝ	‰œ‰‰\[Ùˆ‹[OX[˜Ý[Û˜
^ÚYŠ[‹˜[\›˜]KOO[[	‰J‹KL
K[›Ë˜Ý\œ™[ˆOO[[
^ÜÝÚ]Ú
‹YÊ^ØØ\ÙHÌN˜Ø\ÙHLÎ˜Ø\ÙHNNœ™]\›ˆ›ÏOO[[Ý

N›‹˜[\›˜]OOO[[	‰™ÝOOOL	‰ŠÝOLÊK‹™›YÜÉKLMË‹™›YÜßMMLÍ‹‹›[™\ÏXKOOSØOÛ‹™›YÜßLMŒÎŠ[‹\]T]Y]YKOO[[Û‹\]T]Y]YO[™]ÈÙ]
Ü—JN˜Y
ŠKY
K‹JJKLNØØ\ÙHŒŽœ™]\›ˆ‹™›YÜßMMLÍ‹OOSØOÛ‹™›YÜßLMŒÎŠ[‹\]T]Y]YKOO[[Ê^Ý˜[œÚ][ÛœÎ›[X\šÙ\’[œÝ[˜Ù\Î›[™]žT]Y]YN›™]ÈÙ]
Ü—J_K‹\]T]Y]YO]
NŠ]œ™]žT]Y]YKOO[[Ýœ™]žT]Y]YO[™]ÈÙ]
Ü—JN›‹˜Y
ŠJKY
K‹JJKL_]›ÝÈ\œ›ÜŠJÍK‹YÊJ_\™]\›ˆY
K‹JK

KL_ZYŠJ\™]\›ˆ[›Ë˜Ý\œ™[OO[[ÊˆOOPšI‰ŠQ\œ›ÜŠJŒÊKØØ]\ÙNœŸJKZJšJŠJJKOYK˜Ý\œ™[˜[\›˜]KK™›YÜßMMLÍ‹IKXKK›[™\ßXKXšJ‹ŠKORÜÊKœÝ]S›ÙK‹JK˜JKJKÝHOOM	‰ŠÝOLŠJNŠJ™›YÜÉMLÍŠI‰Š™›YÜßLMŠK™›YÜßMMLÍ‹›[™\ÏXKˆOOPšI‰ŠOQ\œ›ÜŠJŒŠKØØ]\ÙNœŸJKZJšJKŠJJJKLNÝ˜\ˆÏQ\œ›ÜŠJLŒ
KØØ]\ÙNœŸJNÚYŠÏXšJËŠKÝOOO[[ÔÝOVÛ×N”ÝKœ\Ú
ÊKÝHOOM	‰ŠÝOLŠKOO[[
\™]\›ˆLÜXšJ‹ŠK]ÙÞÜÝÚ]Ú
‹YÊ^ØØ\ÙHÎœ™]\›ˆ‹™›YÜßMMLÍ‹OXI‹XK‹›[™\ßYKORÜÊ‹œÝ]S›ÙK‹JK˜J‹JKLNØØ\ÙHNšYŠ[‹\KÏ[‹œÝ]S›ÙKJ‹™›YÜÉŒLŽ
I‰Š\[Ùˆ™Ù]\š]™YÝ]Qœ›ÛQ\œ›ÜOX[˜Ý[Û˜ÈOO[[	‰\[ÙˆË˜ÛÛ\Û™[YØ]ÚOX[˜Ý[Û˜	‰ŠÝOOO[[ZÝKš\ÊÊJJJ\™]\›ˆ‹™›YÜßMMLÍ‹IKXK‹›[™\ßXKO\\ÊJK™YJKK‹ŠK˜J‹JKLNØœ™XZÎØØ\ÙHŒŽšYŠ‹›Y[[Ú^™YÝ]HOO[[
\™]\›ˆ‹™›YÜßMMLÍ‹L_[[‹œ™]\›Ÿ]Ú[JˆOO[[
NÜ™]\›ˆL_]˜\ˆœÏQ\œ›ÜŠJŒJJK\ÏHLNÙ[˜Ý[ÛˆÊK‹Š^Ý˜Ú[YOOO[[Õ˜J[‹ŠN˜JK˜Ú[‹Š_Y[˜Ý[ÛˆœÊK‹‹J^Û[‹œ™[™\ŽÝ˜\ˆO]œ™YŽÚYŠ™Y˜[ˆŠ^Ý˜\ˆÏ^ßNÙ›ÜŠ˜\ˆÈ[ˆŠ\ÈOOX™Y˜	‰ŠÖÜ×O\–Ü×J_Y[ÙHÏ\ŽÜ™]\›ˆ˜J
KQÊK‹ËKJKÏP[Ê
KHOO[[	‰ˆV\ÏÊ›ÊKJKÊKJJNŠI‰œÉ‰“ZJ
K™›YÜßLKÊK‹JK˜Ú[
_Y[˜Ý[Ûˆ\ÊK‹‹J^ÚYŠOOO[[
^Ý˜\ˆO[‹\NÜ™]\›ˆ\[ÙˆOOX[˜Ý[Û˜	‰ˆYšJJI‰˜K™Y˜][›ÜÏOO]›ÚY	‰›‹˜ÛÛ\\™OOO[[ÊYÏLMK\OXK	ÊKK‹JJNŠO[ZJ‹\K[‹›[ÙKJKKœ™Y]œ™Y‹Kœ™]\›]˜Ú[YJ_ZYŠOYK˜Ú[TØÊKJJ^Ý˜\ˆÏXK›Y[[Ú^™Y›ÜÎÚYŠ[‹˜ÛÛ\\™K[OO[[ÕŽ›‹ŠËŠI‰™Kœ™YOO]œ™YŠ\™]\›ˆÊKJ_\™]\›ˆ™›YÜßLKO\JKŠKKœ™Y]œ™Y‹Kœ™]\›]˜Ú[Y_Y[˜Ý[Ûˆ	ÊK‹‹J^ÚYŠHOO[[
^Ý˜\ˆOYK›Y[[Ú^™Y›ÜÎÚYŠŠKŠI‰™Kœ™YOO]œ™YŠZYŠ\ÏHLKœ[™[™Ô›ÜÏ\XKØÊKJJYK™›YÜÉŒLÌLÌ‰‰Š\ÏHL
NÙ[ÙH™]\›ˆ›[™\ÏYK›[™\ËÊKJ_\™]\›ˆØÊK‹‹J_Y[˜Ý[ÛˆXÊK‹Š^Ý˜\ˆO\‹˜Ú[™[‹OYOOO[[Û[™K›Y[[Ú^™YÝ]NÚYŠOOO[[	‰œÝ]S›ÙOOO[[	‰ŠœÝ]S›ÙO^×Ýš\ÚXš[]NŒKÜ[™[™ÓX\šÙ\œÎ›[Ü™]žPØXÚN›[Ý˜[œÚ][ÛœÎ›[JK‹›[ÙOOOXY[˜
^ÚYŠ™›YÜÉŒLŽ
^ÚYŠOXOOO[[ÛŽ˜K˜˜\ÙS[™\ß‹HOO[[
^Ù›ÜŠ]˜Ú[YK˜Ú[OLÜˆOO[[ÊZOZ_‹›[™\ß‹˜Ú[[™\Ë\‹œÚX›[™ÎÜZIŸ˜_Y[ÙHL˜Ú[[[Ü™]\›ˆ˜ÊKK‹Š_ZYŠ‰LÍŽÌLLŠ]›Y[[Ú^™YÝ]O^Ø˜\ÙS[™\ÎŒØXÚTÛÛ›[KHOO[[	‰ØJOOO[[Û[˜K˜ØXÚTÛÛ
KOOO[[Ù[Ê
N‘YYJJKÛÊ
NÙ[ÙH™]\›ˆ]›[™\ÏMLÍŽÌLL‹˜ÊKOOO[[ÛŽ˜K˜˜\ÙS[™\ß‹‹Š_Y[ÙHOOO[[ÊHOO[[	‰ØJ[
K[Ê
KÛÊ
JNŠØJK˜ØXÚTÛÛ
KYYJJKÛÊ
K›Y[[Ú^™YÝ]O[[
NÜ™]\›ˆÊKKŠK˜Ú[Y[˜Ý[ÛˆÊK
^Ü™]\›ˆHOO[[	‰™KYÏOOLŒŸœÝ]S›ÙHOO[[
œÝ]S›ÙO^×Ýš\ÚXš[]NŒKÜ[™[™ÓX\šÙ\œÎ›[Ü™]žPØXÚN›[Ý˜[œÚ][ÛœÎ›[JKœÚX›[™ßY[˜Ý[Ûˆ˜ÊK‹‹J^Ý˜\ˆOTØJ
NÜ™]\›ˆOXOOO[[Û[žÜ\™[›K—ØÝ\œ™[˜[YKÛÛ˜_K›Y[[Ú^™YÝ]O^Ø˜\ÙS[™\Î›‹ØXÚTÛÛ˜_KHOO[[	‰ØJ[
K[Ê
KÛÊ
KHOO[[	‰JK‹L
K˜Ú[[™\ÏZK[Y[˜Ý[Ûˆ˜ÊK
^Ü™]\›ˆ\ÊÛ[ÙN›[ÙKÚ[™[Ž˜Ú[™[ŸKK›[ÙJKœ™YYKœ™Y‹K˜Ú[]œ™]\›YKY[˜Ý[ÛˆXÊKŠ^Ü™]\›ˆ˜JK˜Ú[[ŠKO\˜Êœ[™[™Ô›ÜÊKK™›YÜßL‹ÛÊ
K›Y[[Ú^™YÝ]O[[_Y[˜Ý[ÛˆXÊKŠ^Ý˜\ˆ]œ[™[™Ô›ÜËOJ™›YÜÉŒLŽ
HOLÚYŠ™›YÜÉKLLŽKOOO[[
^ÚYŠJ^ÚYŠ‹›[ÙOOOXY[˜
\™]\›ˆO\˜ÊŠK›[™\ÏMLÍŽÌLL‹K›Y[[Ú^™YÝ]O^Ø˜\ÙS[™\ÎŒØXÚTÛÛ›[KÊ[JNÚYŠ[Ê
K
ORZJOÊOTŠKšJKOYHOO[[	‰™K™]OOOX	˜ÙN›[HOO[[	‰Š›Y[[Ú^™YÝ]O^ÙZY˜]Y™K™YPÛÛ^‘OOO[[Û[žÚY“ÚKÝ™\™›ÝÎšÚ_K™]žS[™NLÍŽÌLL‹Y˜][Û‘\œ›ÜœÎ›[KWÚJJK‹œ™]\›]˜Ú[[‹šO]ZO[[
JN™O[[OOO[[
]›ÝÈšJ
NÜ™]\›ˆ›[™\ÏMLÍŽÌLL‹[\™]\›ˆ˜ÊŠ_]˜\ˆÏYK›Y[[Ú^™YÝ]NÚYŠÈOO[[
^Ý˜\ˆÏ[Ë™ZY˜]YÚYŠ[Ê
KJZYŠ™›YÜÉŒMŠ]™›YÜÉKLMËZXÊKŠNÙ[ÙHYŠ›Y[[Ú^™YÝ]HOO[[
]˜Ú[YK˜Ú[™›YÜßLLŽ[[Ù[ÙH›ÝÈ\œ›ÜŠJMN
JNÙ[ÙHYŠ\ßJK‹LJKOJ‰™K˜Ú[[™\ÊHOOL\ßJ^ÚYŠXK˜Ý\œ™[OO[[
^ÚYŠ\ÝKˆOO[[	‰ŠÏ\
‹ŠKÈOOL	‰œÈOO[Ëœ™]žS[™JJ]›ÝÈËœ™]žS[™O\ËÚJKÊKÝJ‹KÊKœÎÝ

_]ZXÊKŠ_Y[ÙHO[Ë™YPÛÛ^ZOSŠË›™^ÚX›[™ÊKšO]OHLšO[[šOHLKHOO[[	‰”JJK\˜ÊŠK™›YÜßLLÍŒŒNÜ™]\›ˆ\™]\›ˆO\JK˜Ú[Û[ÙNœ‹›[ÙKÚ[™[Žœ‹˜Ú[™[ŸJKKœ™Y]œ™Y‹˜Ú[YKKœ™]\›]_Y[˜Ý[ÛˆØÊK
^Ý˜\ˆ]œ™YŽÚYŠOO[[
YHOO[[	‰™Kœ™YˆOO[[	‰Š™›YÜßMNMMŠNÙ[Ù^ÚYŠ\[ÙˆˆOX[˜Ý[Û˜	‰\[ÙˆˆOXØš™XÝ
]›ÝÈ\œ›ÜŠJŽ
JNÊOOO[[Kœ™YˆOO[ŠI‰Š™›YÜßMNMMŠ__Y[˜Ý[ÛˆØÊK‹‹J^Ü™]\›ˆ˜J
KQÊK‹‹›ÚYJKP[Ê
KHOO[[	‰ˆV\ÏÊ›ÊKJKÊKJJNŠI‰œ‰‰“ZJ
K™›YÜßLKÊK‹JK˜Ú[
_Y[˜Ý[Ûˆ™YJK‹‹KJ^Ü™]\›ˆ˜J
K\]T]Y]YO[[ZÛÊ‹‹JKÛÊJKP[Ê
KHOO[[	‰ˆV\ÏÊ›ÊKJKÊKJJNŠI‰œ‰‰“ZJ
K™›YÜßLKÊK‹JK˜Ú[
_Y[˜Ý[Ûˆ™YJK‹‹J^ÚYŠ˜J
KœÝ]S›ÙOOO[[
^Ý˜\ˆO]ZKÏ[‹˜ÛÛ^\NÝ\[ÙˆÏOXØš™XÝ	‰›É‰ŠOZXJÊJKO[™]ÈŠ‹JK›Y[[Ú^™YÝ]OXKœÝ]HOO[[	‰˜KœÝ]HOO]›ÚYØKœÝ]N›[K\]\TœËœÝ]S›ÙOXKK—Ü™XXÝ[\›˜[Ï]O]œÝ]S›ÙKKœ›ÜÏ\‹KœÝ]O]›Y[[Ú^™YÝ]KKœ™YœÏ^ßKXJ
KÏ[‹˜ÛÛ^\KK˜ÛÛ^]\[ÙˆÏOXØš™XÝ	‰›ÏÚXJÊNZKKœÝ]O]›Y[[Ú^™YÝ]KÏ[‹™Ù]\š]™YÝ]Qœ›ÛT›ÜË\[ÙˆÏOX[˜Ý[Û˜	‰ŠÊ‹ËŠKKœÝ]O]›Y[[Ú^™YÝ]JK\[Ùˆ‹™Ù]\š]™YÝ]Qœ›ÛT›ÜÏOX[˜Ý[Û˜\[ÙˆK™Ù]Û˜\ÚÝ™Y›Ü™U\]OOX[˜Ý[Û˜\[ÙˆK•S”ÐQ‘WØÛÛ\Û™[Ú[[Ý[OX[˜Ý[Û˜	‰\[ÙˆK˜ÛÛ\Û™[Ú[[Ý[OX[˜Ý[Û˜
ÏXKœÝ]K\[ÙˆK˜ÛÛ\Û™[Ú[[Ý[OX[˜Ý[Û˜	‰˜K˜ÛÛ\Û™[Ú[[Ý[

K\[ÙˆK•S”ÐQ‘WØÛÛ\Û™[Ú[[Ý[OX[˜Ý[Û˜	‰˜K•S”ÐQ‘WØÛÛ\Û™[Ú[[Ý[

KÈOOXKœÝ]I‰”œË™[œ]Y]YT™\XÙTÝ]JKKœÝ]K[
K˜J‹KJKJ
KKœÝ]O]›Y[[Ú^™YÝ]JK\[ÙˆK˜ÛÛ\Û™[Y[Ý[OX[˜Ý[Û˜	‰Š™›YÜßMNMÌ
KHLY[ÙHYŠOOO[[
^ØO]œÝ]S›ÙNÝ˜\ˆÏ]›Y[[Ú^™Y›ÜËUœÊ‹ÊNØKœ›ÜÏ[Ý˜\ˆOXK˜ÛÛ^[‹˜ÛÛ^\NÛÏ]ZK\[ÙˆOXØš™XÝ	‰™	‰ŠÏZXJ
JNÝ˜\ˆ[‹™Ù]\š]™YÝ]Qœ›ÛT›ÜÎÙ]\[ÙˆOX[˜Ý[Û˜\[ÙˆK™Ù]Û˜\ÚÝ™Y›Ü™U\]OOX[˜Ý[Û˜Ï]œ[™[™Ô›ÜÈOO\Ë\[ÙˆK•S”ÐQ‘WØÛÛ\Û™[Ú[™XÙZ]™T›ÜÈOX[˜Ý[Û˜	‰\[ÙˆK˜ÛÛ\Û™[Ú[™XÙZ]™T›ÜÈOX[˜Ý[Û˜
ßHOO[ÊI‰œÊK‹ÊKOHLNÝ˜\ˆ]›Y[[Ú^™YÝ]NØKœÝ]O\˜J‹KJKJ
KO]›Y[[Ú^™YÝ]KßOO]_OÊ\[ÙˆOX[˜Ý[Û˜	‰ŠÊ‹‹ŠKO]›Y[[Ú^™YÝ]JK
R_œÊ‹‹KÊJOÊ\[ÙˆK•S”ÐQ‘WØÛÛ\Û™[Ú[[Ý[OX[˜Ý[Û˜	‰\[ÙˆK˜ÛÛ\Û™[Ú[[Ý[OX[˜Ý[Û˜
\[ÙˆK˜ÛÛ\Û™[Ú[[Ý[OX[˜Ý[Û˜	‰˜K˜ÛÛ\Û™[Ú[[Ý[

K\[ÙˆK•S”ÐQ‘WØÛÛ\Û™[Ú[[Ý[OX[˜Ý[Û˜	‰˜K•S”ÐQ‘WØÛÛ\Û™[Ú[[Ý[

JK\[ÙˆK˜ÛÛ\Û™[Y[Ý[OX[˜Ý[Û˜	‰Š™›YÜßMNMÌ
JNŠ\[ÙˆK˜ÛÛ\Û™[Y[Ý[OX[˜Ý[Û˜	‰Š™›YÜßMNMÌ
K›Y[[Ú^™Y›ÜÏ\‹›Y[[Ú^™YÝ]O]JKKœ›ÜÏ\‹KœÝ]O]KK˜ÛÛ^[Ë[
NŠ\[ÙˆK˜ÛÛ\Û™[Y[Ý[OX[˜Ý[Û˜	‰Š™›YÜßMNMÌ
KHLJ_Y[Ù^ØO]œÝ]S›ÙKØJK
KÏ]›Y[[Ú^™Y›ÜËUœÊ‹ÊKKœ›ÜÏY]œ[™[™Ô›ÜËXK˜ÛÛ^O[‹˜ÛÛ^\K]ZK\[ÙˆOOXØš™XÝ	‰I‰ŠZXJJJKÏ[‹™Ù]\š]™YÝ]Qœ›ÛT›ÜË
O]\[ÙˆÏOX[˜Ý[Û˜\[ÙˆK™Ù]Û˜\ÚÝ™Y›Ü™U\]OOX[˜Ý[Û˜
_\[ÙˆK•S”ÐQ‘WØÛÛ\Û™[Ú[™XÙZ]™T›ÜÈOX[˜Ý[Û˜	‰\[ÙˆK˜ÛÛ\Û™[Ú[™XÙZ]™T›ÜÈOX[˜Ý[Û˜
ÈOOYŸOO[
I‰œÊK‹
KOHLK]›Y[[Ú^™YÝ]KKœÝ]O\˜J‹KJKJ
NÝ˜\ˆO]›Y[[Ú^™YÝ]NÛÈOOYŸOO[__HOO[[	‰™K™\[™[˜ÚY\ÈOO[[	‰›˜JK™\[™[˜ÚY\ÊOÊ\[ÙˆÏOX[˜Ý[Û˜	‰ŠÊ‹ËŠKO]›Y[[Ú^™YÝ]JK
R_œÊ‹‹K
_HOO[[	‰™K™\[™[˜ÚY\ÈOO[[	‰›˜JK™\[™[˜ÚY\ÊJOÊ_\[ÙˆK•S”ÐQ‘WØÛÛ\Û™[Ú[\]HOX[˜Ý[Û˜	‰\[ÙˆK˜ÛÛ\Û™[Ú[\]HOX[˜Ý[Û˜
\[ÙˆK˜ÛÛ\Û™[Ú[\]OOX[˜Ý[Û˜	‰˜K˜ÛÛ\Û™[Ú[\]J‹K
K\[ÙˆK•S”ÐQ‘WØÛÛ\Û™[Ú[\]OOX[˜Ý[Û˜	‰˜K•S”ÐQ‘WØÛÛ\Û™[Ú[\]J‹K
JK\[ÙˆK˜ÛÛ\Û™[Y\]OOX[˜Ý[Û˜	‰Š™›YÜßM
K\[ÙˆK™Ù]Û˜\ÚÝ™Y›Ü™U\]OOX[˜Ý[Û˜	‰Š™›YÜßLL
JNŠ\[ÙˆK˜ÛÛ\Û™[Y\]HOX[˜Ý[Û˜ÏOOYK›Y[[Ú^™Y›ÜÉ‰œOOYK›Y[[Ú^™YÝ]_
™›YÜßM
K\[ÙˆK™Ù]Û˜\ÚÝ™Y›Ü™U\]HOX[˜Ý[Û˜ÏOOYK›Y[[Ú^™Y›ÜÉ‰œOOYK›Y[[Ú^™YÝ]_
™›YÜßLL
K›Y[[Ú^™Y›ÜÏ\‹›Y[[Ú^™YÝ]O[JKKœ›ÜÏ\‹KœÝ]O[KK˜ÛÛ^[Y
NŠ\[ÙˆK˜ÛÛ\Û™[Y\]HOX[˜Ý[Û˜ÏOOYK›Y[[Ú^™Y›ÜÉ‰œOOYK›Y[[Ú^™YÝ]_
™›YÜßM
K\[ÙˆK™Ù]Û˜\ÚÝ™Y›Ü™U\]HOX[˜Ý[Û˜ÏOOYK›Y[[Ú^™Y›ÜÉ‰œOOYK›Y[[Ú^™YÝ]_
™›YÜßLL
KHLJ_\™]\›ˆO\‹ØÊK
KJ™›YÜÉŒLŽ
HOL_ÊO]œÝ]S›ÙK\‰‰\[Ùˆ‹™Ù]\š]™YÝ]Qœ›ÛQ\œ›ÜˆOX[˜Ý[Û˜Û[˜Kœ™[™\Š
K™›YÜßLKHOO[[	‰œÊ˜Ú[P˜JK˜Ú[[JK˜Ú[P˜J[‹JJN–ÊK‹JK›Y[[Ú^™YÝ]OXKœÝ]KO]˜Ú[
N™O^ÊKJK_Y[˜Ý[ÛˆYJK‹Š^Ü™]\›ˆÚJ
K™›YÜßLM‹ÊK‹ŠK˜Ú[]˜\ˆØÏ^ÙZY˜]Y›[™YPÛÛ^›[™]žS[™NŒY˜][Û‘\œ›ÜœÎ›[NÙ[˜Ý[ÛˆÊJ^Ü™]\›žØ˜\ÙS[™\Î™KØXÚTÛÛØJ
__Y[˜Ý[ÛˆXÊKŠ^Ü™]\›ˆOYOOO[[Ì™K˜Ú[[™\ÉŸ›‹	‰Š_XJK_Y[˜Ý[ÛˆÊKŠ^Ý˜\ˆ]œ[™[™Ô›ÜËOHLKOJ™›YÜÉŒLŽ
HOLÎÚYŠ
ÏXJ_
ÏYHOO[[	‰™K›Y[[Ú^™YÝ]OOO[[ÈLNŠË˜Ý\œ™[	ŒŠHOL
KÉ‰ŠOHL™›YÜÉKLLŽJKÏJ™›YÜÉŒÌŠHOL™›YÜÉKLÌËOOO[[
^ÚYŠJ^ÚYŠOÚ[Ê
NœÛÊ
K
ORZJOÊOTŠKšJKOYHOO[[	‰™K™]HOOX	˜ÙN›[HOO[[	‰Š›Y[[Ú^™YÝ]O^ÙZY˜]Y™K™YPÛÛ^‘OOO[[Û[žÚY“ÚKÝ™\™›ÝÎšÚ_K™]žS[™NLÍŽÌLL‹Y˜][Û‘\œ›ÜœÎ›[KWÚJJK‹œ™]\›]˜Ú[[‹šO]ZO[[
JN™O[[OOO[[
]›ÝÈšJ
NÜ™]\›ˆYŠJOÝ›[™\ÏLÌŽ›[™\ÏMLÍŽÌLL‹[\™]\›ˆO\‹˜Ú[™[‹\‹™˜[˜XÚËOÊÛÊ
KO]›[ÙKO\ÊÛ[ÙN˜Y[˜Ú[™[Ž˜_KJKZJ‹K‹[
KKœ™]\›]‹œ™]\›]KœÚX›[™Ï\‹˜Ú[XK]˜Ú[‹›Y[[Ú^™YÝ]O[ÊŠK‹˜Ú[[™\Ï]XÊKËŠK›Y[[Ú^™YÝ]OXØËÊ[ŠJNŠ[Ê
K˜ÊJJ_]˜\ˆÏYK›Y[[Ú^™YÝ]NÚYŠÈOO[[
^Ý˜\ˆ\Ë™ZY˜]YÚYŠOO[[
\™]\›ˆÊKKË‹ËŠ_\™]\›ˆOÊÛÊ
KO\‹™˜[˜XÚËO]›[ÙKÏYK˜Ú[\ËœÚX›[™Ë\JËÛ[ÙN˜Y[˜Ú[™[Žœ‹˜Ú[™[ŸJK‹œÝX™YQ›YÜÏ\ËœÝX™YQ›YÜÉŒLŒŽLLMÍ‹OO[[ÊOZJKK‹[
KK™›YÜßLŠNšO\JJKKœ™]\›]‹œ™]\›]‹œÚX›[™ÏZK˜Ú[\‹Ê[ŠK]˜Ú[OYK˜Ú[›Y[[Ú^™YÝ]KOOO[[ÚO[ÊŠNŠOZK˜ØXÚTÛÛOOO[[ØO]ØJ
NŠÏ[K—ØÝ\œ™[˜[YKOXKœ\™[OO\ÏØNžÜ\™[œËÛÛœßJKO^Ø˜\ÙS[™\ÎšK˜˜\ÙS[™\ß‹ØXÚTÛÛ˜_JK‹›Y[[Ú^™YÝ]OZK‹˜Ú[[™\Ï]XÊKËŠK›Y[[Ú^™YÝ]OXØËÊK˜Ú[ŠJNŠ[Ê
KYK˜Ú[O[‹œÚX›[™Ë\J‹Û[ÙN˜š\ÚX›XÚ[™[Žœ‹˜Ú[™[ŸJK‹œ™]\›]‹œÚX›[™Ï[[HOO[[	‰ŠÏ]™[][ÛœËÏOO[[Ê™[][ÛœÏVÙWK™›YÜßLMŠN›Ëœ\Ú
JJK˜Ú[[‹›Y[[Ú^™YÝ]O[[Š_Y[˜Ý[Ûˆ˜ÊK
^Ü™]\›ˆ\ÊÛ[ÙN˜š\ÚX›XÚ[™[ŽKK›[ÙJKœ™]\›YKK˜Ú[]Y[˜Ý[ÛˆÊK
^Ü™]\›ˆOYJŒ‹K[
KK›[™\ÏL_Y[˜Ý[ÛˆXÊKŠ^Ü™]\›ˆ˜JK˜Ú[[ŠKOY˜Êœ[™[™Ô›ÜË˜Ú[™[ŠKK™›YÜßL‹›Y[[Ú^™YÝ]O[[_Y[˜Ý[ÛˆÊK‹‹KËË
^ÚYŠŠ\™]\›ˆ™›YÜÉŒMÊ[Ê
K™›YÜÉKLMËXÊK
JN›Y[[Ú^™YÝ]OOO[[ÊÛÊ
KÏXK™˜[˜XÚËÏ]›[ÙKO\ÊÛ[ÙN˜š\ÚX›XÚ[™[Ž˜K˜Ú[™[ŸKÊKÏZJËË[
KË™›YÜßL‹Kœ™]\›]Ëœ™]\›]KœÚX›[™Ï[Ë˜Ú[XK˜JK˜Ú[[
KO]˜Ú[K›Y[[Ú^™YÝ]O[Ê
KK˜Ú[[™\Ï]XÊK‹
K›Y[[Ú^™YÝ]OXØËÊ[JJNŠÛÊ
K˜Ú[YK˜Ú[™›YÜßLLŽ[
NÚYŠ[Ê
KYŠÊJ^ÚYŠ[Ë›™^ÚX›[™É‰›Ë›™^ÚX›[™Ë™]\Ù]Š]˜\ˆO\‹™ÜÝÜ™]\›ˆ]KˆOOX	‰ŠOQ\œ›ÜŠJNJJKKœÝXÚÏXK™YÙ\Ý\‹ZJÝ˜[YN˜KÛÝ\˜ÙN›[ÝXÚÎ›[JJKXÊK
_ZYŠ\ßJKLJKJ	™K˜Ú[[™\ÊHOOL\ßŠ^ÚYŠXK˜Ý\œ™[OO[[
\™]\›ˆXÊK
NÚYŠ\ÝKˆOO[[	‰ŠO\
‹
KHOOL	‰˜HOO\Ëœ™]žS[™JJ]›ÝÈËœ™]žS[™OXKÚJKJKÝJ‹KJKœÎÜ™]\›ˆ™ŠÊ_

KXÊK
_\™]\›ˆ™ŠÊOÊ™›YÜßLNL‹˜Ú[YK˜Ú[[
NŠO\Ë™YPÛÛ^ZOSŠË›™^ÚX›[™ÊKšO]OHLšO[[šOHLKHOO[[	‰”JJKY˜ÊK˜Ú[™[ŠK™›YÜßLLÍŒŒN
_Y[˜Ý[ÛˆØÊKŠ^ÙK›[™\ß]Ý˜\ˆYK˜[\›˜]NÜˆOO[[	‰Š‹›[™\ß]
K	JKœ™]\›‹Š_Y[˜Ý[ÛˆØÊJ^Ù›ÜŠ˜\ˆ[[ÙHOO[[Ê^Ý˜\ˆYK˜[\›˜]NÛˆOO[[	‰œÊŠOOO[[	‰ŠYJKOYKœÚX›[™ß\™]\›ˆY[˜Ý[Ûˆ˜ÊK‹‹KJ^Ý˜\ˆÏYK›Y[[Ú^™YÝ]NÛÏOO[[ÙK›Y[[Ú^™YÝ]O^Ú\Ð˜XÚÝØ\™Î™[™\š[™Î›[™[™\š[™ÔÝ\[YNŒ\Ýœ‹Z[›‹Z[[ÙNšK™YQ›ÜšÐÛÝ[˜_NŠËš\Ð˜XÚÝØ\™Ï]Ëœ™[™\š[™Ï[[Ëœ™[™\š[™ÔÝ\[YOLË›\Ý\‹ËZ[[‹ËZ[[ÙOZKË™YQ›ÜšÐÛÝ[XJ_Y[˜Ý[ÛˆXÊJ^Ý˜\ˆYK˜Ú[Ù›ÜŠK˜Ú[[[ÝOO[[Ê^Ý˜\ˆ]œÚX›[™ÎÝœÚX›[™ÏYK˜Ú[K˜Ú[][Ÿ_Y[˜Ý[Ûˆ˜ÊKŠ^Ý˜\ˆ]œ[™[™Ô›ÜËO\‹œ™]™X[Ü™\‹O\‹Z[Ü\‹˜Ú[™[ŽÝ˜\ˆÏ[Ë˜Ý\œ™[ÚYŠ™›YÜÉŒLŽ
\™]\›ˆ[ÊÊK[Ý˜\ˆÏJÉŒŠHOLÚYŠÏÊÏ[ÉŒ_‹™›YÜßLLŽ
N›ÉLK[ÊÊKOOOX˜XÚÝØ\™Ø	‰™HOO[[ÊXÊJKÊK‹ŠKXÊJJN–ÊK‹ŠKSOÝÚNŒ\É‰™HOO[[	‰™K™›YÜÉŒLŽ
XN™›ÜŠO]˜Ú[ÙHOO[[Ê^ÚYŠKYÏOOLLÊYK›Y[[Ú^™YÝ]HOO[[	‰™ØÊK‹
NÙ[ÙHYŠKYÏOOLNJYØÊK‹
NÙ[ÙHYŠK˜Ú[OO[[
^ÙK˜Ú[œ™]\›YKOYK˜Ú[ØÛÛ[Y_ZYŠOOO]
Xœ™XZÈNÙ›ÜŠÙKœÚX›[™ÏOO[[Ê^ÚYŠKœ™]\›OO[[Kœ™]\›OO]
Xœ™XZÈNÙOYKœ™]\›ŸYKœÚX›[™Ëœ™]\›YKœ™]\›‹OYKœÚX›[™ß\ÝÚ]Ú
J^ØØ\ÙX˜XÚÝØ\™Ø›WØÊ˜Ú[
KOO[[ÊO]˜Ú[˜Ú[[[
NŠO[‹œÚX›[™Ë‹œÚX›[™Ï[[XÊ
JK˜ÊLK[KŠNØœ™XZÎØØ\ÙX[œÝX›WÛYØXÞKX˜XÚÝØ\™Ø™›ÜŠ[[O]˜Ú[˜Ú[[[ÚHOO[[Ê^ÚYŠOZK˜[\›˜]KHOO[[	‰œÊJOOO[[
^Ý˜Ú[ZNØœ™XZßYOZKœÚX›[™ËKœÚX›[™Ï[‹ZKOY_]˜ÊL‹[KŠNØœ™XZÎØØ\ÙXÙÙ]\˜˜ÊLK[[›ÚYŠNØœ™XZÎØØ\ÙX[™\[™[›Y[[Ú^™YÝ]O[[Øœ™XZÎÙY˜][›WØÊ˜Ú[
KOO[[ÊO]˜Ú[˜Ú[[[
NŠO[‹œÚX›[™Ë‹œÚX›[™Ï[[
K˜ÊLKK‹KŠ_\™]\›ˆ˜Ú[Y[˜Ý[ÛˆYYJKŠ^Ý˜\ˆ]œ[™[™Ô›ÜÎÜ™]\›ˆšJ\K‹˜[YJKÊK‹˜Ú[™[‹ŠK˜Ú[Y[˜Ý[ÛˆÊKŠ^ÚYŠHOO[[	‰Š™\[™[˜ÚY\ÏYK™\[™[˜ÚY\ÊKÝ_]›[™\Ë
‰˜Ú[[™\ÊOOOL
ZYŠHOO[[
^ÚYŠJK‹LJK
‰˜Ú[[™\ÊOOOL
\™]\›ˆ[Y[ÙH™]\›ˆ[ÚYŠHOO[[	‰˜Ú[OOYK˜Ú[
]›ÝÈ\œ›ÜŠJMLÊJNÚYŠ˜Ú[OO[[
^Ù›ÜŠO]˜Ú[\JKKœ[™[™Ô›ÜÊK˜Ú[[‹‹œ™]\›]ÙKœÚX›[™ÈOO[[ÊYOYKœÚX›[™Ë[‹œÚX›[™Ï\JKKœ[™[™Ô›ÜÊK‹œ™]\›]Û‹œÚX›[™Ï[[\™]\›ˆ˜Ú[Y[˜Ý[ÛˆØÊK
^Ü™]\›ŠK›[™\É
OOOLÊOYK™\[™[˜ÚY\ËHJHOO[[	‰›˜JJJJNˆLY[˜Ý[ÛˆØÊKŠ^ÜÝÚ]Ú
YÊ^ØØ\ÙHÎžJœÝ]S›ÙK˜ÛÛZ[™\’[™›ÊKšJKK›Y[[Ú^™YÝ]K˜ØXÚJKÚJ
NØœ™XZÎØØ\ÙHÎ˜Ø\ÙHNÙJ
NØœ™XZÎØØ\ÙHžJœÝ]S›ÙK˜ÛÛZ[™\’[™›ÊNØœ™XZÎØØ\ÙHL–šJ\K›Y[[Ú^™Y›ÜË˜[YJNØœ™XZÎØØ\ÙHÌNšYŠ›Y[[Ú^™YÝ]HOO[[
\™]\›ˆ™›YÜßLLŽ[Ê
K[Øœ™XZÎØØ\ÙHLÎ˜\ˆ]›Y[[Ú^™YÝ]NÚYŠˆOO[[
^ÚYŠ‹™ZY˜]YOO[[
\™]\›ˆ[Ê
K™›YÜßLLŽ[Ü]JK‹LJNÝ˜\ˆO]˜Ú[˜Ú[[™\ÎÜ™]\›ˆŸ
‰šJHOOLÙÊKŠNŠ[Ê
KO^ÊKŠKOOO[[Û[™KœÚX›[™Ê_Z[Ê
NØœ™XZÎØØ\ÙHNNšYŠ™›YÜÉŒLŽ
\™]\›ˆ˜ÊKŠNÚYŠOJK™›YÜÉŒLŽ
HOLJ‰˜Ú[[™\ÊHOOLŸJJK‹LJK
‰˜Ú[[™\ÊHOOL
KJ^ÚYŠŠ\™]\›ˆ˜ÊKŠNÝ™›YÜßLLŽZYŠO]›Y[[Ú^™YÝ]KHOO[[	‰ŠKœ™[™\š[™Ï[[KZ[[[K›\ÝY™™XÝ[[
K[ÊË˜Ý\œ™[
KŠXœ™XZÎÜ™]\›ˆ[ØØ\ÙHŒŽœ™]\›ˆ›[™\ÏLXÊK‹œ[™[™Ô›ÜÊNØØ\ÙH–šJKK›Y[[Ú^™YÝ]K˜ØXÚJ_\™]\›ˆÊKŠ_Y[˜Ý[ÛˆØÊKŠ^ÚYŠHOO[[
ZYŠK›Y[[Ú^™Y›ÜÈOO]œ[™[™Ô›ÜÊV\ÏHLÙ[Ù^ÚYŠTØÊKŠI‰ˆJ™›YÜÉŒLŽ
J\™]\›ˆ\ÏHLKØÊKŠNÖ\ÏHHJK™›YÜÉŒLÌLÌŠ_Y[ÙH\ÏHLKI‰™›YÜÉŒLMÍ‰‰ššJÚKš[™^
NÜÝÚ]Ú
›[™\ÏLYÊ^ØØ\ÙHMŽ˜NžÝ˜\ˆ]œ[™[™Ô›ÜÎÚYŠOZ˜J™[[Y[\JK\OYK\[ÙˆOOX[˜Ý[Û˜
YšJJOÊUœÊKŠKYÏLKU™YJ[K‹ŠJNŠYÏL\ØÊ[K‹ŠJNÙ[Ù^ÚYŠHO[[
^Ý˜\ˆOYK‰	\[ÙŽÚYŠOOOT
^ÝYÏLLKVœÊ[K‹ŠNØœ™XZÈ_Y[ÙHYŠOOOS
^ÝYÏLMT\Ê[K‹ŠNØœ™XZÈ_Y[ÙHYŠOOOSŠ^ÝYÏLL\OYKUYYJ[ŠNØœ™XZÈ__]›ÝÈ\ÙJJ_K\œ›ÜŠJÌ‹
J__\™]\›ˆØØ\ÙHœ™]\›ˆØÊK\Kœ[™[™Ô›ÜËŠNØØ\ÙHNœ™]\›ˆ]\KOUœÊ‹œ[™[™Ô›ÜÊK™YJK‹KŠNØØ\ÙHÎ˜NžÚYŠJœÝ]S›ÙK˜ÛÛZ[™\’[™›ÊKOOO[[
]›ÝÈ\œ›ÜŠJÎÊJNÜ]œ[™[™Ô›ÜÎÝ˜\ˆÏ]›Y[[Ú^™YÝ]NØO[Ë™[[Y[ØJK
K˜J‹[ŠNÝ˜\ˆÏ]›Y[[Ú^™YÝ]NÚYŠ\Ë˜ØXÚKšJKŠKˆOO[Ë˜ØXÚI‰™XJÛWK‹L
KJ
K\Ë™[[Y[Ëš\ÑZY˜]Y
ZYŠÏ^Ù[[Y[œ‹\ÑZY˜]YˆLKØXÚNœË˜ØXÚ_K\]T]Y]YK˜˜\ÙTÝ]O[Ë›Y[[Ú^™YÝ]O[Ë™›YÜÉŒMŠ^ÝRYJK‹ŠNØœ™XZÈ_Y[ÙHYŠˆOOXJ^ØOXšJ\œ›ÜŠJ
JK
KZJJKRYJK‹ŠNØœ™XZÈ_Y[Ù^ÜÝÚ]Ú
O]œÝ]S›ÙK˜ÛÛZ[™\’[™›ËK››ÙU\J^ØØ\ÙHN™OYK˜›ÙNØœ™XZÎÙY˜][™OYK››ÙS˜[YOOOXSÙK›ÝÛ™\‘ØÝ[Y[˜›ÙN™_Y›ÜŠZOSŠK™š\œÝÚ[
KšO]OHLšO[[šOHLU˜J[‹ŠK˜Ú[[ŽÛŽÊ[‹™›YÜÏ[‹™›YÜÉ‹LßLÍŒŒN[‹œÚX›[™ßY[Ù^ÚYŠÚJ
KOOXJ^Ý^ÊKŠNØœ™XZÈ_VÊK‹Š_]]˜Ú[\™]\›ˆØØ\ÙHŽœ™]\›ˆØÊK
KOOO[[ÊY\
\K[œ[™[™Ô›ÜË[
JOÝ›Y[[Ú^™YÝ]O[Ž“_
œÝ]S›ÙO\ÙŠ\Kœ[™[™Ô›ÜËYK˜Ý\œ™[
JN›Y[[Ú^™YÝ]OY\
\KK›Y[[Ú^™Y›ÜËœ[™[™Ô›ÜËK›Y[[Ú^™YÝ]JK[ØØ\ÙHÎœ™]\›ˆÙJ
KOOO[[	‰“I‰Š]œÝ]S›ÙORŠ\Kœ[™[™Ô›ÜËYK˜Ý\œ™[
KšO]šOHLORZKYŠ\JOÊ™XKZOSŠ‹™š\œÝÚ[
JN’ZOXJKÊKœ[™[™Ô›ÜË˜Ú[™[‹ŠKØÊK
KOOO[[	‰Š™›YÜßMNMÌ
K˜Ú[ØØ\ÙHNœ™]\›ˆOOO[[	‰“I‰Š
O\RZJI‰ŠS™Š‹\Kœ[™[™Ô›ÜËšJKOO[[ØOHLNŠœÝ]S›ÙO\‹šO]ZOSŠ‹™š\œÝÚ[
KšOHLKOHL
JK_šJ
JKÙJ
KO]\KÏ]œ[™[™Ô›ÜËÏYOOO[[Û[™K›Y[[Ú^™Y›ÜË[Ë˜Ú[™[‹ÙŠKÊOÜ[[œÈOO[[	‰˜ÙŠKÊI‰Š™›YÜßLÌŠK›Y[[Ú^™YÝ]HOO[[	‰ŠOQÊKYK[[ŠK—ØÝ\œ™[˜[YOXJKØÊK
KÊK‹ŠK˜Ú[ØØ\ÙHŽœ™]\›ˆOOO[[	‰“I‰Š
O[RZJI‰ŠR]J‹œ[™[™Ô›ÜËšJKOO[[ÙOHLNŠœÝ]S›ÙO[‹šO]ZO[[OHL
JK_šJ
JK[ØØ\ÙHLÎœ™]\›ˆÊKŠNØØ\ÙHœ™]\›ˆJœÝ]S›ÙK˜ÛÛZ[™\’[™›ÊK]œ[™[™Ô›ÜËOOO[[Ý˜Ú[P˜J[‹ŠN–ÊK‹ŠK˜Ú[ØØ\ÙHLNœ™]\›ˆœÊK\Kœ[™[™Ô›ÜËŠNØØ\ÙHÎœ™]\›ˆ]œ[™[™Ô›ÜËØÊK
KÊK‹ŠK˜Ú[ØØ\ÙHœ™]\›ˆÊKœ[™[™Ô›ÜË˜Ú[™[‹ŠK˜Ú[ØØ\ÙHLŽœ™]\›ˆÊKœ[™[™Ô›ÜË˜Ú[™[‹ŠK˜Ú[ØØ\ÙHLœ™]\›ˆYYJKŠNØØ\ÙHNœ™]\›ˆO]\K—ØÛÛ^]œ[™[™Ô›ÜË˜Ú[™[‹˜J
KOZXJJK\ŠJK™›YÜßLKÊK‹ŠK˜Ú[ØØ\ÙHMœ™]\›ˆ\ÊK\Kœ[™[™Ô›ÜËŠNØØ\ÙHMNœ™]\›ˆ	ÊK\Kœ[™[™Ô›ÜËŠNØØ\ÙHNNœ™]\›ˆ˜ÊKŠNØØ\ÙHÌNœ™]\›ˆXÊKŠNØØ\ÙHŒŽœ™]\›ˆXÊK‹œ[™[™Ô›ÜÊNØØ\ÙHœ™]\›ˆ˜J
KZXJJKOOO[[ÊOTØJ
KOOO[[	‰ŠO\ÝKÏ]XJ
KKœÛÛYØXÚO[ËËœ™YÛÝ[
ÊËÈOO[[	‰ŠKœÛÛYØXÚS[™\ß[ŠKO[ÊK›Y[[Ú^™YÝ]O^Ü\™[œ‹ØXÚN˜_KXJ
KšJKJJNŠ
K›[™\É›ŠHOOL	‰ŠØJK
K˜J[[ŠKJ
JKOYK›Y[[Ú^™YÝ]KÏ]›Y[[Ú^™YÝ]KKœ\™[OO\Ê[Ë˜ØXÚKšJKŠKˆOOXK˜ØXÚI‰™XJÛWK‹L
JNŠO^Ü\™[œ‹ØXÚNœŸK›Y[[Ú^™YÝ]OXK›[™\ÏOOL	‰Š›Y[[Ú^™YÝ]O]\]T]Y]YK˜˜\ÙTÝ]OXJKšJKŠJJKÊKœ[™[™Ô›ÜË˜Ú[™[‹ŠK˜Ú[ØØ\ÙHÌœ™]\›ˆœÝ]S›ÙOOO[[	‰ŠœÝ]S›ÙO^Ø]]Ó˜[YN›[Z\™Y›[ÛÛ™\Î›[™YŽ›[JK]œ[™[™Ô›ÜË‹›˜[YHO[[	‰œ‹›˜[YHOOX]]ØÝ™›YÜßYOOO[[ÌNMŒŒNÍÍŽ“I‰“ZJ
KHOO[[	‰™K›Y[[Ú^™Y›ÜË›˜[YHOO\‹›˜[YOÝ™›YÜßMNMMŽ›ØÊK
KÊK‹˜Ú[™[‹ŠK˜Ú[ØØ\ÙHŽN›ÝÈœ[™[™Ô›Üß]›ÝÈ\œ›ÜŠJMM‹YÊJ_Y[˜Ý[ÛˆÊJ^ÙK™›YÜßMY[˜Ý[ÛˆXÊK‹‹J^Ý˜\ˆNÚYŠ
OJK›[ÙIŒÌŠHOL
I‰ŠO[OO[[Û\
ŠN›\
ŠI‰Š‹œÜ˜ÈOO[‹œÜ˜ß‹œÜ˜ÔÙ]OO[‹œÜ˜ÔÙ]
JKJ^ÚYŠK™›YÜßLMÍÍÌŒM‹
IŒÌÍMMLŽ
OOOZJZYŠKœÝ]S›ÙK˜ÛÛ\]JYK™›YÜßNNLŽÙ[ÙHYŠ	YJ
JYK™›YÜßNNLŽÙ[ÙH›ÝÈXOSØKX_Y[ÙHK™›YÜÉKLMÍÍÌŒMßY[˜Ý[ÛˆÊK
^ÚYŠ\HOOXÝ[\ÚY]œÝ]K›ØY[™É
YK™›YÜÉKLMÍÍÌŒMÎÙ[ÙHYŠK™›YÜßLMÍÍÌŒM‹Z

JZYŠ	YJ
JYK™›YÜßNNLŽÙ[ÙH›ÝÈXOSØKX_Y[˜Ý[ÛˆØÊK
^ÝOO[[	‰ŠK™›YÜßM
KK™›YÜÉŒMŒÎ	‰ŠYKYÏOOLŒÍLÍŽÌLLŽœÝ

KK›[™\ß]_]
_Y[˜Ý[ÛˆØÊK
^ÚYŠSJ\ÝÚ]Ú
KZ[[ÙJ^ØØ\ÙXš\ÚX›X˜œ™XZÎØØ\ÙXÛÛ\ÙY™›ÜŠ˜\ˆYKZ[[[ÛˆOO[[Ê[‹˜[\›˜]HOO[[	‰Š[ŠK[‹œÚX›[™ÎÜOO[[ÝKZ[OO[[ÙKZ[[[™KZ[œÚX›[™Ï[[œ‹œÚX›[™Ï[[Øœ™XZÎÙY˜][™›ÜŠYKZ[[[ÝOO[[Ê]˜[\›˜]HOO[[	‰Š]
K]œÚX›[™ÎÛOO[[ÙKZ[[[›‹œÚX›[™Ï[[_Y[˜Ý[ÛˆXÊJ^Ý˜\ˆYK˜[\›˜]HOO[[	‰™K˜[\›˜]K˜Ú[OOYK˜Ú[LLÚYŠ
Y›ÜŠ˜\ˆOYK˜Ú[ÚHOO[[Ê[ŸZK›[™\ßK˜Ú[[™\ËŸZKœÝX™YQ›YÜÉŒLŒŽLLMÍ‹ŸZK™›YÜÉŒLŒŽLLMÍ‹Kœ™]\›YKOZKœÚX›[™ÎÙ[ÙH›ÜŠOYK˜Ú[ÚHOO[[Ê[ŸZK›[™\ßK˜Ú[[™\ËŸZKœÝX™YQ›YÜËŸZK™›YÜËKœ™]\›YKOZKœÚX›[™ÎÜ™]\›ˆKœÝX™YQ›YÜß\‹K˜Ú[[™\Ï[‹Y[˜Ý[Ûˆ˜ÊKŠ^Ý˜\ˆ]œ[™[™Ô›ÜÎÜÝÚ]Ú
šJ
KYÊ^ØØ\ÙHMŽ˜Ø\ÙHMN˜Ø\ÙH˜Ø\ÙHLN˜Ø\ÙHÎ˜Ø\ÙH˜Ø\ÙHLŽ˜Ø\ÙHN˜Ø\ÙHMœ™]\›ˆXÊ
K[ØØ\ÙHNœ™]\›ˆXÊ
K[ØØ\ÙHÎœ™]\›ˆ]œÝ]S›ÙK[[HOO[[	‰ŠYK›Y[[Ú^™YÝ]K˜ØXÚJK›Y[[Ú^™YÝ]K˜ØXÚHOO\‰‰Š™›YÜßLŒ
KZJJKÙJ
K‹œ[™[™ÐÛÛ^	‰Š‹˜ÛÛ^[‹œ[™[™ÐÛÛ^‹œ[™[™ÐÛÛ^[[
K
OOO[[K˜Ú[OO[[
I‰ŠÚJ
OÕÊ
N™OOO[[K›Y[[Ú^™YÝ]Kš\ÑZY˜]Y	‰ˆJ™›YÜÉŒMŠ_
™›YÜßLLÚJ
JJKXÊ
K[ØØ\ÙHŽ˜\ˆO]\KÏ]›Y[[Ú^™YÝ]NÜ™]\›ˆOOO[[ÊÊ
KÏOO[[ÊXÊ
KXÊK[‹ŠJNŠXÊ
KÊÊJJN›ÏÛÏOOYK›Y[[Ú^™YÝ]OÊXÊ
K™›YÜÉKLMÍÍÌŒMÊNŠÊ
KXÊ
KÊÊJNŠOYK›Y[[Ú^™Y›ÜËHOO\‰‰•Ê
KXÊ
KXÊKK‹ŠJK[ØØ\ÙHÎšYŠÙJ
K^YK˜Ý\œ™[O]\KHOO[[	‰œÝ]S›ÙHO[[
YK›Y[[Ú^™Y›ÜÈOO\‰‰•Ê
NÙ[Ù^ÚYŠ\Š^ÚYŠœÝ]S›ÙOOO[[
]›ÝÈ\œ›ÜŠJMŠJNÜ™]\›ˆXÊ
KœÝX™YQ›YÜÉKLÌÍMMÌË[YOWÙK˜Ý\œ™[ÚJ
OÒJJNŠORŠK‹ŠKœÝ]S›ÙOYKÊ
J_\™]\›ˆXÊ
KœÝX™YQ›YÜÉKLÌÍMMÌË[ØØ\ÙHNšYŠÙJ
KO]\KHOO[[	‰œÝ]S›ÙHO[[
YK›Y[[Ú^™Y›ÜÈOO\‰‰•Ê
NÙ[Ù^ÚYŠ\Š^ÚYŠœÝ]S›ÙOOO[[
]›ÝÈ\œ›ÜŠJMŠJNÜ™]\›ˆXÊ
KœÝX™YQ›YÜÉKLÌÍMMÌË[ZYŠÏWÙK˜Ý\œ™[ÚJ
JRJÊNÙ[Ù^Ý˜\ˆÏXYŠYK˜Ý\œ™[
NÜÝÚ]Ú
Ê^ØØ\ÙHN›Ï\Ë˜Ü™X]Q[[Y[”Ê‹ËÝÝÝËÌË›Ü™ËÌŒÜÝ™ØJNØœ™XZÎØØ\ÙHŽ›Ï\Ë˜Ü™X]Q[[Y[”Ê‹ËÝÝÝËÌË›Ü™ËÌNNNÓX]ÓX]SJNØœ™XZÎÙY˜][œÝÚ]Ú
J^ØØ\ÙXÝ™Ø›Ï\Ë˜Ü™X]Q[[Y[”Ê‹ËÝÝÝËÌË›Ü™ËÌŒÜÝ™ØJNØœ™XZÎØØ\ÙXX]›Ï\Ë˜Ü™X]Q[[Y[”Ê‹ËÝÝÝËÌË›Ü™ËÌNNNÓX]ÓX]SJNØœ™XZÎØØ\ÙXØÜš\›Ï\Ë˜Ü™X]Q[[Y[
]˜
KËš[›™\’SXØÜš\ÜØÜš\˜Ï[Ëœ™[[Ý™PÚ[
Ë™š\œÝÚ[
NØœ™XZÎØØ\ÙXÙ[XÝ›Ï]\[Ùˆ‹š\ÏOXÝš[™ØÜË˜Ü™X]Q[[Y[
Ù[XÝÚ\Îœ‹š\ßJNœË˜Ü™X]Q[[Y[
Ù[XÝ
K‹›][\OÛË›][\OHLœ‹œÚ^™I‰ŠËœÚ^™O\‹œÚ^™JNØœ™XZÎÙY˜][›Ï]\[Ùˆ‹š\ÏOXÝš[™ØÜË˜Ü™X]Q[[Y[
KÚ\Îœ‹š\ßJNœË˜Ü™X]Q[[Y[
J__[ÖÞ]O]ÖØO\ŽØN™›ÜŠÏ]˜Ú[ÜÈOO[[Ê^ÚYŠËYÏOOM_ËYÏOOMŠ[Ë˜\[™Ú[
ËœÝ]S›ÙJNÙ[ÙHYŠËYÈOOM	‰œËYÈOOLÉ‰œË˜Ú[OO[[
^ÜË˜Ú[œ™]\›\ËÏ\Ë˜Ú[ØÛÛ[Y_ZYŠÏOO]
Xœ™XZÈNÙ›ÜŠÜËœÚX›[™ÏOO[[Ê^ÚYŠËœ™]\›OO[[Ëœ™]\›OO]
Xœ™XZÈNÜÏ\Ëœ™]\›Ÿ\ËœÚX›[™Ëœ™]\›\Ëœ™]\›‹Ï\ËœÚX›[™ß]œÝ]S›ÙO[ÎØNœÝÚ]Ú
YŠËKŠKJ^ØØ\ÙX]Û˜˜Ø\ÙX[œ]˜Ø\ÙXÙ[XÝ˜Ø\ÙX^\™XXœHH\‹˜]]Ñ›ØÝ\ÎØœ™XZÈNØØ\ÙX[YØœHLØœ™XZÈNÙY˜][œHL_\‰‰•Ê
__\™]\›ˆXÊ
KœÝX™YQ›YÜÉKLÌÍMMÌËXÊ\KOOO[[Û[™K›Y[[Ú^™Y›ÜËœ[™[™Ô›ÜËŠK[ØØ\ÙHŽšYŠI‰œÝ]S›ÙHO[[
YK›Y[[Ú^™Y›ÜÈOO\‰‰•Ê
NÙ[Ù^ÚYŠ\[ÙˆˆOXÝš[™Ø	‰œÝ]S›ÙOOO[[
]›ÝÈ\œ›ÜŠJMŠJNÚYŠO^YK˜Ý\œ™[ÚJ
J^ÚYŠO]œÝ]S›ÙK]›Y[[Ú^™Y›ÜË[[OQšKHOO[[
\ÝÚ]Ú
KYÊ^ØØ\ÙHÎ˜Ø\ÙHNœXK›Y[[Ú^™Y›ÜßYVÞ]O]OHHJK››ÙU˜[YOOO[ŸˆOO[[	‰ˆLOO\‹œÝ\™\ÜÒY˜][Û•Ø\›š[™ß™
K››ÙU˜[YKŠJK_šJL
_Y[ÙHOXYŠJK˜Ü™X]U^›ÙJŠKVÞ]O]œÝ]S›ÙOY_\™]\›ˆXÊ
K[ØØ\ÙHÌNšYŠ]›Y[[Ú^™YÝ]KOOO[[K›Y[[Ú^™YÝ]HOO[[
^ÚYŠUÚJ
KˆOO[[
^ÚYŠOOO[[
^ÚYŠ\Š]›ÝÈ\œ›ÜŠJÌN
JNÚYŠO]›Y[[Ú^™YÝ]KOYOOO[[Û[™K™ZY˜]YYJ]›ÝÈ\œ›ÜŠJMMÊJNÙVÞ]O]Y[ÙHÚJ
KJ™›YÜÉŒLŽ
I‰Š›Y[[Ú^™YÝ]O[[
K™›YÜßMÐXÊ
KOHL_Y[ÙHRÚJ
KHOO[[	‰™K›Y[[Ú^™YÝ]HOO[[	‰ŠK›Y[[Ú^™YÝ]KšY˜][Û‘\œ›ÜœÏ[ŠKOHLÚYŠYJ\™]\›ˆ™›YÜÉŒMÊÛÊ
K
NŠÛÊ
K[
NÚYŠ™›YÜÉŒLŽ
]›ÝÈ\œ›ÜŠJMN
J_\™]\›ˆXÊ
K[ØØ\ÙHLÎšYŠ]›Y[[Ú^™YÝ]KOOO[[K›Y[[Ú^™YÝ]HOO[[	‰™K›Y[[Ú^™YÝ]K™ZY˜]YOO[[
^ÚYŠOUÚJ
KˆOO[[	‰œ‹™ZY˜]YOO[[
^ÚYŠOOO[[
^ÚYŠXJ]›ÝÈ\œ›ÜŠJÌN
JNÚYŠO]›Y[[Ú^™YÝ]KOXOOO[[Û[˜K™ZY˜]YXJ]›ÝÈ\œ›ÜŠJÌMÊJNØVÞ]O]Y[ÙHÚJ
KJ™›YÜÉŒLŽ
I‰Š›Y[[Ú^™YÝ]O[[
K™›YÜßMÐXÊ
KOHL_Y[ÙHORÚJ
KHOO[[	‰™K›Y[[Ú^™YÝ]HOO[[	‰ŠK›Y[[Ú^™YÝ]KšY˜][Û‘\œ›ÜœÏXJKOHLÚYŠXJ\™]\›ˆ™›YÜÉŒMÊÛÊ
K
NŠÛÊ
K[
_\™]\›ˆÛÊ
K™›YÜÉŒLŽÊ›[™\Ï[‹
NŠ\ˆOO[[OYHOO[[	‰™K›Y[[Ú^™YÝ]HOO[[‰‰Š]˜Ú[O[[‹˜[\›˜]HOO[[	‰œ‹˜[\›˜]K›Y[[Ú^™YÝ]HOO[[	‰œ‹˜[\›˜]K›Y[[Ú^™YÝ]K˜ØXÚTÛÛOO[[	‰ŠO\‹˜[\›˜]K›Y[[Ú^™YÝ]K˜ØXÚTÛÛœÛÛ
KÏ[[‹›Y[[Ú^™YÝ]HOO[[	‰œ‹›Y[[Ú^™YÝ]K˜ØXÚTÛÛOO[[	‰ŠÏ\‹›Y[[Ú^™YÝ]K˜ØXÚTÛÛœÛÛ
KÈOOXI‰Š‹™›YÜßLŒ
JKˆOOYI‰›‰‰Š˜Ú[™›YÜßNNLŠKØÊ\]T]Y]YJKXÊ
K[
NØØ\ÙHœ™]\›ˆÙJ
KOOO[[	‰›JœÝ]S›ÙK˜ÛÛZ[™\’[™›ÊK™›YÜßMÌLXÊ
K[ØØ\ÙHLœ™]\›ˆZJ\JKXÊ
K[ØØ\ÙHNNšYŠ›Ê
K]›Y[[Ú^™YÝ]KOO[[
\™]\›ˆXÊ
K[ÚYŠOJ™›YÜÉŒLŽ
HOLÏ\‹œ™[™\š[™ËÏOO[[
ZYŠJZØÊ‹LJNÙ[Ù^ÚYŠÝHOOLHOO[[	‰™K™›YÜÉŒLŽ
Y›ÜŠO]˜Ú[ÙHOO[[Ê^ÚYŠÏ\ÊJKÈOO[[
^Ù›ÜŠ™›YÜßLLŽØÊ‹LJKO[Ë\]T]Y]YK\]T]Y]YOYKØÊJKœÝX™YQ›YÜÏLO[‹]˜Ú[ÛˆOO[[Ê^YYJ‹JK[‹œÚX›[™ÎÜ™]\›ˆ[ÊË˜Ý\œ™[	Œ_ŠKI‰ZJ‹™YQ›ÜšÐÛÝ[
K˜Ú[YOYKœÚX›[™ß\‹Z[OO[[	‰“J
O‘I‰Š™›YÜßLLŽOHLØÊ‹LJK›[™\ÏMNMÌ
_Y[Ù^ÚYŠXJZYŠO\ÊÊKHOO[[
^ÚYŠ™›YÜßLLŽOHLOYK\]T]Y]YK\]T]Y]YOYKØÊJKØÊ‹L
K‹Z[OO[[	‰œ‹Z[[ÙHOOXÛÛ\ÙY	‰œ‹Z[[ÙHOOXš\ÚX›X	‰ˆ[Ë˜[\›˜]I‰ˆSJ\™]\›ˆXÊ
K[Y[ÙHŠ“J
K\‹œ™[™\š[™ÔÝ\[YO‘I‰›ˆOOMLÍŽÌLL‰‰Š™›YÜßLLŽOHLØÊ‹LJK›[™\ÏMNMÌ
NÜ‹š\Ð˜XÚÝØ\™ÏÊËœÚX›[™Ï]˜Ú[˜Ú[[ÊNŠO\‹›\ÝOOO[[Ý˜Ú[[Î™KœÚX›[™Ï[Ë‹›\Ý[Ê_ZYŠ‹Z[OO[[
^ÙO\‹Z[ØNžÙ›ÜŠYNÛˆOO[[Ê^ÚYŠ‹˜[\›˜]HOO[[
^ÛHLNØœ™XZÈ_[[‹œÚX›[™ß[HL\™]\›ˆ‹œ™[™\š[™ÏYK‹Z[YKœÚX›[™Ë‹œ™[™\š[™ÔÝ\[YOSJ
KKœÚX›[™Ï[[Ï[Ë˜Ý\œ™[ÏXOÛÉŒ_Ž›ÉŒK‹Z[[ÙOOOXš\ÚX›X‹Z[[ÙOOOXÛÛ\ÙY[ŸOÝ[ÊÊNŠ[ËÙJ›Ë
KÙJËŠK›ÏOO[[	‰Š›Ï]
JKI‰ZJ‹™YQ›ÜšÐÛÝ[
K_\™]\›ˆXÊ
K[ØØ\ÙHŒŽ˜Ø\ÙHŒÎœ™]\›ˆÛÊ
KÊ
K]›Y[[Ú^™YÝ]HOO[[OOO[[Ü‰‰Š™›YÜßNNLŠN™K›Y[[Ú^™YÝ]HOO[[OO\‰‰Š™›YÜßNNLŠKÛ‰LÍŽÌLL‰‰ˆJ™›YÜÉŒLŽ
I‰ŠXÊ
KœÝX™YQ›YÜÉ‰‰Š™›YÜßNNLŠJNXÊ
K]\]T]Y]YKˆOO[[	‰“ØÊ‹œ™]žT]Y]YJK[[HOO[[	‰™K›Y[[Ú^™YÝ]HOO[[	‰™K›Y[[Ú^™YÝ]K˜ØXÚTÛÛOO[[	‰ŠYK›Y[[Ú^™YÝ]K˜ØXÚTÛÛœÛÛ
K[[›Y[[Ú^™YÝ]HOO[[	‰›Y[[Ú^™YÝ]K˜ØXÚTÛÛOO[[	‰Š]›Y[[Ú^™YÝ]K˜ØXÚTÛÛœÛÛ
KˆOO[‰‰Š™›YÜßLŒ
KHOO[[	‰šJJK[ØØ\ÙHœ™]\›ˆ[[HOO[[	‰ŠYK›Y[[Ú^™YÝ]K˜ØXÚJK›Y[[Ú^™YÝ]K˜ØXÚHOO[‰‰Š™›YÜßLŒ
KZJJKXÊ
K[ØØ\ÙHNœ™]\›ˆ[ØØ\ÙHÌœ™]\›ˆ™›YÜßLÌÍMMÌ‹XÊ
K[]›ÝÈ\œ›ÜŠJMM‹YÊJ_Y[˜Ý[ÛˆXÊK
^ÜÝÚ]Ú
šJ
KYÊ^ØØ\ÙHNœ™]\›ˆO]™›YÜËIMLÍÊ™›YÜÏYI‹MMLÍßLŽ
N›[ØØ\ÙHÎœ™]\›ˆZJJKÙJ
KO]™›YÜËIMLÍ‰‰ˆJIŒLŽ
OÊ™›YÜÏYI‹MMLÍßLŽ
N›[ØØ\ÙHŽ˜Ø\ÙHÎ˜Ø\ÙHNœ™]\›ˆÙJ
K[ØØ\ÙHÌNšYŠ›Y[[Ú^™YÝ]HOO[[
^ÚYŠÛÊ
K˜[\›˜]OOO[[
]›ÝÈ\œ›ÜŠJÍ
JNÑÚJ
_\™]\›ˆO]™›YÜËIMLÍÊ™›YÜÏYI‹MMLÍßLŽ
N›[ØØ\ÙHLÎšYŠÛÊ
KO]›Y[[Ú^™YÝ]KHOO[[	‰™K™ZY˜]YOO[[
^ÚYŠ˜[\›˜]OOO[[
]›ÝÈ\œ›ÜŠJÍ
JNÑÚJ
_\™]\›ˆO]™›YÜËIMLÍÊ™›YÜÏYI‹MMLÍßLŽ
N›[ØØ\ÙHNNœ™]\›ˆ›Ê
KO]™›YÜËIMLÍÊ™›YÜÏYI‹MMLÍßLŽO]›Y[[Ú^™YÝ]KHOO[[	‰ŠKœ™[™\š[™Ï[[KZ[[[
K™›YÜßM
N›[ØØ\ÙHœ™]\›ˆÙJ
K[ØØ\ÙHLœ™]\›ˆZJ\JK[ØØ\ÙHŒŽ˜Ø\ÙHŒÎœ™]\›ˆÛÊ
KÊ
KHOO[[	‰šJJKO]™›YÜËIMLÍÊ™›YÜÏYI‹MMLÍßLŽ
N›[ØØ\ÙHœ™]\›ˆZJJK[ØØ\ÙHNœ™]\›ˆ[ÙY˜][œ™]\›ˆ[_Y[˜Ý[Ûˆ˜ÊK
^ÜÝÚ]Ú
šJ
KYÊ^ØØ\ÙHÎ”ZJJKÙJ
NØœ™XZÎØØ\ÙHŽ˜Ø\ÙHÎ˜Ø\ÙHNÙJ
NØœ™XZÎØØ\ÙH”ÙJ
NØœ™XZÎØØ\ÙHÌN›Y[[Ú^™YÝ]HOO[[	‰˜ÛÊ
NØœ™XZÎØØ\ÙHLÎ˜ÛÊ
NØœ™XZÎØØ\ÙHNN™›Ê
NØœ™XZÎØØ\ÙHL”ZJ\JNØœ™XZÎØØ\ÙHŒŽ˜Ø\ÙHŒÎ˜ÛÊ
KÊ
KHOO[[	‰šJJNØœ™XZÎØØ\ÙH”ZJJ__Y[˜Ý[ÛˆÊK
^Ýž^Ý˜\ˆ]\]T]Y]YK[OO[[Û[›‹›\ÝY™™XÝÚYŠˆOO[[
^Ý˜\ˆO\‹›™^ÛZNÙÞÚYŠ
‹YÉ™JOOOYJ^Ü]›ÚYÝ˜\ˆO[‹˜Ü™X]KÏ[‹š[œÝÜXJ
KË™\Ý›ÞO\Ÿ[[‹›™^]Ú[JˆOOZJ__XØ]Ú
J^Ý™
œ™]\›‹J__Y[˜Ý[Ûˆ˜ÊKŠ^Ýž^Ý˜\ˆ]\]T]Y]YKO\OO[[Û[œ‹›\ÝY™™XÝÚYŠHOO[[
^Ý˜\ˆOZK›™^ÜXNÙÞÚYŠ
‹YÉ™JOOOYJ^Ý˜\ˆÏ\‹š[œÝÏ[Ë™\Ý›ÞNÚYŠÈOO]›ÚY
^ÛË™\Ý›ÞO]›ÚYO]Ý˜\ˆ[‹O\ÎÝž^ÝJ
_XØ]Ú
J^Ý™
KJ___\\‹›™^]Ú[JˆOOXJ__XØ]Ú
J^Ý™
œ™]\›‹J__Y[˜Ý[ÛˆXÊJ^Ý˜\ˆYK\]T]Y]YNÚYŠOO[[
^Ý˜\ˆYKœÝ]S›ÙNÝž^ÕYJŠ_XØ]Ú

^Ý™
KKœ™]\›‹
___Y[˜Ý[ÛˆÊKŠ^Û‹œ›ÜÏUœÊK\KK›Y[[Ú^™Y›ÜÊK‹œÝ]OYK›Y[[Ú^™YÝ]NÝž^Û‹˜ÛÛ\Û™[Ú[[›[Ý[

_XØ]Ú
Š^Ý™
KŠ__Y[˜Ý[Ûˆ˜ÊK
^Ýž^Ý˜\ˆYKœ™YŽÚYŠˆOO[[
^ÜÝÚ]Ú
KYÊ^ØØ\ÙHŽ˜Ø\ÙHÎ˜Ø\ÙHN˜\ˆYKœÝ]S›ÙNØœ™XZÎØØ\ÙHÌ˜\ˆOYKœÝ]S›ÙKOVœŠK›Y[[Ú^™Y›ÜËJNÊKœ™YOO[[Kœ™Y‹›˜[YHOOXJI‰ŠKœ™Y^ŠJJKZKœ™YŽØœ™XZÎØØ\ÙHÎšYŠKœÝ]S›ÙOOO[[
^Ý˜\ˆÏ[™]ÈÙŠJNÜ
K˜Ú[LKKË›ÚY›ÚY
KKœÝ]S›ÙO[ß\YKœÝ]S›ÙNØœ™XZÎÙY˜][œYKœÝ]S›Ù_]\[ÙˆOX[˜Ý[Û˜ÙKœ™YÛX[\[ŠŠN›‹˜Ý\œ™[\Ÿ_XØ]Ú
Š^Ý™
KŠ__Y[˜Ý[Ûˆ˜ÊK
^Ý˜\ˆYKœ™Y‹YKœ™YÛX[\ÚYŠˆOO[[
ZYŠ\[ÙˆOX[˜Ý[Û˜
]ž^ÜŠ
_XØ]Ú
Š^Ý™
KŠ_Yš[˜[^ÙKœ™YÛX[\[[OYK˜[\›˜]KHO[[	‰ŠKœ™YÛX[\[[
_Y[ÙHYŠ\[ÙˆOX[˜Ý[Û˜
]ž^ÛŠ[
_XØ]Ú
Š^Ý™
KŠ_Y[ÙH‹˜Ý\œ™[[[Y[˜Ý[Ûˆ˜ÊK
^ÚYŠ
KYÏOOM_KYÏOOLßKYÏOOMŠI‰™K˜[\›˜]OOO[[	‰OO[[
Y›ÜŠ˜\ˆLÛ›[™ÝÛŠÊÊTJKœÝ]S›ÙKÛ—J_Y[˜Ý[ÛˆÙYJJ^Ù›ÜŠ˜\ˆYKœ™]\›ŽÝOO[[	‰ŠXÊ
I‰”JKœÝ]S›ÙKœÝ]S›ÙJKRÊ
JNÊ]]œ™]\›ŸY[˜Ý[Ûˆ˜ÊJ^Ù›ÜŠ˜\ˆYKœ™]\›ŽÝOO[[	‰ŠXÊ
I‰‘JKœÝ]S›ÙKœÝ]S›ÙJKRÊ
JNÊ]]œ™]\›ŸY[˜Ý[ÛˆÊJ^Ü™]\›ˆKYÏOOM_KYÏOOLßKYÏOOLßY[˜Ý[ÛˆXÊJ^Ü™]\›ˆI‰™KYÏOOMÉ‰™KœÝ]S›ÙHOO[[Y[˜Ý[ÛˆØÊJ^Ý˜\ˆYK\KYK›Y[[Ú^™Y›ÜËYKœÝ]S›ÙNÝž^ØNœÝÚ]Ú

^ØØ\ÙX]Û˜˜Ø\ÙX[œ]˜Ø\ÙXÙ[XÝ˜Ø\ÙX^\™XX›‹˜]]Ñ›ØÝ\É‰œ‹™›ØÝ\Ê
NØœ™XZÈNØØ\ÙX[YØ›‹œÜ˜ÏÜ‹œÜ˜Ï[‹œÜ˜Î›‹œÜ˜ÔÙ]	‰Š‹œÜ˜ÜÙ][‹œÜ˜ÔÙ]
__XØ]Ú

^Ý™
KKœ™]\›‹
__Y[˜Ý[ÛˆØÊKŠ^Ýž^Ý˜\ˆYKœÝ]S›ÙNÛ]J‹K\K‹
K–ØO]XØ]Ú

^Ý™
KKœ™]\›‹
__Y[˜Ý[ÛˆÙYJJ^Ü™]\›ˆKYÏOOM_KYÏOOLßKYÏOOLŸKYÏOOLÉ‰›YŠK\J_KYÏOOMY[˜Ý[ÛˆØÊJ^ØN™›ÜŠÎÊ^Ù›ÜŠÙKœÚX›[™ÏOO[[Ê^ÚYŠKœ™]\›OO[[ÙYJKœ™]\›ŠJ\™]\›ˆ[ÙOYKœ™]\›ŸY›ÜŠKœÚX›[™Ëœ™]\›YKœ™]\›‹OYKœÚX›[™ÎÙKYÈOOMI‰™KYÈOOM‰‰™KYÈOOLNÊ^ÚYŠKYÏOOLÉ‰›YŠK\J_K™›YÜÉŒŸK˜Ú[OO[[KYÏOOM
XÛÛ[YHNÙK˜Ú[œ™]\›YKOYK˜Ú[ZYŠJK™›YÜÉŒŠJ\™]\›ˆKœÝ]S›Ù__Y[˜Ý[ÛˆXÊK‹Š^Ý˜\ˆOYKYÎÚYŠOOOM_OOOMŠZOYKœÝ]S›ÙKÊ‹››ÙU\OOONOÛ‹˜›ÙN›‹››ÙS˜[YOOOXSÛ‹›ÝÛ™\‘ØÝ[Y[˜›ÙN›ŠKš[œÙ\™Y›Ü™JK
NŠ[‹››ÙU\OOONOÛ‹˜›ÙN›‹››ÙS˜[YOOOXSÛ‹›ÝÛ™\‘ØÝ[Y[˜›ÙN›‹˜\[™Ú[
JK[‹—Ü™XXÝ›ÛÝÛÛZ[™\‹ˆO[[›Û˜ÛXÚÈOO[[
›Û˜ÛXÚÏ[[ŠJK˜ÊKŠK]HLÙ[ÙHYŠHOOM	‰ŠOOOLÉ‰Š˜ÊKŠK[[YŠK\JI‰ŠYKœÝ]S›ÙK[[
JKOYK˜Ú[HOO[[
JY›ÜŠXÊK‹ŠKOYKœÚX›[™ÎÙHOO[[Ê\XÊK‹ŠKOYKœÚX›[™ßY[˜Ý[Ûˆ˜ÊK‹Š^Ý˜\ˆOYKYÎÚYŠOOOM_OOOMŠZOYKœÝ]S›ÙKÛ‹š[œÙ\™Y›Ü™JK
N›‹˜\[™Ú[
JK˜ÊKŠK]HLÙ[ÙHYŠHOOM	‰ŠOOOLÉ‰Š˜ÊKŠK[[YŠK\JI‰ŠYKœÝ]S›ÙJJKOYK˜Ú[HOO[[
JY›ÜŠ˜ÊK‹ŠKOYKœÚX›[™ÎÙHOO[[ÊR˜ÊK‹ŠKOYKœÚX›[™ßY[˜Ý[ÛˆÙYJJ^Ý˜\ˆYKœÝ]S›ÙKYK›Y[[Ú^™Y›ÜÎÝž^Ù›ÜŠ˜\ˆYK\KO]˜]šX]\ÎÚK›[™ÝÊ]œ™[[Ý™P]šX]S›ÙJVÌJNÙYŠ‹ŠKÞ]OYKØO[ŸXØ]Ú

^Ý™
KKœ™]\›‹
__]˜\ˆXÏHLKÏ[[Ù[˜Ý[Ûˆ˜ÊJ^ÊKYÏOOLÌKœÝX™YQ›YÜÉŒÌÍMMÌŠI‰ŠXÏHL
_]˜\ˆXÏ[[Ù[˜Ý[ÛˆYYJ
^Ý˜\ˆOTXÎÜ™]\›ˆXÏ[[_]˜\ˆ	ÏLÙ[˜Ý[Ûˆ[
K‹‹J^Ü™]\›ˆ	ÏL
K˜Ú[‹‹J_Y[˜Ý[Ûˆ
K‹‹J^Ù›ÜŠ˜\ˆOHLNÙHOO[[Ê^ÚYŠKYÏOOMJ^Ý˜\ˆÏYKœÝ]S›ÙNÚYŠˆOO[[
^Ý˜\ˆÏ]™ŠÊNÜ‹œ\Ú
ÊKËšY]É‰ŠOHL
_Y[ÙH_™ŠÊKšY]É‰ŠOHL
NÖXÏHLJË	ÏOOLÝ
ØØ
ÉËŠK	ÊÊßY[ÙJKYÈOOLŒŸK›Y[[Ú^™YÝ]OOO[[
I‰ŠKYÏOOLÌ	‰š_
K˜Ú[‹‹JI‰ŠOHL
JNÙOYKœÚX›[™ß\™]\›ˆ_Y[˜Ý[Ûˆ›
K
^Ù›ÜŠÙHOO[[ÊYKYÏOOMO×ÙŠKœÝ]S›ÙKK›Y[[Ú^™Y›ÜÊNŠKYÈOOLŒŸK›Y[[Ú^™YÝ]OOO[[
I‰ŠKYÏOOLÌ	‰›
K˜Ú[
JKOYKœÚX›[™ßY[˜Ý[Ûˆ›
J^ÚYŠKœÝX™YQ›YÜÉŒNÍÍŽ
Y›ÜŠOYK˜Ú[ÙHOO[[Ê^ÚYŠ
KYÈOOLŒŸK›Y[[Ú^™YÝ]OOO[[
I‰Š›
JKKYÏOOLÌ	‰™K™›YÜÉŒNÍÍŽ	‰™KœÝ]S›ÙKœZ\™Y
J^Ý˜\ˆYK›Y[[Ú^™Y›ÜÎÚYŠ›˜[YOO[[›˜[YOOOX]]Ø
]›ÝÈ\œ›ÜŠJM
JNÝ˜\ˆ]›˜[YNÝIŠ™Y˜][œÚ\™JKOOX›Û™X	‰Š[
K‹[LJ_›
K˜Ú[LJJ_YOYKœÚX›[™ß_Y[˜Ý[Ûˆ[
K
^ÚYŠKYÏOOLÌ
^Ý˜\ˆYKœÝ]S›ÙKYK›Y[[Ú^™Y›ÜËOVœŠ‹ŠKOIŠ‹™Y˜][‹œZ\™YÜ‹œÚ\™Nœ‹™[\ŠNØOOOX›Û™XÜ›
JN™[
KKK[LJOÊ›
JK‹œZ\™Y]JK‹›Û‘[\ŠJN››
K˜Ú[LJ_Y[ÙHYŠKœÝX™YQ›YÜÉŒÌÍMMÌŠY›ÜŠOYK˜Ú[ÙHOO[[ÊZ[
K
KOYKœÚX›[™ÎÙ[ÙH›
J_Y[˜Ý[Ûˆ[
J^ÚYŠÈOO[[	‰–ËœÚ^™HOOL
^Ý˜\ˆVÎÚYŠKœÝX™YQ›YÜÉŒNÍÍŽ
Y›ÜŠOYK˜Ú[ÙHOO[[Ê^ÚYŠKYÈOOLŒŸK›Y[[Ú^™YÝ]OOO[[
^ÚYŠKYÏOOLÌ	‰™K™›YÜÉŒNÍÍŽ
^Ý˜\ˆYK›Y[[Ú^™Y›ÜË[‹›˜[YNÚYŠˆO[[	‰œˆOOX]]Ø
^Ý˜\ˆO]™Ù]
ŠNÚYŠHOO]›ÚY
^Ý˜\ˆOIŠ‹™Y˜][‹œÚ\™JNÚYŠHOOX›Û™X	‰Š[
K‹K[LJOÊOYKœÝ]S›ÙKKœZ\™YXKKœZ\™YZK]JK‹›Û”Ú\™JJN››
K˜Ú[LJJK™[]JŠKœÚ^™OOOL
Xœ™XZß__X[
J_YOYKœÚX›[™ß__Y[˜Ý[ÛˆÛ
J^ÚYŠKYÏOOLÌ
^Ý˜\ˆYK›Y[[Ú^™Y›ÜËVœŠKœÝ]S›ÙJKVÏOO[[Ý›ÚY–Ë™Ù]
ŠKOIŠ™Y˜][OO]›ÚYÝ™^]œÚ\™JNÚHOOX›Û™X	‰Š[
K‹K[LJOÜOO]›ÚYÕ]JK›Û‘^]
NŠOYKœÝ]S›ÙK‹œZ\™YZKKœZ\™Y\‹Ë™[]JŠK]JK›Û”Ú\™JJN››
K˜Ú[LJJKÈOO[[	‰˜[
J_Y[ÙHYŠKœÝX™YQ›YÜÉŒÌÍMMÌŠY›ÜŠOYK˜Ú[ÙHOO[[Ê[Û
JKOYKœÚX›[™ÎÙ[ÙHÈOO[[	‰˜[
J_Y[˜Ý[ÛˆÛ
J^Ù›ÜŠOYK˜Ú[ÙHOO[[Ê^ÚYŠKYÏOOLÌ
^Ý˜\ˆYK›Y[[Ú^™Y›ÜËVœŠKœÝ]S›ÙJNÝIŠ™Y˜][\]JKK™›YÜÉKMKOOX›Û™X	‰™[
K‹K›Y[[Ú^™YÝ]OV×KLJ_Y[ÙHKœÝX™YQ›YÜÉŒÌÍMMÌ‰‰œÛ
JNÙOYKœÚX›[™ß_Y[˜Ý[ÛˆÛ
J^ÚYŠKœÝX™YQ›YÜÉŒNÍÍŽ
Y›ÜŠOYK˜Ú[ÙHOO[[Ê^ÚYŠKYÈOOLŒŸK›Y[[Ú^™YÝ]OOO[[
^ÚYŠKYÏOOLÌ	‰™K™›YÜÉŒNÍÍŽ
^Ý˜\ˆYKœÝ]S›ÙNÝœZ\™YOO[[	‰ŠœZ\™Y[[›
K˜Ú[LJJ_XÛ
J_YOYKœÚX›[™ß_Y[˜Ý[Ûˆ
J^ÚYŠKYÏOOLÌ
YKœÝ]S›ÙKœZ\™Y[[›
K˜Ú[LJKÛ
JNÙ[ÙHYŠKœÝX™YQ›YÜÉŒÌÍMMÌŠY›ÜŠOYK˜Ú[ÙHOO[[Ê[
JKOYKœÚX›[™ÎÙ[ÙHÛ
J_Y[˜Ý[Ûˆ™YJJ^Ù›ÜŠOYK˜Ú[ÙHOO[[ÊYKYÏOOLÌÛ›
K˜Ú[LJN™KœÝX™YQ›YÜÉŒÌÍMMÌ‰‰’™YJJKOYKœÚX›[™ßY[˜Ý[Ûˆ[
K‹‹KKÊ^Ù›ÜŠ˜\ˆÏHLNÝOO[[Ê^ÚYŠYÏOOMJ^Ý˜\ˆ]œÝ]S›ÙNÚYŠHOO[[	‰‰ÏK›[™Ý
^Ý˜\ˆOXVÉ×K]™Š
NÊKšY]ßšY]ÊI‰ŠÏHL
NÝ˜\ˆŽÚYŠJK™›YÜÉ
OOL
ZYŠ˜Û\
YHLÙ[Ù^Ù]Kœ™XÝÝ˜\ˆYœ™XÝÙY‹žHOO\ž_‹žOO\ž‹šZYÚOO\šZYÚ‹ÚYOO\ÚYY‰‰ŠK™›YÜßM
K˜XœÏÙH]K˜XœÎŠO]Kœ™XÝYœ™XÝ]KšZYÚOOYšZYÚKÚYOOYÚY
K	‰ŠK™›YÜßLÌŠ_Y[ÙHK™›YÜßLÌŽÙK™›YÜÉ	‰˜J	ÏOOLÛŽ›ŠØØ
ÉËJKÉ‰™K™›YÜÉ
XÏOO[[	‰ŠXÏV×JKXËœ\Ú
	ÏOOLÜŽœŠØØ
ÉË›Y[[Ú^™Y›ÜÊJK	ÊÊßY[ÙJYÈOOLŒŸ›Y[[Ú^™YÝ]OOO[[
I‰ŠYÏOOLÌ	‰›ÏÙK™›YÜß]™›YÜÉŒÌŽ[
K˜Ú[‹‹KKÊI‰ŠÏHL
JNÝ]œÚX›[™ß\™]\›ˆßY[˜Ý[ÛˆYYJK
^Ù›ÜŠOYK˜Ú[ÙHOO[[Ê^ÚYŠKYÏOOLÌ
^Ý˜\ˆYK›Y[[Ú^™Y›ÜËYKœÝ]S›ÙKOVœŠ‹ŠKOIŠ‹™Y˜][‹\]JNÚYŠ
^Ü\‹˜ÛÛ™\ÎÝ˜\ˆÏ\OO[[Û[œ‹›X\
ÝJ_Y[ÙHÏYK›Y[[Ú^™YÝ]KK›Y[[Ú^™YÝ]O[[ÜYNÝ˜\ˆÏYK˜Ú[ÉÏLO][
‹ËKKKËLJKK™›YÜÉ	‰šI‰Š]JK‹›Û•\]JJ_Y[ÙHKœÝX™YQ›YÜÉŒÌÍMMÌ‰‰–YYJK
NÙOYKœÚX›[™ß_]˜\ˆHLK›HLKHLK[HLK]\[ÙˆÙXZÔÙ]OX[˜Ý[Û˜ÕÙXZÔÙ]”Ù]Û[[ÛHLK›HLK[HLK›HLNÙ[˜Ý[Ûˆ
KŠ^ÚYŠOYK˜ÛÛZ[™\’[™›Ë™ZÜOP\ŠJKœŠJJ^ÚYŠÙ[XÝ[Û”Ý\[ˆJ]˜\ˆ^ÜÝ\™KœÙ[XÝ[Û”Ý\[™™KœÙ[XÝ[Û‘[™NÙ[ÙHNžÜJYK›ÝÛ™\‘ØÝ[Y[
I‰œ‹™Y˜][šY]ßÚ[™ÝÎÝ˜\ˆO\‹™Ù]Ù[XÝ[Û‰‰œ‹™Ù]Ù[XÝ[ÛŠ
NÚYŠI‰šKœ˜[™ÙPÛÝ[OOL
^ÜZK˜[˜ÚÜ“›ÙNÝ˜\ˆOZK˜[˜ÚÜ“Ù™œÙ]ÏZK™›ØÝ\Ó›ÙNÚOZK™›ØÝ\ÓÙ™œÙ]Ýž^Ü‹››ÙU\KË››ÙU\_XØ]ÚÜ[[Øœ™XZÈ_]˜\ˆÏLKLKOKLKLLYKO[[ØŽ™›ÜŠÎÊ^Ù›ÜŠ˜\ˆÜOO\ŸHOOL	‰œ››ÙU\HOOLß
\ÊØJKOO[ßHOOL	‰œ››ÙU\HOOLß
O\ÊÚJK››ÙU\OOOLÉ‰ŠÊÏ\››ÙU˜[YK›[™Ý
K
\™š\œÝÚ[
HOO[[Ê[O\ZÙ›ÜŠÎÊ^ÚYŠOOYJXœ™XZÈŽÚYŠOOO\‰‰ŠÊÙOOXI‰Š\ÊKOOO[É‰ŠÊÙOOZI‰ŠO\ÊK
\›™^ÚX›[™ÊHOO[[
Xœ™XZÎÜ[KO\œ\™[›Ù_\Z\[OOKL_OOOKLOÛ[žÜÝ\›[™__Y[ÙH[[\Ÿ^ÜÝ\Œ[™Œ_Y[ÙH[[Ù›ÜŠ™^Ù›ØÝ\ÙY[[N™KÙ[XÝ[Û”˜[™ÙNœŸKÜHLKJ‰ŒÌÍMM
OOO[‹Û][ÎLÌŒLÙÛOO[[Ê^ÚYŠOYÛ‰‰ŠYK™[][ÛœËˆOO[[
JY›ÜŠOLØO‹›[™ÝØJÊÊ[‰‰›Û
–ØWJNÚYŠK˜[\›˜]OOO[[	‰™K™›YÜÉŒŠ[‰‰–˜ÊJKÛ
ŠNÙ[Ù^ÚYŠKYÏOOLŒŠ^ÚYŠYK˜[\›˜]KK›Y[[Ú^™YÝ]HOO[[
^ÜˆOO[[	‰œ‹›Y[[Ú^™YÝ]OOO[[	‰›‰‰›Û
ŠKÛ
ŠNØÛÛ[Y_Y[ÙHYŠˆOO[[	‰œ‹›Y[[Ú^™YÝ]HOO[[
^Û‰‰–˜ÊJKÛ
ŠNØÛÛ[Y__\YK˜Ú[
KœÝX™YQ›YÜÉ
HOOL	‰œˆOO[[Ê‹œ™]\›YKÛ\ŠNŠ‰‰œÛ
JKÛ
ŠJ__VÏ[[Y[˜Ý[ÛˆÛ
J^Ù›ÜŠÙÛOO[[Ê^Ý˜\ˆYÛYK]˜[\›˜]KO]™›YÜÎÜÝÚ]Ú
YÊ^ØØ\ÙH˜Ø\ÙHLN˜Ø\ÙHMN˜œ™XZÎØØ\ÙHNšYŠIŒL	‰œˆOO[[
^Û]›ÚYO\‹›Y[[Ú^™Y›ÜË\‹›Y[[Ú^™YÝ]NÝ˜\ˆÏ]œÝ]S›ÙNÝž^Ý˜\ˆÏUœÊ\KJNÛ[Ë™Ù]Û˜\ÚÝ™Y›Ü™U\]JËŠKË—×Ü™XXÝ[\›˜[Û˜\ÚÝ™Y›Ü™U\]O[ŸXØ]Ú
J^Ý™
œ™]\›‹J__Xœ™XZÎØØ\ÙHÎšYŠIŒL
^ÚYŠ]œÝ]S›ÙK˜ÛÛZ[™\’[™›Ë\‹››ÙU\KOONJSYŠŠNÙ[ÙHYŠOOLJ\ÝÚ]Ú
‹››ÙS˜[YJ^ØØ\ÙXPQ˜Ø\ÙXS˜Ø\ÙX“ÑX“YŠŠNØœ™XZÎÙY˜][œ‹^ÛÛ[X_Xœ™XZÎØØ\ÙHN˜Ø\ÙHŽ˜Ø\ÙHÎ˜Ø\ÙHŽ˜Ø\ÙH˜Ø\ÙHMÎ˜œ™XZÎØØ\ÙHÌ›‰‰œˆOO[[	‰ŠVœŠ‹›Y[[Ú^™Y›ÜË‹œÝ]S›ÙJKO]›Y[[Ú^™Y›ÜËOIŠK™Y˜][K\]JKHOOX›Û™X	‰™[
‹‹K‹›Y[[Ú^™YÝ]OV×KL
JNØœ™XZÎÙY˜][šYŠIŒL
]›ÝÈ\œ›ÜŠJMŒÊJ_ZYŠ]œÚX›[™ËˆOO[[
^Ü‹œ™]\›]œ™]\›‹Û\ŽØœ™XZßYÛ]œ™]\›Ÿ_Y[˜Ý[ÛˆYJKŠ^Ý˜\ˆ[‹™›YÜÎÜÝÚ]Ú
‹YÊ^ØØ\ÙH˜Ø\ÙHLN˜Ø\ÙHMN•›
KŠK‰	‰”ÊKŠNØœ™XZÎØØ\ÙHNšYŠ›
KŠK‰
ZYŠO[‹œÝ]S›ÙKOO[[
]ž^ÙK˜ÛÛ\Û™[Y[Ý[

_XØ]Ú
J^Ý™
‹‹œ™]\›‹J_Y[Ù^Ý˜\ˆOUœÊ‹\K›Y[[Ú^™Y›ÜÊNÝ]›Y[[Ú^™YÝ]NÝž^ÙK˜ÛÛ\Û™[Y\]JKK—×Ü™XXÝ[\›˜[Û˜\ÚÝ™Y›Ü™U\]J_XØ]Ú
J^Ý™
‹‹œ™]\›‹J__\‰	‰’XÊŠK‰LL‰‰”˜Ê‹‹œ™]\›ŠNØœ™XZÎØØ\ÙHÎšYŠ›
KŠK‰	‰ŠO[‹\]T]Y]YKHOO[[
J^ÚYŠ[[‹˜Ú[OO[[
\ÝÚ]Ú
‹˜Ú[YÊ^ØØ\ÙHÎ˜Ø\ÙHN[‹˜Ú[œÝ]S›ÙNØœ™XZÎØØ\ÙHN[‹˜Ú[œÝ]S›Ù_]ž^ÕYJK
_XØ]Ú
J^Ý™
‹‹œ™]\›‹J__Xœ™XZÎØØ\ÙHÎOO[[	‰œ‰	‰’ÙYJŠNØØ\ÙHŽ˜Ø\ÙHN•›
KŠKOO[[	‰œ‰	‰•ØÊŠK‰LL‰‰”˜Ê‹‹œ™]\›ŠNØœ™XZÎØØ\ÙHLŽ•›
KŠNØœ™XZÎØØ\ÙHÌN•›
KŠK‰	‰[
KŠNØœ™XZÎØØ\ÙHLÎ•›
KŠK‰	‰š›
KŠK‰	‰ŠO[‹›Y[[Ú^™YÝ]KHOO[[	‰ŠOYK™ZY˜]YHOO[[	‰Š^˜š[™
[ŠKJKŠJJJNØœ™XZÎØØ\ÙHŒŽšYŠ[‹›Y[[Ú^™YÝ]HOO[[\Š^Ý˜\ˆO]OO[[	‰›Y[[Ú^™YÝ]HOO[[›ÝYOY›\‹
›XJI‰ˆZOÊL‹‹œÝX™YQ›YÜÉŽÍÌ‰‰ŠŸLJK[
K‹ŠJN•›
KŠK]›Z_Xœ™XZÎØØ\ÙHÌ•›
KŠK‰LL‰‰”˜Ê‹‹œ™]\›ŠNØœ™XZÎØØ\ÙHÎœ‰LL‰‰”˜Ê‹‹œ™]\›ŠNÙY˜][•›
KŠ__Y[˜Ý[ÛˆÛ
K
^Ù›ÜŠOYK˜Ú[ÙHOO[[ÊV™YJK
KOYKœÚX›[™ßY[˜Ý[Ûˆ™YJK
^ÜÝÚ]Ú
KYÊ^ØØ\ÙHN˜Ø\ÙHŽž^Ý˜\ˆYKœÝ]S›ÙNÚYŠ
^Ý˜\ˆ[‹œÝ[NÝ\[Ùˆ‹œÙ]›Ü\OOX[˜Ý[Û˜Ü‹œÙ]›Ü\J\Ü^X›Û™X[\Ü[
Nœ‹™\Ü^OX›Û™XY[Ù^Ý˜\ˆOYKœÝ]S›ÙKOYK›Y[[Ú^™Y›ÜËœÝ[KÏXHO[[	‰˜Kš\ÓÝÛ”›Ü\J\Ü^X
OØK™\Ü^N›[ÚKœÝ[K™\Ü^O[ÏO[[\[ÙˆÏOX›ÛÛX[˜ØŠ
ÛÊKš[J
__XØ]Ú

^Ý™
KKœ™]\›‹
_]Û
K
NØœ™XZÎØØ\ÙHŽž^ÙKœÝ]S›ÙK››ÙU˜[YO]Ø™K›Y[[Ú^™Y›ÜË]HLXØ]Ú

^Ý™
KKœ™]\›‹
_Xœ™XZÎØØ\ÙHNž^Ý˜\ˆÏYKœÝ]S›ÙNÝÙÙŠËL
N™ÙŠKœÝ]S›ÙKLJ_XØ]Ú

^Ý™
KKœ™]\›‹
_Xœ™XZÎØØ\ÙHŒŽ˜Ø\ÙHŒÎ™K›Y[[Ú^™YÝ]OOO[[	‰Û
K
NØœ™XZÎÙY˜][Û
K
__Y[˜Ý[ÛˆÛ
K
^ÚYŠKœÝX™YQ›YÜÉÌL
Y›ÜŠOYK˜Ú[ÙHOO[[Ê^ØNžÝ˜\ˆYK]ÜÝÚ]Ú
‹YÊ^ØØ\ÙH–™YJ‹ŠNØœ™XZÈNØØ\ÙHŒŽ›‹›Y[[Ú^™YÝ]OOO[[	‰Û
‹ŠNØœ™XZÈNÙY˜][Û
‹Š__YOYKœÚX›[™ß_Y[˜Ý[Ûˆ
J^Ý˜\ˆYK˜[\›˜]NÝOO[[	‰ŠK˜[\›˜]O[[

JKK˜Ú[[[K™[][ÛœÏ[[KœÚX›[™Ï[[KYÏOOMI‰ŠYKœÝ]S›ÙKOO[[	‰“Ý

JKKœÝ]S›ÙO[[Kœ™]\›[[K™\[™[˜ÚY\Ï[[K›Y[[Ú^™Y›ÜÏ[[K›Y[[Ú^™YÝ]O[[Kœ[™[™Ô›ÜÏ[[KœÝ]S›ÙO[[K\]T]Y]YO[[]˜\ˆ[[[HLNÙ[˜Ý[ÛˆÛ
KŠ^Ù›ÜŠ[‹˜Ú[ÛˆOO[[ÊZÛ
KŠK[‹œÚX›[™ßY[˜Ý[ÛˆÛ
KŠ^ÚYŠYI‰\[ÙˆYK›ÛÛÛ[Z]šX™\•[›[Ý[OX[˜Ý[Û˜
]ž^ÜYK›ÛÛÛ[Z]šX™\•[›[Ý[
ÙKŠ_XØ]Úß\ÝÚ]Ú
‹YÊ^ØØ\ÙHŽ™›˜Ê‹
KÛ
KŠK‹›Y[[Ú^™YÝ]OÛ‹›Y[[Ú^™YÝ]K˜ÛÝ[KN›‹œÝ]S›ÙI‰ˆY›	‰Š[‹œÝ]S›ÙK‹œ\™[›ÙKœ™[[Ý™PÚ[
ŠJNØœ™XZÎØØ\ÙHÎ™›˜Ê‹
K˜ÊŠNÝ˜\ˆQ[OQÛYŠ‹\JI‰Š[[‹œÝ]S›ÙKHLJKÛ
KŠKYŠ‹œÝ]S›ÙK‹\K‹›Y[[Ú^™Y›ÜÊK[\‹ZNØœ™XZÎØØ\ÙHN™›˜Ê‹
K˜ÊŠNØØ\ÙHŽšYŠ‹YÏOOM‰‰•˜ÊŠKQ[OQ[[[Û
KŠK[\‹ZK[OO[[
ZYŠ
]ž^Ê[››ÙU\OOONOÑ[˜›ÙN‘[››ÙS˜[YOOOXSÑ[›ÝÛ™\‘ØÝ[Y[˜›ÙN‘[
Kœ™[[Ý™PÚ[
‹œÝ]S›ÙJK]HLXØ]Ú
J^Ý™
‹J_Y[ÙHž^Ñ[œ™[[Ý™PÚ[
‹œÝ]S›ÙJK]HLXØ]Ú
J^Ý™
‹J_Xœ™XZÎØØ\ÙHN‘[OO[[	‰ŠÊOQ[ŠK››ÙU\OOONOÙK˜›ÙN™K››ÙS˜[YOOOXSÙK›ÝÛ™\‘ØÝ[Y[˜›ÙN™K‹œÝ]S›ÙJKœ
JJNšŠ[‹œÝ]S›ÙJJNØœ™XZÎØØ\ÙHœQ[OQ[[‹œÝ]S›ÙK˜ÛÛZ[™\’[™›ËHLÛ
KŠK[\‹ZNØœ™XZÎØØ\ÙH˜Ø\ÙHLN˜Ø\ÙHM˜Ø\ÙHMN‘˜Ê‹‹
K›˜Ê‹
KÛ
KŠNØœ™XZÎØØ\ÙHN™›
˜Ê‹
K[‹œÝ]S›ÙK\[Ùˆ‹˜ÛÛ\Û™[Ú[[›[Ý[OX[˜Ý[Û˜	‰“Ê‹ŠJKÛ
KŠNØœ™XZÎØØ\ÙHŒN“Û
KŠNØœ™XZÎØØ\ÙHŒŽ™›JY›
_‹›Y[[Ú^™YÝ]HOO[[Û
KŠK›\ŽØœ™XZÎØØ\ÙHÌž˜Ê‹
KÛ
KŠNØœ™XZÎØØ\ÙHÎ™›˜Ê‹
KÛ
KŠNØœ™XZÎÙY˜][“Û
KŠ__Y[˜Ý[Ûˆ[
K
^ÚYŠ›Y[[Ú^™YÝ]OOO[[	‰ŠO]˜[\›˜]KHOO[[	‰ŠOYK›Y[[Ú^™YÝ]KHOO[[
JJ^ÙOYK™ZY˜]YÝž^Öœ
J_XØ]Ú
J^Ý™
œ™]\›‹J___Y[˜Ý[Ûˆ›
K
^ÚYŠ›Y[[Ú^™YÝ]OOO[[	‰ŠO]˜[\›˜]KHOO[[	‰ŠOYK›Y[[Ú^™YÝ]KHOO[[	‰ŠOYK™ZY˜]YHOO[[
JJJ]ž^Öœ
J_XØ]Ú
J^Ý™
œ™]\›‹J__Y[˜Ý[Ûˆ[
J^ÜÝÚ]Ú
KYÊ^ØØ\ÙHÌN˜Ø\ÙHLÎ˜Ø\ÙHNN˜\ˆYKœÝ]S›ÙNÜ™]\›ˆOO[[	‰ŠYKœÝ]S›ÙO[™]È
KØØ\ÙHŒŽœ™]\›ˆOYKœÝ]S›ÙKYK—Ü™]žPØXÚKOO[[	‰ŠYK—Ü™]žPØXÚO[™]È
KÙY˜][›ÝÈ\œ›ÜŠJÍKKYÊJ__Y[˜Ý[Ûˆ›
K
^Ý˜\ˆS[
JNÝ™›Ü‘XXÚ
[˜Ý[ÛŠ
^ÚYŠ[‹š\Ê
J^Û‹˜Y

NÝ˜\ˆX]K˜š[™
[K
NÝ[Š‹Š__J_Y[˜Ý[Ûˆ
KŠ^Ý˜\ˆ]™[][ÛœÎÚYŠˆOO[[
Y›ÜŠ˜\ˆOLØO‹›[™ÝØJÊÊ^Ý˜\ˆÏ\–ØWKÏYK]O[ØN™›ÜŠÝHOO[[Ê^ÜÝÚ]Ú
KYÊ^ØØ\ÙHÎšYŠYŠK\JJ^Ñ[]KœÝ]S›ÙKHLNØœ™XZÈ_Xœ™XZÎØØ\ÙHN‘[]KœÝ]S›ÙKHLNØœ™XZÈNØØ\ÙHÎ˜Ø\ÙH‘[]KœÝ]S›ÙK˜ÛÛZ[™\’[™›ËHLØœ™XZÈ_]O]Kœ™]\›ŸZYŠ[OO[[
]›ÝÈ\œ›ÜŠJMŒ
JNÚÛ
ËÊK[[[HLKÏ[Ë˜[\›˜]KÈOO[[	‰ŠËœ™]\›[[
KËœ™]\›[[ZYŠœÝX™YQ›YÜÉŒLÎŠY›ÜŠ]˜Ú[ÝOO[[ÊR[
KŠK]œÚX›[™ß]˜\ˆ›[[Ù[˜Ý[Ûˆ[
KŠ^Ý˜\ˆYK˜[\›˜]KOYK™›YÜÎÜÝÚ]Ú
KYÊ^ØØ\ÙH˜Ø\ÙHLN˜Ø\ÙHM˜Ø\ÙHMNšYŠI	‰ŠYK\]T]Y]YK\OO[[Û[œ‹™]™[ËˆOO[[
JY›ÜŠ˜\ˆÏLÛÏ‹›[™ÝÛÊÊÊ^Ý˜\ˆÏ\–Û×NÜËœ™Y‹š[\\Ë›™^[\T
KŠK
JKI	‰Š˜ÊËKKœ™]\›ŠKÊËJK˜ÊKKKœ™]\›ŠJNØœ™XZÎØØ\ÙHN”
KŠK
JKILL‰‰Š›OO[[˜Ê‹‹œ™]\›ŠJKI	‰™	‰ŠOYK\]T]Y]YKHOO[[	‰ŠYK˜Ø[˜XÚÜËOO[[	‰ŠYKœÚ\™YšY[Ø[˜XÚÜËKœÚ\™YšY[Ø[˜XÚÜÏ[OO[[Ý›‹˜ÛÛ˜Ø]

JJJNØœ™XZÎØØ\ÙHŽšYŠÏQ›
KŠK
JKILL‰‰Š›OO[[˜Ê‹‹œ™]\›ŠJKI
ZYŠO\OO[[Û[œ‹›Y[[Ú^™YÝ]KYK›Y[[Ú^™YÝ]KOO[[
ZYŠOO[[
ZYŠKœÝ]S›ÙOOO[[
ZYŠ
YKœÝ]S›ÙO\ÙŠK\KK›Y[[Ú^™Y›ÜË˜ÛÛZ[™\’[™›ËJNÙ[Ù^ØNžÝYK\KYK›Y[[Ú^™Y›ÜËO[Ë›ÝÛ™\‘ØÝ[Y[ÎØŽœÝÚ]Ú

^ØØ\ÙX]XœXK™Ù][[Y[ÐžUYÓ˜[YJ]X
VÌK
\Ÿ–Ñ]_–Þ]_‹›˜[Y\ÜXÙUT’OOOX‹ËÝÝÝËÌË›Ü™ËÌŒÜÝ™Ø‹š\Ð]šX]J][\›Ü
JI‰ŠXK˜Ü™X]Q[[Y[

KKšXYš[œÙ\™Y›Ü™J‹Kœ]Y\žTÙ[XÝÜŠXYˆ]X
JJKYŠ‹ŠK–Þ]OYK
ŠK\ŽØœ™XZÈNØØ\ÙX[šØšYŠÏY
[šØ™Y˜JK™Ù]

Ê‹š™YŸ
JJ^Ù›ÜŠÏLÜÏË›[™ÝÜÊÊÊZYŠ[ÖÜ×K‹™Ù]]šX]J™Y˜
OOOJ‹š™YO[[‹š™YOOXÛ[›‹š™YŠI‰œ‹™Ù]]šX]J™[
OOOJ‹œ™[O[[Û[›‹œ™[
I‰œ‹™Ù]]šX]J]X
OOOJ‹]OO[[Û[›‹]JI‰œ‹™Ù]]šX]JÜ›ÜÜÛÜšYÚ[˜
OOOJ‹˜Ü›ÜÜÓÜšYÚ[O[[Û[›‹˜Ü›ÜÜÓÜšYÚ[ŠJ^ÛËœÜXÙJËJNØœ™XZÈŸ_\XK˜Ü™X]Q[[Y[

KYŠ‹ŠKKšXY˜\[™Ú[
ŠNØœ™XZÎØØ\ÙXY]XšYŠÏY
Y]XÛÛ[JK™Ù]

Ê‹˜ÛÛ[
JJ^Ù›ÜŠÏLÜÏË›[™ÝÜÊÊÊZYŠ[ÖÜ×K‹™Ù]]šX]JÛÛ[
OOOJ‹˜ÛÛ[O[[Û[˜
Û‹˜ÛÛ[
I‰œ‹™Ù]]šX]J˜[YX
OOOJ‹›˜[YOO[[Û[›‹›˜[YJI‰œ‹™Ù]]šX]J›Ü\X
OOOJ‹œ›Ü\OO[[Û[›‹œ›Ü\JI‰œ‹™Ù]]šX]JY\]Z]˜
OOOJ‹š\]Z]O[[Û[›‹š\]Z]ŠI‰œ‹™Ù]]šX]JÚ\œÙ]
OOOJ‹˜Ú\”Ù]O[[Û[›‹˜Ú\”Ù]
J^ÛËœÜXÙJËJNØœ™XZÈŸ_\XK˜Ü™X]Q[[Y[

KYŠ‹ŠKKšXY˜\[™Ú[
ŠNØœ™XZÎÙY˜][›ÝÈ\œ›ÜŠJŽ
J_\–Þ]OYK
ŠK\ŸYKœÝ]S›ÙO]Y[ÙHœ
ËK\KKœÝ]S›ÙJNÙ[ÙHKœÝ]S›ÙOQÝJË‹K›Y[[Ú^™Y›ÜÊNÙ[ÙHOOO[ÛOO[[	‰™KœÝ]S›ÙHOO[[	‰‘ØÊKK›Y[[Ú^™Y›ÜË‹›Y[[Ú^™Y›ÜÊNŠOOO[[Ê\‹œÝ]S›ÙKOO[[›œ\™[›ÙKœ™[[Ý™PÚ[

JN˜K˜ÛÝ[KKOO[[Ùœ
ËK\KKœÝ]S›ÙJN‘ÝJË‹K›Y[[Ú^™Y›ÜÊJNØœ™XZÎØØ\ÙHÎ”
KŠK
JKILL‰‰Š›OO[[˜Ê‹‹œ™]\›ŠJKˆOO[[	‰˜I	‰‘ØÊKK›Y[[Ú^™Y›ÜË‹›Y[[Ú^™Y›ÜÊNØœ™XZÎØØ\ÙHNšYŠÏ\HLK
KŠK[Ë
JKILL‰‰Š›OO[[˜Ê‹‹œ™]\›ŠJKK™›YÜÉŒÌŠ^ÝYKœÝ]S›ÙNÝž^ØÛŠ
K]HLXØ]Ú

^Ý™
KKœ™]\›‹
__XI	‰™KœÝ]S›ÙHO[[	‰ŠYK›Y[[Ú^™Y›ÜËØÊKOO[[Ýœ‹›Y[[Ú^™Y›ÜÊJKIŒL	‰Š[HL
NØœ™XZÎØØ\ÙHŽšYŠ
KŠK
JKI
^ÚYŠKœÝ]S›ÙOOO[[
]›ÝÈ\œ›ÜŠJMŒŠJNÝYK›Y[[Ú^™Y›ÜËYKœÝ]S›ÙNÝž^Û‹››ÙU˜[YO]]HLXØ]Ú

^Ý™
KKœ™]\›‹
__Xœ™XZÎØØ\ÙHÎšYŠ]HLK\[[ÏQ››\YŠ˜ÛÛZ[™\’[™›ÊK
KŠK›[Ë
JKI	‰œˆOO[[	‰œ‹›Y[[Ú^™YÝ]Kš\ÑZY˜]Y
]ž^Öœ
˜ÛÛZ[™\’[™›Ê_XØ]Ú

^Ý™
KKœ™]\›‹
_[[	‰Š[HLK›
JJK]HLNØœ™XZÎØØ\ÙH˜O\YUÝ

KÏQ››\YŠKœÝ]S›ÙK˜ÛÛZ[™\’[™›ÊK
KŠK
JK›[Ë]	‰›	‰Š[HL
K]\‹XNØœ™XZÎØØ\ÙHLŽ”
KŠK
JNØœ™XZÎØØ\ÙHÌN”
KŠK
JKI	‰ŠYK\]T]Y]YKOO[[	‰ŠK\]T]Y]YO[[›
K
JJNØœ™XZÎØØ\ÙHLÎ”
KŠK
JKK˜Ú[™›YÜÉŽNL‰‰™K›Y[[Ú^™YÝ]HOO[[OJˆOO[[	‰œ‹›Y[[Ú^™YÝ]HOO[[
I‰ŠOSJ
JKI	‰ŠYK\]T]Y]YKOO[[	‰ŠK\]T]Y]YO[[›
K
JJNØœ™XZÎØØ\ÙHŒŽ›ÏYK›Y[[Ú^™YÝ]HOO[[Ï\ˆOO[[	‰œ‹›Y[[Ú^™YÝ]HOO[[Ý˜\ˆYOY›\Ù[ËYË›]_Ë
KŠK›]KY[
JKIŽNL‰‰ŠYKœÝ]S›ÙK—Ýš\ÚXš[]O[ÏÝ—Ýš\ÚXš[]I‹LŽ—Ýš\ÚXš[]_K[ßOO[[ß›
\ß›YY›[ß›]
KŠK[‹›\ŠK[É‰œÛ
KÊJKI	‰ŠYK\]T]Y]YKOO[[	‰Š]œ™]žT]Y]YKˆOO[[	‰Šœ™]žT]Y]YO[[›
KŠJJJNØœ™XZÎØØ\ÙHNN”
KŠK
JKI	‰ŠYK\]T]Y]YKOO[[	‰ŠK\]T]Y]YO[[›
K
JJNØœ™XZÎØØ\ÙHÌ˜ILL‰‰Š›OO[[˜Ê‹‹œ™]\›ŠJKOUÝ

KÏ]›ÏJ‰ŒÌÍMM
OOO[‹YK›Y[[Ú^™Y›ÜË›\É‰‰Š™Y˜][\]JHOOX›Û™X
KŠK
JKÉ‰œˆOO[[	‰•]	‰ŠK™›YÜßM
K›[Ë]XNØœ™XZÎØØ\ÙHŒN˜œ™XZÎØØ\ÙHÎ˜ILL‰‰Š›OO[[˜Ê‹‹œ™]\›ŠJK‰‰œ‹œÝ]S›ÙHOO[[	‰Š‹œÝ]S›ÙK—Ùœ˜YÛY[šX™\YJNÙY˜][”
KŠK
J__Y[˜Ý[Ûˆ
J^Ý˜\ˆYK™›YÜÎÚYŠ	ŒŠ^Ýž^Ù›ÜŠ˜\ˆ‹YKœ™]\›ŽÜˆOO[[Ê^ÚYŠÙYJŠJ^Û\ŽØœ™XZß\\‹œ™]\›Ÿ\[[Ù›ÜŠ˜\ˆOYKœ™]\›ŽØHOO[[Ê^ÚYŠXÊJJ^Ý˜\ˆÏXKœÝ]S›ÙNÜOO[[ÜVÛ×Nœ‹œ\Ú
Ê_ZYŠÊJJXœ™XZÎØOXKœ™]\›Ÿ]˜\ˆÏ\ŽÚYŠO[[
]›ÝÈ\œ›ÜŠJMŒ
JNÜÝÚ]Ú
‹YÊ^ØØ\ÙHÎ˜\ˆ[‹œÝ]S›ÙNÒ˜ÊKØÊJKÊNØœ™XZÎØØ\ÙHN˜\ˆO[‹œÝ]S›ÙNÛ‹™›YÜÉŒÌ‰‰ŠÛŠK
K‹™›YÜÉKLÌÊK˜ÊKØÊJKKÊNØœ™XZÎØØ\ÙHÎ˜Ø\ÙH˜\ˆ[‹œÝ]S›ÙK˜ÛÛZ[™\’[™›ÎÜXÊKØÊJKÊNØœ™XZÎÙY˜][›ÝÈ\œ›ÜŠJMŒJJ__XØ]Ú

^Ý™
KKœ™]\›‹
_YK™›YÜÉKLß]	M‰‰ŠK™›YÜÉKMMÊ_Y[˜Ý[Ûˆ›
J^ÚYŠKœÝX™YQ›YÜÉŒL
Y›ÜŠOYK˜Ú[ÙHOO[[Ê^Ý˜\ˆYNÔ›

KYÏOOMI‰™›YÜÉŒL	‰Š]œÝ]S›ÙKÜHLœ™\Ù]

KÜHLJKOYKœÚX›[™ß_Y[˜Ý[Ûˆ›
K
^ÚYŠœÝX™YQ›YÜÉŽLÌ
Y›ÜŠ]˜Ú[ÝOO[[ÊP›
JK]œÚX›[™ÎÙ[ÙHYYJLJ_Y[˜Ý[Ûˆ›
K
^Ý˜\ˆYK˜[\›˜]NÚYŠOO[[
Z[
KLJNÙ[ÙHÝÚ]Ú
KYÊ^ØØ\ÙHÎšYŠ›WÛHLKYYJ
K›
JKWÛ	‰ˆ^[
^ÚYŠOTXËHOO[[
Y›ÜŠ˜\ˆLÜK›[™ÝÜŠÏLÊ^ÛYVÜ—NÝ˜\ˆOYVÜŠÌWN×ÙŠ‹VÜŠÌ—JK[‹›ÝÛ™\‘ØÝ[Y[™ØÝ[Y[[[Y[ˆOO[[	‰›‹˜[š[X]JÛÜXÚ]N–ÌKÚ[\‘]™[Î–Ø›Û™X›Û™X_KÙ\˜][ÛŽŒš[˜›ÜØ\™ØÙ]YÑ[[Y[˜ŽšY]Ë]˜[œÚ][Û‹YÜ›Ý\

ÚJØ
XJ_YO]˜ÛÛZ[™\’[™›ËOYK››ÙU\OOONOÙK™ØÝ[Y[[[Y[™K›ÝÛ™\‘ØÝ[Y[™ØÝ[Y[[[Y[HOO[[	‰™KœÝ[KšY]Õ˜[œÚ][Û“˜[YOOOX	‰ŠKœÝ[KšY]Õ˜[œÚ][Û“˜[YOX›Û™XK˜[š[X]JÛÜXÚ]N–ÌKÚ[\‘]™[Î–Ø›Û™X›Û™X_KÙ\˜][ÛŽŒš[˜›ÜØ\™ØÙ]YÑ[[Y[˜ŽšY]Ë]˜[œÚ][Û‹YÜ›Ý\
›ÛÝ
XJKK˜[š[X]JÝÚY–ÌKZYÚ–Ì_KÙ\˜][ÛŽŒš[˜›ÜØ\™ØÙ]YÑ[[Y[˜ŽšY]Ë]˜[œÚ][Û˜JJK›HLTXÏ[[Øœ™XZÎØØ\ÙHNž›
JNØœ™XZÎØØ\ÙHœWÛÛHLK›
JKÛ	‰Š[HL
KÛ\ŽØœ™XZÎØØ\ÙHŒŽ™K›Y[[Ú^™YÝ]OOO[[	‰Š‹›Y[[Ú^™YÝ]OOO[[Þ›
JNš[
KLJJNØœ™XZÎØØ\ÙHÌœWÛO\YYJ
KÛHLK›
JKÛ	‰ŠK™›YÜßM
NÝ˜\ˆOYK›Y[[Ú^™Y›ÜËÏYKœÝ]S›ÙNÝVœŠKÊKÏVœŠ‹›Y[[Ú^™Y›ÜËÊNÝ˜\ˆÏIŠK™Y˜][K\]JNÜÏOOX›Û™XÝHLNŠO[‹›Y[[Ú^™YÝ]K‹›Y[[Ú^™YÝ]O[[YK˜Ú[	ÏL][
K‹ËËKL
K	ÈOOJOOO[[Ì˜K›[™Ý
I‰ŠK™›YÜßLÌŠJKK™›YÜÉ	‰Ê]JKK›Y[[Ú^™Y›ÜË›Û•\]JKXÏZJNšHOO[[	‰ŠKœ\Ú˜\JKXÊKXÏZJKÛYK™›YÜÉŒÌÈLœŽØœ™XZÎÙY˜][ž›
J__Y[˜Ý[Ûˆ›
K
^ÚYŠœÝX™YQ›YÜÉŽÍÌŠY›ÜŠ]˜Ú[ÝOO[[ÊVYJK˜[\›˜]K
K]œÚX›[™ßY[˜Ý[Ûˆ
K
^Ù›ÜŠOYK˜Ú[ÙHOO[[Ê^Ý˜\ˆYK]ÜÝÚ]Ú
‹YÊ^ØØ\ÙH˜Ø\ÙHLN˜Ø\ÙHM˜Ø\ÙHMN‘˜Ê‹‹œ™]\›ŠK
‹ŠNØœ™XZÎØØ\ÙHNž˜Ê‹‹œ™]\›ŠNÝ˜\ˆO[‹œÝ]S›ÙNÝ\[ÙˆK˜ÛÛ\Û™[Ú[[›[Ý[OX[˜Ý[Û˜	‰“Ê‹‹œ™]\›‹JK
‹ŠNØœ™XZÎØØ\ÙHÎœ‰Œ‰‰•YŠ‹œÝ]S›ÙK‹\K‹›Y[[Ú^™Y›ÜÊNØØ\ÙHNž˜Ê‹‹œ™]\›ŠK‹YÈOOMI‰›‹YÈOOLß˜ÊŠK
‹ŠNØœ™XZÎØØ\ÙHŽ•˜ÊŠNØœ™XZÎØØ\ÙHŽž˜Ê‹‹œ™]\›ŠKO[‹œÝ]S›ÙK‹›Y[[Ú^™YÝ]HOO[[OOO[[›Kœ\™[›ÙKœ™[[Ý™PÚ[
JK
‹ŠNØœ™XZÎØØ\ÙHŒŽ›‹›Y[[Ú^™YÝ]OOO[[	‰’
‹ŠNØœ™XZÎØØ\ÙHÌž˜Ê‹‹œ™]\›ŠK
‹ŠNØœ™XZÎØØ\ÙHÎž˜Ê‹‹œ™]\›ŠNÙY˜][’
‹Š_YOYKœÚX›[™ß_Y[˜Ý[Ûˆ[
KŠ^Ù›ÜŠ]œÝX™YQ›YÜÉŽÍÌÛŽ›‰‹L‹]˜Ú[ÝOO[[Ê^Ý˜\ˆ]˜[\›˜]KOYKO]ÏXK™›YÜËÏJ‰ŒJHOLÜÝÚ]Ú
KYÊ^ØØ\ÙH˜Ø\ÙHLN˜Ø\ÙHMN•[
KKŠKÊJNØœ™XZÎØØ\ÙHNšYŠ[
KKŠKXKO\‹œÝ]S›ÙK\[ÙˆK˜ÛÛ\Û™[Y[Ý[OX[˜Ý[Û˜
]ž^ÚK˜ÛÛ\Û™[Y[Ý[

_XØ]Ú
J^Ý™
‹‹œ™]\›‹J_ZYŠXKO\‹\]T]Y]YKHOO[[
^Ý˜\ˆ\‹œÝ]S›ÙNÝž^Ý˜\ˆOZKœÚ\™YšY[Ø[˜XÚÜÎÚYŠHOO[[
Y›ÜŠKœÚ\™YšY[Ø[˜XÚÜÏ[[OLÚOK›[™ÝÚJÊÊ]ÙYJVÚWK
_XØ]Ú
J^Ý™
‹‹œ™]\›‹J__\É‰›É	‰’XÊJK˜ÊKKœ™]\›ŠNØœ™XZÎØØ\ÙHÎ›‰Œ‰‰’ÙYJJNØØ\ÙHN˜KYÈOOMI‰˜KYÈOOLßÙYJJK[
KKŠKÉ‰œOO[[	‰›É	‰•ØÊJK˜ÊKKœ™]\›ŠNØœ™XZÎØØ\ÙHŽ•ÙYJJNØœ™XZÎØØ\ÙHŽ›XKœÝ]S›ÙKK›Y[[Ú^™YÝ]HOO[[OO[[œ
YŠ›ÝÛ™\‘ØÝ[Y[
KK\K
K[
KKŠKÉ‰œOO[[	‰›É	‰•ØÊJK˜ÊKKœ™]\›ŠNØœ™XZÎØØ\ÙHLŽ•[
KKŠNØœ™XZÎØØ\ÙHÌN•[
KKŠKÉ‰›É	‰[
KJNØœ™XZÎØØ\ÙHLÎ•[
KKŠKÉ‰›É	‰š›
KJNØœ™XZÎØØ\ÙHŒŽ˜K›Y[[Ú^™YÝ]OOO[[	‰•[
KKŠK˜ÊKKœ™]\›ŠNØœ™XZÎØØ\ÙHÌ•[
KKŠK˜ÊKKœ™]\›ŠNØœ™XZÎØØ\ÙHÎ”˜ÊKKœ™]\›ŠNÙY˜][•[
KKŠ_]]œÚX›[™ß_Y[˜Ý[ÛˆÛ
K
^Ý˜\ˆ[[ÙHOO[[	‰™K›Y[[Ú^™YÝ]HOO[[	‰™K›Y[[Ú^™YÝ]K˜ØXÚTÛÛOO[[	‰ŠYK›Y[[Ú^™YÝ]K˜ØXÚTÛÛœÛÛ
KO[[›Y[[Ú^™YÝ]HOO[[	‰›Y[[Ú^™YÝ]K˜ØXÚTÛÛOO[[	‰ŠO]›Y[[Ú^™YÝ]K˜ØXÚTÛÛœÛÛ
KHOO[‰‰ŠHO[[	‰™Kœ™YÛÝ[
ÊËˆO[[	‰™JŠJ_Y[˜Ý[ÛˆÛ
K
^ÙO[[˜[\›˜]HOO[[	‰ŠO]˜[\›˜]K›Y[[Ú^™YÝ]K˜ØXÚJK]›Y[[Ú^™YÝ]K˜ØXÚKOOYI‰Šœ™YÛÝ[
ÊËHO[[	‰™JJJ_Y[˜Ý[ÛˆÛ
K‹Š^Ý˜\ˆOJ‰ŒÌÍMM
OOO[ŽÚYŠœÝX™YQ›YÜÉŠOÌLŒŽŒLMŠJY›ÜŠ]˜Ú[ÝOO[[Ê\[
K‹ŠK]œÚX›[™ÎÙ[ÙHI‰’™YJ
_Y[˜Ý[Ûˆ[
K‹Š^Ý˜\ˆOJ‰ŒÌÍMM
OOO[ŽÚI‰˜[\›˜]OOO[[	‰œ™]\›ˆOO[[	‰œ™]\›‹˜[\›˜]HOO[[	‰›

NÝ˜\ˆO]™›YÜÎÜÝÚ]Ú
YÊ^ØØ\ÙH˜Ø\ÙHLN˜Ø\ÙHMN’Û
K‹ŠKIŒŒ	‰”ÊK
NØœ™XZÎØØ\ÙHN’Û
K‹ŠNØœ™XZÎØØ\ÙHÎ’Û
K‹ŠKI‰˜›	‰ŠOYK˜ÛÛZ[™\’[™›ËOYK››ÙU\OOONOÙK˜›ÙN™K››ÙS˜[YOOOXSÙK›ÝÛ™\‘ØÝ[Y[˜›ÙN™KKœÝ[KšY]Õ˜[œÚ][Û“˜[YOOOX›ÛÝ	‰ŠKœÝ[KšY]Õ˜[œÚ][Û“˜[YOX
KOYK›ÝÛ™\‘ØÝ[Y[™ØÝ[Y[[[Y[HOO[[	‰™KœÝ[KšY]Õ˜[œÚ][Û“˜[YOOOX›Û™X	‰ŠKœÝ[KšY]Õ˜[œÚ][Û“˜[YOX
JKIŒŒ	‰ŠO[[˜[\›˜]HOO[[	‰ŠO]˜[\›˜]K›Y[[Ú^™YÝ]K˜ØXÚJK]›Y[[Ú^™YÝ]K˜ØXÚKOOXI‰Šœ™YÛÝ[
ÊËHO[[	‰™JJJJNØœ™XZÎØØ\ÙHLŽšYŠIŒŒ
^ÒÛ
K‹ŠKO]œÝ]S›ÙNÝž^Ý˜\ˆÏ]›Y[[Ú^™Y›ÜËÏ[ËšY[Ë›Û”ÜÝÛÛ[Z]Ý\[ÙˆOX[˜Ý[Û˜	‰›
Ë˜[\›˜]OOO[[Ø[Ý[˜\]XKœ\ÜÚ]™QY™™XÝ\˜][Û‹L
_XØ]Ú
J^Ý™
œ™]\›‹J__Y[ÙHÛ
K‹ŠNØœ™XZÎØØ\ÙHÌN’Û
K‹ŠNØœ™XZÎØØ\ÙHLÎ’Û
K‹ŠNØœ™XZÎØØ\ÙHŒÎ˜œ™XZÎØØ\ÙHŒŽ›Ï]œÝ]S›ÙKÏ]˜[\›˜]K›Y[[Ú^™YÝ]OOO[[ÊI‰œÈOO[[	‰œË›Y[[Ú^™YÝ]HOO[[	‰›

KË—Ýš\ÚXš[]IŒÒÛ
K‹ŠNŠË—Ýš\ÚXš[]_L‹›
K‹‹
œÝX™YQ›YÜÉŒLMŠHOLLJJJNŠI‰œÈOO[[	‰œË›Y[[Ú^™YÝ]OOO[[	‰›
ÊKË—Ýš\ÚXš[]IŒÒÛ
K‹ŠN–[
K
JKIŒŒ	‰•Û
Ë
NØœ™XZÎØØ\ÙH’Û
K‹ŠKIŒŒ	‰‘Û
˜[\›˜]K
NØœ™XZÎØØ\ÙHÌšI‰ŠO]˜[\›˜]KHOO[[	‰Š›
K˜Ú[L
K›
˜Ú[L
JJKÛ
K‹ŠNØœ™XZÎÙY˜][’Û
K‹Š__Y[˜Ý[Ûˆ›
K‹‹J^Ù›ÜŠI‰JœÝX™YQ›YÜÉŒLMŠHOLLK]˜Ú[ÝOO[[Ê^Ý˜\ˆOYKÏ]Ï[‹\‹O[Ë™›YÜÎÜÝÚ]Ú
ËYÊ^ØØ\ÙH˜Ø\ÙHLN˜Ø\ÙHMN’›
KËËJKÊÊNØœ™XZÎØØ\ÙHŒÎ˜œ™XZÎØØ\ÙHŒŽ˜\ˆ[ËœÝ]S›ÙNÛË›Y[[Ú^™YÝ]OOO[[Ê—Ýš\ÚXš[]_L‹›
KËËJJN™—Ýš\ÚXš[]IŒÒ›
KËËJN–[
KÊKI‰IŒŒ	‰•Û
Ë˜[\›˜]KÊNØœ™XZÎØØ\ÙH’›
KËËJKI‰IŒŒ	‰‘Û
Ë˜[\›˜]KÊNØœ™XZÎÙY˜][’›
KËËJ_]]œÚX›[™ß_Y[˜Ý[Ûˆ[
K
^ÚYŠœÝX™YQ›YÜÉŒLMŠY›ÜŠ]˜Ú[ÝOO[[Ê^Ý˜\ˆYK]O\‹™›YÜÎÜÝÚ]Ú
‹YÊ^ØØ\ÙHŒŽ–[
‹ŠKIŒŒ	‰•Û
‹˜[\›˜]KŠNØœ™XZÎØØ\ÙH–[
‹ŠKIŒŒ	‰‘Û
‹˜[\›˜]KŠNØœ™XZÎÙY˜][–[
‹Š_]]œÚX›[™ß_]˜\ˆNNLŽÙ[˜Ý[Ûˆ›
KŠ^ÚYŠKœÝX™YQ›YÜÉ–
Y›ÜŠOYK˜Ú[ÙHOO[[ÊT[
KŠKOYKœÚX›[™ßY[˜Ý[Ûˆ[
KŠ^ÜÝÚ]Ú
KYÊ^ØØ\ÙHŽ–›
KŠKK™›YÜÉ–	‰ŠK›Y[[Ú^™YÝ]OOO[[ÊOYKœÝ]S›ÙK
	ŒÌÍMMLŽ
OOO]	‰—Ü
‹JJN’ÝJ‹›K›Y[[Ú^™YÝ]KK›Y[[Ú^™Y›ÜÊJNØœ™XZÎØØ\ÙHN–›
KŠKK™›YÜÉ–	‰ŠOYKœÝ]S›ÙK
	ŒÌÍMMLŽ
OOO]	‰—Ü
‹JJNØœ™XZÎØØ\ÙHÎ˜Ø\ÙH˜\ˆQ›Ñ›\YŠKœÝ]S›ÙK˜ÛÛZ[™\’[™›ÊK›
KŠK›\ŽØœ™XZÎØØ\ÙHŒŽ™K›Y[[Ú^™YÝ]OOO[[	‰ŠYK˜[\›˜]KˆOO[[	‰œ‹›Y[[Ú^™YÝ]HOO[[ÊVLMÍÍÌŒM‹›
KŠK\ŠN–›
KŠJNØœ™XZÎØØ\ÙHÌšYŠ
K™›YÜÉ–
HOOL	‰ŠYK›Y[[Ú^™Y›ÜË›˜[YKˆO[[	‰œˆOOX]]Ø
J^Ý˜\ˆOYKœÝ]S›ÙNÚKœZ\™Y[[ÏOO[[	‰ŠÏ[™]ÈX\
KËœÙ]
‹J_V›
KŠNØœ™XZÎÙY˜][–›
KŠ__Y[˜Ý[Ûˆ	
J^Ý˜\ˆYK˜[\›˜]NÚYŠOO[[	‰ŠO]˜Ú[HOO[[
J^Ý˜Ú[[[ÙÈYKœÚX›[™ËKœÚX›[™Ï[[O]ÝÚ[JHOO[[
__Y[˜Ý[Ûˆ]JJ^Ý˜\ˆYK™[][ÛœÎÚYŠK™›YÜÉŒMŠ^ÚYŠOO[[
Y›ÜŠ˜\ˆLÛ›[™ÝÛŠÊÊ^Ý˜\ˆ]Û—NÙÛ\‹J‹J_I
J_ZYŠKœÝX™YQ›YÜÉŒLMŠY›ÜŠOYK˜Ú[ÙHOO[[Ê]JJKOYKœÚX›[™ßY[˜Ý[ÛˆJJ^ÜÝÚ]Ú
KYÊ^ØØ\ÙH˜Ø\ÙHLN˜Ø\ÙHMN™]JJKK™›YÜÉŒŒ	‰‘˜ÊKKKœ™]\›ŠNØœ™XZÎØØ\ÙHÎ™]JJNØœ™XZÎØØ\ÙHLŽ™]JJNØœ™XZÎØØ\ÙHŒŽ˜\ˆYKœÝ]S›ÙNÙK›Y[[Ú^™YÝ]HOO[[	‰—Ýš\ÚXš[]IŒ‰‰ŠKœ™]\›OO[[Kœ™]\›‹YÈOOLLÊOÊ—Ýš\ÚXš[]IKLËJJJN™]JJNØœ™XZÎÙY˜][™]JJ__Y[˜Ý[ÛˆJJ^Ý˜\ˆYK™[][ÛœÎÚYŠK™›YÜÉŒMŠ^ÚYŠOO[[
Y›ÜŠ˜\ˆLÛ›[™ÝÛŠÊÊ^Ý˜\ˆ]Û—NÙÛ\‹J‹J_I
J_Y›ÜŠOYK˜Ú[ÙHOO[[Ê^ÜÝÚ]Ú
YKYÊ^ØØ\ÙH˜Ø\ÙHLN˜Ø\ÙHMN‘˜Êœ™]\›ŠKJ
NØœ™XZÎØØ\ÙHŒŽ›]œÝ]S›ÙK‹—Ýš\ÚXš[]IŒ‰‰Š‹—Ýš\ÚXš[]IKLËJ
JNØœ™XZÎÙY˜][›J
_YOYKœÚX›[™ß_Y[˜Ý[ÛˆJK
^Ù›ÜŠÙÛOO[[Ê^Ý˜\ˆYÛÜÝÚ]Ú
‹YÊ^ØØ\ÙH˜Ø\ÙHLN˜Ø\ÙHMN‘˜Ê‹
NØœ™XZÎØØ\ÙHŒÎ˜Ø\ÙHŒŽšYŠ‹›Y[[Ú^™YÝ]HOO[[	‰›‹›Y[[Ú^™YÝ]K˜ØXÚTÛÛOO[[
^Ý˜\ˆ[‹›Y[[Ú^™YÝ]K˜ØXÚTÛÛœÛÛÜˆO[[	‰œ‹œ™YÛÝ[
ÊßXœ™XZÎØØ\ÙH™J‹›Y[[Ú^™YÝ]K˜ØXÚJ_ZYŠ[‹˜Ú[ˆOO[[
\‹œ™]\›[‹Û\ŽÙ[ÙHN™›ÜŠYNÙÛOO[[Ê^ÜYÛÝ˜\ˆO\‹œÚX›[™ËO\‹œ™]\›ŽÚYŠ
ŠKOO[Š^ÙÛ[[Øœ™XZÈ_ZYŠHOO[[
^ÚKœ™]\›XKÛZNØœ™XZÈ_YÛX___]˜\ˆ]O^ÙÙ]ØXÚQ›Ü•\N™[˜Ý[ÛŠJ^Ý˜\ˆZXJJK]™]K™Ù]
JNÜ™]\›ˆOO]›ÚY	‰ŠYJ
K™]KœÙ]
KŠJKŸKØXÚTÚYÛ˜[™[˜Ý[ÛŠ
^Ü™]\›ˆXJJK˜ÛÛ›Û\‹œÚYÛ˜[_K]O]\[ÙˆÙXZÓX\OX[˜Ý[Û˜ÕÙXZÓX\“X\ÝOLÝO[[ÝO[[OL]OLO[[OHLKOHLK]OHLKOLÝOLÝOLOL]OLOLOLÝO[[ÝO[[ÝOHLKOL]OLOLKÌÝO[[ÝO[[]OLO[[]O[[OLOLO[[]O[[O[[O[[O[[OLO[[Ù[˜Ý[ÛˆJ
^Ü™]\›ˆÝIŒ‰‰›HOOLÛI‹[N›K•OO[[ÙÝ

N‘™

_Y[˜Ý[ÛˆYYJ
^ÚYŠOOOL
ZYŠJILÍŽÌLLŠ_J^Ý˜\ˆOY]Ù]LKJ]	ŒÎLÌŒMŒ
I‰Š]LŒŒM
KOY_Y[ÙHOMLÍŽÌLLŽÜ™]\›ˆO[›Ë˜Ý\œ™[HOO[[	‰ŠK™›YÜßLÌŠK_Y[˜Ý[Ûˆ]JK
^ÚYŠO[[
^Ý˜\ˆYKœÝ]S›ÙK[‹œ™YŽÜOO[[	‰Š[‹œ™Y^ŠœŠK›Y[[Ú^™Y›ÜËŠJJKOOO[[	‰ŠOV×JKKœ\Ú
˜š[™
[ŠJ__Y[˜Ý[ÛˆÝJKŠ^ÊOOO\ÝI‰Š]OOOLŸ]OOONJ_K˜Ø[˜Ù[[™[™ÐÛÛ[Z]OO[[
I‰ŠJK
KJKKKLJJK
KŠK
JÝIŒŠ_HOO\ÝJI‰ŠOOO\ÝI‰ŠJÝIŒŠI‰Š_[ŠKÝOOOM	‰’JKKKLJJKÙ
JJ_Y[˜Ý[ÛˆÝJKŠ^ÚYŠÝIŠ]›ÝÈ\œ›ÜŠJÌÊJNÝ˜\ˆH[‰‰Š	ŒLÊOOL	‰Š	™K™^\™Y[™\ÊOOOL]
K
KO\ÝJK
N›™
KL
KÏ\ŽÙÞÚYŠOOOL
^ÜI‰ˆ\‰‰’JKLJNØœ™XZßY[Ù^ÚYŠYK˜Ý\œ™[˜[\›˜]KÉ‰ˆ\]JŠJ^ØO[™
KLJKÏHLNØÛÛ[Y_ZYŠOOOLŠ^ÚYŠÏ]K™\œ›Ü”™XÛÝ™\žQ\ØX›Y[™\É›Ê]˜\ˆÏLÙ[ÙHÏYKœ[™[™Ó[™\É‹MLÍŽÌLLËÏ\ÏOOLÜÉLÍŽÌLLÍLÍŽÌLLŽŒœÎÚYŠÈOOL
^Ý\ÎØNžÝ˜\ˆYNØOTÝNÝ˜\ˆO[˜Ý\œ™[›Y[[Ú^™YÝ]Kš\ÑZY˜]YÚYŠI‰ŠJÊK™›YÜßLMŠKÏ[™
ËLJKÈOOL‰‰œÈOOMŠ^ÚYŠ]I‰ˆ]J^Û™\œ›Ü”™XÛÝ™\žQ\ØX›Y[™\ß[Ë_[ËOMØœ™XZÈ_[ÏPÝKÝOXKÈOO[[	‰ŠÝOOO[[ÐÝO[ÎÝKœ\Ú˜\JÝKÊJ_XO\ßZYŠÏHLKHOOLŠXÛÛ[Y__ZYŠOOOLJ^ÖJK
KJKL
NØœ™XZßXNžÜÝÚ]Ú
YKÏXKÊ^ØØ\ÙH˜Ø\ÙHN›ÝÈ\œ›ÜŠJÍJJNØØ\ÙHšYŠ
	NM
HOO]	‰Š	ŒŽLMMŒ
HOO]
Xœ™XZÎØØ\ÙHŽ’J‹KYJNØœ™XZÈNØØ\ÙHŽÝO[[Øœ™XZÎØØ\ÙHÎ˜Ø\ÙHN˜œ™XZÎÙY˜][›ÝÈ\œ›ÜŠJÌŽJJ_ZYŠ
	ŒŽLMMŒ
OOO]	‰ŠOUJÌÌSJ
KLJJ^ÚYŠJ‹KYJK
‹L
HOOL
Xœ™XZÈNÓO]‹[Y[Ý][™O]YŠÝK˜š[™
[‹‹ÝKÝKÝKKKKKË›ÝYL
KJNØœ™XZÈ_RÝJ‹‹ÝKÝKÝKKKKKË[L
__Xœ™XZß]Ú[JJNÚÙ
J_Y[˜Ý[ÛˆÝJK‹‹KKËËK‹J^ÙK[Y[Ý][™OKLNÝ˜\ˆ]œÝX™YQ›YÜËÏJIŒÌÍMM
OOOXNÚYŠ[[
ß	ŽNLŸ
	ŒMÎM
OOLMÎM
I‰Š^ÜÝ[\ÚY]Î›[ÛÝ[Œ[YÐÛÝ[Œ[YÐž]\ÎŒÝ\Ü[œÙ^R[XYÙ\Î–×KØZ][™Ñ›Ü’[XYÙ\ÎˆLØZ][™Ñ›Ü•šY]Õ˜[œÚ][ÛŽˆLK[œÝ\Ü[™›[ŸKÏ[[[
KŠKÉ‰ŠY‹ÏYK˜ÛÛZ[™\’[™›ËÏJË››ÙU\OOONOÙÎ™Ë›ÝÛ™\‘ØÝ[Y[
K—×Ü™XXÝšY]Õ˜[œÚ][Û‹ÈO[[	‰Š˜ÛÝ[
ÊËØZ][™Ñ›Ü•šY]Õ˜[œÚ][ÛHL^˜š[™

KË™š[š\ÚY[Š
JJKJIŒŽLMMŒ
OOOXOÕKSJ
NŠINM
OOOXOÑ]KSJ
NŒ^\
‹
KOO[[
J^ÓOXKK˜Ø[˜Ù[[™[™ÐÛÛ[Z]Z
˜š[™
[KK‹‹KËËK‹[JJKJKKË]JNÜ™]\›Ÿ[
KK‹‹KËËKŠ_Y[˜Ý[Ûˆ]JJ^Ù›ÜŠ˜\ˆYNÎÊ^Ý˜\ˆ]YÎÚYŠ
OOLOOLL_OOLMJI‰™›YÜÉŒMŒÎ	‰Š]\]T]Y]YKˆOO[[	‰Š[‹œÝÜ™\ËˆOO[[
JJY›ÜŠ˜\ˆLÜ‹›[™ÝÜŠÊÊ^Ý˜\ˆO[–Ü—KOZK™Ù]Û˜\ÚÝÚOZK˜[YNÝž^ÚYŠ]ÜŠJ
KJJ\™]\›ˆL_XØ]ÚÜ™]\›ˆL__ZYŠ]˜Ú[œÝX™YQ›YÜÉŒMŒÎ	‰›ˆOO[[
[‹œ™]\›][ŽÙ[Ù^ÚYŠOOYJXœ™XZÎÙ›ÜŠÝœÚX›[™ÏOO[[Ê^ÚYŠœ™]\›OO[[œ™]\›OOYJ\™]\›ˆLÝ]œ™]\›Ÿ]œÚX›[™Ëœ™]\›]œ™]\›‹]œÚX›[™ß_\™]\›ˆLY[˜Ý[ÛˆJK‹Š^ÝX]
K
K	_ž]K	_KKœÝ\Ü[™Y[™\ß]Kœ[™ÙY[™\É_‰‰ŠKØ\›S[™\ß]
KYK™^\˜][Û•[Y\ÎÙ›ÜŠ˜\ˆO]ÌNÊ^Ý˜\ˆOLÌKVYJJKÏLONÜ–ØWOKLKI_›ß[ˆOOL	‰™
K‹
_Y[˜Ý[Ûˆ]J
^Ü™]\›ˆÝIÈLŠY
LJKLJ_Y[˜Ý[ÛˆJ
^ÚYŠÝHOO[[
^ÚYŠ]OOOL
]˜\ˆOXÝKœ™]\›ŽÙ[ÙHOXÝKOVZO[[[ÊJK˜O[[XOLOXÝNÙ›ÜŠÙHOO[[ÊS˜ÊK˜[\›˜]KJKOYKœ™]\›ŽØÝO[[_Y[˜Ý[ÛˆJK
^Ý˜\ˆYK[Y[Ý][™NÜ™]\›ˆˆOOKLI‰ŠK[Y[Ý][™OKLKŠŠJKYK˜Ø[˜Ù[[™[™ÐÛÛ[Z]ˆOO[[	‰ŠK˜Ø[˜Ù[[™[™ÐÛÛ[Z][[Š
JKOLJ
KÝOYKÝO[\JK˜Ý\œ™[[
KO]]OLO[[OHLKOZ]
K
K]OHLKOXO^]O]OWÝOYÝOLÝOTÝO[[ÝOHLKOX]
K
KZJ
KŸY[˜Ý[Ûˆ]JK
^ÚÏ[[K’SœËOOU_OOQOÊS˜J
K]OLÊNOOQXOÊS˜J
K]OM
N]O]OORœÏÎ\[ÙˆOXØš™XÝ	‰	‰\[Ùˆ[OX[˜Ý[Û˜ÍŽŒKO]ÝOOO[[	‰ŠÝOLKÜÊKšJK˜Ý\œ™[
JJ_Y[˜Ý[Ûˆ	YJ
^Ý˜\ˆO[›Ë˜Ý\œ™[Ü™]\›ˆOOO[[ÈLŠINM
OOO[OÜ›ÏOO[[ŠIŒŽLMMŒ
OOO[_ILÍŽÌLLÙOOO\›ÎˆL_Y[˜Ý[Ûˆ	J
^Ý˜\ˆO[K’Ü™]\›ˆK’SœËOOO[[ÓœÎ™_Y[˜Ý[ÛˆY

^Ý˜\ˆO[KNÜ™]\›ˆKOZ]K_Y[˜Ý[Ûˆ

^ÙÝOM_
INM
HOO[I‰››Ë˜Ý\œ™[OO[[
OHL
KJÝIŒLÍŒMÍÌÊI‰ˆJIŒLÍŒMÍÌÊ_ÝOOO[[JÝKKKLJ_Y[˜Ý[Ûˆ™
KŠ^Ý˜\ˆ[ÝNÛÝ_LŽÝ˜\ˆOIJ
KOYY

NÊÝHOOY_HOO]
I‰ŠÝO[[JK
JKHLNÝ˜\ˆÏYÝNØN™Èž^ÚYŠ]HOOL	‰˜ÝHOO[[
^Ý˜\ˆÏXÝKYNÜÝÚ]Ú
]J^ØØ\ÙH–J
KÏMŽØœ™XZÈNØØ\ÙHÎ˜Ø\ÙHŽ˜Ø\ÙHN˜Ø\ÙHŽ››Ë˜Ý\œ™[OO[[	‰ŠHL
NÝ˜\ˆO]]NÚYŠ]OLO[[Ù
KËJK‰‰œJ^ÛÏLØœ™XZÈ_Xœ™XZÎÙY˜][O]]K]OLO[[Ù
KËJ__Y]J
KÏYÝNØœ™XZßXØ]Ú

^Ô]JK
_]Ú[JJNÜ™]\›ˆ	‰™KœÚ[Ý\Ü[™ÛÝ[\ŠÊËOVZO[[ÝO\‹K’ZKKOXKÝOOO[[	‰ŠÝO[[OLZJ
JKßY[˜Ý[Ûˆ]J
^Ù›ÜŠØÝHOO[[ÊZY
ÝJ_Y[˜Ý[ÛˆJK
^Ý˜\ˆ[ÝNÛÝ_LŽÝ˜\ˆIJ
KOYY

NÜÝHOOY_HOO]ÊÝO[[OSJ
JÍLJK
JNœOZ]
K
NØN™Èž^ÚYŠ]HOOL	‰˜ÝHOO[[
^ÝXÝNÝ˜\ˆÏYNØŽœÝÚ]Ú
]J^ØØ\ÙHN]OLO[[Ù
KËJNØœ™XZÎØØ\ÙHŽ˜Ø\ÙHNšYŠØJÊJ^Ý]OLO[[Y

NØœ™XZß]Y[˜Ý[ÛŠ
^Ý]HOOL‰‰]HOON_ÝHOOY_
]OMÊKÙ
J_KË[Š
NØœ™XZÈNØØ\ÙHÎ]OMÎØœ™XZÈNØØ\ÙH]OMNØœ™XZÈNØØ\ÙHÎšØJÊOÊ]OLO[[Y

JNŠ]OLO[[Ù
KËÊJNØœ™XZÎØØ\ÙHN˜\ˆÏ[[ÜÝÚ]Ú
ÝKYÊ^ØØ\ÙHŽœÏXÝK›Y[[Ú^™YÝ]NØØ\ÙHN˜Ø\ÙHÎ˜\ˆXÝNÚYŠÏÚ
ÊN›œÝ]S›ÙK˜ÛÛ\]J^Ý]OLO[[Ý˜\ˆO[œÚX›[™ÎÚYŠHOO[[
XÝO]NÙ[Ù^Ý˜\ˆ[œ™]\›ŽÙOO[[ØÝO[[ŠÝOYÙ

J_Xœ™XZÈŸ_]]OLO[[Ù
KËJNØœ™XZÎØØ\ÙHŽ]OLO[[Ù
KËŠNØœ™XZÎØØ\ÙH–J
KÝOMŽØœ™XZÈNÙY˜][›ÝÈ\œ›ÜŠJŒŠJ__\™

NØœ™XZßXØ]Ú

^Ô]JK
_]Ú[JJNÜ™]\›ˆOVZO[[K’\‹KOXKÝO[‹ÝOOO[[ÊÝO[[OLZJ
KÝJNŒY[˜Ý[Ûˆ™

^Ù›ÜŠØÝHOO[[	‰ˆQ™J
NÊZY
ÝJ_Y[˜Ý[ÛˆY
J^Ý˜\ˆ]ØÊK˜[\›˜]KKJNÙK›Y[[Ú^™Y›ÜÏYKœ[™[™Ô›ÜËOO[[ÜÙ
JN˜ÝO]Y[˜Ý[ÛˆY
J^Ý˜\ˆYK]˜[\›˜]NÜÝÚ]Ú
YÊ^ØØ\ÙHMN˜Ø\ÙHP™YJ‹œ[™[™Ô›ÜË\K›ÚYJNØœ™XZÎØØ\ÙHLNP™YJ‹œ[™[™Ô›ÜË\Kœ™[™\‹œ™Y‹JNØœ™XZÎØØ\ÙHN“[Ê
NÝ˜\ˆ]ÜOOQšI‰ŠOÊZJŠK‹YÏOOMI‰œ‹œÝ]S›ÙHO[[	‰ŠZO\‹œÝ]S›ÙJJNŠZJŠKOHL
JNÙY˜][“˜Ê‹
KXÝO^YYJJK]ØÊ‹J_YK›Y[[Ú^™Y›ÜÏYKœ[™[™Ô›ÜËOO[[ÜÙ
JN˜ÝO]Y[˜Ý[ÛˆÙ
K‹Š^ÖOVZO[[[Ê
K˜O[[XOLÝ˜\ˆO]œ™]\›ŽÝž^ÚYŠ™YJKK‹JJ^ÙÝOLKÜÊKšJ‹K˜Ý\œ™[
JKÝO[[Ü™]\›Ÿ_XØ]Ú

^ÚYŠHOO[[
]›ÝÈÝOZKÙÝOLKÜÊKšJ‹K˜Ý\œ™[
JKÝO[[Ü™]\›Ÿ]™›YÜÉŒÌÍŽÊ_OOLOÙOHLœ_ILÍŽÌLLÙOHLNŠOYOHL
OOLŸOON_OOLßOOMŠI‰Š[›Ë˜Ý\œ™[ˆOO[[	‰œ‹YÏOOLLÉ‰Š‹™›YÜßLMŒÎ
JJKÙ
JJNœÙ

_Y[˜Ý[ÛˆÙ
J^Ý˜\ˆYNÙÞÚYŠ™›YÜÉŒÌÍŽ
^ØÙ
JNÜ™]\›ŸYO]œ™]\›ŽÝ˜\ˆZ˜Ê˜[\›˜]KJNÚYŠˆOO[[
^ØÝO[ŽÜ™]\›ŸZYŠ]œÚX›[™ËOO[[
^ØÝO]Ü™]\›ŸXÝO]Y_]Ú[JOO[[
NÙÝOOOL	‰ŠÝOMJ_Y[˜Ý[ÛˆÙ
K
^ÙÞÝ˜\ˆSXÊK˜[\›˜]KJNÚYŠˆOO[[
^Û‹™›YÜÉLÌÍËÝO[ŽÜ™]\›ŸZYŠYKœ™]\›‹ˆOO[[	‰Š‹™›YÜßLÌÍŽ‹œÝX™YQ›YÜÏL‹™[][ÛœÏ[[
K]	‰ŠOYKœÚX›[™ËHOO[[
J^ØÝOYNÜ™]\›ŸXÝOYO[Ÿ]Ú[JHOO[[
NÙÝOM‹ÝO[[Y[˜Ý[Ûˆ
K‹‹KËËK‹
^ÙK˜Ø[˜Ù[[™[™ÐÛÛ[Z][[ÙÈ

NÝÚ[J]HOOL
NÚYŠÝIŠ]›ÝÈ\œ›ÜŠJÌÊJNÚYŠOO[[
^ÚYŠOOYK˜Ý\œ™[
]›ÝÈ\œ›ÜŠJMÍÊJNÙOOO\ÝI‰ŠÝO\ÝO[[OL
K]O]OYKO[‹OXK]O\‹Y
K‹ËK
__Y[˜Ý[ÛˆY
K‹‹KKÊ^Ý˜\ˆÏ]›[™\ß˜Ú[[™\ÎÚYŠO\Ëß\šK]
K‹Ë‹KJKO[[
‰ŒÌÍMM
OOO[ÊO[XJJKLLŒŠNŠO[[LLMŠK
œÝX™YQ›YÜÉœŠHOOL
™›YÜÉœŠHOOLÊK˜Ø[˜XÚÓ›ÙO[[K˜Ø[˜XÚÔš[Üš]OLÙ
™K[˜Ý[ÛŠ
^Ü™]\›ˆÙ

K[JJNŠK˜Ø[˜XÚÓ›ÙO[[K˜Ø[˜XÚÔš[Üš]OL
KXÏHLKJ™›YÜÉŒLÎÎ
HOLœÝX™YQ›YÜÉŒLÎÎŠ^Ü[K•K•[[O]YKœYKœL‹O[ÝKÝ_MÝž^Þ
KŠ_Yš[˜[^ÛÝOXKYKœZKK•\Ÿ_P]OLKXÏÓO^YŠËK˜ÛÛZ[™\’[™›ËK™KÙK[[
NŠ

K™

K

J_Y[˜Ý[ÛˆJJ^ÚYŠ]HOOL
^Ý˜\ˆZK›Û”™XÛÝ™\˜X›Q\œ›ÜŽÝ
KØÛÛ\Û™[ÝXÚÎ›[J__Y[˜Ý[ÛˆJ
^Ð]OOOLÉ‰Š]OL›
]KJK]OM
_Y[˜Ý[Ûˆ

^ÚYŠ]OOOLJ^Ð]OLÝ˜\ˆOZKS]KSKJ™›YÜÉŒLÎÎ
HOLÚYŠœÝX™YQ›YÜÉŒLÎÎŠ^Ü[K•K•[[Ý˜\ˆO]YKœÝYKœLŽÝ˜\ˆO[ÝNÛÝ_MÝž^Ý›^[HLK[
KŠK\™ŽÝ˜\ˆÏP\ŠK˜ÛÛZ[™\’[™›ÊKÏ[‹™›ØÝ\ÙY[[K[‹œÙ[XÝ[Û”˜[™ÙNÚYŠÈOO\É‰œÉ‰œË›ÝÛ™\‘ØÝ[Y[	‰šÜŠË›ÝÛ™\‘ØÝ[Y[™ØÝ[Y[[[Y[ÊJ^ÚYŠOO[[	‰šœŠÊJ^Ý˜\ˆO[œÝ\[™[™ÚYŠOO]›ÚY	‰Š]JKÙ[XÝ[Û”Ý\[ˆÊ\ËœÙ[XÝ[Û”Ý\]KËœÙ[XÝ[Û‘[™SX]›Z[ŠË˜[YK›[™Ý
NÙ[Ù^Ý˜\ˆ\Ë›ÝÛ™\‘ØÝ[Y[ØÝ[Y[Y‰‰™‹™Y˜][šY]ßÚ[™ÝÎÚYŠ™Ù]Ù[XÝ[ÛŠ^Ý˜\ˆO\™Ù]Ù[XÝ[ÛŠ
K\Ë^ÛÛ[›[™ÝÏSX]›Z[ŠœÝ\
KÏ[™[™OO]›ÚYÙÎ“X]›Z[Š™[™
NÈ[K™^[™	‰™Ï—É‰ŠÏWËÏYËÏ[ÊNÝ˜\ˆSÜŠËÊKOSÜŠËÊNÚYŠ‰‰žI‰ŠKœ˜[™ÙPÛÝ[OOL_K˜[˜ÚÜ“›ÙHOO]‹››Ù_K˜[˜ÚÜ“Ù™œÙ]OO]‹›Ù™œÙ]K™›ØÝ\Ó›ÙHOO^K››Ù_K™›ØÝ\ÓÙ™œÙ]OO^K›Ù™œÙ]
J^Ý˜\ˆY‹˜Ü™X]T˜[™ÙJ
NØ‹œÙ]Ý\
‹››ÙK‹›Ù™œÙ]
KKœ™[[Ý™P[˜[™Ù\Ê
KÏ—ÏÊK˜Y˜[™ÙJŠKK™^[™
K››ÙKK›Ù™œÙ]
JNŠ‹œÙ][™
K››ÙKK›Ù™œÙ]
KK˜Y˜[™ÙJŠJ____Y›ÜŠV×KO\ÎÛO[Kœ\™[›ÙNÊ[K››ÙU\OOOLI‰™‹œ\Ú
Ù[[Y[›KY›KœØÜ›ÛYÜ›KœØÜ›ÛÜJNÙ›ÜŠ\[ÙˆË™›ØÝ\ÏOX[˜Ý[Û˜	‰œË™›ØÝ\Ê
KÏLÜÏ‹›[™ÝÜÊÊÊ^Ý˜\ˆY–Ü×NÞ™[[Y[œØÜ›ÛY^›Y™[[Y[œØÜ›ÛÜ^Ü_ZÜHH[™‹™[™[[Yš[˜[^ÛÝOXKYKœZKK•\Ÿ_YK˜Ý\œ™[]]OLŸ_Y[˜Ý[Ûˆ™

^ÚYŠ]OOOLŠ^Ð]OLÝ˜\ˆOZKS]KJ™›YÜÉŽÍÌŠHOLÚYŠœÝX™YQ›YÜÉŽÍÌŸŠ^Û[K•K•[[Ý˜\ˆ]YKœÝYKœLŽÝ˜\ˆO[ÝNÛÝ_MÝž^ÖYJK˜[\›˜]K
_Yš[˜[^ÛÝOZKYKœ\‹K•[Ÿ_P]OLß_Y[˜Ý[Ûˆ

^ÚYŠ]OOOM]OOOLÊ^Ð]OLÝ˜\ˆOSNÓO[[YJ
NÝ˜\ˆZKS]KSKOR]KOJ‰ŒÌÍMM
OOO\ÌLŒŽŒLMŽÚYŠ
‹œÝX™YQ›YÜÉ˜JHOOL
‹™›YÜÉ˜JHOOLÐ]OMNŠ]OL]OZO[[Y
œ[™[™Ó[™\ÊJKO]œ[™[™Ó[™\ËOOOL	‰ŠÝO[[
K
ŠK[‹œÝ]S›ÙKYI‰\[ÙˆYK›ÛÛÛ[Z]šX™\”›ÛÝOX[˜Ý[Û˜
]ž^ÜYK›ÛÛÛ[Z]šX™\”›ÛÝ
ÙK‹›ÚY
‹˜Ý\œ™[™›YÜÉŒLŽ
OOLLŽ
_XØ]ÚßZYŠHOO[[
^Û[K•O]YKœYKœL‹K•[[Ýž^Ù›ÜŠ˜\ˆÏ]›Û”™XÛÝ™\˜X›Q\œ›Ü‹ÏLÜÏK›[™ÝÜÊÊÊ^Ý˜\ˆZVÜ×NÛÊ˜[YKØÛÛ\Û™[ÝXÚÎ›œÝXÚßJ__Yš[˜[^ÛK•[‹YKœX__ZYŠOTKÏ^KO[[HOO[[	‰ŠO[[ÏOO[[	‰ŠÏV×JKHOO[[
JY›ÜŠLÛK›[™ÝÛ
ÊÊ[JVÛJJÊKˆOO]›ÚY	‰™K™š[š\ÚY™š[˜[JŠNÓIŒÉ‰š

KÙ

KO]œ[™[™Ó[™\Ë‰ŒŒNLÌ	‰˜IÝOOUOÐJÊÎŠOLO]
NŠOLO[[
KY
LJ__Y[˜Ý[ÛˆY
K
^ÊKœÛÛYØXÚS[™\É]
OOOL	‰ŠYKœÛÛYØXÚKO[[	‰ŠKœÛÛYØXÚO[[J
JJ_Y[˜Ý[Ûˆ

^Ü™]\›ˆHOO[[	‰ŠKœÚÚ\˜[œÚ][ÛŠ
KO[[
K

K™

K

KÙ

_Y[˜Ý[ÛˆÙ

^ÚYŠ]HOOMJ\™]\›ˆLNÝ˜\ˆOZKTNÔOLÝ˜\ˆZ
JK[K•O]YKœÝž^ÝYKœLÌ›ÌÌŽ›‹K•[[QKO[[Ý˜\ˆÏZKÏSNÚYŠ]OL]OZO[[OLÝIŠ]›ÝÈ\œ›ÜŠJÌÌJJNÝ˜\ˆ[ÝNÚYŠÝ_MJË˜Ý\œ™[
K[
ËË˜Ý\œ™[ËŠKÝO[Y
LJKYI‰\[ÙˆYK›Û”ÜÝÛÛ[Z]šX™\”›ÛÝOX[˜Ý[Û˜
]ž^ÜYK›Û”ÜÝÛÛ[Z]šX™\”›ÛÝ
ÙKÊ_XØ]Úß\™]\›ˆLYš[˜[^ÝYKœXKK•\‹Y
K
__Y[˜Ý[ÛˆÙ
KŠ^ÝXšJ‹
KRÜÊKœÝ]S›ÙKŠKORØJKŠKHOO[[	‰Š
KŠKÙ
JJ_Y[˜Ý[Ûˆ™
KŠ^ÚYŠKYÏOOLÊWÙ
KKŠNÙ[ÙH›ÜŠÝOO[[Ê^ÚYŠYÏOOLÊ^×Ù
KŠNØœ™XZßY[ÙHYŠYÏOOLJ^Ý˜\ˆ]œÝ]S›ÙNÚYŠ\[Ùˆ\K™Ù]\š]™YÝ]Qœ›ÛQ\œ›ÜOX[˜Ý[Û˜\[Ùˆ‹˜ÛÛ\Û™[YØ]ÚOX[˜Ý[Û˜	‰ŠÝOOO[[ZÝKš\ÊŠJJ^ÙOXšJ‹JK\\ÊŠKRØJ‹ŠKˆOO[[	‰Š™YJ‹‹JK
‹ŠKÙ
ŠJNØœ™XZß_]]œ™]\›Ÿ_Y[˜Ý[ÛˆY
KŠ^Ý˜\ˆYKœ[™ÐØXÚNÚYŠOO[[
^ÜYKœ[™ÐØXÚO[™]È]NÝ˜\ˆO[™]ÈÙ]Ü‹œÙ]
J_Y[ÙHO\‹™Ù]

KOOO]›ÚY	‰ŠO[™]ÈÙ]‹œÙ]
JJNÚKš\ÊŠ_
]OHLK˜Y
ŠKOZ]K˜š[™
[KŠK[ŠKJJ_Y[˜Ý[Ûˆ]JKŠ^Ý˜\ˆYKœ[™ÐØXÚNÜˆOO[[	‰œ‹™[]J
KKœ[™ÙY[™\ßYKœÝ\Ü[™Y[™\É›‹KØ\›S[™\É_›‹ÝOOOYI‰ŠI›ŠOOO[‰‰ŠÝOOOMÝOOOLÉ‰ŠIŒŽLMMŒ
OOO[I‰ŒÌ“J
KUOÛÝIŒÞ]_[Ž–JK
Nž]_[‹OOO[I‰ŠOL
JKÙ
J_Y[˜Ý[Ûˆ™
K
^ÝOOL	‰Š\Ý

JKO\ÚJK
KHOO[[	‰Š
K
KÙ
JJ_Y[˜Ý[Ûˆ
J^Ý˜\ˆYK›Y[[Ú^™YÝ]KLÝOO[[	‰Š]œ™]žS[™JK™
KŠ_Y[˜Ý[Ûˆ]JK
^Ý˜\ˆLÜÝÚ]Ú
KYÊ^ØØ\ÙHÌN˜Ø\ÙHLÎ˜\ˆYKœÝ]S›ÙKOYK›Y[[Ú^™YÝ]NØHOO[[	‰ŠXKœ™]žS[™JNØœ™XZÎØØ\ÙHNNœYKœÝ]S›ÙNØœ™XZÎØØ\ÙHŒŽœYKœÝ]S›ÙK—Ü™]žPØXÚNØœ™XZÎÙY˜][›ÝÈ\œ›ÜŠJÌM
J_\ˆOO[[	‰œ‹™[]J
K™
KŠ_Y[˜Ý[ÛˆÙ
K
^Ü™]\›ˆ™JK
_]˜\ˆÙ[[Ù[[HLKYHLKHLKÙLÙ[˜Ý[ÛˆÙ
J^ÙHOO]Ù	‰™K›™^OO[[	‰ŠÙOO[[ÐÙ]ÙYNÙ]Ù›™^YJKYHL
HLÝJ
J_Y[˜Ý[ÛˆY
K
^ÚYŠQ	‰‘Y
^ÑHLÙÈ›ÜŠ˜\ˆHLKPÙÜˆOO[[Ê^ÚYŠ]
ZYŠHOOL
^Ý˜\ˆO\‹œ[™[™Ó[™\ÎÚYŠOOOL
]˜\ˆOLÙ[Ù^Ý˜\ˆÏ\‹œÝ\Ü[™Y[™\ËÏ\‹œ[™ÙY[™\ÎØOJOÌKVYJŸJJÌJKLKIZIŸŠÉŸœÊKOXIŒŒLÌÍOØIŒŒLÌÍ_N˜OØ_ŽŒXHOOL	‰ŠHL
‹JJ_Y[ÙHO[KO\
‹OO\ÝOØNŒ‹˜Ø[˜Ù[[™[™ÐÛÛ[Z]OO[[‹[Y[Ý][™HOOKLJKJIŒÊ_]
‹J_
HL
‹JJNÜ\‹›™^]Ú[JŠNÑHL__Y[˜Ý[Ûˆ™

^ÓY

_Y[˜Ý[ÛˆY

^ÑYUHLNÝ˜\ˆOLÓÙOOL	‰—ÝJ
I‰ŠOSÙ
NÙ›ÜŠ˜\ˆSJ
K[[PÙÜˆOO[[Ê^Ý˜\ˆO\‹›™^O[ÝJ‹
NØOOOLÊ‹›™^[[OO[[ÐÙZN›‹›™^ZKOOO[[	‰ŠÙ[ŠJNŠ\‹
HOOLIŒÊI‰ŠYHL
JKZ_P]HOOL	‰]HOOM_Y
KLJKÙOOL	‰ŠÙL
_Y[˜Ý[ÛˆÝJK
^Ù›ÜŠ˜\ˆYKœÝ\Ü[™Y[™\ËYKœ[™ÙY[™\ËOYK™^\˜][Û•[Y\ËOYKœ[™[™Ó[™\É‹MŒŽLMMŒNÌNÊ^Ý˜\ˆÏLÌKVYJJKÏLOËZVÛ×NÛOOKLOÊ
É›ŠOOOL
ÉœŠHOOL
I‰ŠVÛ×O[Ý
Ë
JN›]	‰ŠK™^\™Y[™\ß\ÊKI_œßZYŠ\ÝK[K\
KOOO]ÛŽŒK˜Ø[˜Ù[[™[™ÐÛÛ[Z]OO[[K[Y[Ý][™HOOKLJKYK˜Ø[˜XÚÓ›ÙKOOLOOO]	‰Š]OOOLŸ]OOONJ_K˜Ø[˜Ù[[™[™ÐÛÛ[Z]OO[[
\™]\›ˆˆOO[[	‰œˆOO[[	‰”JŠKK˜Ø[˜XÚÓ›ÙO[[K˜Ø[˜XÚÔš[Üš]OLÚYŠJ‰ŒÊ_]
KŠJ^ÚYŠ[‰‹[‹OOYK˜Ø[˜XÚÔš[Üš]J\™]\›ˆÜÝÚ]Ú
ˆOO[[	‰”JŠK
ŠJ^ØØ\ÙHŽ˜Ø\ÙH›P™NØœ™XZÎØØ\ÙHÌŽ›U™NØœ™XZÎØØ\ÙHŽÍMMŽ›UYNØœ™XZÎÙY˜][›U™_\™]\›ˆS™˜š[™
[JKS™J‹ŠKK˜Ø[˜XÚÔš[Üš]O]K˜Ø[˜XÚÓ›ÙO[‹\™]\›ˆˆOO[[	‰œˆOO[[	‰”JŠKK˜Ø[˜XÚÔš[Üš]OL‹K˜Ø[˜XÚÓ›ÙO[[ŸY[˜Ý[Ûˆ™
K
^ÚYŠ]HOOL	‰]HOOMJ\™]\›ˆK˜Ø[˜XÚÓ›ÙO[[K˜Ø[˜XÚÔš[Üš]OL[Ý˜\ˆYK˜Ø[˜XÚÓ›ÙNÚYŠ

I‰™K˜Ø[˜XÚÓ›ÙHOO[Š\™]\›ˆ[Ý˜\ˆ[NÜ™]\›ˆ\
KOOO\ÝOÜŽŒK˜Ø[˜Ù[[™[™ÐÛÛ[Z]OO[[K[Y[Ý][™HOOKLJKOOLÛ[ŠÝJK‹
KÝJKJ
JKK˜Ø[˜XÚÓ›ÙHO[[	‰™K˜Ø[˜XÚÓ›ÙOOO[Ó™˜š[™
[JN›[
_Y[˜Ý[Ûˆ
K
^ÚYŠ

J\™]\›ˆ[ÑÝJKL
_Y[˜Ý[ÛˆÝJ
^Þ]J[˜Ý[ÛŠ
^ÛÝIÓ™J™K™
N“Y

_J_Y[˜Ý[Ûˆ™

^ÚYŠÙOOL
^Ý˜\ˆOWØNÙOOOL	‰ŠOIK	OLKJ	IŒŒN
I‰Š	OLMŠJKÙY_\™]\›ˆÙY[˜Ý[ÛˆY
J^Ü™]\›ˆOO[[\[ÙˆOOXÞ[X›Û\[ÙˆOOX›ÛÛX[˜Û[\[ÙˆOOX[˜Ý[Û˜ÙNœŠJ_Y[˜Ý[ÛˆÝJK‹‹J^ÚYŠOOXÝX›Z]	‰›‰‰›‹œÝ]S›ÙOOOZJ^Ý˜\ˆORY

VØ_[
K˜XÝ[ÛŠKÏ\‹œÝX›Z]\ŽÛÉ‰ŠJ[ÖØ_[
OÒY
™›Ü›PXÝ[ÛŠN›Ë™Ù]]šX]J›Ü›PXÝ[Û˜
KOO[[	‰ŠO]Ï[[
JNÝ˜\ˆÏ[™]ÈŠXÝ[Û˜XÝ[Û˜[‹JNÙKœ\Ú
Ù]™[œË\Ý[™\œÎ–ÞÚ[œÝ[˜ÙN›[\Ý[™\Ž™[˜Ý[ÛŠ
^ÚYŠ‹™Y˜][™]™[Y
^ÚYŠÙOOL
^Ý˜\ˆO[™]È›Ü›Q]JKÊNÞ\Ê‹Ü[™[™ÎˆL]N™KY]ÙšK›Y]ÙXÝ[ÛŽ˜_K[J__Y[ÙH\[ÙˆOOX[˜Ý[Û˜	‰ŠËœ™]™[Y˜][

KO[™]È›Ü›Q]JKÊK\Ê‹Ü[™[™ÎˆL]N™KY]ÙšK›Y]ÙXÝ[ÛŽ˜_KKJJ_KÝ\œ™[\™Ù]š_W_J__Y›ÜŠ˜\ˆLÓ\‹›[™ÝÓ
ÊÊ^Ý˜\ˆ™V\–ÓNÖŠ™ÓÝÙ\Ø\ÙJ
KÛ˜
Ê™ÌKÕ\\Ø\ÙJ
JÔ™œÛXÙJJJJ_VŠ\‹Û[š[X][Û‘[™
KŠÜ‹Û[š[X][Û’]\˜][Û˜
KŠÜ‹Û[š[X][Û”Ý\
KŠ›ÛXÚØÛ‘ÝX›PÛXÚØ
KŠ›ØÝ\Ú[˜Û‘›ØÝ\Ø
KŠ›ØÝ\ÛÝ]Û›\˜
KŠYKÛ•˜[œÚ][Û”[˜
KŠÜ‹Û•˜[œÚ][Û”Ý\
KŠ\‹Û•˜[œÚ][ÛØ[˜Ù[
KŠœ‹Û•˜[œÚ][Û‘[™
K
Û“[Ý\ÙQ[\˜Ø[Ý\Ù[Ý][Ý\Ù[Ý™\˜JK
Û“[Ý\ÙSX]™XØ[Ý\Ù[Ý][Ý\Ù[Ý™\˜JK
Û”Ú[\‘[\˜ØÚ[\›Ý]Ú[\›Ý™\˜JK
Û”Ú[\“X]™XØÚ[\›Ý]Ú[\›Ý™\˜JK
ÛÚ[™ÙXÚ[™ÙHÛXÚÈ›ØÝ\Ú[ˆ›ØÝ\ÛÝ][œ]Ù^YÝÛˆÙ^]\Ù[XÝ[Û˜Ú[™ÙXœÜ]

JK
Û”Ù[XÝ›ØÝ\ÛÝ]ÛÛ^Y[H˜YÙ[™›ØÝ\Ú[ˆÙ^YÝÛˆÙ^]\[Ý\ÙYÝÛˆ[Ý\Ù]\Ù[XÝ[Û˜Ú[™ÙXœÜ]

JK
Û™Y›Ü™R[œ]ØÛÛ\ÜÚ][Û™[™Ù^\™\ÜØ^[œ]\ÝXJK
ÛÛÛ\ÜÚ][Û‘[™ÛÛ\ÜÚ][Û™[™›ØÝ\ÛÝ]Ù^YÝÛˆÙ^\™\ÜÈÙ^]\[Ý\ÙYÝÛ˜œÜ]

JK
ÛÛÛ\ÜÚ][Û”Ý\ÛÛ\ÜÚ][ÛœÝ\›ØÝ\ÛÝ]Ù^YÝÛˆÙ^\™\ÜÈÙ^]\[Ý\ÙYÝÛ˜œÜ]

JK
ÛÛÛ\ÜÚ][Û•\]XÛÛ\ÜÚ][Û\]H›ØÝ\ÛÝ]Ù^YÝÛˆÙ^\™\ÜÈÙ^]\[Ý\ÙYÝÛ˜œÜ]

JNÝ˜\ˆ™XX›ÜØ[œ^HØ[œ^]›ÝYÚ\˜][Û˜Ú[™ÙH[\YY[˜Üž\Y[™Y\œ›ÜˆØYY]HØYYY]Y]HØYÝ\]\ÙH^H^Z[™È›ÙÜ™\ÜÈ˜]XÚ[™ÙH™\Ú^™HÙYZÙYÙYZÚ[™ÈÝ[YÝ\Ü[™[Y]\]H›Û[YXÚ[™ÙHØZ][™ØœÜ]

K™[™]ÈÙ]
™Y›Ü™]ÙÙÛHØ[˜Ù[ÛÜÙH[˜[YØYØÜ›ÛØÜ›Û[™ÙÙÛXœÜ]

K˜ÛÛ˜Ø]
™
JNÙ[˜Ý[Ûˆ™
K
^ÝJ	
HOLÙ›ÜŠ˜\ˆLÛK›[™ÝÛŠÊÊ^Ý˜\ˆYVÛ—KO\‹™]™[Ü\‹›\Ý[™\œÎØNžÝ˜\ˆO]›ÚYÚYŠ
Y›ÜŠ˜\ˆÏ\‹›[™ÝLNÌ[ÎÛËKJ^Ý˜\ˆÏ\–Û×K\Ëš[œÝ[˜ÙKO\Ë˜Ý\œ™[\™Ù]ÚYŠÏ\Ë›\Ý[™\‹OOXI‰šKš\Ô›ÜYØ][Û”ÝÜY

JXœ™XZÈNØO\ËK˜Ý\œ™[\™Ù]]NÝž^ØJJ_XØ]Ú
J^ÙZJJ_ZK˜Ý\œ™[\™Ù][[O[Y[ÙH›ÜŠÏLÛÏ‹›[™ÝÛÊÊÊ^ÚYŠÏ\–Û×K\Ëš[œÝ[˜ÙKO\Ë˜Ý\œ™[\™Ù]Ï\Ë›\Ý[™\‹OOXI‰šKš\Ô›ÜYØ][Û”ÝÜY

JXœ™XZÈNØO\ËK˜Ý\œ™[\™Ù]]NÝž^ØJJ_XØ]Ú
J^ÙZJJ_ZK˜Ý\œ™[\™Ù][[O[___Y[˜Ý[Ûˆ
K
^Ý˜\ˆ]ÔÝNÛOO]›ÚY	‰Š]ÔÝO[™]ÈÙ]
NÝ˜\ˆYJØ×ØX˜›XÛ‹š\ÊŠ_
Ù
K‹LJK‹˜Y
ŠJ_Y[˜Ý[ÛˆY
KŠ^Ý˜\ˆLÝ	‰ŠŸM
KÙ
‹K‹
_]˜\ˆÙXÜ™XXÝ\Ý[š[™Ø
ÓX]œ˜[™ÛJ
KÔÝš[™ÊÍŠKœÛXÙJŠNÙ[˜Ý[ÛˆJJ^ÚYŠYVÕÙJ^ÙVÕÙOHL™›Ü‘XXÚ
[˜Ý[ÛŠ
^ÝOOXÙ[XÝ[Û˜Ú[™ÙX	‰Š™š\Ê
_Y
LKJKY
LJJ_JNÝ˜\ˆYK››ÙU\OOONOÙN™K›ÝÛ™\‘ØÝ[Y[ÝOO[[ÕÙ_
ÕÙOHLY
Ù[XÝ[Û˜Ú[™ÙXLK
J__Y[˜Ý[ÛˆÙ
K‹Š^ÜÝÚ]Ú
™J
J^ØØ\ÙHŽ˜\ˆOINØœ™XZÎØØ\ÙHšOY[™NØœ™XZÎÙY˜][šOP\[ZK˜š[™
[‹JKO]›ÚY]ÛŸOOXÝXÚÝ\	‰OOXÝXÚ[Ý™X	‰OOXÚY[
OHL
KÚOOO]›ÚYÙK˜Y]™[\Ý[™\Š‹L
N™K˜Y]™[\Ý[™\Š‹ØØ\\™NˆL\ÜÚ]™Nš_JNšOOO]›ÚYÙK˜Y]™[\Ý[™\Š‹LJN™K˜Y]™[\Ý[™\Š‹Ü\ÜÚ]™Nš_J_Y[˜Ý[ÛˆÙ
K‹‹J^Ý˜\ˆO\ŽÚYŠJ	ŒJI‰ˆJ	ŒŠI‰œˆOO[[
XN™›ÜŠÎÊ^ÚYŠOO[[
\™]\›ŽÝ˜\ˆÏ\‹YÎÚYŠÏOOLßÏOOM
^Ý˜\ˆ\‹œÝ]S›ÙK˜ÛÛZ[™\’[™›ÎÚYŠOOZJXœ™XZÎÚYŠÏOOM
Y›ÜŠÏ\‹œ™]\›ŽÜÈOO[[Ê^Ý˜\ˆO\ËYÎÚYŠ
OOOLßOOOM
I‰œËœÝ]S›ÙK˜ÛÛZ[™\’[™›ÏOOZJ\™]\›ŽÜÏ\Ëœ™]\›ŸY›ÜŠÛOO[[Ê^ÚYŠÏZÝ

KÏOO[[
\™]\›ŽÚYŠO\ËYËOOOM_OOOMŸOOOLŸOOOLÊ^ÜXO\ÎØÛÛ[YH_[[œ\™[›Ù__\\‹œ™]\›Ÿ^Š[˜Ý[ÛŠ
^Ý˜\ˆXKOYÛŠŠKÏV×NØNžÝ˜\ˆYÙYK™Ù]
JNÚYŠOO]›ÚY
^Ý˜\ˆOT‹YNÜÝÚ]Ú
J^ØØ\ÙXÙ^\™\ÜØšYŠ[ŠŠOOOL
Xœ™XZÈNØØ\ÙXÙ^YÝÛ˜˜Ø\ÙXÙ^]\OR›ŽØœ™XZÎØØ\ÙX›ØÝ\Ú[˜™X›ØÝ\ØOU›ŽØœ™XZÎØØ\ÙX›ØÝ\ÛÝ]™X›\˜OU›ŽØœ™XZÎØØ\ÙX™Y›Ü™X›\˜˜Ø\ÙXY\˜›\˜OU›ŽØœ™XZÎØØ\ÙXÛXÚØšYŠ‹˜]ÛOOLŠXœ™XZÈNØØ\ÙX]^ÛXÚØ˜Ø\ÙX›ÛXÚØ˜Ø\ÙX[Ý\ÙYÝÛ˜˜Ø\ÙX[Ý\Ù[[Ý™X˜Ø\ÙX[Ý\Ù]\˜Ø\ÙX[Ý\Ù[Ý]˜Ø\ÙX[Ý\Ù[Ý™\˜˜Ø\ÙXÛÛ^Y[XOP›ŽØœ™XZÎØØ\ÙX˜YØ˜Ø\ÙX˜YÙ[™˜Ø\ÙX˜YÙ[\˜˜Ø\ÙX˜YÙ^]˜Ø\ÙX˜YÛX]™X˜Ø\ÙX˜YÛÝ™\˜˜Ø\ÙX˜YÜÝ\˜Ø\ÙX›ÜOZYYNØœ™XZÎØØ\ÙXÝXÚØ[˜Ù[˜Ø\ÙXÝXÚ[™˜Ø\ÙXÝXÚ[Ý™X˜Ø\ÙXÝXÚÝ\O\ÙYNØœ™XZÎØØ\ÙH\Ž˜Ø\ÙHÜŽ˜Ø\ÙHÜŽOXYYNØœ™XZÎØØ\ÙHœŽOV›ŽØœ™XZÎØØ\ÙXØÜ›Û˜Ø\ÙXØÜ›Û[™O\™YNØœ™XZÎØØ\ÙXÚY[OT[ŽØœ™XZÎØØ\ÙXÛÜX˜Ø\ÙXÝ]˜Ø\ÙX\ÝXORŽØœ™XZÎØØ\ÙXÛÝÚ[\˜Ø\\™X˜Ø\ÙXÜÝÚ[\˜Ø\\™X˜Ø\ÙXÚ[\˜Ø[˜Ù[˜Ø\ÙXÚ[\™ÝÛ˜˜Ø\ÙXÚ[\›[Ý™X˜Ø\ÙXÚ[\›Ý]˜Ø\ÙXÚ[\›Ý™\˜˜Ø\ÙXÚ[\\OV[ŽØœ™XZÎØØ\ÙXÝX›Z]OVŽØœ™XZÎØØ\ÙXÙÙÛX˜Ø\ÙX™Y›Ü™]ÙÙÛXOIŸ]˜\ˆJ	
HOLHY‰‰ŠOOOXØÜ›ÛOOOXØÜ›Û[™
KOYÛOO[[Û[›
ØØ\\™X›ÙV×NÙ›ÜŠ˜\ˆ\‹ÎÚOO[[Ê^Ý˜\ˆÏZÚYŠÏWËœÝ]S›ÙKÏWËYËÈOOMI‰—ÈOOL‰‰—ÈOOLßÏOO[[OOO[[
ÏTÛŠJKÈO[[	‰™‹œ\Ú
Y
ËÊJJK
Xœ™XZÎÚZœ™]\›ŸL‹›[™Ý	‰Š[™]ÈJ[‹JKËœ\Ú
Ù]™[›\Ý[™\œÎ™ŸJJ__ZYŠJ	ÊJ^ØNžÚYŠOYOOOX[Ý\Ù[Ý™\˜OOOXÚ[\›Ý™\˜YOOOX[Ý\Ù[Ý]OOOXÚ[\›Ý]I‰›ˆOOZ‰‰Š[‹œ™[]Y\™Ù]‹™œ›ÛQ[[Y[
I‰ŠÝ

_ÞJJXœ™XZÈNÊJI‰ŠZKÚ[™ÝÏOOZOÚNŠOZK›ÝÛ™\‘ØÝ[Y[
OÝK™Y˜][šY]ßKœ\™[Ú[™ÝÎÚ[™ÝËÊO[‹œ™[]Y\™Ù]‹Ñ[[Y[\‹O]OÚÝ
JN›[HOO[[	‰Š[ÊJK]KYËHOO\ˆOOMI‰™ˆOOLÉ‰™ˆOOMŠI‰ŠO[[
JNŠ[[O\ŠKOO]I‰ŠP›‹ÏXÛ“[Ý\ÙSX]™XOXÛ“[Ý\ÙQ[\˜X[Ý\ÙX
OOOXÚ[\›Ý]OOOXÚ[\›Ý™\˜
I‰ŠV[‹ÏXÛ”Ú[\“X]™XOXÛ”Ú[\‘[\˜XÚ[\˜
K[O[[Ùš

KÏ]OO[[Ùš
JK[™]ÈŠË
ØX]™X‹JK\™Ù]\œ™[]Y\™Ù]YËÏ[[Ý
JOOO\‰‰Š[™]ÈŠK
Ø[\˜K‹JK‹\™Ù]YË‹œ™[]Y\™Ù]\ÏYŠKWË[	‰OÝÊK]JN›[OO[[	‰–Y
Ë‹LJKHOO[[	‰œOO[[	‰–Y
ËK‹L
JJ_XNžÚYŠ\Ú
ŠNÚ[™ÝËO[››ÙS˜[YI‰›››ÙS˜[YKÓÝÙ\Ø\ÙJ
KOOOXÙ[XÝOOOX[œ]	‰›\OOOXš[X
]˜\ˆWÜŽÙ[ÙHYŠœŠ
JZYŠYYJ]PÜŽÙ[Ù^Ý\YNÝ˜\ˆO^ŸY[ÙHO[››ÙS˜[YK]_KÓÝÙ\Ø\ÙJ
HOOX[œ]\HOOXÚXÚØ›Þ	‰›\HOOX˜Y[ØÜ‰‰[Š‹™[[Y[\JI‰ŠWÜŠNTÜŽÚYŠ‰‰]ŠKŠJ^ÜŠË‹‹JNØœ™XZÈ_^I‰žJKŠ_\ÝÚ]Ú
O\Ú
ŠNÚ[™ÝËJ^ØØ\ÙX›ØÝ\Ú[˜ŠœŠJ_K˜ÛÛ[Y]X›OOOXYX
I‰Šœ^K\‹œ[[
NØœ™XZÎØØ\ÙX›ØÝ\ÛÝ]‘œTSœ[[Øœ™XZÎØØ\ÙX[Ý\ÙYÝÛ˜’\HLØœ™XZÎØØ\ÙXÛÛ^Y[X˜Ø\ÙX[Ý\Ù]\˜Ø\ÙX˜YÙ[™’\HLKŠË‹JNØœ™XZÎØØ\ÙXÙ[XÝ[Û˜Ú[™ÙXšYŠ\ŠXœ™XZÎØØ\ÙXÙ^YÝÛ˜˜Ø\ÙXÙ^]\“ŠË‹J_]˜\ˆŽÚYŠŠXŽžÜÝÚ]Ú
J^ØØ\ÙXÛÛ\ÜÚ][ÛœÝ\˜\ˆXÛÛÛ\ÜÚ][Û”Ý\Øœ™XZÈŽØØ\ÙXÛÛ\ÜÚ][Û™[™žXÛÛÛ\ÜÚ][Û‘[™Øœ™XZÈŽØØ\ÙXÛÛ\ÜÚ][Û\]XžXÛÛÛ\ÜÚ][Û•\]XØœ™XZÈŸ^]›ÚYY[ÙHÜÛÜŠKŠI‰ŠXÛÛÛ\ÜÚ][Û‘[™
N™OOOXÙ^YÝÛ˜	‰›‹šÙ^PÛÙOOOLŒŽI‰ŠXÛÛÛ\ÜÚ][Û”Ý\
NÞ	‰Šœ‰‰›‹›ØØ[HOOXÛØ	‰ŠÜŸOOXÛÛÛ\ÜÚ][Û”Ý\ÞOOXÛÛÛ\ÜÚ][Û‘[™	‰˜Ü‰‰ŠZÛŠ
JNŠ[ZKX˜[YX[ˆ[Ñ[‹˜[YN‘[‹^ÛÛ[ÜHL
JKOR™
‹
KK›[™Ý	‰Š[™]È[ŠK[‹JKËœ\Ú
Ù]™[ž\Ý[™\œÎž_JKÞ™]OXŽŠ\ÜŠŠKˆOO[[	‰Š™]OXŠJJJK
XÙYOÛŠKŠN\ŠKŠJI‰ŠR™
‹Û™Y›Ü™R[œ]
K›[™Ý	‰ŠO[™]È[ŠÛ™Y›Ü™R[œ]™Y›Ü™Z[œ][‹JKËœ\Ú
Ù]™[žK\Ý[™\œÎžJKK™]OXŠJKÝJËK‹‹J_U™
Ë
_J_Y[˜Ý[ÛˆY
KŠ^Ü™]\›žÚ[œÝ[˜ÙN™K\Ý[™\ŽÝ\œ™[\™Ù]›Ÿ_Y[˜Ý[Ûˆ™
K
^Ù›ÜŠ˜\ˆ]
ØØ\\™XV×NÙHOO[[Ê^Ý˜\ˆOYKOZKœÝ]S›ÙNÚYŠOZKYËHOOMI‰šHOOL‰‰šHOOLßOOO[[
OTÛŠKŠKHO[[	‰œ‹[œÚY
Y
KKJJKOTÛŠK
KHO[[	‰œ‹œ\Ú
Y
KKJJJKKYÏOOLÊ\™]\›ˆŽÙOYKœ™]\›Ÿ\™]\›–×_Y[˜Ý[Ûˆ]JJ^ÚYŠOOO[[
\™]\›ˆ[ÙÈOYKœ™]\›ŽÝÚ[JI‰™KYÈOOMI‰™KYÈOOLÊNÜ™]\›ˆ_[Y[˜Ý[ÛˆY
K‹‹J^Ù›ÜŠ˜\ˆO]—Ü™XXÝ˜[YKÏV×NÛˆOO[[	‰›ˆOO\ŽÊ^Ý˜\ˆÏ[‹\Ë˜[\›˜]KO\ËœÝ]S›ÙNÚYŠÏ\ËYËOO[[	‰›OO\ŠXœ™XZÎÜÈOOMI‰œÈOOL‰‰œÈOOLßOOO[[
]KOÊOTÛŠ‹JKHO[[	‰›Ë[œÚY
Y
‹K
JJNš_
OTÛŠ‹JKHO[[	‰›Ëœ\Ú
Y
‹K
JJJK[‹œ™]\›Ÿ[Ë›[™ÝOOL	‰™Kœ\Ú
Ù]™[\Ý[™\œÎ›ßJ_]˜\ˆOK×—ËÙËK×LQ‘‘‘ÙÎÙ[˜Ý[ÛˆJJ^Ü™]\›Š\[ÙˆOOXÝš[™ØÙN˜
ÙJKœ™\XÙJK˜
Kœ™\XÙJ
_Y[˜Ý[Ûˆ™
K
^Ü™]\›ˆYJ
KJJOOO]Y[˜Ý[ÛˆY
K‹‹KÊ^ÜÝÚ]Ú
Š^ØØ\ÙXÚ[™[˜šYŠ\[ÙˆOXÝš[™Ø
]OOX›ÙXOOX^\™XX	‰œOOXÛŠKŠNÙ[ÙHYŠ\[ÙˆOX[X™\˜\[ÙˆOXšYÚ[
]OOX›ÙX	‰˜ÛŠK
ÜŠNÙ[ÙH™]\›ŽØœ™XZÎØØ\ÙXÛ\ÜÓ˜[YX’Ý
KÛ\ÜØŠNØœ™XZÎØØ\ÙXX’[™^’Ý
KXš[™^ŠNØœ™XZÎØØ\ÙX\˜˜Ø\ÙX›ÛX˜Ø\ÙXšY]Ð›Þ˜Ø\ÙXÚY˜Ø\ÙXZYÚ’Ý
K‹ŠNØœ™XZÎØØ\ÙXÝ[X›ŠK‹ÊNÜ™]\›ŽØØ\ÙX]XšYŠOOXØš™XÝ
^ÒÝ
K]XŠNØœ™XZßXØ\ÙXÜ˜Ø˜Ø\ÙX™Y˜šYŠOOX	‰ŠOOXXˆOOX™Y˜
J^ÙKœ™[[Ý™P]šX]JŠNØœ™XZßZYŠO[[\[ÙˆOX[˜Ý[Û˜\[ÙˆOXÞ[X›Û\[ÙˆOX›ÛÛX[˜
^ÙKœ™[[Ý™P]šX]JŠNØœ™XZß\\ŠŠKKœÙ]]šX]J‹ŠNØœ™XZÎØØ\ÙXXÝ[Û˜˜Ø\ÙX›Ü›PXÝ[Û˜šYŠ\[ÙˆOX[˜Ý[Û˜
^ÙKœÙ]]šX]J‹˜]˜\ØÜš\›ÝÈ™]È\œ›ÜŠ	ÐH™XXÝ›Ü›HØ\È[™^XÝYHÝX›Z]YˆYˆ[ÝHØ[Y›Ü›KœÝX›Z]

HX[X[KÛÛœÚY\ˆ\Ú[™È›Ü›Kœ™\]Y\ÝÝX›Z]

H[œÝXYˆYˆ[ÝW	Ü™HžZ[™ÈÈ\ÙH]™[œÝÜ›ÜYØ][ÛŠ
H[ˆHÝX›Z]]™[[™\‹ÛÛœÚY\ˆ[ÛÈØ[[™È]™[œ™]™[Y˜][

K‰ÊX
NØœ™XZßY[ÙH\[ÙˆÏOX[˜Ý[Û˜	‰ŠOOX›Ü›PXÝ[Û˜ÊOOX[œ]	‰”Y
K˜[YXK›˜[YKK[
KY
K›Ü›Q[˜Õ\XK™›Ü›Q[˜Õ\KK[
KY
K›Ü›SY]ÙK™›Ü›SY]ÙK[
KY
K›Ü›U\™Ù]K™›Ü›U\™Ù]K[
JNŠY
K[˜Õ\XK™[˜Õ\KK[
KY
KY]ÙK›Y]ÙK[
KY
K\™Ù]K\™Ù]K[
JJNÚYŠO[[\[ÙˆOXÞ[X›Û\[ÙˆOX›ÛÛX[˜
^ÙKœ™[[Ý™P]šX]JŠNØœ™XZß\\ŠŠKKœÙ]]šX]J‹ŠNØœ™XZÎØØ\ÙXÛÛXÚØœˆO[[	‰ŠK›Û˜ÛXÚÏ[[ŠNÜ™]\›ŽØØ\ÙXÛ”ØÜ›ÛœˆO[[	‰’
ØÜ›ÛJNÜ™]\›ŽØØ\ÙXÛ”ØÜ›Û[™œˆO[[	‰’
ØÜ›Û[™JNÜ™]\›ŽØØ\ÙX[™Ù\›Ý\ÛTÙ][›™\’SšYŠˆO[[
^ÚYŠ\[ÙˆˆOXØš™XÝJ×Ú[[ˆŠJ]›ÝÈ\œ›ÜŠJŒJJNÚYŠ\‹—×Ú[ˆO[[
^ÚYŠK˜Ú[™[ˆO[[
]›ÝÈ\œ›ÜŠJŒ
JNÛÏË—×Ú[OO[‰‰ŠKš[›™\’S[Š__Xœ™XZÎØØ\ÙX][\X™K›][\O\‰‰\[ÙˆˆOX[˜Ý[Û˜	‰\[ÙˆˆOXÞ[X›ÛØœ™XZÎØØ\ÙX]]Y™K›]]Y\‰‰\[ÙˆˆOX[˜Ý[Û˜	‰\[ÙˆˆOXÞ[X›ÛØœ™XZÎØØ\ÙXÝ\™\ÜÐÛÛ[Y]X›UØ\›š[™Ø˜Ø\ÙXÝ\™\ÜÒY˜][Û•Ø\›š[™Ø˜Ø\ÙXY˜][˜[YX˜Ø\ÙXY˜][ÚXÚÙY˜Ø\ÙX[›™\’S˜Ø\ÙX™Y˜˜œ™XZÎØØ\ÙX]]Ñ›ØÝ\Ø˜œ™XZÎØØ\ÙX[šÒ™Y˜šYŠO[[\[ÙˆOX[˜Ý[Û˜\[ÙˆOX›ÛÛX[˜\[ÙˆOXÞ[X›Û
^ÙKœ™[[Ý™P]šX]J[šÎš™Y˜
NØœ™XZß[\ŠŠKKœÙ]]šX]S”Ê‹ËÝÝÝËÌË›Ü™ËÌNNNKÞ[šØ[šÎš™Y˜ŠNØœ™XZÎØØ\ÙXÛÛ[Y]X›X˜Ø\ÙXÜ[ÚXÚØ˜Ø\ÙX˜YÙØX›X˜Ø\ÙX˜[YX˜Ø\ÙX]]Ô™]™\œÙX˜Ø\ÙX^\›˜[™\ÛÝ\˜Ù\Ô™\]Z\™Y˜Ø\ÙX›ØÝ\ØX›X˜Ø\ÙX™\Ù\™P[XœˆO[[	‰\[ÙˆˆOX[˜Ý[Û˜	‰\[ÙˆˆOXÞ[X›ÛÙKœÙ]]šX]J‹ŠN™Kœ™[[Ý™P]šX]JŠNØœ™XZÎØØ\ÙX[™\˜Ø\ÙX[ÝÑ[ØÜ™Y[˜˜Ø\ÙX\Þ[˜Ø˜Ø\ÙX]]Ô^X˜Ø\ÙXÛÛ›ÛØ˜Ø\ÙXÜ™Y[X[\ÜØ˜Ø\ÙXY˜][˜Ø\ÙXY™\˜˜Ø\ÙX\ØX›Y˜Ø\ÙX\ØX›TXÝ\™R[”XÝ\™X˜Ø\ÙX\ØX›T™[[ÝT^X˜XÚØ˜Ø\ÙX›Ü›S›Õ˜[Y]X˜Ø\ÙXY[˜˜Ø\ÙXÛÜ˜Ø\ÙX›Ó[Ù[X˜Ø\ÙX›Õ˜[Y]X˜Ø\ÙXÜ[˜˜Ø\ÙX^\Ò[›[™X˜Ø\ÙX™XYÛ›X˜Ø\ÙX™\]Z\™Y˜Ø\ÙX™]™\œÙY˜Ø\ÙXØÛÜY˜Ø\ÙXÙX[[\ÜØ˜Ø\ÙX][TØÛÜXœ‰‰\[ÙˆˆOX[˜Ý[Û˜	‰\[ÙˆˆOXÞ[X›ÛÙKœÙ]]šX]J‹
N™Kœ™[[Ý™P]šX]JŠNØœ™XZÎØØ\ÙXØ\\™X˜Ø\ÙXÝÛ›ØYˆLOO\ÙKœÙ]]šX]J‹
NˆLHOO\‰‰œˆO[[	‰\[ÙˆˆOX[˜Ý[Û˜	‰\[ÙˆˆOXÞ[X›ÛÙKœÙ]]šX]J‹ŠN™Kœ™[[Ý™P]šX]JŠNØœ™XZÎØØ\ÙXÛÛØ˜Ø\ÙX›ÝÜØ˜Ø\ÙXÚ^™X˜Ø\ÙXÜ[˜œˆO[[	‰\[ÙˆˆOX[˜Ý[Û˜	‰\[ÙˆˆOXÞ[X›Û	‰ˆZ\Ó˜SŠŠI‰ŒO\ÙKœÙ]]šX]J‹ŠN™Kœ™[[Ý™P]šX]JŠNØœ™XZÎØØ\ÙX›ÝÔÜ[˜˜Ø\ÙXÝ\œO[[\[ÙˆOX[˜Ý[Û˜\[ÙˆOXÞ[X›Û\Ó˜SŠŠOÙKœ™[[Ý™P]šX]JŠN™KœÙ]]šX]J‹ŠNØœ™XZÎØØ\ÙXÜÝ™\˜’
™Y›Ü™]ÙÙÛXJK
ÙÙÛXJKÝ
KÜÝ™\˜ŠNØœ™XZÎØØ\ÙX[šÐXÝX]Xœ]
K‹ËÝÝÝËÌË›Ü™ËÌNNNKÞ[šØ[šÎ˜XÝX]XŠNØœ™XZÎØØ\ÙX[šÐ\˜Ü›ÛXœ]
K‹ËÝÝÝËÌË›Ü™ËÌNNNKÞ[šØ[šÎ˜\˜Ü›ÛXŠNØœ™XZÎØØ\ÙX[šÔ›ÛXœ]
K‹ËÝÝÝËÌË›Ü™ËÌNNNKÞ[šØ[šÎœ›ÛXŠNØœ™XZÎØØ\ÙX[šÔÚÝØœ]
K‹ËÝÝÝËÌË›Ü™ËÌNNNKÞ[šØ[šÎœÚÝØŠNØœ™XZÎØØ\ÙX[šÕ]Xœ]
K‹ËÝÝÝËÌË›Ü™ËÌNNNKÞ[šØ[šÎ]XŠNØœ™XZÎØØ\ÙX[šÕ\Xœ]
K‹ËÝÝÝËÌË›Ü™ËÌNNNKÞ[šØ[šÎ\XŠNØœ™XZÎØØ\ÙX[˜\ÙXœ]
K‹ËÝÝÝËÌË›Ü™ËÖSÌNNNÛ˜[Y\ÜXÙX[˜˜\ÙXŠNØœ™XZÎØØ\ÙX[[™Øœ]
K‹ËÝÝÝËÌË›Ü™ËÖSÌNNNÛ˜[Y\ÜXÙX[›[™ØŠNØœ™XZÎØØ\ÙX[ÜXÙXœ]
K‹ËÝÝÝËÌË›Ü™ËÖSÌNNNÛ˜[Y\ÜXÙX[œÜXÙXŠNØœ™XZÎØØ\ÙX\Ø‘Ý
K\ØŠNØœ™XZÎØØ\ÙX[›™\•^˜Ø\ÙX^ÛÛ[œ™]\›ŽÙY˜][šYŠJ‹›[™Ý
_–ÌHOOXØ	‰›–ÌHOOXØ–ÌWHOOX˜	‰›–ÌWHOOX˜
[Y‹™Ù]
Š_‹Ý
K‹ŠNÙ[ÙH™]\›ŸU]HLY[˜Ý[Ûˆ	
K‹‹KÊ^ÜÝÚ]Ú
Š^ØØ\ÙXÝ[X›ŠK‹ÊNÜ™]\›ŽØØ\ÙX[™Ù\›Ý\ÛTÙ][›™\’SšYŠˆO[[
^ÚYŠ\[ÙˆˆOXØš™XÝJ×Ú[[ˆŠJ]›ÝÈ\œ›ÜŠJŒJJNÚYŠ\‹—×Ú[ˆO[[
^ÚYŠK˜Ú[™[ˆO[[
]›ÝÈ\œ›ÜŠJŒ
JNÛÏË—×Ú[OO[‰‰ŠKš[›™\’S[Š__Xœ™XZÎØØ\ÙXÚ[™[˜šYŠ\[ÙˆOXÝš[™Ø
XÛŠKŠNÙ[ÙHYŠ\[ÙˆOX[X™\˜\[ÙˆOXšYÚ[
XÛŠK
ÜŠNÙ[ÙH™]\›ŽØœ™XZÎØØ\ÙXÛ”ØÜ›ÛœˆO[[	‰’
ØÜ›ÛJNÜ™]\›ŽØØ\ÙXÛ”ØÜ›Û[™œˆO[[	‰’
ØÜ›Û[™JNÜ™]\›ŽØØ\ÙXÛÛXÚØœˆO[[	‰ŠK›Û˜ÛXÚÏ[[ŠNÜ™]\›ŽØØ\ÙXÝ\™\ÜÐÛÛ[Y]X›UØ\›š[™Ø˜Ø\ÙXÝ\™\ÜÒY˜][Û•Ø\›š[™Ø˜Ø\ÙX[›™\’S˜Ø\ÙX™Y˜œ™]\›ŽØØ\ÙX[›™\•^˜Ø\ÙX^ÛÛ[œ™]\›ŽÙY˜][šYŠR]š\ÓÝÛ”›Ü\JŠJXNžÚYŠ–ÌOOOXØ	‰›–ÌWOOOX˜	‰ŠO[‹™[™ÕÚ]
Ø\\™X
KÏ[‹œÛXÙJ‹OÛ‹›[™ÝMÎ›ÚY
KYVØ_[]O[[Û[Û—K\[ÙˆOX[˜Ý[Û˜	‰™Kœ™[[Ý™Q]™[\Ý[™\ŠËJK\[ÙˆOX[˜Ý[Û˜
J^Ý\[ÙˆOX[˜Ý[Û˜	‰OO[[	‰Šˆ[ˆOÙVÛ—O[[™Kš\Ð]šX]JŠI‰™Kœ™[[Ý™P]šX]JŠJKK˜Y]™[\Ý[™\ŠË‹JNØœ™XZÈ_U]HLˆ[ˆOÙVÛ—O\ŽˆLOO\ÙKœÙ]]šX]J‹
N‘Ý
K‹Š_\™]\›ŸU]HLY[˜Ý[ÛˆYŠKŠ^ÜÝÚ]Ú

^ØØ\ÙX]˜˜Ø\ÙXÜ[˜˜Ø\ÙXÝ™Ø˜Ø\ÙX]˜Ø\ÙXX˜Ø\ÙXØ˜Ø\ÙX˜Ø\ÙXX˜œ™XZÎØØ\ÙX[YØ’
\œ›Ü˜JK
ØYJNÝ˜\ˆHLKOHLKÎÙ›ÜŠÈ[ˆŠZYŠ‹š\ÓÝÛ”›Ü\JÊJ^Ý˜\ˆÏ[–Û×NÚYŠÈO[[
\ÝÚ]Ú
Ê^ØØ\ÙXÜ˜ØœHLØœ™XZÎØØ\ÙXÜ˜ÔÙ]˜OHLØœ™XZÎØØ\ÙXÚ[™[˜˜Ø\ÙX[™Ù\›Ý\ÛTÙ][›™\’S›ÝÈ\œ›ÜŠJLÍË
JNÙY˜][”Y
KËË‹[
__XI‰”Y
KÜ˜ÔÙ]‹œÜ˜ÔÙ]‹[
K‰‰”Y
KÜ˜Ø‹œÜ˜Ë‹[
NÜ™]\›ŽØØ\ÙX[œ]’
[˜[YJNÝ˜\ˆ[Ï\ÏXO[[O[[[[Ù›ÜŠˆ[ˆŠZYŠ‹š\ÓÝÛ”›Ü\JŠJ^Ý˜\ˆ[–Ü—NÚYŠˆO[[
\ÝÚ]Ú
Š^ØØ\ÙX˜[YX˜OYŽØœ™XZÎØØ\ÙX\XœÏYŽØœ™XZÎØØ\ÙXÚXÚÙYOYŽØœ™XZÎØØ\ÙXY˜][ÚXÚÙY™YŽØœ™XZÎØØ\ÙX˜[YX›ÏYŽØœ™XZÎØØ\ÙXY˜][˜[YX›YŽØœ™XZÎØØ\ÙXÚ[™[˜˜Ø\ÙX[™Ù\›Ý\ÛTÙ][›™\’SšYŠˆO[[
]›ÝÈ\œ›ÜŠJLÍË
JNØœ™XZÎÙY˜][”Y
K‹‹‹[
__[›ŠKËKËKLJNÜ™]\›ŽØØ\ÙXÙ[XÝ™›ÜŠH[ˆ
[˜[YJK\Ï[Ï[[ŠZYŠ‹š\ÓÝÛ”›Ü\JJI‰Š[–ØWKO[[
J\ÝÚ]Ú
J^ØØ\ÙX˜[YX›Ï[Øœ™XZÎØØ\ÙXY˜][˜[YXœÏ[Øœ™XZÎØØ\ÙX][\Xœ[ÙY˜][”Y
KK‹[
_][Ë\ËK›][\OHH\‹O[[ÛˆO[[	‰˜[ŠKH\‹‹L
N˜[ŠKH\‹LJNÜ™]\›ŽØØ\ÙX^\™XX™›ÜŠÈ[ˆ
[˜[YJKÏXO\[[ŠZYŠ‹š\ÓÝÛ”›Ü\JÊI‰Š[–Ü×KO[[
J\ÝÚ]Ú
Ê^ØØ\ÙX˜[YXœ[Øœ™XZÎØØ\ÙXY˜][˜[YX˜O[Øœ™XZÎØØ\ÙXÚ[™[˜›Ï[Øœ™XZÎØØ\ÙX[™Ù\›Ý\ÛTÙ][›™\’SšYŠO[[
]›ÝÈ\œ›ÜŠJLJJNØœ™XZÎÙY˜][”Y
KË‹[
_\ÛŠK‹KÊNÜ™]\›ŽØØ\ÙXÜ[Û˜™›ÜŠH[ˆŠZYŠ‹š\ÓÝÛ”›Ü\JJI‰Š[–ÝWKˆO[[
J\ÝÚ]Ú
J^ØØ\ÙXÙ[XÝY™KœÙ[XÝY\‰‰\[ÙˆˆOX[˜Ý[Û˜	‰\[ÙˆˆOXÞ[X›ÛØœ™XZÎÙY˜][”Y
KK‹‹[
_\™]\›ŽØØ\ÙXX[ÙØ’
™Y›Ü™]ÙÙÛXJK
ÙÙÛXJK
Ø[˜Ù[JK
ÛÜÙXJNØœ™XZÎØØ\ÙXYœ˜[YX˜Ø\ÙXØš™XÝ’
ØYJNØœ™XZÎØØ\ÙXšY[Ø˜Ø\ÙX]Y[Ø™›ÜŠLÜ™›[™ÝÜŠÊÊR
™Ü—KJNØœ™XZÎØØ\ÙX[XYÙX’
\œ›Ü˜JK
ØYJNØœ™XZÎØØ\ÙX]Z[Ø’
ÙÙÛXJNØœ™XZÎØØ\ÙX[X™Y˜Ø\ÙXÛÝ\˜ÙX˜Ø\ÙX[šØ’
\œ›Ü˜JK
ØYJNØØ\ÙX\™XX˜Ø\ÙX˜\ÙX˜Ø\ÙXœ˜˜Ø\ÙXÛÛ˜Ø\ÙX˜˜Ø\ÙXÙ^YÙ[˜˜Ø\ÙXY]X˜Ø\ÙX\˜[X˜Ø\ÙX˜XÚØ˜Ø\ÙXØœ˜˜Ø\ÙXY[Z][X™›ÜŠ[ˆŠZYŠ‹š\ÓÝÛ”›Ü\J
I‰Š[–ÙKˆO[[
J\ÝÚ]Ú

^ØØ\ÙXÚ[™[˜˜Ø\ÙX[™Ù\›Ý\ÛTÙ][›™\’S›ÝÈ\œ›ÜŠJLÍË
JNÙY˜][”Y
K‹‹[
_\™]\›ŽÙY˜][šYŠ[Š
J^Ù›ÜŠˆ[ˆŠ[‹š\ÓÝÛ”›Ü\JŠI‰Š[–Ù—KˆOO]›ÚY	‰‰
K‹‹‹›ÚY
JNÜ™]\›Ÿ_Y›ÜŠ[ˆŠ[‹š\ÓÝÛ”›Ü\J
I‰Š[–ÛKˆO[[	‰”Y
K‹‹[
J_]˜\ˆO^ßNÙ[˜Ý[Ûˆ]JK‹Š^ÜÝÚ]Ú

^ØØ\ÙX]˜˜Ø\ÙXÜ[˜˜Ø\ÙXÝ™Ø˜Ø\ÙX]˜Ø\ÙXX˜Ø\ÙXØ˜Ø\ÙX˜Ø\ÙXX˜œ™XZÎØØ\ÙX[œ]˜\ˆO[[Ï[[Ï[[[[O[[[[[[Ù›ÜŠ[ˆŠ^Ý˜\ˆ[–ÚNÚYŠ‹š\ÓÝÛ”›Ü\J
I‰œO[[
\ÝÚ]Ú

^ØØ\ÙXÚXÚÙY˜œ™XZÎØØ\ÙX˜[YX˜œ™XZÎØØ\ÙXY˜][˜[YXO\ÙY˜][œ‹š\ÓÝÛ”›Ü\J
_Y
K[‹
__Y›ÜŠ˜\ˆH[ˆŠ^Ý˜\ˆ\–ÛWNÚYŠ[–ÛWK‹š\ÓÝÛ”›Ü\JJI‰ŠO[[O[[
J\ÝÚ]Ú
J^ØØ\ÙX\XšOO\	‰Š]HL
KÏZØœ™XZÎØØ\ÙX˜[YXšOO\	‰Š]HL
KOZØœ™XZÎØØ\ÙXÚXÚÙYšOO\	‰Š]HL
KZØœ™XZÎØØ\ÙXY˜][ÚXÚÙYšOO\	‰Š]HL
KZØœ™XZÎØØ\ÙX˜[YXšOO\	‰Š]HL
KÏZØœ™XZÎØØ\ÙXY˜][˜[YXšOO\	‰Š]HL
KZØœ™XZÎØØ\ÙXÚ[™[˜˜Ø\ÙX[™Ù\›Ý\ÛTÙ][›™\’SšYŠO[[
]›ÝÈ\œ›ÜŠJLÍË
JNØœ™XZÎÙY˜][šOO\	‰”Y
KK‹
__]ŠKËK‹ËJNÜ™]\›ŽØØ\ÙXÙ[XÝ™›ÜŠÈ[ˆ\Ï[[O[[ŠZYŠO[–Û×K‹š\ÓÝÛ”›Ü\JÊI‰HO[[
\ÝÚ]Ú
Ê^ØØ\ÙX˜[YX˜œ™XZÎØØ\ÙX][\Xš]NÙY˜][œ‹š\ÓÝÛ”›Ü\JÊ_Y
KË[‹J_Y›ÜŠH[ˆŠZYŠÏ\–ØWKO[–ØWK‹š\ÓÝÛ”›Ü\JJI‰ŠÈO[[HO[[
J\ÝÚ]Ú
J^ØØ\ÙX˜[YX›ÈOO]I‰Š]HL
KO[ÎØœ™XZÎØØ\ÙXY˜][˜[YX›ÈOO]I‰Š]HL
K[ÎØœ™XZÎØØ\ÙX][\X›ÈOO]I‰Š]HL
KÏ[ÎÙY˜][›ÈOO]I‰”Y
KKË‹J_][\ËZOO[[ÈH\ˆOHH[‰‰ŠO[[Ø[ŠKH[‹Ö×N˜LJN˜[ŠKH[‹L
JN˜[ŠKH[‹KLJNÜ™]\›ŽØØ\ÙX^\™XX™›ÜŠ[ˆ[O[[ŠZYŠO[–ÛK‹š\ÓÝÛ”›Ü\J
I‰˜HO[[	‰ˆ\‹š\ÓÝÛ”›Ü\J
J\ÝÚ]Ú

^ØØ\ÙX˜[YX˜œ™XZÎØØ\ÙXÚ[™[˜˜œ™XZÎÙY˜][”Y
K[‹J_Y›ÜŠÈ[ˆŠZYŠO\–Ü×KÏ[–Ü×K‹š\ÓÝÛ”›Ü\JÊI‰ŠHO[[ÈO[[
J\ÝÚ]Ú
Ê^ØØ\ÙX˜[YX˜HOO[É‰Š]HL
KOXNØœ™XZÎØØ\ÙXY˜][˜[YX˜HOO[É‰Š]HL
KXNØœ™XZÎØØ\ÙXÚ[™[˜˜œ™XZÎØØ\ÙX[™Ù\›Ý\ÛTÙ][›™\’SšYŠHO[[
]›ÝÈ\œ›ÜŠJLJJNØœ™XZÎÙY˜][˜HOO[É‰”Y
KËK‹Ê_[ÛŠKK
NÜ™]\›ŽØØ\ÙXÜ[Û˜™›ÜŠ˜\ˆÈ[ˆŠZYŠO[–Ù×K‹š\ÓÝÛ”›Ü\JÊI‰›HO[[	‰ˆ\‹š\ÓÝÛ”›Ü\JÊJ\ÝÚ]Ú
Ê^ØØ\ÙXÙ[XÝY™KœÙ[XÝYHLNØœ™XZÎÙY˜][”Y
KË[‹J_Y›ÜŠH[ˆŠZYŠO\–ÝWK[–ÝWK‹š\ÓÝÛ”›Ü\JJI‰›HOOZ	‰ŠHO[[O[[
J\ÝÚ]Ú
J^ØØ\ÙXÙ[XÝY›HOOZ	‰Š]HL
KKœÙ[XÝY[I‰\[ÙˆHOX[˜Ý[Û˜	‰\[ÙˆHOXÞ[X›ÛØœ™XZÎÙY˜][”Y
KKK‹
_\™]\›ŽØØ\ÙX[YØ˜Ø\ÙX[šØ˜Ø\ÙX\™XX˜Ø\ÙX˜\ÙX˜Ø\ÙXœ˜˜Ø\ÙXÛÛ˜Ø\ÙX[X™Y˜Ø\ÙX˜˜Ø\ÙXÙ^YÙ[˜˜Ø\ÙXY]X˜Ø\ÙX\˜[X˜Ø\ÙXÛÝ\˜ÙX˜Ø\ÙX˜XÚØ˜Ø\ÙXØœ˜˜Ø\ÙXY[Z][X™›ÜŠ˜\ˆÈ[ˆŠ[O[–××K‹š\ÓÝÛ”›Ü\JÊI‰›HO[[	‰ˆ\‹š\ÓÝÛ”›Ü\JÊI‰”Y
KË[‹JNÙ›ÜŠ[ˆŠZYŠO\–ÙK[–ÙK‹š\ÓÝÛ”›Ü\J
I‰›HOOZ	‰ŠHO[[O[[
J\ÝÚ]Ú

^ØØ\ÙXÚ[™[˜˜Ø\ÙX[™Ù\›Ý\ÛTÙ][›™\’SšYŠHO[[
]›ÝÈ\œ›ÜŠJLÍË
JNØœ™XZÎÙY˜][”Y
KK‹
_\™]\›ŽÙY˜][šYŠ[Š
J^Ù›ÜŠ˜\ˆˆ[ˆŠ[O[–Ý—K‹š\ÓÝÛ”›Ü\JŠI‰›HOO]›ÚY	‰ˆ\‹š\ÓÝÛ”›Ü\JŠI‰‰
K‹›ÚY‹JNÙ›ÜŠˆ[ˆŠ[O\–Ù—K[–Ù—K\‹š\ÓÝÛ”›Ü\JŠ_OOOZOOO]›ÚY	‰šOO]›ÚY	
K‹K‹
NÜ™]\›Ÿ_Y›ÜŠ˜\ˆH[ˆŠ[O[–ÞWK‹š\ÓÝÛ”›Ü\JJI‰›HO[[	‰ˆ\‹š\ÓÝÛ”›Ü\JJI‰”Y
KK[‹JNÙ›ÜŠ[ˆŠ[O\–ÜK[–ÜK\‹š\ÓÝÛ”›Ü\J
_OOOZOO[[	‰šO[[Y
KK‹
_Y[˜Ý[ÛˆŠJ^ÜÝÚ]Ú
J^ØØ\ÙXÜÜØ˜Ø\ÙXØÜš\˜Ø\ÙX›Û˜Ø\ÙX[YØ˜Ø\ÙX[XYÙX˜Ø\ÙX[œ]˜Ø\ÙX[šØœ™]\›ˆLÙY˜][œ™]\›ˆL__Y[˜Ý[ÛˆJ
^ÚYŠ\[Ùˆ\™›Ü›X[˜ÙK™Ù][šY\ÐžU\OOX[˜Ý[Û˜
^Ù›ÜŠ˜\ˆOLL\\™›Ü›X[˜ÙK™Ù][šY\ÐžU\J™\ÛÝ\˜ÙX
KLÜ‹›[™ÝÜŠÊÊ^Ý˜\ˆO[–Ü—KOZK˜[œÙ™\”Ú^™KÏZKš[š]X]Ü•\KÏZK™\˜][ÛŽÚYŠI‰œÉ‰ŠÊJ^Ù›ÜŠÏLÏZKœ™\ÜÛœÙQ[™ŠÏLNÜ‹›[™ÝÜŠÊÊ^Ý˜\ˆ[–Ü—KO[œÝ\[YNÚYŠOœÊXœ™XZÎÝ˜\ˆ[˜[œÙ™\”Ú^™K[š[š]X]Ü•\NÙ	‰ŠŠI‰Š[œ™\ÜÛœÙQ[™ÊÏY
ŠÏÌNŠË]JKÊ]JJJ_ZYŠK\‹
ÏN
ŠJÛÊKÊK™\˜][Û‹ÌYLÊKJÊËLJXœ™XZß_ZYŠJ\™]\›ˆÙKÌYMŸ\™]\›ˆ˜]šYØ]Ü‹˜ÛÛ›™XÝ[Û‰‰ŠO[˜]šYØ]Ü‹˜ÛÛ›™XÝ[Û‹™ÝÛ›[šË\[ÙˆOOX[X™\˜
OÙN_]˜\ˆ™[[™[[Ù[˜Ý[ÛˆYŠJ^Ü™]\›ˆK››ÙU\OOONOÙN™K›ÝÛ™\‘ØÝ[Y[Y[˜Ý[ÛˆÙŠJ^ÜÝÚ]Ú
J^ØØ\ÙX‹ËÝÝÝËÌË›Ü™ËÌŒÜÝ™Øœ™]\›ˆNØØ\ÙX‹ËÝÝÝËÌË›Ü™ËÌNNNÓX]ÓX]Sœ™]\›ˆŽÙY˜][œ™]\›ˆ_Y[˜Ý[ÛˆÝJK
^ÚYŠOOOL
\ÝÚ]Ú

^ØØ\ÙXÝ™Øœ™]\›ˆNØØ\ÙXX]œ™]\›ˆŽÙY˜][œ™]\›ˆ\™]\›ˆOOOLI‰OOX›Ü™ZYÛ“Øš™XÝÌ™_Y[˜Ý[ÛˆÙŠK‹Š^Ü™]\›ˆXYŠŠK˜Ü™X]Q[[Y[
JK–Þ]O\‹–ØO]YŠ‹K
K
ŠKŸY[˜Ý[ÛˆÙŠK
^Ü™]\›ˆOOOX^\™XXOOOX›ÜØÜš\\[Ùˆ˜Ú[™[OXÝš[™Ø\[Ùˆ˜Ú[™[OX[X™\˜\[Ùˆ˜Ú[™[OXšYÚ[\[Ùˆ™[™Ù\›Ý\ÛTÙ][›™\’SOXØš™XÝ	‰™[™Ù\›Ý\ÛTÙ][›™\’SOO[[	‰™[™Ù\›Ý\ÛTÙ][›™\’S—×Ú[O[[]˜\ˆ[[Ù[˜Ý[ÛˆÝJ
^Ý˜\ˆO]Ú[™ÝË™]™[Ü™]\›ˆI‰™K\OOOXÜÝ]XÙOOO[ÈLNŠYKL
NŠ[[LJ_]˜\ˆY]\[ÙˆÙ][Y[Ý]OX[˜Ý[Û˜ÜÙ][Y[Ý]›ÚY]\[ÙˆÛX\•[Y[Ý]OX[˜Ý[Û˜ØÛX\•[Y[Ý]›ÚYO]\[Ùˆ›ÛZ\ÙOOX[˜Ý[Û˜Ô›ÛZ\ÙN›ÚY™]\[Ùˆ™\]Y\Ý[š[X][Û‘œ˜[YOOX[˜Ý[Û˜Ü™\]Y\Ý[š[X][Û‘œ˜[YNY‹]O]\[Ùˆ]Y]YSZXÜ›Ý\ÚÏOX[˜Ý[Û˜Ü]Y]YSZXÜ›Ý\ÚÎOOO]›ÚYÝYŽ™[˜Ý[ÛŠJ^Ü™]\›ˆKœ™\ÛÛ™J[
K[ŠJK˜Ø]Ú
Š_NÙ[˜Ý[ÛˆŠJ^ÜÙ][Y[Ý]
[˜Ý[ÛŠ
^Ý›ÝÈ_J_Y[˜Ý[ÛˆYŠJ^Ü™]\›ˆOOOXXYY[˜Ý[ÛˆŠK
^Ý˜\ˆ]LÙÞÝ˜\ˆO[‹›™^ÚX›[™ÎÚYŠKœ™[[Ý™PÚ[
ŠKI‰šK››ÙU\OOON
ZYŠZK™]KOOXÉOOXÉ˜
^ÚYŠOOL
^ÙKœ™[[Ý™PÚ[
JKœ

NÜ™]\›Ÿ\‹K_Y[ÙHYŠOOX	OOX	ØOOX	˜OOX	XOOX	˜
\ŠÊÎÙ[ÙHYŠOOX[
UÙŠK›ÝÛ™\‘ØÝ[Y[™ØÝ[Y[[[Y[
NÙ[ÙHYŠOOXXY
^ÛYK›ÝÛ™\‘ØÝ[Y[šXYÙŠŠNÙ›ÜŠ˜\ˆO[‹™š\œÝÚ[ØNÊ^Ý˜\ˆÏXK›™^ÚX›[™ËÏXK››ÙS˜[YNØVÑ]_ÏOOXÐÔ’TÏOOXÕSXÏOOXS’Ø	‰˜Kœ™[ÓÝÙ\Ø\ÙJ
OOOXÝ[\ÚY]‹œ™[[Ý™PÚ[
JKO[ß_Y[ÙHOOX›ÙX	‰•ÙŠK›ÝÛ™\‘ØÝ[Y[˜›ÙJNÛZ_]Ú[JŠNÖœ

_Y[˜Ý[ÛˆÙŠK
^Ý˜\ˆYNÙOLÙÞÝ˜\ˆ[‹›™^ÚX›[™ÎÚYŠ‹››ÙU\OOOLOÝÊ‹—ÜÝ\ÚY\Ü^O[‹œÝ[K™\Ü^K‹œÝ[K™\Ü^OX›Û™X
NŠ‹œÝ[K™\Ü^O[‹—ÜÝ\ÚY\Ü^_‹™Ù]]šX]JÝ[X
OOOX	‰›‹œ™[[Ý™P]šX]JÝ[X
JN›‹››ÙU\OOOLÉ‰ŠÊ‹—ÜÝ\ÚY^[‹››ÙU˜[YK‹››ÙU˜[YOX
N›‹››ÙU˜[YO[‹—ÜÝ\ÚY^
K‰‰œ‹››ÙU\OOON
ZYŠ\‹™]KOOXÉ
^ÚYŠOOOL
Xœ™XZÎÙKK_Y[ÙHˆOOX		‰›ˆOOX	Ø	‰›ˆOOX	˜	‰›ˆOOX	XJÊÎÛ\Ÿ]Ú[JŠ_Y[˜Ý[ÛˆJKŠ^ÚYŠPÔÔË™\ØØ\J
OOO]Ý˜‹X
ØØJ
Kœ™\XÙJÏKÙË
KKœÝ[KšY]Õ˜[œÚ][Û“˜[YO]ˆO[[	‰ŠKœÝ[KšY]Õ˜[œÚ][ÛÛ\ÜÏ[ŠKYÙ]ÛÛ\]YÝ[JJK‹™\Ü^OOOX[›[™X
^ÚYŠYK™Ù]ÛY[™XÝÊ
K›[™ÝOOLJ]˜\ˆLNÙ[ÙH›ÜŠ˜\ˆO\LÚO›[™ÝÚJÊÊ^Ý˜\ˆO]ÚWNÌKÚY	‰ŒKšZYÚ	‰œŠÊß\OOLI‰ŠOYKœÝ[KK™\Ü^O]›[™ÝOOLOØ[›[™KX›ØÚØ˜›ØÚØK›X\™Ú[•ÜXX
Û‹œY[™ÕÜK›X\™Ú[›ÝÛOXX
Û‹œY[™Ð›ÝÛJ__Y[˜Ý[ÛˆÙŠK
^ÙOYKœÝ[K]œÝ[NÝ˜\ˆ]O[[Û[š\ÓÝÛ”›Ü\JšY]Õ˜[œÚ][Û“˜[YX
OÝšY]Õ˜[œÚ][Û“˜[YNš\ÓÝÛ”›Ü\JšY]Ë]˜[œÚ][Û‹[˜[YX
OÝØšY]Ë]˜[œÚ][Û‹[˜[YXN›[ÙKšY]Õ˜[œÚ][Û“˜[YO[O[[\[ÙˆOX›ÛÛX[˜ØŠ
ÛŠKš[J
K]O[[Û[š\ÓÝÛ”›Ü\JšY]Õ˜[œÚ][ÛÛ\ÜØ
OÝšY]Õ˜[œÚ][ÛÛ\ÜÎš\ÓÝÛ”›Ü\JšY]Ë]˜[œÚ][Û‹XÛ\ÜØ
OÝØšY]Ë]˜[œÚ][Û‹XÛ\ÜØN›[KšY]Õ˜[œÚ][ÛÛ\ÜÏ[O[[\[ÙˆOX›ÛÛX[˜ØŠ
ÛŠKš[J
KK™\Ü^OOOX[›[™KX›ØÚØ	‰ŠO[[ÙK™\Ü^OYK›X\™Ú[XŠ]™\Ü^KK™\Ü^O[O[[\[ÙˆOX›ÛÛX[˜Ø›‹]›X\™Ú[‹O[[Ê]š\ÓÝÛ”›Ü\JX\™Ú[•Ü
OÝ›X\™Ú[•ÜØX\™Ú[‹]ÜKK›X\™Ú[•Ü[O[[\[ÙˆOX›ÛÛX[˜Ø›‹]š\ÓÝÛ”›Ü\JX\™Ú[›ÝÛX
OÝ›X\™Ú[›ÝÛNØX\™Ú[‹X›ÝÛXKK›X\™Ú[›ÝÛO]O[[\[ÙˆOX›ÛÛX[˜Ø
N™K›X\™Ú[[ŠJ_Y[˜Ý[ÛˆJKŠ^Ü™]\›ˆ[‹›ÝÛ™\‘ØÝ[Y[™Y˜][šY]ËÜ™XÝ™KXœÎœÜÚ][ÛOOXXœÛÛ]XœÜÚ][ÛOOXš^YÛ\˜Û\]OOX›Û™X›Ý™\™›ÝÈOOXš\ÚX›X™š[\ˆOOX›Û™X›X\ÚÈOOX›Û™X›X\ÚÈOOX›Û™X˜›Ü™\”˜Y]\ÈOOXšY]ÎŒYK˜›ÝÛI‰ŒYKœšYÚ	‰™KÜ[‹š[›™\’ZYÚ	‰™K›Y[‹š[›™\•ÚY_Y[˜Ý[Ûˆ™ŠJ^Ü™]\›ˆJK™Ù]›Ý[™[™ÐÛY[™XÝ

KÙ]ÛÛ\]YÝ[JJKJ_Y[˜Ý[ÛˆÝJJ^Ý˜\ˆYK™Ù]›Ý[™[™ÐÛY[™XÝ

NÝ[™]ÈÓT™XÝ
ž
Ì™MžJÌ™MÚYšZYÚ
NÝ˜\ˆYÙ]ÛÛ\]YÝ[JJNÜ™]\›ˆJ‹J_Y[˜Ý[ÛˆÝJJ^Ü™]\›ˆK™ØÝ[Y[[[Y[˜ÛY[ZYÚY[˜Ý[ÛˆÝJJ^Ý\Ë˜Y]™[\Ý[™\ŠØYJK\Ë˜Y]™[\Ý[™\Š\œ›Ü˜J_Y[˜Ý[ÛˆYŠK‹‹KKËË
^Ý˜\ˆO]››ÙU\OOONOÝ›ÝÛ™\‘ØÝ[Y[Ýž^Ý˜\ˆ]KœÝ\šY]Õ˜[œÚ][ÛŠÝ\]N™[˜Ý[ÛŠ
^Ý˜\ˆ]K™Y˜][šY]Ë]›˜]šYØ][Û‰‰›˜]šYØ][Û‹˜[œÚ][Û‹Ï]K™›ÛËœÝ]\ÎÜŠ
NÝ˜\ˆÏV×NÚYŠÏOOXØYY	‰ŠÝJJKK™›ÛËœÝ]\ÏOOXØY[™Ø	‰œËœ\Ú
K™›ÛËœ™XYJJKÏ\Ë›[™ÝHOO[[
Y›ÜŠ˜\ˆYKœÝ\Ü[œÙ^R[XYÙ\ËLLÙ›[™ÝÙŠÊÊ^Ý˜\ˆ[Ù—NÚYŠ\˜ÛÛ\]J^Ý˜\ˆO\™Ù]›Ý[™[™ÐÛY[™XÝ

NÚYŠK˜›ÝÛI‰ŒKœšYÚ	‰›KÜš[›™\’ZYÚ	‰›K›Yš[›™\•ÚY
^ÚYŠ
ÏYÜ

Kœ
^ÜË›[™Ý[ÎØœ™XZß\[™]È›ÛZ\ÙJÝK˜š[™

JKËœ\Ú

___ZYŠË›[™Ý
\™]\›ˆT›ÛZ\ÙKœ˜XÙJÔ›ÛZ\ÙK˜[
ÊK™]È›ÛZ\ÙJ[˜Ý[ÛŠJ^Ü™]\›ˆÙ][Y[Ý]
KL
_JWJK[ŠKJK
Ô›ÛZ\ÙK˜[Ù]Y
Û‹™š[š\ÚYJN
K[ŠKJNÚYŠJ
KŠ\™]\›ˆ‹™š[š\ÚY[ŠKJNØJ
_K\\Î›ŸJNÝK—×Ü™XXÝšY]Õ˜[œÚ][ÛYÝ˜\ˆV×NÜ™]\›ˆœ™XYK[Š[˜Ý[ÛŠ
^Ù›ÜŠ˜\ˆO]K™ØÝ[Y[[[Y[™Ù][š[X][ÛœÊÜÝX™YNˆLJKLÝK›[™ÝÝ
ÊÊ^Ý˜\ˆYVÝK[‹™Y™™XÝO\‹œÙ]YÑ[[Y[ÚYŠHO[[	‰šKœÝ\ÕÚ]
ŽšY]Ë]˜[œÚ][Û˜
J^Ù‹œ\Ú
ŠK\‹™Ù]Ù^Yœ˜[Y\Ê
NÙ›ÜŠ˜\ˆOZO]›ÚYÏHLLÛ‹›[™ÝÛ
ÊÊ^Ý˜\ˆ[–ÛKYÚYÚYŠOOO]›ÚY
ZO\Ù[ÙHYŠHOO\
^ÜÏHLNØœ™XZßZYŠYšZYÚOOO]›ÚY
XO\Ù[ÙHYŠHOO\
^ÜÏHLNØœ™XZßY[]HÚY[]HšZYÚ˜[œÙ›Ü›OOOX›Û™X	‰™[]H˜[œÙ›Ü›_\É‰šHOO]›ÚY	‰˜HOO]›ÚY	‰Š‹œÙ]Ù^Yœ˜[Y\ÊŠKÏYÙ]ÛÛ\]YÝ[J‹\™Ù]‹œÙ]YÑ[[Y[
KËÚYOOZ_ËšZYÚOOXJI‰ŠÏ[–ÌKËÚYZKËšZYÚXKÏ[–Û‹›[™ÝLWKËÚYZKËšZYÚXK‹œÙ]Ù^Yœ˜[Y\ÊŠJ__[Ê
_K[˜Ý[ÛŠJ^ÝK—×Ü™XXÝšY]Õ˜[œÚ][ÛOOY	‰ŠK—×Ü™XXÝšY]Õ˜[œÚ][Û[[
NÝž^ÚYŠ\[ÙˆOOXØš™XÝ	‰™J\ÝÚ]Ú
K›˜[YJ^ØØ\ÙX[˜[YÝ]Q\œ›Ü˜ŠK›Y\ÜØYÙOOOXšY]È˜[œÚ][ÛˆØ\ÈÚÚ\Y™XØ]\ÙHØÝ[Y[š\ÚXš[]HÝ]H\ÈY[‹˜K›Y\ÜØYÙOOOXÚÚ\[™ÈšY]È˜[œÚ][Ûˆ™XØ]\ÙHØÝ[Y[š\ÚXš[]HÝ]H\È™XÛÛYHY[‹˜K›Y\ÜØYÙOOOXÚÚ\[™ÈšY]È˜[œÚ][Ûˆ™XØ]\ÙHšY]ÜÜÚ^™HÚ[™ÙY˜K›Y\ÜØYÙOOOX˜[œÚ][ÛˆØ\ÈX›ÜY™XØ]\ÙHÙˆ[˜[YÝ]X
I‰ŠO[[
_YHOO[[	‰›
J_Yš[˜[^ÜŠ
KJ
KÊ
__JK™š[š\ÚY™š[˜[J[˜Ý[ÛŠ
^Ù›ÜŠ˜\ˆOLÙO‹›[™ÝÙJÊÊY–ÙWK˜Ø[˜Ù[

NÝK—×Ü™XXÝšY]Õ˜[œÚ][ÛOOY	‰ŠK—×Ü™XXÝšY]Õ˜[œÚ][Û[[
KÊ
_JKXØ]ÚÜ™]\›ˆŠ
KJ
KÊ
K[_Y[˜Ý[Ûˆ™ŠK
^Ý\Ë—ÜØÛÜOYØÝ[Y[™ØÝ[Y[[[Y[\Ë—ÜÙ[XÝÜXŽšY]Ë]˜[œÚ][Û‹X
ÙJØ

Ý
Ø
XX™‹œ›ÝÝ\K˜[š[X]OY[˜Ý[ÛŠK
^Ü™]\›ˆ]\[ÙˆOX[X™\˜ÞÙ\˜][ÛŽN•
ßK
KœÙ]YÑ[[Y[]\Ë—ÜÙ[XÝÜ‹\Ë—ÜØÛÜK˜[š[X]JK
_K™‹œ›ÝÝ\K™Ù][š[X][ÛœÏY[˜Ý[ÛŠ
^Ù›ÜŠ˜\ˆO]\Ë—ÜØÛÜK]\Ë—ÜÙ[XÝÜ‹YK™Ù][š[X][ÛœÊÜÝX™YNˆLJKV×KOLÚO‹›[™ÝÚJÊÊ^Ý˜\ˆO[–ÚWK™Y™™XÝØHOO[[	‰˜K\™Ù]OOYI‰˜KœÙ]YÑ[[Y[OO]	‰œ‹œ\Ú
–ÚWJ_\™]\›ˆŸK™‹œ›ÝÝ\K™Ù]ÛÛ\]YÝ[OY[˜Ý[ÛŠ
^Ü™]\›ˆÙ]ÛÛ\]YÝ[J\Ë—ÜØÛÜK\Ë—ÜÙ[XÝÜŠ_NÙ[˜Ý[ÛˆŠJ^Ü™]\›žÛ˜[YN™KÜ›Ý\›™]È™ŠÜ›Ý\JK[XYÙTZ\Ž›™]È™Š[XYÙK\Z\˜JKÛ›™]È™ŠÛJK™]Î›™]È™Š™]ØJ__Y[˜Ý[ÛˆÙŠJ^Ý\Ë—Ùœ˜YÛY[šX™\YK\Ë—ÛØœÙ\™\œÏ]\Ë—Ù]™[\Ý[™\œÏ[[TÙ‹œ›ÝÝ\K˜Y]™[\Ý[™\Y[˜Ý[ÛŠKŠ^Ý˜\ˆ[[O[[ÚYŠJˆO[[	‰\[ÙˆˆOX›ÛÛX[˜	‰Š[‹œÚYÛ˜[[ˆOO[[	‰œ‹˜X›ÜY
JJ^Ý\Ë—Ù]™[\Ý[™\œÏOO[[	‰Š\Ë—Ù]™[\Ý[™\œÏV×JNÝ˜\ˆO]\Ë—Ù]™[\Ý[™\œÎÚYŠŠKKŠOOOKLJ^Ý˜\ˆÏ]\ËÏ]ÛˆO[[	‰\[ÙˆˆOX›ÛÛX[˜	‰ˆLOO[‹›Û˜ÙI‰ŠÏY[˜Ý[ÛŠŠ^ÛËœ™[[Ý™Q]™[\Ý[™\ŠKŠK\[ÙˆOX[˜Ý[Û˜Ý˜Ø[
\ËŠNš[™Q]™[
Š_JKˆOO[[	‰ŠO[Ëœ™[[Ý™Q]™[\Ý[™\‹˜š[™
ËKŠK‹˜Y]™[\Ý[™\ŠX›ÜKÛÛ˜ÙNˆLJKO\‹œ™[[Ý™Q]™[\Ý[™\‹˜š[™
‹X›ÜJJKPÙŠŠKKœ\Ú
Ý\N™K\Ý[™\ŽÜ[ÛœÓÜ•\ÙPØ\\™N›‹]XÚY\Ý[™\ŽœËÛX[\š_JK
\Ë—Ùœ˜YÛY[šX™\‹˜Ú[LKKKËŠ_]\Ë—Ù]™[\Ý[™\œÏX__NÙ[˜Ý[ÛˆJK‹Š^Ü™]\›ˆŠJK˜Y]™[\Ý[™\Š‹ŠKL_TÙ‹œ›ÝÝ\Kœ™[[Ý™Q]™[\Ý[™\Y[˜Ý[ÛŠKŠ^Ý˜\ˆ]\Ë—Ù]™[\Ý[™\œÎÚYŠˆOO[[	‰ŠUŠ‹KŠKOOKLJJ^Ý˜\ˆO\–ÝNÛZK˜]XÚY\Ý[™\ŽÝ˜\ˆOZK˜ÛX[\ÚOPÙŠK›Ü[ÛœÓÜ•\ÙPØ\\™JK
\Ë—Ùœ˜YÛY[šX™\‹˜Ú[LK]KK‹JK‹œÜXÙJJKHOO[[	‰˜J
__NÙ[˜Ý[Ûˆ]JK‹Š^Ü™]\›ˆŠJKœ™[[Ý™Q]™[\Ý[™\Š‹ŠKL_Y[˜Ý[ÛˆÙŠJ^Ü™]\›ˆHO[[	‰\[ÙˆHOX›ÛÛX[˜	‰ŠLOOYK›Û˜Ù_KœÚYÛ˜[[œÝ[˜Ù[ÙˆX›ÜÚYÛ˜[
OÞØØ\\™N™K˜Ø\\™K\ÜÚ]™N™Kœ\ÜÚ]™_N™_Y[˜Ý[ÛˆÙŠJ^Ü™]\›ˆOO[[ØÏL\[ÙˆOOX›ÛÛX[˜ØÏX
ÊOØX˜
N˜ÏX
ÊK˜Ø\\™OØX˜
_Y[˜Ý[ÛˆŠK‹Š^ÚYŠK›[™ÝOOL
\™]\›‹LNÜ]ÙŠŠNÙ›ÜŠ˜\ˆOLÚOK›[™ÝÚJÊÊ^Ý˜\ˆOYVÚWNÚYŠK\OOO]	‰˜K›\Ý[™\OO[‰‰ÙŠK›Ü[ÛœÓÜ•\ÙPØ\\™JOOO\Š\™]\›ˆ_\™]\›‹L_TÙ‹œ›ÝÝ\K™\Ü]Ú]™[Y[˜Ý[ÛŠJ^Ý˜\ˆ[J\Ë—Ùœ˜YÛY[šX™\ŠNÚYŠOO[[
\™]\›ˆLÝ]Š
NÝ˜\ˆ]\Ë—Ù]™[\Ý[™\œÎÚYŠˆOO[[	‰Œ‹›[™ÝYK˜X˜›\Ê^Ý˜\ˆ]››ÙU\OOONOÝ˜Ü™X]PÛÛ[Y[

N™ØÝ[Y[˜Ü™X]U^›ÙJ
NÚYŠŠY›ÜŠ˜\ˆOLÚO‹›[™ÝÚJÊÊ^Ý˜\ˆO[–ÚWNÜ‹˜Y]™[\Ý[™\ŠK\KK˜]XÚY\Ý[™\‹ÙŠK›Ü[ÛœÓÜ•\ÙPØ\\™JJ_ZYŠ˜\[™Ú[
ŠKO\‹™\Ü]Ú]™[
JKŠY›ÜŠOLÚO‹›[™ÝÚJÊÊXO[–ÚWK‹œ™[[Ý™Q]™[\Ý[™\ŠK\KK˜]XÚY\Ý[™\‹ÙŠK›Ü[ÛœÓÜ•\ÙPØ\\™JJNÜ™]\›ˆœ™[[Ý™PÚ[
ŠK_\™]\›ˆ™\Ü]Ú]™[
J_KÙ‹œ›ÝÝ\K™›ØÝ\ÏY[˜Ý[ÛŠJ^Ü
\Ë—Ùœ˜YÛY[šX™\‹˜Ú[LKK›ÚY›ÚY
_NÙ[˜Ý[ÛˆJK
^Ü™]\›ˆKYÏOOMÈLNŠO]ŠJK™ŠK
J_TÙ‹œ›ÝÝ\K™›ØÝ\Ó\ÝY[˜Ý[ÛŠJ^Ý˜\ˆV×NÜ
\Ë—Ùœ˜YÛY[šX™\‹˜Ú[LY‹›ÚY›ÚY
NÙ›ÜŠ˜\ˆ]›[™ÝLNÌ[‰‰ˆQJÛ—KJNÛ‹KJNßNÙ[˜Ý[ÛˆYŠK
^Ü™]\›ˆœ\Ú
JKL_TÙ‹œ›ÝÝ\K˜›\Y[˜Ý[ÛŠ
^Ý˜\ˆO[J\Ë—Ùœ˜YÛY[šX™\ŠNÙHOO[[	‰ŠO]ŠJKOXYŠJK˜XÝ]™Q[[Y[HOO[[	‰œ
\Ë—Ùœ˜YÛY[šX™\‹˜Ú[LKÝKK›ÚY›ÚY
J_NÙ[˜Ý[ÛˆÝJK
^Ü™]\›ˆKYÏOOMÈLNŠO]ŠJKOOO]K˜ÛÛZ[œÊ
OÊ˜›\Š
KL
NˆLJ_TÙ‹œ›ÝÝ\K›ØœÙ\™U\Ú[™ÏY[˜Ý[ÛŠJ^Ý\Ë—ÛØœÙ\™\œÏOO[[	‰Š\Ë—ÛØœÙ\™\œÏ[™]ÈÙ]
K\Ë—ÛØœÙ\™\œË˜Y
JK
\Ë—Ùœ˜YÛY[šX™\‹˜Ú[LKÝKK›ÚY›ÚY
_NÙ[˜Ý[ÛˆÝJK
^Ü™]\›ˆKYÏOOMÈLNŠO]ŠJK›ØœÙ\™JJKLJ_TÙ‹œ›ÝÝ\K[›ØœÙ\™U\Ú[™ÏY[˜Ý[ÛŠJ^Ý˜\ˆ]\Ë—ÛØœÙ\™\œÎÚYŠOO[[	‰š\ÊJJ^Ý™[]JJK
\Ë—Ùœ˜YÛY[šX™\‹˜Ú[LK]KK›ÚY›ÚY
NÙ›ÜŠ˜\ˆ]LÛ‹›[™ÝÛŠÊÊ^Ý˜\ˆQ–Û—NÜ‹™œ˜YÛY[[œÝ[˜ÙOOO]\É‰œ‹›ØœÙ\™\OOYOÙK[›ØœÙ\™J‹š[œÝ[˜ÙJN‘–Ý
Ê×O\ŸQ‹›[™Ý]_NÙ[˜Ý[Ûˆ]JK
^Ü™]\›ˆKYÏOOMÈLNŠO]ŠJK[›ØœÙ\™JJKLJ_]˜\ˆV×KÙHLNÙ[˜Ý[ÛˆJKŠ^Ñ‹œ\Ú
Ùœ˜YÛY[[œÝ[˜ÙN™KØœÙ\™\Ž[œÝ[˜ÙN›ŸJKÙŸ
ÙHLJ[˜Ý[ÛŠ
^ÓÙHLNÝ˜\ˆOQŽÑV×NÙ›ÜŠ˜\ˆLÝK›[™ÝÝ
ÊÊ^Ý˜\ˆYVÝNÛ‹›ØœÙ\™\‹[›ØœÙ\™J‹š[œÝ[˜ÙJ__JJ_TÙ‹œ›ÝÝ\K™Ù]ÛY[™XÝÏY[˜Ý[ÛŠ
^Ý˜\ˆOV×NÜ™]\›ˆ
\Ë—Ùœ˜YÛY[šX™\‹˜Ú[LKÙ‹K›ÚY›ÚY
K_NÙ[˜Ý[ÛˆÙŠK
^ÚYŠKYÏOOMŠ^ÙOYKœÝ]S›ÙNÝ˜\ˆYK›ÝÛ™\‘ØÝ[Y[˜Ü™X]T˜[™ÙJ
NÛ‹œÙ[XÝ›ÙPÛÛ[ÊJKœ\Ú˜\J‹™Ù]ÛY[™XÝÊ
J_Y[ÙHO]ŠJKœ\Ú˜\JK™Ù]ÛY[™XÝÊ
JNÜ™]\›ˆL_TÙ‹œ›ÝÝ\K™Ù]›ÛÝ›ÙOY[˜Ý[ÛŠJ^Ý˜\ˆ[J\Ë—Ùœ˜YÛY[šX™\ŠNÜ™]\›ˆOO[[Ý\ÎŠ
K™Ù]›ÛÝ›ÙJJ_KÙ‹œ›ÝÝ\K˜ÛÛ\\™QØÝ[Y[ÜÚ][ÛY[˜Ý[ÛŠJ^Ý˜\ˆ[J\Ë—Ùœ˜YÛY[šX™\ŠNÚYŠOO[[
\™]\›ˆ›ÙK‘ÐÕSQS•ÔÔÒUSÓ—ÑTÐÓÓ“‘PÕQÝ˜\ˆV×NÜ
\Ë—Ùœ˜YÛY[šX™\‹˜Ú[LKY‹‹›ÚY›ÚY
NÝ˜\ˆ]Š
NÚYŠ‹›[™ÝOOL
^ÚYŠ\‹
\Ë—Ùœ˜YÛY[šX™\ŠJ^ØNžÙ›ÜŠ]\Ë—Ùœ˜YÛY[šX™\‹œ™]\›ŽÝOO[[Ê^ÚYŠYÏOOM
^Ý]œÝ]S›ÙK˜ÛÛZ[™\’[™›ÎØœ™XZÈ_ZYŠYÏOOLßYÏOOM_YÏOOLÊXœ™XZÎÝ]œ™]\›Ÿ][[]O[[	‰Š]
_]]\Ë—Ùœ˜YÛY[šX™\ŽÝ˜\ˆO\[‹˜ÛÛ\\™QØÝ[Y[ÜÚ][ÛŠJNÜ™]\›ˆOOYOÚOS›ÙK‘ÐÕSQS•ÔÔÒUSÓ—ÐÓÓ•RS”Îœ‰“›ÙK‘ÐÕSQS•ÔÔÒUSÓ—ÐÓÓ•RS‘QÐ–I‰ŠYÊ
VÌWKOO[[ÚOS›ÙK‘ÐÕSQS•ÔÔÒUSÓ—Ô‘PÑQS‘ÎŠO]ŠŠK˜ÛÛ\\™QØÝ[Y[ÜÚ][ÛŠJKOYOOOLI“›ÙK‘ÐÕSQS•ÔÔÒUSÓ—Ñ“ÓÕÒS‘ÏÓ›ÙK‘ÐÕSQS•ÔÔÒUSÓ—Ñ“ÓÕÒS‘Î“›ÙK‘ÐÕSQS•ÔÔÒUSÓ—Ô‘PÑQS‘ÊJK_S›ÙK‘ÐÕSQS•ÔÔÒUSÓ—ÒSTSQS•USÓ—ÔÔPÒQ’Pß]]Š–ÌJKO]Š–Û‹›[™ÝLWJNÝ˜\ˆOZ
\Ë—Ùœ˜YÛY[šX™\ŠOÝœ\™[[[Y[œŽÚYŠOO[[
\™]\›ˆ›ÙK‘ÐÕSQS•ÔÔÒUSÓ—ÑTÐÓÓ“‘PÕQÜXK˜ÛÛ\\™QØÝ[Y[ÜÚ][ÛŠ
I“›ÙK‘ÐÕSQS•ÔÔÒUSÓ—ÐÓÓ•RS‘QÐ–KOXK˜ÛÛ\\™QØÝ[Y[ÜÚ][ÛŠJI“›ÙK‘ÐÕSQS•ÔÔÒUSÓ—ÐÓÓ•RS‘QÐ–NÝ˜\ˆÏ]˜ÛÛ\\™QØÝ[Y[ÜÚ][ÛŠJKÏZK˜ÛÛ\\™QØÝ[Y[ÜÚ][ÛŠJK[É“›ÙK‘ÐÕSQS•ÔÔÒUSÓ—ÐÓÓ•RS‘QÐ–_É“›ÙK‘ÐÕSQS•ÔÔÒUSÓ—ÐÓÓ•RS‘QÐ–NÜ™]\›ˆÏ\‰‰˜I‰›É“›ÙK‘ÐÕSQS•ÔÔÒUSÓ—Ñ“ÓÕÒS‘É‰œÉ“›ÙK‘ÐÕSQS•ÔÔÒUSÓ—Ô‘PÑQS‘Ë\‰‰OOY_I‰šOOOY_ÏÓ›ÙK‘ÐÕSQS•ÔÔÒUSÓ—ÐÓÓ•RS‘QÐ–Nˆ\‰‰OOY_XI‰šOOOYOÓ›ÙK‘ÐÕSQS•ÔÔÒUSÓ—ÒSTSQS•USÓ—ÔÔPÒQ’PÎ›Ë	“›ÙK‘ÐÕSQS•ÔÔÒUSÓ—ÑTÐÓÓ“‘PÕQ	“›ÙK‘ÐÕSQS•ÔÔÒUSÓ—ÒSTSQS•USÓ—ÔÔPÒQ’PßYŠ\Ë—Ùœ˜YÛY[šX™\‹–ÌK–Û‹›[™ÝLWKJOÝ“›ÙK‘ÐÕSQS•ÔÔÒUSÓ—ÒSTSQS•USÓ—ÔÔPÒQ’PßNÙ[˜Ý[ÛˆYŠK‹‹J^Ý˜\ˆOZÝ
JNÚYŠI“›ÙK‘ÐÕSQS•ÔÔÒUSÓ—ÐÓÓ•RS‘QÐ–J^ÚYŠHHXJXNžÙ›ÜŠØHOO[[Ê^ÚYŠKYÏOOMÉ‰ŠOOO]K˜[\›˜]OOO]
J^ÛHLØœ™XZÈ_XOXKœ™]\›Ÿ[HL_\™]\›ˆŸZYŠI“›ÙK‘ÐÕSQS•ÔÔÒUSÓ—ÐÓÓ•RS”Ê^ÚYŠOOO[[
\™]\›ˆOZK›ÝÛ™\‘ØÝ[Y[OOOX_OOOXK™ØÝ[Y[[[Y[OOOXK˜›ÙNØNžÙ›ÜŠO][J
NØHOO[[Ê^ÚYŠJKYÈOOMI‰˜KYÈOOLÉ‰˜KYÈOOLßHOO]	‰˜K˜[\›˜]HOO]
J^ØOHLØœ™XZÈ_XOXKœ™]\›ŸXOHL_\™]\›ˆ_\™]\›ˆI“›ÙK‘ÐÕSQS•ÔÔÒUSÓ—Ô‘PÑQS‘ÏÊ
HHXJI‰ˆJXOOO[ŠI‰Š]Ê‹KÊKOO[[ÝHLNŠ
LKŠKO^KO[[XHOO[[
JK
N™I“›ÙK‘ÐÕSQS•ÔÔÒUSÓ—Ñ“ÓÕÒS‘ÏÊ
HHXJI‰ˆJXOOO\ŠI‰Š]Ê‹KÊKOO[[ÝHLNŠ
LËKŠKO^K^O[[XHOO[[
JK
NˆL_Y[˜Ý[Ûˆ]JK
^Ý˜\ˆYK›ÝÛ™\‘ØÝ[Y[˜Ü™X]T˜[™ÙJ
NÛ‹œÙ[XÝ›ÙPÛÛ[ÊJKO[‹™Ù]›Ý[™[™ÐÛY[™XÝ

KÚ[™ÝËœØÜ›ÛÊÚ[™ÝËœØÜ›Û
ÙK›YÝÚ[™ÝËœØÜ›ÛJÙKÜÚ[™ÝËœØÜ›ÛJÙK˜›ÝÛK]Ú[™ÝËš[›™\’ZYÚ
_TÙ‹œ›ÝÝ\KœØÜ›Û[ÕšY]ÏY[˜Ý[ÛŠJ^ÚYŠ\[ÙˆOOXØš™XÝ
]›ÝÈ\œ›ÜŠJMŠJNÝ˜\ˆV×NÜ
\Ë—Ùœ˜YÛY[šX™\‹˜Ú[LKY‹›ÚY›ÚY
NÝ˜\ˆHLHOOYNÚYŠ›[™ÝOOL
^Ý˜\ˆYÊ\Ë—Ùœ˜YÛY[šX™\ŠNÚYŠ[Ü–ÌW_–Ì_J\Ë—Ùœ˜YÛY[šX™\ŠNœ–Ì_–ÌWKOO[[
\™]\›ŽÚYŠ‹YÏOOMŠ^ÙO]ŠŠK]JKŠNÜ™]\›ŸZYŠ]ŠŠK‹››ÙU\HOONJ^ÚYŠ‹››ÙU\OOOLLJ^ÛXÜÝ[ˆÜ‹šÜÝ›[ˆOO[[	‰›‹œØÜ›Û[ÕšY]ÊJNÜ™]\›Ÿ\‹œØÜ›Û[ÕšY]ÊJ__Y›ÜŠ[Ý›[™ÝLNŒÜˆOOJËLN›[™Ý
NÊ^Ý˜\ˆO]Ü—NØKYÏOOMÊO]ŠJK]JKŠJNŠJKœØÜ›Û[ÕšY]ÊJKŠÏ[ËLNŒ__NÙ[˜Ý[ÛˆJK
^Ü™]\›ˆO]ŠJK™ŠK
KL_Y[˜Ý[Ûˆ™ŠK
^ÙKœ™XXÝœ˜YÛY[ÏÏÏ[™]ÈÙ]Kœ™XXÝœ˜YÛY[Ë˜Y

_Y[˜Ý[ÛˆJK
^Ý˜\ˆ]—Ù]™[\Ý[™\œÎÚYŠˆOO[[
Y›ÜŠ˜\ˆLÜ‹›[™ÝÜŠÊÊ^Ý˜\ˆO[–Ü—NÙK˜Y]™[\Ý[™\ŠK\KK˜]XÚY\Ý[™\‹ÙŠK›Ü[ÛœÓÜ•\ÙPØ\\™JJ_YK››ÙU\HOOLÉ‰Š]—ÛØœÙ\™\œËˆOO[[	‰›‹™›Ü‘XXÚ
[˜Ý[ÛŠŠ^Ù›ÜŠ˜\ˆLOLÚO‹›[™ÝÚJÊÊ^Ý˜\ˆOQ–ÚWNÊK™œ˜YÛY[[œÝ[˜ÙHOO]K›ØœÙ\™\ˆOO[ŸKš[œÝ[˜ÙHOOYJI‰Š–ÜŠÊ×OXJ_Q‹›[™Ý\‹‹›ØœÙ\™JJ_JK™ŠK
J_Y[˜Ý[ÛˆJK
^Ý˜\ˆ]—Ù]™[\Ý[™\œÎÚYŠˆOO[[
Y›ÜŠ˜\ˆLÜ‹›[™ÝÜŠÊÊ^Ý˜\ˆO[–Ü—NÙKœ™[[Ý™Q]™[\Ý[™\ŠK\KK˜]XÚY\Ý[™\‹ÙŠK›Ü[ÛœÓÜ•\ÙPØ\\™JJ_YK››ÙU\HOOLÉ‰Š]—ÛØœÙ\™\œËˆOO[[	‰›‹™›Ü‘XXÚ
[˜Ý[ÛŠŠ^Ý\[Ùˆ‹œ›ÛÝX\™Ú[OXÝš[™ØÚJ‹JN›‹[›ØœÙ\™JJ_JKKœ™XXÝœ˜YÛY[ÈO[[	‰™Kœ™XXÝœ˜YÛY[Ë™[]J
J_Y[˜Ý[ÛˆYŠJ^Ý˜\ˆYK™š\œÝÚ[Ù›ÜŠ	‰››ÙU\OOOLL	‰Š]›™^ÚX›[™ÊNÝÊ^Ý˜\ˆ]ÜÝÚ]Ú
]›™^ÚX›[™Ë‹››ÙS˜[YJ^ØØ\ÙXS˜Ø\ÙXPQ˜Ø\ÙX“ÑX“YŠŠKÝ
ŠNØÛÛ[YNØØ\ÙXÐÔ’T˜Ø\ÙXÕSX˜ÛÛ[YNØØ\ÙXS’ØšYŠ‹œ™[ÓÝÙ\Ø\ÙJ
OOOXÝ[\ÚY]
XÛÛ[Y_YKœ™[[Ý™PÚ[
Š__Y[˜Ý[Ûˆ™ŠK‹Š^Ù›ÜŠÙK››ÙU\OOOLNÊ^Ý˜\ˆO[ŽÚYŠK››ÙS˜[YKÓÝÙ\Ø\ÙJ
HOO]ÓÝÙ\Ø\ÙJ
J^ÚYŠ\‰‰ŠK››ÙS˜[YHOOXS”UK\HOOXY[˜
JXœ™XZßY[ÙHYŠ\ŠZYŠOOX[œ]	‰™K\OOOXY[˜
^Ý˜\ˆOZK›˜[YOO[[Û[˜
ÚK›˜[YNÚYŠK\OOOXY[˜	‰™K™Ù]]šX]J˜[YX
OOOXJ\™]\›ˆ_Y[ÙH™]\›ˆNÙ[ÙHYŠYVÑ]J\ÝÚ]Ú

^ØØ\ÙXY]XšYŠYKš\Ð]šX]J][\›Ü
JXœ™XZÎÜ™]\›ˆNØØ\ÙX[šØšYŠOYK™Ù]]šX]J™[
KOOOXÝ[\ÚY]	‰™Kš\Ð]šX]J]K\™XÙY[˜ÙX
_HOOZKœ™[K™Ù]]šX]J™Y˜
HOOJKš™YO[[Kš™YOOXÛ[šKš™YŠ_K™Ù]]šX]JÜ›ÜÜÛÜšYÚ[˜
HOOJK˜Ü›ÜÜÓÜšYÚ[O[[Û[šK˜Ü›ÜÜÓÜšYÚ[Š_K™Ù]]šX]J]X
HOOJK]OO[[Û[šK]JJXœ™XZÎÜ™]\›ˆNØØ\ÙXÝ[XšYŠKš\Ð]šX]J]K\™XÙY[˜ÙX
JXœ™XZÎÜ™]\›ˆNØØ\ÙXØÜš\šYŠOYK™Ù]]šX]JÜ˜Ø
K
HOOJKœÜ˜ÏO[[Û[šKœÜ˜Ê_K™Ù]]šX]J\X
HOOJK\OO[[Û[šK\J_K™Ù]]šX]JÜ›ÜÜÛÜšYÚ[˜
HOOJK˜Ü›ÜÜÓÜšYÚ[O[[Û[šK˜Ü›ÜÜÓÜšYÚ[ŠJI‰˜I‰™Kš\Ð]šX]J\Þ[˜Ø
I‰ˆYKš\Ð]šX]J][\›Ü
JXœ™XZÎÜ™]\›ˆNÙY˜][œ™]\›ˆ_ZYŠOSŠK›™^ÚX›[™ÊKOOO[[
Xœ™XZß\™]\›ˆ[Y[˜Ý[Ûˆ]JKŠ^ÚYŠOOX
\™]\›ˆ[Ù›ÜŠÙK››ÙU\HOOLÎÊZYŠ
K››ÙU\HOOL_K››ÙS˜[YHOOXS”UK\HOOXY[˜
I‰ˆ[Ÿ
OSŠK›™^ÚX›[™ÊKOOO[[
J\™]\›ˆ[Ü™]\›ˆ_Y[˜Ý[ÛˆŠK
^Ù›ÜŠÙK››ÙU\HOONÊZYŠ
K››ÙU\HOOL_K››ÙS˜[YHOOXS”UK\HOOXY[˜
I‰ˆ]
OSŠK›™^ÚX›[™ÊKOOO[[
J\™]\›ˆ[Ü™]\›ˆ_Y[˜Ý[Ûˆ™ŠJ^Ü™]\›ˆK™]OOOX	ØK™]OOOX	˜Y[˜Ý[ÛˆYŠJ^Ü™]\›ˆK™]OOOX	XK™]OOOX	Ø	‰™K›ÝÛ™\‘ØÝ[Y[œ™XYTÝ]HOOXØY[™ØY[˜Ý[ÛˆJK
^Ý˜\ˆYK›ÝÛ™\‘ØÝ[Y[ÚYŠK™]OOOX	˜
YK—Ü™XXÝ™]žO]Ù[ÙHYŠK™]HOOX	Ø‹œ™XYTÝ]HOOXØY[™Ø
]

NÙ[Ù^Ý˜\ˆY[˜Ý[ÛŠ
^Ý

K‹œ™[[Ý™Q]™[\Ý[™\ŠÓPÛÛ[ØYYŠ_NÛ‹˜Y]™[\Ý[™\ŠÓPÛÛ[ØYYŠKK—Ü™XXÝ™]žO\Ÿ_Y[˜Ý[ÛˆŠJ^Ù›ÜŠÙHO[[ÙOYK›™^ÚX›[™Ê^Ý˜\ˆYK››ÙU\NÚYŠOOL_OOLÊXœ™XZÎÚYŠOON
^ÚYŠYK™]KOOX	OOX	XOOX	ØOOX	˜OOX	˜OOXˆXOOX˜
Xœ™XZÎÚYŠOOXÉOOXÉ˜
\™]\›ˆ[_\™]\›ˆ_]˜\ˆ™[[Ù[˜Ý[Ûˆ™ŠJ^ÙOYK›™^ÚX›[™ÎÙ›ÜŠ˜\ˆLÙNÊ^ÚYŠK››ÙU\OOON
^Ý˜\ˆYK™]NÚYŠOOXÉOOXÉ˜
^ÚYŠOOL
\™]\›ˆŠK›™^ÚX›[™ÊNÝK_Y[ÙHˆOOX		‰›ˆOOX	X	‰›ˆOOX	Ø	‰›ˆOOX	˜	‰›ˆOOX	˜
ÊßYOYK›™^ÚX›[™ß\™]\›ˆ[Y[˜Ý[Ûˆ™ŠJ^ÙOYKœ™]š[Ý\ÔÚX›[™ÎÙ›ÜŠ˜\ˆLÙNÊ^ÚYŠK››ÙU\OOON
^Ý˜\ˆYK™]NÚYŠOOX	OOX	XOOX	ØOOX	˜OOX	˜
^ÚYŠOOL
\™]\›ˆNÝK_Y[ÙHˆOOXÉ	‰›ˆOOXÉ˜
ÊßYOYKœ™]š[Ý\ÔÚX›[™ß\™]\›ˆ[Y[˜Ý[Ûˆ™ŠK
^Ù[˜Ý[ÛˆŠ
^ÜHLZYŠK›ÝÛ™\‘ØÝ[Y[˜XÝ]™Q[[Y[OOYJ\™]\›ˆLÝ˜\ˆHLNÝž^ÙK›ÝÛ™\‘ØÝ[Y[˜Y]™[\Ý[™\Š›ØÝ\Ø‹L
K
K™›ØÝ\ßS[[Y[œ›ÝÝ\K™›ØÝ\ÊK˜Ø[
K
_Yš[˜[^ÙK›ÝÛ™\‘ØÝ[Y[œ™[[Ý™Q]™[\Ý[™\Š›ØÝ\Ø‹L
_\™]\›ˆŸY[˜Ý[ÛˆJJ^Ù™Š[˜Ý[ÛŠ
^Ù™Š[˜Ý[ÛŠ
^Ü™]\›ˆJ
_J_J_Y[˜Ý[ÛˆŠKŠ^ÜÝÚ]Ú
XYŠŠKJ^ØØ\ÙX[šYŠO]™ØÝ[Y[[[Y[YJ]›ÝÈ\œ›ÜŠJLŠJNÜ™]\›ˆNØØ\ÙXXYšYŠO]šXYYJ]›ÝÈ\œ›ÜŠJLÊJNÜ™]\›ˆNØØ\ÙX›ÙXšYŠO]˜›ÙKYJ]›ÝÈ\œ›ÜŠJM
JNÜ™]\›ˆNÙY˜][›ÝÈ\œ›ÜŠJLJJ__Y[˜Ý[ÛˆYŠKŠ^Ù›ÜŠ˜\ˆˆ[ˆŠ^Ý˜\ˆO[–Ü—NÛ‹š\ÓÝÛ”›Ü\JŠI‰šHO[[	‰”Y
K‹[KJ_[‹™[™Ù\›Ý\ÛTÙ][›™\’SO[[	‰ŠK^ÛÛ[X
KK›Û˜ÛXÚÏOO[[‰‰ŠK›Û˜ÛXÚÏ[[
KÝ
J_Y[˜Ý[ÛˆÙŠJ^Ù›ÜŠ˜\ˆYK˜]šX]\ÎÝ›[™ÝÊYKœ™[[Ý™P]šX]S›ÙJÌJNÓÝ
J_]˜\ˆÙ[™]ÈX\Ù[™]ÈÙ]Ù[˜Ý[ÛˆYŠJ^ÚYŠ\[ÙˆK™Ù]›ÛÝ›ÙOOX[˜Ý[Û˜
^Ý˜\ˆYK™Ù]›ÛÝ›ÙJ
NÚYŠ››ÙU\OOON_››ÙU\OOOLLJ\™]\›ˆ\™]\›ˆK››ÙU\OOONOÙN™K›ÝÛ™\‘ØÝ[Y[]˜\ˆ™]YK™ÝYK™^ÙŽžKŽK•KÎ’K–™‹N•]K”Y‹Î•ÝKN‰ŸNÙ[˜Ý[ÛˆJ
^Ý˜\ˆOR™‹™Š
KV]J
NÜ™]\›ˆ_Y[˜Ý[ÛˆJJ^Ý˜\ˆP]
JNÝOO[[	‰YÏOOMI‰\OOOX›Ü›XÞÊ
N’™‹œŠJ_]˜\ˆY]\[ÙˆØÝ[Y[˜XÛ[™ØÝ[Y[Ù[˜Ý[ÛˆŠKŠ^Ý˜\ˆVYŽÚYŠ‰‰\[ÙˆOXÝš[™Ø	‰
^Ý˜\ˆOY[Š
NÚOX[šÖÜ™[H˜
ÙJØ—VÚ™YH˜
ÚJØ—X\[ÙˆOXÝš[™Ø	‰ŠJÏXØÜ›ÜÜÛÜšYÚ[H˜
ÛŠØ—X
KÙ‹š\ÊJ_
Ù‹˜Y
JKO^Ü™[™KÜ›ÜÜÓÜšYÚ[Ž›‹™YŽK‹œ]Y\žTÙ[XÝÜŠJOOO[[	‰Š\‹˜Ü™X]Q[[Y[
[šØ
KYŠ[šØJK

K‹šXY˜\[™Ú[

JJ__Y[˜Ý[ÛˆJJ^Ò™‹‘
JKŠœË\™Y™]ÚK[
_Y[˜Ý[ÛˆJK
^Ò™‹ÊK
KŠ™XÛÛ›™XÝK
_Y[˜Ý[Ûˆ™ŠKŠ^Ò™‹“
KŠNÝ˜\ˆVYŽÚYŠ‰‰™I‰
^Ý˜\ˆOX[šÖÜ™[Hœ™[ØY—VØ\ÏH˜
Ù[Š
JØ—XÝOOX[XYÙX	‰›‰‰›‹š[XYÙTÜ˜ÔÙ]ÊJÏXÚ[XYÙ\Ü˜ÜÙ]H˜
Ù[Š‹š[XYÙTÜ˜ÔÙ]
JØ—X\[Ùˆ‹š[XYÙTÚ^™\ÏOXÝš[™Ø	‰ŠJÏXÚ[XYÙ\Ú^™\ÏH˜
Ù[Š‹š[XYÙTÚ^™\ÊJØ—X
JNšJÏXÚ™YH˜
Ù[ŠJJØ—XÝ˜\ˆOZNÜÝÚ]Ú

^ØØ\ÙXÝ[X˜O]
JNØœ™XZÎØØ\ÙXØÜš\˜OX\
J_ZYŠJÙ‹š\ÊJ_
OU
Ü™[˜™[ØY™YŽOOX[XYÙX	‰›‰‰›‹š[XYÙTÜ˜ÔÙ]Ý›ÚY™K\ÎKŠKÙ‹œÙ]
KJK‹œ]Y\žTÙ[XÝÜŠJHOO[[OOXÝ[X	‰œ‹œ]Y\žTÙ[XÝÜŠœ
JJ_OOXØÜš\	‰œ‹œ]Y\žTÙ[XÝÜŠÜ
JJJJJ^Ý˜\ˆÏ\‹˜Ü™X]Q[[Y[
[šØ
NÙYŠË[šØJKOOXÝ[X	‰ŠÖÑOHLË›Û›ØY[Ë›Û™\œ›ÜY[˜Ý[ÛŠ
^Ô
Ê_JK
ÊK‹šXY˜\[™Ú[
Ê___Y[˜Ý[Ûˆ]JK
^Ò™‹›JK
NÝ˜\ˆVYŽÚYŠ‰‰™J^Ý˜\ˆ]	‰\[Ùˆ˜\ÏOXÝš[™ØÝ˜\Î˜ØÜš\OX[šÖÜ™[H›[Ù[\™[ØY—VØ\ÏH˜
Ù[ŠŠJØ—VÚ™YH˜
Ù[ŠJJØ—XOZNÜÝÚ]Ú
Š^ØØ\ÙX]Y[ÝÛÜšÛ]˜Ø\ÙXZ[ÛÜšÛ]˜Ø\ÙXÙ\šXÙ]ÛÜšÙ\˜˜Ø\ÙXÚ\™YÛÜšÙ\˜˜Ø\ÙXÛÜšÙ\˜˜Ø\ÙXØÜš\˜OX\
J_ZYŠQÙ‹š\ÊJI‰ŠOU
Ü™[˜[Ù[\™[ØY™YŽ™_K
KÙ‹œÙ]
KJK‹œ]Y\žTÙ[XÝÜŠJOOO[[
J^ÜÝÚ]Ú
Š^ØØ\ÙX]Y[ÝÛÜšÛ]˜Ø\ÙXZ[ÛÜšÛ]˜Ø\ÙXÙ\šXÙ]ÛÜšÙ\˜˜Ø\ÙXÚ\™YÛÜšÙ\˜˜Ø\ÙXÛÜšÙ\˜˜Ø\ÙXØÜš\šYŠ‹œ]Y\žTÙ[XÝÜŠÜ
JJJ\™]\›Ÿ\[‹˜Ü™X]Q[[Y[
[šØ
KYŠ‹[šØJK
ŠK‹šXY˜\[™Ú[
Š___Y[˜Ý[ÛˆÝJKŠ^Ò™‹”ÊKŠNÝ˜\ˆVYŽÚYŠ‰‰™J^Ý˜\ˆOS]
ŠKšÚ\ÝX›TÝ[\ËO]
JNÝXY˜][Ý˜\ˆÏZK™Ù]
JNÚYŠ[Ê^Ý˜\ˆÏ^ÛØY[™ÎŒ™[ØY›[NÚYŠÏ\‹œ]Y\žTÙ[XÝÜŠœ
JJJ\Ë›ØY[™ÏMNÙ[Ù^ÙOU
Ü™[˜Ý[\ÚY]™YŽ™K™]K\™XÙY[˜ÙHŽKŠK
QÙ‹™Ù]
JJI‰˜Ü
KŠNÝ˜\ˆ[Ï\‹˜Ü™X]Q[[Y[
[šØ
NÓ

KYŠ[šØJK—Ü[™]È›ÛZ\ÙJ[˜Ý[ÛŠK
^Û›Û›ØYYK›Û™\œ›Ü]JK˜Y]™[\Ý[™\ŠØY[˜Ý[ÛŠ
^ÜË›ØY[™ßL_JK˜Y]™[\Ý[™\Š\œ›Ü˜[˜Ý[ÛŠ
^ÜË›ØY[™ßLŸJKË›ØY[™ßMÜ
ËŠ_[Ï^Ý\N˜Ý[\ÚY][œÝ[˜ÙN›ËÛÝ[ŒKÝ]NœßKKœÙ]
KÊ___Y[˜Ý[ÛˆYŠK
^Ò™‹–
K
NÝ˜\ˆVYŽÚYŠ‰‰™J^Ý˜\ˆS]
ŠKšÚ\ÝX›TØÜš\ËOX\
JKO\‹™Ù]
JNØ_
O[‹œ]Y\žTÙ[XÝÜŠÜ
JJK_
OU
ÜÜ˜Î™K\Þ[˜ÎˆLK
K
QÙ‹™Ù]
JJI‰›
K
KO[‹˜Ü™X]Q[[Y[
ØÜš\
K
JKYŠK[šØJK‹šXY˜\[™Ú[
JJKO^Ý\N˜ØÜš\[œÝ[˜ÙN˜KÛÝ[ŒKÝ]N›[K‹œÙ]
KJJ__Y[˜Ý[Ûˆ	ŠK
^Ò™‹“JK
NÝ˜\ˆVYŽÚYŠ‰‰™J^Ý˜\ˆS]
ŠKšÚ\ÝX›TØÜš\ËOX\
JKO\‹™Ù]
JNØ_
O[‹œ]Y\žTÙ[XÝÜŠÜ
JJK_
OU
ÜÜ˜Î™K\Þ[˜ÎˆL\N˜[Ù[XK
K
QÙ‹™Ù]
JJI‰›
K
KO[‹˜Ü™X]Q[[Y[
ØÜš\
K
JKYŠK[šØJK‹šXY˜\[™Ú[
JJKO^Ý\N˜ØÜš\[œÝ[˜ÙN˜KÛÝ[ŒKÝ]N›[K‹œÙ]
KJJ__Y[˜Ý[Ûˆ\
K‹Š^Ý˜\ˆOJO^YK˜Ý\œ™[
OÜYŠJN›[ÚYŠXJ]›ÝÈ\œ›ÜŠJŠJNÜÝÚ]Ú
J^ØØ\ÙXY]X˜Ø\ÙX]Xœ™]\›ˆ[ØØ\ÙXÝ[Xœ™]\›ˆ\[Ùˆ‹œ™XÙY[˜ÙOOXÝš[™Ø	‰\[Ùˆ‹š™YOXÝš[™ØÊ]
‹š™YŠKS]
JKšÚ\ÝX›TÝ[\Ë]™Ù]
ŠKŸ
^Ý\N˜Ý[X[œÝ[˜ÙN›[ÛÝ[ŒÝ]N›[KœÙ]
‹ŠJKŠNžÝ\N˜›ÚY[œÝ[˜ÙN›[ÛÝ[ŒÝ]N›[NØØ\ÙX[šØšYŠ‹œ™[OOXÝ[\ÚY]	‰\[Ùˆ‹š™YOXÝš[™Ø	‰\[Ùˆ‹œ™XÙY[˜ÙOOXÝš[™Ø
^ÙO]
‹š™YŠNÝ˜\ˆÏS]
JKšÚ\ÝX›TÝ[\ËÏ[Ë™Ù]
JNÚYŠß
OXK›ÝÛ™\‘ØÝ[Y[KÏ^Ý\N˜Ý[\ÚY][œÝ[˜ÙN›[ÛÝ[ŒÝ]NžÛØY[™ÎŒ™[ØY›[_KËœÙ]
KÊK
ÏXKœ]Y\žTÙ[XÝÜŠœ
JJJOÛË—Ü
Ëš[œÝ[˜ÙO[ËËœÝ]K›ØY[™ÏMJNŠÏQÙ‹™Ù]
JKß
Ï^Ü™[˜™[ØY\Î˜Ý[X™YŽ›‹š™Y‹Ü›ÜÜÓÜšYÚ[Ž›‹˜Ü›ÜÜÓÜšYÚ[‹[YÜš]N›‹š[YÜš]KYYXN›‹›YYXK™Y“[™Î›‹š™Y“[™Ë™Y™\œ™\”ÛXÞN›‹œ™Y™\œ™\”ÛXÞ_KÙ‹œÙ]
KÊJK\
KKËËœÝ]JJJK	‰œOO[[
]›ÝÈ\œ›ÜŠJLŽ
JNÜ™]\›ˆßZYŠ	‰œˆOO[[
]›ÝÈ\œ›ÜŠJLŽK
JNÜ™]\›ˆ[ØØ\ÙXØÜš\œ™]\›ˆ[‹˜\Þ[˜Ë[‹œÜ˜Ë\[ÙˆOXÝš[™Ø	‰	‰\[ÙˆOX[˜Ý[Û˜	‰\[ÙˆOXÞ[X›ÛÊX\
ŠKS]
JKšÚ\ÝX›TØÜš\Ë]™Ù]
ŠKŸ
^Ý\N˜ØÜš\[œÝ[˜ÙN›[ÛÝ[ŒÝ]N›[KœÙ]
‹ŠJKŠNžÝ\N˜›ÚY[œÝ[˜ÙN›[ÛÝ[ŒÝ]N›[NÙY˜][›ÝÈ\œ›ÜŠJJJ__Y[˜Ý[Ûˆ
J^Ü™]\›˜™YH˜
Ù[ŠJJØ˜Y[˜Ý[Ûˆœ
J^Ü™]\›˜[šÖÜ™[HœÝ[\ÚY]—VØ
ÙJØXY[˜Ý[Ûˆœ
J^Ü™]\›ˆ
ßKKÈ™]K\™XÙY[˜ÙHŽ™Kœ™XÙY[˜ÙK™XÙY[˜ÙN›[J_Y[˜Ý[Ûˆ\
K‹Š^ÚYŠYKœ]Y\žTÙ[XÝÜŠ[šÖÜ™[Hœ™[ØY—VØ\ÏHœÝ[H—VØ
Ý
ØX
J^ÚYŠLOO]ÑJ^Ü‹›ØY[™ÏLNÜ™]\›Ÿ_Y[ÙHYK˜Ü™X]Q[[Y[
[šØ
KÑOHL›Û›ØY]›Û™\œ›ÜT˜š[™
[
KYŠ[šØŠK

KKšXY˜\[™Ú[

NÜ‹œ™[ØY]˜Y]™[\Ý[™\ŠØY[˜Ý[ÛŠ
^Ü™]\›ˆ‹›ØY[™ßL_JK˜Y]™[\Ý[™\Š\œ›Ü˜[˜Ý[ÛŠ
^Ü™]\›ˆ‹›ØY[™ßLŸJ_Y[˜Ý[Ûˆ\
J^Ü™]\›˜ÜÜ˜ÏH˜
Ù[ŠJJØ—XY[˜Ý[ÛˆÜ
J^Ü™]\›˜ØÜš\Ø\Þ[˜×X
Ù_Y[˜Ý[ÛˆÝJKŠ^ÚYŠ˜ÛÝ[
ÊËš[œÝ[˜ÙOOO[[
\ÝÚ]Ú
\J^ØØ\ÙXÝ[X˜\ˆYKœ]Y\žTÙ[XÝÜŠÝ[VÙ]KZ™YŸH˜
Ù[Š‹š™YŠJØ—X
NÚYŠŠ\™]\›ˆš[œÝ[˜ÙO\‹
ŠKŽÝ˜\ˆOU
ßK‹È™]KZ™YˆŽ›‹š™Y‹™]K\™XÙY[˜ÙHŽ›‹œ™XÙY[˜ÙK™YŽ›[™XÙY[˜ÙN›[JNÜ™]\›ˆJK›ÝÛ™\‘ØÝ[Y[JK˜Ü™X]Q[[Y[
Ý[X
K
ŠKYŠ‹Ý[XJKÜ
‹‹œ™XÙY[˜ÙKJKš[œÝ[˜ÙO\ŽØØ\ÙXÝ[\ÚY]˜O]
‹š™YŠNÝ˜\ˆÏYKœ]Y\žTÙ[XÝÜŠœ
JJNÚYŠÊ\™]\›ˆœÝ]K›ØY[™ßMš[œÝ[˜ÙO[Ë
ÊKÎÜ\œ
ŠK
OQÙ‹™Ù]
JJI‰˜Ü
‹JKÏJK›ÝÛ™\‘ØÝ[Y[JK˜Ü™X]Q[[Y[
[šØ
K
ÊNÝ˜\ˆÏ[ÎÜ™]\›ˆË—Ü[™]È›ÛZ\ÙJ[˜Ý[ÛŠK
^ÜË›Û›ØYYKË›Û™\œ›Ü]JKYŠË[šØŠKœÝ]K›ØY[™ßMÜ
Ë‹œ™XÙY[˜ÙKJKš[œÝ[˜ÙO[ÎØØ\ÙXØÜš\œ™]\›ˆÏX\
‹œÜ˜ÊK
OYKœ]Y\žTÙ[XÝÜŠÜ
ÊJJOÊš[œÝ[˜ÙOXK
JKJNŠ[‹
OQÙ‹™Ù]
ÊJI‰ŠU
ßKŠK
‹JJKOYK›ÝÛ™\‘ØÝ[Y[KOYK˜Ü™X]Q[[Y[
ØÜš\
K
JKYŠK[šØŠKKšXY˜\[™Ú[
JKš[œÝ[˜ÙOXJNØØ\ÙX›ÚYœ™]\›ˆ[ÙY˜][›ÝÈ\œ›ÜŠJË\JJ_Y[ÙH\OOOXÝ[\ÚY]	‰ˆJœÝ]K›ØY[™É
I‰Š]š[œÝ[˜ÙKœÝ]K›ØY[™ßMÜ
‹‹œ™XÙY[˜ÙKJJNÜ™]\›ˆš[œÝ[˜Ù_Y[˜Ý[ÛˆÜ
KŠ^Ù›ÜŠ˜\ˆ[‹œ]Y\žTÙ[XÝÜ[
[šÖÜ™[HœÝ[\ÚY]—VÙ]K\™XÙY[˜ÙWKÝ[VÙ]K\™XÙY[˜ÙWX
KO\‹›[™ÝÜ–Ü‹›[™ÝLWN›[OZKÏLÛÏ‹›[™ÝÛÊÊÊ^Ý˜\ˆÏ\–Û×NÚYŠË™]\Ù]œ™XÙY[˜ÙOOO]
XO\ÎÙ[ÙHYŠHOOZJXœ™XZßXOØKœ\™[›ÙKš[œÙ\™Y›Ü™JKK›™^ÚX›[™ÊNŠ[‹››ÙU\OOONOÛ‹šXY›‹š[œÙ\™Y›Ü™JK™š\œÝÚ[
J_Y[˜Ý[ÛˆÜ
K
^ÙK˜Ü›ÜÜÓÜšYÚ[ÏÏ]˜Ü›ÜÜÓÜšYÚ[‹Kœ™Y™\œ™\”ÛXÞOÏÏ]œ™Y™\œ™\”ÛXÞKK]OÏÏ]]_Y[˜Ý[Ûˆ
K
^ÙK˜Ü›ÜÜÓÜšYÚ[ÏÏ]˜Ü›ÜÜÓÜšYÚ[‹Kœ™Y™\œ™\”ÛXÞOÏÏ]œ™Y™\œ™\”ÛXÞKKš[YÜš]OÏÏ]š[YÜš]_]˜\ˆ\[[Ù[˜Ý[Ûˆ
KŠ^ÚYŠ\OO[[
^Ý˜\ˆ[™]ÈX\O]\[™]ÈX\ÚKœÙ]
‹Š_Y[ÙHO]\ZK™Ù]
ŠKŸ
[™]ÈX\KœÙ]
‹ŠJNÚYŠ‹š\ÊJJ\™]\›ˆŽÙ›ÜŠ‹œÙ]
K[
K[‹™Ù][[Y[ÐžUYÓ˜[YJJKOLÚO‹›[™ÝÚJÊÊ^Ý˜\ˆO[–ÚWNÚYŠJVÑ]_VÞ]_OOOX[šØ	‰˜K™Ù]]šX]J™[
OOOXÝ[\ÚY]
I‰˜K›˜[Y\ÜXÙUT’HOOX‹ËÝÝÝËÌË›Ü™ËÌŒÜÝ™Ø
^Ý˜\ˆÏXK™Ù]]šX]J
_ÛÏYJÛÎÝ˜\ˆÏ\‹™Ù]
ÊNÜÏÜËœ\Ú
JNœ‹œÙ]
ËØWJ__\™]\›ˆŸY[˜Ý[Ûˆœ
KŠ^ÙOYK›ÝÛ™\‘ØÝ[Y[KKšXYš[œÙ\™Y›Ü™J‹OOX]XÙKœ]Y\žTÙ[XÝÜŠXYˆ]X
N›[
_Y[˜Ý[Ûˆ
KŠ^ÚYŠOOL_š][T›ÜO[[
\™]\›ˆLNÜÝÚ]Ú
J^ØØ\ÙXY]X˜Ø\ÙX]Xœ™]\›ˆLØØ\ÙXÝ[XšYŠ\[Ùˆœ™XÙY[˜ÙHOXÝš[™Ø\[Ùˆš™YˆOXÝš[™Øš™YOOX
Xœ™XZÎÜ™]\›ˆLØØ\ÙX[šØšYŠ\[Ùˆœ™[OXÝš[™Ø\[Ùˆš™YˆOXÝš[™Øš™YOOX›Û“ØY›Û‘\œ›ÜŠXœ™XZÎÜÝÚ]Ú
œ™[
^ØØ\ÙXÝ[\ÚY]œ™]\›ˆO]™\ØX›Y\[Ùˆœ™XÙY[˜ÙOOXÝš[™Ø	‰™OO[[ÙY˜][œ™]\›ˆLXØ\ÙXØÜš\šYŠ˜\Þ[˜É‰\[Ùˆ˜\Þ[˜ÈOX[˜Ý[Û˜	‰\[Ùˆ˜\Þ[˜ÈOXÞ[X›Û	‰ˆ]›Û“ØY	‰ˆ]›Û‘\œ›Ü‰‰œÜ˜É‰\[ÙˆœÜ˜ÏOXÝš[™Ø
\™]\›ˆL\™]\›ˆL_Y[˜Ý[Ûˆ\
K
^Ü™]\›ˆOOOX[YØ	‰œÜ˜ÈO[[	‰œÜ˜ÈOOX	‰›Û“ØYO[[	‰›ØY[™ÈOOX^žXY[˜Ý[Ûˆ
J^Ü™]\›ˆJK\OOOXÝ[\ÚY]	‰ˆJKœÝ]K›ØY[™ÉŒÊJ_Y[˜Ý[ÛˆÜ
J^Ü™]\›ŠKÚYL
JŠKšZYÚL
JŠ\[Ùˆ]šXÙT^[˜][ÏOX[X™\˜Ù]šXÙT^[˜][ÎŒJJ‹Œ_Y[˜Ý[ÛˆÜ
K
^Ý\[Ùˆ™XÛÙOOX[˜Ý[Û˜	‰ŠKš[YÐÛÝ[
ÊË˜ÛÛ\]_
Kš[YÐž]\ÊÏYÜ

KKœÝ\Ü[œÙ^R[XYÙ\Ëœ\Ú

JKOTÜ˜š[™
JK™XÛÙJ
K[ŠKJJ_Y[˜Ý[ÛˆÝJK‹Š^ÚYŠ‹\OOOXÝ[\ÚY]	‰Š\[Ùˆ‹›YYXHOXÝš[™ØLHOO[X]ÚYYXJ‹›YYXJK›X]Ú\ÊI‰ˆJ‹œÝ]K›ØY[™É
J^ÚYŠ‹š[œÝ[˜ÙOOO[[
^Ý˜\ˆO]
‹š™YŠKO]œ]Y\žTÙ[XÝÜŠœ
JJNÚYŠJ^ÝXK—Ü\[ÙˆOXØš™XÝ	‰	‰\[Ùˆ[OX[˜Ý[Û˜	‰ŠK˜ÛÝ[
ÊËO^˜š[™
JK[ŠKJJK‹œÝ]K›ØY[™ßM‹š[œÝ[˜ÙOXK
JNÜ™]\›ŸXO]›ÝÛ™\‘ØÝ[Y[\œ
ŠK
OQÙ‹™Ù]
JJI‰˜Ü
‹JKOXK˜Ü™X]Q[[Y[
[šØ
K
JNÝ˜\ˆÏXNÛË—Ü[™]È›ÛZ\ÙJ[˜Ý[ÛŠK
^ÛË›Û›ØYYKË›Û™\œ›Ü]JKYŠK[šØŠK‹š[œÝ[˜ÙOX_YKœÝ[\ÚY]ÏOO[[	‰ŠKœÝ[\ÚY]Ï[™]ÈX\
KKœÝ[\ÚY]ËœÙ]
‹
K
[‹œÝ]Kœ™[ØY
I‰ˆJ‹œÝ]K›ØY[™ÉŒÊI‰ŠK˜ÛÝ[
ÊË^˜š[™
JK˜Y]™[\Ý[™\ŠØYŠK˜Y]™[\Ý[™\Š\œ›Ü˜ŠJ__]˜\ˆœLÙ[˜Ý[Ûˆ\
K
^Ü™]\›ˆKœÝ[\ÚY]É‰™K˜ÛÝ[OOL	‰Ü
KKœÝ[\ÚY]ÊKK˜ÛÝ[Kš[YÐÛÝ[Ù[˜Ý[ÛŠŠ^Ý˜\ˆ\Ù][Y[Ý]
[˜Ý[ÛŠ
^ÚYŠKœÝ[\ÚY]É‰Ü
KKœÝ[\ÚY]ÊKK[œÝ\Ü[™
^Ý˜\ˆYK[œÝ\Ü[™ÙK[œÝ\Ü[™[[

__K™M
Ý
NÌKš[YÐž]\É‰œOOL	‰ŠœMŒL
šJ
JNÝ˜\ˆO\Ù][Y[Ý]
[˜Ý[ÛŠ
^ÚYŠKØZ][™Ñ›Ü’[XYÙ\ÏHLKK˜ÛÝ[OOL	‰ŠKœÝ[\ÚY]É‰Ü
KKœÝ[\ÚY]ÊKK[œÝ\Ü[™
J^Ý˜\ˆYK[œÝ\Ü[™ÙK[œÝ\Ü[™[[

__K
Kš[YÐž]\ÏœÍLŽ
JÝ
NÜ™]\›ˆK[œÝ\Ü[™[‹[˜Ý[ÛŠ
^ÙK[œÝ\Ü[™[[ÛX\•[Y[Ý]
ŠKÛX\•[Y[Ý]
J__N›[Y[˜Ý[Ûˆœ
J^ÚYŠK˜ÛÝ[OOL	‰ŠKš[YÐÛÝ[OOLYKØZ][™Ñ›Ü’[XYÙ\ÊJ^ÚYŠKœÝ[\ÚY]Ê]Ü
KKœÝ[\ÚY]ÊNÙ[ÙHYŠK[œÝ\Ü[™
^Ý˜\ˆYK[œÝ\Ü[™ÙK[œÝ\Ü[™[[

___Y[˜Ý[Ûˆ

^Ý\Ë˜ÛÝ[KKœ
\Ê_Y[˜Ý[ÛˆÜ

^Ý\Ëš[YÐÛÝ[KKœ
\Ê_]˜\ˆÜ[[Ù[˜Ý[ÛˆÜ
K
^ÙKœÝ[\ÚY]Ï[[K[œÝ\Ü[™OO[[	‰ŠK˜ÛÝ[
ÊËÜ[™]ÈX\™›Ü‘XXÚ
]KJKÜ[[˜Ø[
JJ_Y[˜Ý[Ûˆ]JK
^ÚYŠJœÝ]K›ØY[™É
J^Ý˜\ˆPÜ™Ù]
JNÚYŠŠ]˜\ˆ[‹™Ù]
[
NÙ[Ù^Û[™]ÈX\ÜœÙ]
KŠNÙ›ÜŠ˜\ˆOYKœ]Y\žTÙ[XÝÜ[
[šÖÙ]K\™XÙY[˜ÙWKÝ[VÙ]K\™XÙY[˜ÙWX
KOLØOK›[™ÝØJÊÊ^Ý˜\ˆÏZVØWNÊË››ÙS˜[YOOOXS’ØË™Ù]]šX]JYYXX
HOOX›Ý[
I‰Š‹œÙ]
Ë™]\Ù]œ™XÙY[˜ÙKÊK[Ê_\‰‰›‹œÙ]
[Š_ZO]š[œÝ[˜ÙKÏZK™Ù]]šX]J]K\™XÙY[˜ÙX
KO[‹™Ù]
Ê_‹OOO\‰‰›‹œÙ]
[JK‹œÙ]
ËJK\Ë˜ÛÝ[
ÊË^˜š[™
\ÊKK˜Y]™[\Ý[™\ŠØYŠKK˜Y]™[\Ý[™\Š\œ›Ü˜ŠKOØKœ\™[›ÙKš[œÙ\™Y›Ü™JKK›™^ÚX›[™ÊNŠOYK››ÙU\OOONOÙKšXY™KKš[œÙ\™Y›Ü™JKK™š\œÝÚ[
JKœÝ]K›ØY[™ßM_]˜\ˆ^É	\[ÙŽ“‹›ÝšY\Ž›[ÛÛœÝ[Y\Ž›[ØÝ\œ™[˜[YN™KØÝ\œ™[˜[YLŽ™KÝ™XYÛÝ[ŒNÙ[˜Ý[ÛˆJK‹‹KKËË
^Ý\ËYÏLK\Ë˜ÛÛZ[™\’[™›ÏYK\Ëœ[™ÐØXÚO]\Ë˜Ý\œ™[]\Ëœ[™[™ÐÚ[™[[[\Ë[Y[Ý][™OKLK\Ë˜Ø[˜XÚÓ›ÙO]\Ë›™^]\Ëœ[™[™ÐÛÛ^]\Ë˜ÛÛ^]\Ë˜Ø[˜Ù[[™[™ÐÛÛ[Z][[\Ë˜Ø[˜XÚÔš[Üš]OL\Ë™^\˜][Û•[Y\ÏXÝ
LJK\Ë™[[™ÛY[™\Ï]\ËœÚ[Ý\Ü[™ÛÝ[\]\Ë™\œ›Ü”™XÛÝ™\žQ\ØX›Y[™\Ï]\Ë™^\™Y[™\Ï]\ËØ\›S[™\Ï]\Ëœ[™ÙY[™\Ï]\ËœÝ\Ü[™Y[™\Ï]\Ëœ[™[™Ó[™\ÏL\Ë™[[™Û[Y[ÏXÝ

K\ËšY[•\]\ÏXÝ
[
K\ËšY[YšY\”™Yš^\‹\Ë›Û•[˜Ø]YÚ\œ›ÜZK\Ë›ÛØ]YÚ\œ›ÜXK\Ë›Û”™XÛÝ™\˜X›Q\œ›Ü[Ë\ËœÛÛYØXÚO[[\ËœÛÛYØXÚS[™\ÏL\Ë™›Ü›TÝ]O[\Ë˜[œÚ][Û•\\Ï[[\Ëš[˜ÛÛ\]U˜[œÚ][ÛœÏ[™]ÈX\Y[˜Ý[Ûˆ]JK‹‹KKËËKŠ^Ü™]\›ˆO[™]ÈJK‹ËK‹ÊKLKLOOXI‰ŠL
KOYJË[[
KK˜Ý\œ™[XKKœÝ]S›ÙOYK]XJ
Kœ™YÛÝ[
ÊËKœÛÛYØXÚO]œ™YÛÝ[
ÊËK›Y[[Ú^™YÝ]O^Ù[[Y[œ‹\ÑZY˜]Y›‹ØXÚNKXJJK_Y[˜Ý[ÛˆJJ^Ü™]\›ˆOÊO]ZKJNZ_Y[˜Ý[Ûˆ\
K‹‹KJ^ÚOVJJK‹˜ÛÛ^OO[[Ü‹˜ÛÛ^ZNœ‹œ[™[™ÐÛÛ^ZKQØJ
K‹œ^[ØY^Ù[[Y[›ŸKOXOOO]›ÚYÛ[˜KHOO[[	‰Š‹˜Ø[˜XÚÏXJKRØJK‹
KˆOO[[	‰ŠÝJ‹K
KXJ‹K
J_Y[˜Ý[ÛˆJK
^ÚYŠOYK›Y[[Ú^™YÝ]KHOO[[	‰™K™ZY˜]YOO[[
^Ý˜\ˆYKœ™]žS[™NÙKœ™]žS[™O[ˆOOL	‰›ÛŽ_Y[˜Ý[Ûˆ
K
^ÖJK
K
OYK˜[\›˜]JI‰–JK
_Y[˜Ý[ÛˆÜ
J^ÚYŠKYÏOOLLßKYÏOOLÌJ^Ý˜\ˆ\ÚJKÌL
NÝOO[[	‰•ÝJKÌL
K
KÌL
__Y[˜Ý[Ûˆ]JJ^ÚYŠKYÏOOLLßKYÏOOLÌJ^Ý˜\ˆRJ
NÝ[]

NÝ˜\ˆ\ÚJK
NÛˆOO[[	‰•ÝJ‹K
K
K
__]˜\ˆÜHLÙ[˜Ý[Ûˆ	JK‹Š^Ý˜\ˆO[K•ÛK•[[Ý˜\ˆO]YKœÝž^ÝYKœL‹\
K‹Š_Yš[˜[^ÝYKœXKK•Z__Y[˜Ý[Ûˆ[™JK‹Š^Ý˜\ˆO[K•ÛK•[[Ý˜\ˆO]YKœÝž^ÝYKœN\
K‹Š_Yš[˜[^ÝYKœXKK•Z__Y[˜Ý[Ûˆ\
K‹Š^ÚYŠÜ
^Ý˜\ˆOZœ
ŠNÚYŠOOO[[
RÙ
K‹\ŠK
KŠNÙ[ÙHYŠÜ
KK‹ŠJ\‹œÝÜ›ÜYØ][ÛŠ
NÙ[ÙHYŠ
KŠK		‰‹LOœš[™^ÙŠJJ^Ù›ÜŠÚHOO[[Ê^Ý˜\ˆOP]
JNÚYŠHOO[[
\ÝÚ]Ú
KYÊ^ØØ\ÙHÎšYŠOXKœÝ]S›ÙKK˜Ý\œ™[›Y[[Ú^™YÝ]Kš\ÑZY˜]Y
^Ý˜\ˆÏ[
Kœ[™[™Ó[™\ÊNÚYŠÈOOL
^Ý˜\ˆÏXNÙ›ÜŠËœ[™[™Ó[™\ßL‹Ë™[[™ÛY[™\ßLŽÛÎÊ^Ý˜\ˆLOÌKVYJÊNÜË™[[™Û[Y[ÖÌW_[É_›ZÙ
JKJÝIŠI‰ŠOSJ
JÍLY
LJJ__Xœ™XZÎØØ\ÙHÌN˜Ø\ÙHLÎœÏ\ÚJKŠKÈOO[[	‰•ÝJËKŠK]J
K
KŠ_ZYŠOZœ
ŠKOOO[[	‰’Ù
K‹\ŠKOOOZJXœ™XZÎÚOX_ZHOO[[	‰œ‹œÝÜ›ÜYØ][ÛŠ
_Y[ÙHÙ
K‹[Š__Y[˜Ý[Ûˆœ
J^Ü™]\›ˆOYÛŠJKœ
J_]˜\ˆ\[[Ù[˜Ý[Ûˆœ
J^ÚYŠ\[[OZÝ
JKHOO[[
^Ý˜\ˆ[ÊJNÚYŠOO[[
YO[[Ù[Ù^Ý˜\ˆ]YÎÚYŠOOLLÊ^ÚYŠO\Ê
KHOO[[
\™]\›ˆNÙO[[Y[ÙHYŠOOLÌJ^ÚYŠO[

KHOO[[
\™]\›ˆNÙO[[Y[ÙHYŠOOLÊ^ÚYŠœÝ]S›ÙK˜Ý\œ™[›Y[[Ú^™YÝ]Kš\ÑZY˜]Y
\™]\›ˆYÏOOLÏÝœÝ]S›ÙK˜ÛÛZ[™\’[™›Î›[ÙO[[Y[ÙHOOYI‰ŠO[[
__\™]\›ˆ\YK[Y[˜Ý[Ûˆ™JJ^ÜÝÚ]Ú
J^ØØ\ÙX™Y›Ü™]ÙÙÛX˜Ø\ÙXØ[˜Ù[˜Ø\ÙXÛXÚØ˜Ø\ÙXÛÜÙX˜Ø\ÙXÛÛ^Y[X˜Ø\ÙXÛÜX˜Ø\ÙXÝ]˜Ø\ÙX]^ÛXÚØ˜Ø\ÙX›ÛXÚØ˜Ø\ÙX˜YÙ[™˜Ø\ÙX˜YÜÝ\˜Ø\ÙX›Ü˜Ø\ÙX›ØÝ\Ú[˜˜Ø\ÙX›ØÝ\ÛÝ]˜Ø\ÙX[œ]˜Ø\ÙX[˜[Y˜Ø\ÙXÙ^YÝÛ˜˜Ø\ÙXÙ^\™\ÜØ˜Ø\ÙXÙ^]\˜Ø\ÙX[Ý\ÙYÝÛ˜˜Ø\ÙX[Ý\Ù]\˜Ø\ÙX\ÝX˜Ø\ÙX]\ÙX˜Ø\ÙX^X˜Ø\ÙXÚ[\˜Ø[˜Ù[˜Ø\ÙXÚ[\™ÝÛ˜˜Ø\ÙXÚ[\\˜Ø\ÙX˜]XÚ[™ÙX˜Ø\ÙX™\Ù]˜Ø\ÙXÙYZÙY˜Ø\ÙXÝX›Z]˜Ø\ÙXÙÙÛX˜Ø\ÙXÝXÚØ[˜Ù[˜Ø\ÙXÝXÚ[™˜Ø\ÙXÝXÚÝ\˜Ø\ÙX›Û[YXÚ[™ÙX˜Ø\ÙXÚ[™ÙX˜Ø\ÙXÙ[XÝ[Û˜Ú[™ÙX˜Ø\ÙX^[œ]˜Ø\ÙXÛÛ\ÜÚ][ÛœÝ\˜Ø\ÙXÛÛ\ÜÚ][Û™[™˜Ø\ÙXÛÛ\ÜÚ][Û\]X˜Ø\ÙX™Y›Ü™X›\˜˜Ø\ÙXY\˜›\˜˜Ø\ÙX™Y›Ü™Z[œ]˜Ø\ÙX›\˜˜Ø\ÙX[ØÜ™Y[˜Ú[™ÙX˜Ø\ÙX[ØÜ™Y[™\œ›Ü˜˜Ø\ÙX›ØÝ\Ø˜Ø\ÙX\ÚÚ[™ÙX˜Ø\ÙXÜÝ]X˜Ø\ÙXÙ[XÝ˜Ø\ÙXÙ[XÝÝ\œ™]\›ˆŽØØ\ÙX˜YØ˜Ø\ÙX˜YÙ[\˜˜Ø\ÙX˜YÙ^]˜Ø\ÙX˜YÛX]™X˜Ø\ÙX˜YÛÝ™\˜˜Ø\ÙX[Ý\Ù[[Ý™X˜Ø\ÙX[Ý\Ù[Ý]˜Ø\ÙX[Ý\Ù[Ý™\˜˜Ø\ÙXÚ[\›[Ý™X˜Ø\ÙXÚ[\›Ý]˜Ø\ÙXÚ[\›Ý™\˜˜Ø\ÙX™\Ú^™X˜Ø\ÙXØÜ›Û˜Ø\ÙXÝXÚ[Ý™X˜Ø\ÙXÚY[˜Ø\ÙX[Ý\ÙY[\˜˜Ø\ÙX[Ý\Ù[X]™X˜Ø\ÙXÚ[\™[\˜˜Ø\ÙXÚ[\›X]™Xœ™]\›ˆØØ\ÙXY\ÜØYÙXœÝÚ]Ú
™J
J^ØØ\ÙH™Nœ™]\›ˆŽØØ\ÙH™Nœ™]\›ˆØØ\ÙH™N˜Ø\ÙHNœ™]\›ˆÌŽØØ\ÙHYNœ™]\›ˆŽÍMMŽÙY˜][œ™]\›ˆÌŸYY˜][œ™]\›ˆÌŸ_]˜\ˆHLKœ[[\[[[[œ[™]ÈX\œ[™]ÈX\œV×KœX[Ý\ÙYÝÛˆ[Ý\Ù]\ÝXÚØ[˜Ù[ÝXÚ[™ÝXÚÝ\]^ÛXÚÈ›ÛXÚÈÚ[\˜Ø[˜Ù[Ú[\™ÝÛˆÚ[\\˜YÙ[™˜YÜÝ\›ÜÛÛ\ÜÚ][Û™[™ÛÛ\ÜÚ][ÛœÝ\Ù^YÝÛˆÙ^\™\ÜÈÙ^]\[œ]^[œ]ÛÜHÝ]\ÝHÛXÚÈÚ[™ÙHÛÛ^Y[H™\Ù]œÜ]

NÙ[˜Ý[Ûˆ
K
^ÜÝÚ]Ú
J^ØØ\ÙX›ØÝ\Ú[˜˜Ø\ÙX›ØÝ\ÛÝ]‘œ[[Øœ™XZÎØØ\ÙX˜YÙ[\˜˜Ø\ÙX˜YÛX]™X’\[[Øœ™XZÎØØ\ÙX[Ý\Ù[Ý™\˜˜Ø\ÙX[Ý\Ù[Ý]“[[Øœ™XZÎØØ\ÙXÚ[\›Ý™\˜˜Ø\ÙXÚ[\›Ý]”œ™[]JœÚ[\’Y
NØœ™XZÎØØ\ÙXÛÝÚ[\˜Ø\\™X˜Ø\ÙXÜÝÚ[\˜Ø\\™Xžœ™[]JœÚ[\’Y
__Y[˜Ý[Ûˆ\
K‹‹KJ^Ü™]\›ˆOOO[[K›˜]]™Q]™[OOXOÊO^Ø›ØÚÙYÛŽÛQ]™[˜[YN›‹]™[Þ\Ý[Q›YÜÎœ‹˜]]™Q]™[˜K\™Ù]ÛÛZ[™\œÎ–ÚW_KOO[[	‰ŠP]

KOO[[	‰“Ü

JKJNŠK™]™[Þ\Ý[Q›YÜß\‹YK\™Ù]ÛÛZ[™\œËHOO[[	‰š[™^ÙŠJOOOKLI‰œ\Ú
JKJ_Y[˜Ý[ÛˆÜ
K‹‹J^ÜÝÚ]Ú

^ØØ\ÙX›ØÝ\Ú[˜œ™]\›ˆœU\
œK‹‹JKLØØ\ÙX˜YÙ[\˜œ™]\›ˆ\U\
\K‹‹JKLØØ\ÙX[Ý\Ù[Ý™\˜œ™]\›ˆU\
K‹‹JKLØØ\ÙXÚ[\›Ý™\˜˜\ˆOZKœÚ[\’YÜ™]\›ˆœœÙ]
K\
œ™Ù]
J_[K‹‹JJKLØØ\ÙXÛÝÚ[\˜Ø\\™Xœ™]\›ˆOZKœÚ[\’YœœÙ]
K\
œ™Ù]
J_[K‹‹JJKL\™]\›ˆL_Y[˜Ý[ÛˆÜ
J^Ý˜\ˆZÝ
K\™Ù]
NÚYŠOO[[
^Ý˜\ˆ[Ê
NÚYŠˆOO[[
^ÚYŠ[‹YËOOLLÊ^ÚYŠ\ÊŠKOO[[
^ÙK˜›ØÚÙYÛ]Ý
Kœš[Üš]K[˜Ý[ÛŠ
^Ô]JŠ_JNÜ™]\›Ÿ_Y[ÙHYŠOOLÌJ^ÚYŠ[
ŠKOO[[
^ÙK˜›ØÚÙYÛ]Ý
Kœš[Üš]K[˜Ý[ÛŠ
^Ô]JŠ_JNÜ™]\›Ÿ_Y[ÙHYŠOOLÉ‰›‹œÝ]S›ÙK˜Ý\œ™[›Y[[Ú^™YÝ]Kš\ÑZY˜]Y
^ÙK˜›ØÚÙYÛ[‹YÏOOLÏÛ‹œÝ]S›ÙK˜ÛÛZ[™\’[™›Î›[Ü™]\›Ÿ__YK˜›ØÚÙYÛ[[Y[˜Ý[ÛˆÜ
J^ÚYŠK˜›ØÚÙYÛˆOO[[
\™]\›ˆLNÙ›ÜŠ˜\ˆYK\™Ù]ÛÛZ[™\œÎÌ›[™ÝÊ^Ý˜\ˆZœ
K›˜]]™Q]™[
NÚYŠOO[[
^ÛYK›˜]]™Q]™[Ý˜\ˆ[™]È‹˜ÛÛœÝXÝÜŠ‹\KŠNÚ\‹‹\™Ù]™\Ü]Ú]™[
ŠK[[Y[ÙH™]\›ˆP]
ŠKOO[[	‰“Ü

KK˜›ØÚÙYÛ[‹LNÝœÚY

_\™]\›ˆLY[˜Ý[Ûˆ\
KŠ^ÒÜ
JI‰›‹™[]J
_Y[˜Ý[Ûˆ›™J
^ÔHLKœOO[[	‰’Ü
œ
I‰Šœ[[
K\OO[[	‰’Ü
\
I‰Š\[[
KOO[[	‰’Ü

I‰Š[[
Kœ™›Ü‘XXÚ
\
Kœ™›Ü‘XXÚ
\
_Y[˜Ý[Ûˆœ
KŠ^ÙK˜›ØÚÙYÛOO[‰‰ŠK˜›ØÚÙYÛ[[
HL[œÝX›WÜØÚY[PØ[˜XÚÊ[œÝX›WÓ›Ü›X[š[Üš]K›™JJJ_]˜\ˆ\[[Ù[˜Ý[Ûˆ
J^Ö\OOYI‰Š\YK[œÝX›WÜØÚY[PØ[˜XÚÊ[œÝX›WÓ›Ü›X[š[Üš]K[˜Ý[ÛŠ
^Ö\OOYI‰Š\[[
NÙ›ÜŠ˜\ˆLÝK›[™ÝÝ
ÏLÊ^Ý˜\ˆYVÝKYVÝ
ÌWKOYVÝ
Ì—NÚYŠ\[ÙˆˆOX[˜Ý[Û˜
^ÚYŠœ
ŸŠOOO[[
XÛÛ[YNØœ™XZß]˜\ˆOP]
ŠNØHOO[[	‰ŠKœÜXÙJÊKOLË\ÊKÜ[™[™ÎˆL]NšKY]Ù›‹›Y]ÙXÝ[ÛŽœŸK‹JJ__JJ_Y[˜Ý[Ûˆœ
J^Ù[˜Ý[Ûˆ

^Ü™]\›ˆœ
J_QœOO[[	‰’œ
œJK\OO[[	‰’œ
\JKOO[[	‰’œ
JKœ™›Ü‘XXÚ

Kœ™›Ü‘XXÚ

NÙ›ÜŠ˜\ˆLÛœ›[™ÝÛŠÊÊ^Ý˜\ˆPœÛ—NÜ‹˜›ØÚÙYÛOOYI‰Š‹˜›ØÚÙYÛ[[
_Y›ÜŠÌœ›[™Ý	‰ŠPœÌK‹˜›ØÚÙYÛOO[[
NÊQÜ
ŠK‹˜›ØÚÙYÛOO[[	‰œœÚY

NÚYŠJK›ÝÛ™\‘ØÝ[Y[JK‰	™XXÝ›Ü›T™\^KˆO[[
Y›ÜŠLÜ‹›[™ÝÜŠÏLÊ^Ý˜\ˆO[–Ü—KO[–ÜŠÌWKÏZVØ_[ÚYŠ\[ÙˆOOX[˜Ý[Û˜
[ß
ŠNÙ[ÙHYŠÊ^Ý˜\ˆÏ[[ÚYŠI‰˜Kš\Ð]šX]J›Ü›PXÝ[Û˜
J^ÚYŠOXKÏXVØ_[
\Ï[Ë™›Ü›PXÝ[ÛŽÙ[ÙHYŠœ
JHOO[[
XÛÛ[Y_Y[ÙHÏ[Ë˜XÝ[ÛŽÝ\[ÙˆÏOX[˜Ý[Û˜Û–ÜŠÌWO\ÎŠ‹œÜXÙJ‹ÊK‹OLÊK
Š___Y[˜Ý[Ûˆ\

^Ù[˜Ý[ÛˆJJ^ÙK˜Ø[’[\˜Ù\	‰™Kš[™›ÏOOX™XXÝ]˜[œÚ][Û˜	‰™Kš[\˜Ù\
Ú[™\Ž™[˜Ý[ÛŠ
^Ü™]\›ˆ™]È›ÛZ\ÙJ[˜Ý[ÛŠJ^Ü™]\›ˆOY_J_K›ØÝ\Ô™\Ù]˜X[X[ØÜ›Û˜X[X[J_Y[˜Ý[Ûˆ

^ÚHOO[[	‰ŠJ
KO[[
KŸÙ][Y[Ý]
‹Œ
_Y[˜Ý[ÛˆŠ
^ÚYŠ\‰‰ˆ[˜]šYØ][Û‹˜[œÚ][ÛŠ^Ý˜\ˆO[˜]šYØ][Û‹˜Ý\œ™[[žNÙI‰™K\›O[[	‰›˜]šYØ][Û‹›˜]šYØ]JK\›ÜÝ]N™K™Ù]Ý]J
K[™›Î˜™XXÝ]˜[œÚ][Û˜\ÝÜžN˜™\XÙXJ__ZYŠ\[Ùˆ˜]šYØ][ÛOXØš™XÝ
^Ý˜\ˆHLKO[[Ü™]\›ˆ˜]šYØ][Û‹˜Y]™[\Ý[™\Š˜]šYØ]XJK˜]šYØ][Û‹˜Y]™[\Ý[™\Š˜]šYØ]\ÝXØÙ\ÜØ
K˜]šYØ][Û‹˜Y]™[\Ý[™\Š˜]šYØ]Y\œ›Ü˜
KÙ][Y[Ý]
‹L
K[˜Ý[ÛŠ
^ÜHL˜]šYØ][Û‹œ™[[Ý™Q]™[\Ý[™\Š˜]šYØ]XJK˜]šYØ][Û‹œ™[[Ý™Q]™[\Ý[™\Š˜]šYØ]\ÝXØÙ\ÜØ
K˜]šYØ][Û‹œ™[[Ý™Q]™[\Ý[™\Š˜]šYØ]Y\œ›Ü˜
KHOO[[	‰ŠJ
KO[[
___Y[˜Ý[Ûˆ	
J^Ý\Ë—Ú[\›˜[›ÛÝY_Y[Kœ›ÝÝ\Kœ™[™\Iœ›ÝÝ\Kœ™[™\Y[˜Ý[ÛŠJ^Ý˜\ˆ]\Ë—Ú[\›˜[›ÛÝÚYŠOO[[
]›ÝÈ\œ›ÜŠJJJNÝ˜\ˆ]˜Ý\œ™[Ñ\
‹J
KK[[
_K[Kœ›ÝÝ\K[›[Ý[Iœ›ÝÝ\K[›[Ý[Y[˜Ý[ÛŠ
^Ý˜\ˆO]\Ë—Ú[\›˜[›ÛÝÚYŠHOO[[
^Ý\Ë—Ú[\›˜[›ÛÝ[[Ý˜\ˆYK˜ÛÛZ[™\’[™›ÎÑ\
K˜Ý\œ™[‹[K[[
K]J
KÞO[[_NÙ[˜Ý[Ûˆ[JJ^Ý\Ë—Ú[\›˜[›ÛÝY_Y[Kœ›ÝÝ\K[œÝX›WÜØÚY[RY˜][ÛY[˜Ý[ÛŠJ^ÚYŠJ^Ý˜\ˆYÝ

NÙO^Ø›ØÚÙYÛŽ›[\™Ù]™Kš[Üš]NNÙ›ÜŠ˜\ˆLÛœ›[™Ý	‰OOL	‰œÛ—Kœš[Üš]NÛŠÊÊNÐœœÜXÙJ‹JKOOL	‰‘Ü
J__NÝ˜\ˆO[‹™\œÚ[ÛŽÚYŠHOOXNKŒËŒ
]›ÝÈ\œ›ÜŠJLËKNKŒËŒ
JNÝYK™š[™ÓS›ÙOY[˜Ý[ÛŠJ^Ý˜\ˆYK—Ü™XXÝ[\›˜[ÎÚYŠOO]›ÚY
]›ÝÈ\[ÙˆKœ™[™\OX[˜Ý[Û˜Ñ\œ›ÜŠJN
JNŠOSØš™XÝšÙ^\ÊJKš›Ú[Š
K\œ›ÜŠJŽJJJNÜ™]\›ˆOY

KOYOOO[[Û[™ŠJKOYOOO[[Û[™KœÝ]S›ÙK_NÝ˜\ˆ›O^Ø[™U\NŒ™\œÚ[ÛŽ˜NKŒËŒ™[™\™\”XÚØYÙS˜[YN˜™XXÝYÛXÝ\œ™[\Ü]Ú\”™YŽ›K™XÛÛ˜Ú[\•™\œÚ[ÛŽ˜NKŒËŒNÚYŠ\[Ùˆ×Ô‘PPÕÑU•ÓÓ×ÑÓÐSÒÓÒ××ÏX
^Ý˜\ˆ›OW×Ô‘PPÕÑU•ÓÓ×ÑÓÐSÒÓÒ××ÎÚYŠ\›Kš\Ñ\ØX›Y	‰œ›KœÝ\ÜÑšX™\Š]ž^ÒÙO\›Kš[š™XÝ
›JKYO\›_XØ]Úß_YK˜Ü™X]T›ÛÝY[˜Ý[ÛŠK
^ÚYŠXJJJ]›ÝÈ\œ›ÜŠJŽNJJNÝ˜\ˆHLKXÏRËÏU\ËSYNÜ™]\›ˆO[[	‰ŠLOO][œÝX›WÜÝšXÝ[ÙI‰ŠHL
KšY[YšY\”™Yš^OO]›ÚY	‰Š]šY[YšY\”™Yš^
K›Û•[˜Ø]YÚ\œ›ÜˆOO]›ÚY	‰ŠÏ]›Û•[˜Ø]YÚ\œ›ÜŠK›ÛØ]YÚ\œ›ÜˆOO]›ÚY	‰ŠÏ]›ÛØ]YÚ\œ›ÜŠK›Û”™XÛÝ™\˜X›Q\œ›ÜˆOO]›ÚY	‰Š]›Û”™XÛÝ™\˜X›Q\œ›ÜŠJKV]JKKLK[[‹‹[ËË\
KVÞO]˜Ý\œ™[JJK™]È	

__JJK]\Ê

K
OOžÙ[˜Ý[ÛˆŠ
^ÚYŠJ\[Ùˆ×Ô‘PPÕÑU•ÓÓ×ÑÓÐSÒÓÒ××Ï˜X\[Ùˆ×Ô‘PPÕÑU•ÓÓ×ÑÓÐSÒÓÒ××Ë˜ÚXÚÑÑHOX[˜Ý[Û˜
J]ž^××Ô‘PPÕÑU•ÓÓ×ÑÓÐSÒÓÒ××Ë˜ÚXÚÑÑJŠ_XØ]Ú
J^ØÛÛœÛÛK™\œ›ÜŠJ__[Š
K™^ÜÏXÎ]

_JJKÎOY
Ž]

KJKN]Y
N]

KJK][]

NÙ[˜Ý[ÛˆŽ]
J^Ý˜\ˆ‹XÚYŠ\[ÙˆOOXÝš[™Ø\[ÙˆOOX[X™\˜
\ŠÏYNÙ[ÙHYŠ\[ÙˆOOXØš™XÝ
ZYŠ\œ˜^Kš\Ð\œ˜^JJJ^Ý˜\ˆOYK›[™ÝÙ›ÜŠLÝNÝ
ÊÊYVÝI‰ŠYŽ]
VÝJJI‰Š‰‰ŠŠÏX
KŠÏ[Š_Y[ÙH›ÜŠˆ[ˆJYVÛ—I‰Š‰‰ŠŠÏX
KŠÏ[ŠNÜ™]\›ˆŸY[˜Ý[Ûˆ]

^Ù›ÜŠ˜\ˆKLXOX\™Ý[Y[Ë›[™ÝÛNÛŠÊÊJOX\™Ý[Y[ÖÛ—JI‰ŠYŽ]
JJI‰Š‰‰ŠŠÏX
KŠÏ]
NÜ™]\›ˆŸ]˜\ˆN]YOO\[ÙˆOOX›ÛÛX[˜Ø	Ù_X™OOOLØ™K]\]Î]JK
OO›OžÚYŠË˜\šX[ÏO[[
\™]\›ˆ]
KË˜Û\ÜËË˜Û\ÜÓ˜[YJNÛ]Ý˜\šX[Îœ‹Y˜][˜\šX[Îš_O]OSØš™XÝšÙ^\ÊŠK›X\
OOžÛ][Ë–ÙWKOZOË–ÙWNÚYŠOO[[
\™]\›ˆ[Û]Ï[N]

_N]
JNÜ™]\›ˆ–ÙWVÛ×_JKÏ[‰‰“Øš™XÝ™[šY\ÊŠKœ™YXÙJ
K
OOžÛ]Û‹—O]Ü™]\›ˆOO]›ÚY
VÛ—O\ŠK_KßJNÜ™]\›ˆ]
KKË˜ÛÛ\Ý[™˜\šX[ÏËœ™YXÙJ
K
OOžÛ]ØÛ\ÜÎ›‹Û\ÜÓ˜[YNœ‹‹‹˜_O]Ü™]\›ˆØš™XÝ™[šY\ÊJK™]™\žJOOžÛ]Ý—OYNÜ™]\›ˆ\œ˜^Kš\Ð\œ˜^JŠOÛ‹š[˜ÛY\ÊË‹‹šK‹‹›ßVÝJNžË‹‹šK‹‹›ßVÝOOO[ŸJOÖË‹‹™K‹—N™_K×JKË˜Û\ÜËË˜Û\ÜÓ˜[YJ_KÎ]JK
OOžÛ]P\œ˜^JK›[™Ý
Ý›[™Ý
NÙ›ÜŠ]LÝK›[™ÝÝ
ÊÊ[–ÝOYVÝNÙ›ÜŠ]LÜ›[™ÝÜŠÊÊ[–ÙK›[™Ý
Ü—O]Ü—NÜ™]\›ˆŸKŽ]JK
OOŠØÛ\ÜÑÜ›Ý\Y™K˜[Y]ÜŽJKN]JO[™]ÈX\[[ŠOOŠÛ™^\™K˜[Y]ÜœÎÛ\ÜÑÜ›Ý\Y›ŸJKÎOXXŽ]V×K]X\˜š]˜\žK‹˜Î]YOOžÛ]U]
JKØÛÛ™›XÝ[™ÐÛ\ÜÑÜ›Ý\Î›‹ÛÛ™›XÝ[™ÐÛ\ÜÑÜ›Ý\[ÙYšY\œÎœŸOYNÜ™]\›žÙÙ]Û\ÜÑÜ›Ý\Y™OOžÚYŠKœÝ\ÕÚ]
Ø
I‰™K™[™ÕÚ]
X
J\™]\›ˆÎ]
JNÛ]YKœÜ]
ÎJNÜ™]\›ˆÎ]
‹
Ê–ÌOOOX	‰›‹›[™ÝŒJK
_KÙ]ÛÛ™›XÝ[™ÐÛ\ÜÑÜ›Ý\YÎŠK
OOžÚYŠ
^Û]\–ÙWKO[–ÙWNÜ™]\›ˆÚO×Î]
K
Nš_Ž]\™]\›ˆ–ÙW_Ž]__KÎ]JKŠOOžÚYŠK›[™Ý]OOL
\™]\›ˆ‹˜Û\ÜÑÜ›Ý\YÛ]YVÝKO[‹›™^\™Ù]
ŠNÚYŠJ^Û]PÎ]
K
ÌKJNÚYŠŠ\™]\›ˆŸ[]O[‹˜[Y]ÜœÎÚYŠOOO[[
\™]\›ŽÛ]Ï]OOLÙKš›Ú[ŠÎJN™KœÛXÙJ
Kš›Ú[ŠÎJKÏXK›[™ÝÙ›ÜŠ]OLÙOÎÙJÊÊ^Û]XVÙWNÚYŠ˜[Y]ÜŠÊJ\™]\›ˆ˜Û\ÜÑÜ›Ý\Y_KÎ]YOO™KœÛXÙJKLJKš[™^ÙŠ˜
OOOKLOÝ›ÚYŠ

OOžÛ]YKœÛXÙJKLJK]š[™^ÙŠ˜
K]œÛXÙJŠNÜ™]\›ˆÞ]
ÜŽ›ÚYJJ
K]YOOžÛ]Ý[YNÛ\ÜÑÜ›Ý\Î›ŸOYNÜ™]\›ˆN]
‹
_KN]JK
OOžÛ]^N]

NÙ›ÜŠ]ˆ[ˆJ^Û]OYVÜ—NÑ]
K‹‹
_\™]\›ˆŸK]JK‹ŠOOžÛ]OYK›[™ÝÙ›ÜŠ]OLØONØJÊÊ^Û]OYVØWNÓÎ]
K‹Š__KÎ]JK‹ŠOOžÚYŠ\[ÙˆOOXÝš[™Ø
^ÚÎ]
KŠNÜ™]\›ŸZYŠ\[ÙˆOOX[˜Ý[Û˜
^ÐN]
K‹ŠNÜ™]\›ŸZŽ]
K‹Š_KÎ]JKŠOOžÛ]YOOOXÝ“N]
JNÜ‹˜Û\ÜÑÜ›Ý\Y[ŸKN]JK‹ŠOOžÚYŠŽ]
JJ^Ñ]
JŠK‹ŠNÜ™]\›Ÿ]˜[Y]ÜœÏOO[[	‰Š˜[Y]ÜœÏV×JK˜[Y]ÜœËœ\Ú
Ž]
‹JJ_KŽ]JK‹ŠOOžÛ]OSØš™XÝ™[šY\ÊJKOZK›[™ÝÙ›ÜŠ]OLÙONÙJÊÊ^Û]ØK×OZVÙWNÑ]
ËN]
JK‹Š__KN]JK
OOžÛ]YK]œÜ]
ÎJKO\‹›[™ÝÙ›ÜŠ]OLÙONÙJÊÊ^Û]\–ÙWKO[‹›™^\™Ù]

NÚ_
O^N]

K‹›™^\œÙ]
JJKZ_\™]\›ˆŸKŽ]YOO˜\Õ[YQÙ]\˜[ˆI‰™Kš\Õ[YQÙ]\OOHL]YOOžÚYŠOJ\™]\›žÙÙ]Š
OO›ÚYÙ]Š
OOžß_NÛ]LSØš™XÝ˜Ü™X]J[
KSØš™XÝ˜Ü™X]J[
KOJKJOOžÛ–ÚWOXK
ÊË™I‰ŠL[‹SØš™XÝ˜Ü™X]J[
J_NÜ™]\›žÙÙ]
J^Û][–ÙWNÚYŠOO]›ÚY
\™]\›ˆÚYŠ
\–ÙWJHOO]›ÚY
\™]\›ˆJK
KKÙ]
K
^ÙH[ˆÛ–ÙWO]šJK
___KŽ]XXN]X˜]V×KŽ]JK‹‹JOOŠÛ[ÙYšY\œÎ™K\Ò[\Ü[[ÙYšY\Ž˜\ÙPÛ\ÜÓ˜[YN›‹X^X™TÜÝš^[ÙYšY\”ÜÚ][ÛŽœ‹\Ñ^\›˜[š_JKŽ]YOOžÛ]Ü™Yš^^\š[Y[[\œÙPÛ\ÜÓ˜[YN›ŸOYKYOOžÛ]V×KLLOLKÏYK›[™ÝÙ›ÜŠ]ÏLÜÏÎÜÊÊÊ^Û]ÏYVÜ×NÚYŠOOL	‰œOOL
^ÚYŠÏOORN]
^Ýœ\Ú
KœÛXÙJKÊJKO\ÊÌNØÛÛ[Y_ZYŠÏOOXØ
^ØO\ÎØÛÛ[Y__[ÏOOXØÛŠÊÎ›ÏOOXXÛ‹KN›ÏOOX
ÜŠÊÎ›ÏOOX
X	‰œ‹K_[]Ï]›[™ÝOOLÙN™KœÛXÙJJK\ËOHLNÜË™[™ÕÚ]
Ž]
OÊ\ËœÛXÙJLJKOHL
NœËœÝ\ÕÚ]
Ž]
I‰Š\ËœÛXÙJJKOHL
NÛ]XI‰˜OšOØKZN›ÚYÜ™]\›ˆŽ]
K
_NÚYŠ
^Û]O]
ÒN]\ŽÜ]OœÝ\ÕÚ]
JOÛŠœÛXÙJK›[™Ý
JN”Ž]
]LK›ÚYL
_ZYŠŠ^Û]O\ŽÜ]O›ŠØÛ\ÜÓ˜[YN\œÙPÛ\ÜÓ˜[YN™_J_\™]\›ˆŸKŽ]YOOžÛ][™]ÈX\Ü™]\›ˆK›Ü™\”Ù[œÚ]]™S[ÙYšY\œË™›Ü‘XXÚ

KŠOOžÝœÙ]
KYMŠÛŠ_JKOOžÛ]V×KV×NÙ›ÜŠ]OLÚOK›[™ÝÚJÊÊ^Û]OYVÚWKÏXVÌOOOXØÏ]š\ÊJNÛßÏÊ‹›[™ÝŒ	‰Š‹œÛÜ

K‹œ\Ú
‹‹œŠKV×JK‹œ\Ú
JJNœ‹œ\Ú
J_\™]\›ˆ‹›[™ÝŒ	‰Š‹œÛÜ

K‹œ\Ú
‹‹œŠJKŸ_KŽ]YOOŠØØXÚN”]
K˜ØXÚTÚ^™JK\œÙPÛ\ÜÓ˜[YNžŽ]
JKÛÜ[ÙYšY\œÎŽ]
JKÜÝš^ÛÚÝ\Û\ÜÑÜ›Ý\YÎ’]
JK‹‹”Î]
J_JK]YOOžÛ]SØš™XÝ˜Ü™X]J[
KYKœÜÝš^ÛÚÝ\Û\ÜÑÜ›Ý\ÎÚYŠŠY›ÜŠ]OLÙO‹›[™ÝÙJÊÊ]Û–ÙWWOHLÜ™]\›ˆKN]K×ÊËËÎ]JK
OOžÛ]Ü\œÙPÛ\ÜÓ˜[YN›‹Ù]Û\ÜÑÜ›Ý\Yœ‹Ù]ÛÛ™›XÝ[™ÐÛ\ÜÑÜ›Ý\YÎšKÛÜ[ÙYšY\œÎ˜KÜÝš^ÛÚÝ\Û\ÜÑÜ›Ý\YÎ›ßO]ÏV×KYKš[J
KœÜ]
N]
KOXÙ›ÜŠ]O[›[™ÝLNÙOLËKYJ^Û][ÙWKÚ\Ñ^\›˜[™[ÙYšY\œÎ™‹\Ò[\Ü[[ÙYšY\Žœ˜\ÙPÛ\ÜÓ˜[YN›KX^X™TÜÝš^[ÙYšY\”ÜÚ][ÛŽšO[Š
NÚYŠ
^ÝO]
ÊK›[™ÝŒØ
ÝNJNØÛÛ[Y_[]ÏHHZÎÚYŠÊ^×Ï\ŠKœÝXœÝš[™Ê
JNÛ]OWÉ‰›Ö××OÜŠJN›ÚYÙI‰™HOOWÉ‰ŠÏYKÏHLJ_Y[ÙHÏ\ŠJNÚYŠWÊ^ÚYŠYÊ^ÝO]
ÊK›[™ÝŒØ
ÝNJNØÛÛ[Y_ZYŠÏ\ŠJKWÊ^ÝO]
ÊK›[™ÝŒØ
ÝNJNØÛÛ[Y_YÏHL_[]Y‹›[™ÝOOLØ™‹›[™ÝOOLOÙ–ÌN˜JŠKš›Ú[Š˜
KO\ÝŠÑŽ]‹^J×ÎÚYŠËš[™^ÙŠŠO‹LJXÛÛ[YNÜËœ\Ú
ŠNÛ]ZJËÊNÙ›ÜŠ]OLÙO›[™ÝÊÊÙJ^Û]^ÙWNÜËœ\Ú
JÝ
_]O]
ÊK›[™ÝŒØ
ÝNJ_\™]\›ˆ_KÎ]J‹‹™JOOžÛ]L‹‹OXÙ›ÜŠÝK›[™ÝÊJYVÝ
Ê×JI‰ŠRÎ]
ŠJI‰ŠI‰ŠJÏX
KJÏ\ŠNÜ™]\›ˆ_KÎ]YOOžÚYŠ\[ÙˆOOXÝš[™Ø
\™]\›ˆNÛ]XÙ›ÜŠ]LÜK›[™ÝÜŠÊÊYVÜ—I‰ŠRÎ]
VÜ—JJI‰Š‰‰ŠŠÏX
KŠÏ]
NÜ™]\›ˆŸKN]JK‹‹
OOžÛ]‹‹KKÏ[ÏOŠUŽ]
œ™YXÙJ
K
OO
JKJ
JJK[‹˜ØXÚK™Ù]O[‹˜ØXÚKœÙ]O\ËÊÊJKÏYOOžÛ]\ŠJNÚYŠ
\™]\›ˆÛ]OUÎ]
KŠNÜ™]\›ˆJKJK_NÜ™]\›ˆO[Ë
‹‹™JOO˜JÎ]
‹‹™JJ_KŽ]V×KNOYOOžÛ]]OÙW_Ž]Ü™]\›ˆš\Õ[YQÙ]\HL[YRÙ^OYKKN]K×—ÊÎŠÖ×ËWJŠNŠOÊŠÊWIÚK]K×—

ÎŠÖ×ËWJŠNŠOÊŠÊW
IÚKŽ]K×—
ÊÎ——
ÊO××
ÊÎ——
ÊOÉËN]K×Š
Ê—
ÊOÊOÊßÛ_Yß
IË	]K×
Ê	_Ù[_ÜÙOÝŠÚÚX—_Z[ŸX^
_ß[ŸÛ_[_Ø\Ú^ÛÜJß_ŸZ[ŸX^
J_ŠØ[ßZ[ŸX^Û[\
W
Š×
_Œ	ËY[K×Š™Ø˜OßÛOßØŸ
ÚÊOÊXŸÚ
_ÛÛÜ‹[Z^ÛÛÜŸYÚY\šÊW
Š×
IË[K×Š[œÙ]ÊOËOÊ

ÊO×Ê
ÊVØK^—Jß
WËOÊ

ÊO×Ê
ÊVØK^—Jß
KË™[K×Š\›[XYÙ_[XYÙK\Ù]Ü›ÜÜËY˜Y_[[Y[
™\X][™ËJOÊ[™X\Ÿ˜YX[ÛÛšXÊKYÜ˜YY[
W
Š×
IËŽOYOO–Ž]\Ý
JKNOYOOˆHYI‰ˆS[X™\‹š\Ó˜SŠ[X™\ŠJJKŽOYOOˆHYI‰“[X™\‹š\Ò[YÙ\Š[X™\ŠJJK™[YOO™K™[™ÕÚ]
	X
I‰“NJKœÛXÙJLJJKOYOO”N]\Ý
JKY[J
OOˆLY[YOO‰]\Ý
JI‰ˆYY[‹\Ý
JKÙ[J
OOˆLKÙ[YOO[‹\Ý
JKÙ[YOO›™[‹\Ý
JK[YOOˆQŽJJI‰ˆTŽJJKY[YOO™KœÝ\ÕÚ]
ÛÛZ[™\˜
I‰ŠVÌLOOOXØ	‰™VÌLWHOO]›ÚYVÌLWOOOXØ	‰™VÌM—HOO]›ÚY	‰™KœÝ\ÕÚ]
\Ú^™KØL
_VÌLWOOOX˜	‰™VÌNHOO]›ÚY	‰™KœÝ\ÕÚ]
[›Ü›X[ØL
JK[YOO•ŽJKÙ[‹Ù[ŠKŽOYOO–N]\Ý
JKNOYOO•ŽJK[‹Y[ŠK™[YOO•ŽJKY[‹NJK[YOO•ŽJKÙ[‹Y[ŠKY[YOO•ŽJK[‹Ù[ŠK[YOO•ŽJKÙ[‹Ù[ŠKÙ[YOO•ŽJKÙ[‹Ù[ŠKOYOO•ŽJKÙ[‹Ù[ŠKŽOYOO–]\Ý
JKŽOYOO’JK[ŠKÙ[YOO’JK[ŠK™[YOO’JKÙ[ŠKY[YOO’JKÙ[ŠK™[YOO’JKÙ[ŠKŽOYOO’JKÙ[‹L
K[YOO’JKÙ[‹L
KŽOJKŠOOžÛ]VN]™^XÊJNÜ™]\›ˆÜ–ÌWOÝ
–ÌWJN›Š–Ì—JNˆL_KOJKHLJOOžÛ]V]™^XÊJNÜ™]\›ˆÜ–ÌWOÝ
–ÌWJN›ŽˆL_KÙ[YOO™OOOXÜÚ][Û˜OOOX\˜Ù[YÙXÙ[YOO™OOOX[XYÙXOOOX\›Ù[YOO™OOOX[™ÝOOOXÚ^™XOOOX™Ë\Ú^™X[YOO™OOOX[™ÝY[YOO™OOOX[X™\˜[YOO™OOOX˜[Z[K[˜[YXÙ[YOO™OOOX[X™\˜OOOXÙZYÚÙ[YOO™OOOXÚYÝØY[\N]


OOžÛ]OPNJÛÛÜ˜
KPNJ›Û
KPNJ^
KPNJ›Û]ÙZYÚ
KOPNJ˜XÚÚ[™Ø
KOPNJXY[™Ø
KÏPNJœ™XZÜÚ[
KÏPNJÛÛZ[™\˜
KPNJÜXÚ[™Ø
KOPNJ˜Y]\Ø
KPNJÚYÝØ
KPNJ[œÙ]\ÚYÝØ
KPNJ^\ÚYÝØ
KOPNJ›Ü\ÚYÝØ
KPNJ›\˜
KÏPNJ\œÜXÝ]™X
KÏPNJ\ÜXÝ
KPNJX\ÙX
KOPNJ[š[X]X
KJ
OO–Ø]]Ø]›ÚY[]›ÚY\YÙXYÙXYšYÚÛÛ[[˜KJ
OO–ØÙ[\˜Ü›ÝÛXYšYÚÜ[YY]ÜÜ\šYÚšYÚ]Ü›ÝÛK\šYÚšYÚX›ÝÛX›ÝÛK[YYX›ÝÛXKÏJ
OO–Ë‹‹ž

KŽKŽWKÏJ
OO–Ø]]ØY[˜Û\š\ÚX›XØÜ›ÛKÏJ
OO–Ø]]ØÛÛZ[˜›Û™XKJ
OO–ÔŽKŽKKOJ
OO–ÚŽK[]]Ø‹‹•

WKJ
OO–ÓŽK›Û™XÝX™ÜšYŽKŽWKÏJ
OO–Ø]]ØÜÜ[Ž–Ø[ŽKŽKŽW_KŽKŽKŽWKÏJ
OO–ÓŽK]]ØŽKŽWKOJ
OO–Ø]]ØZ[˜X^œ˜ŽKŽWKJ
OO–ØÝ\[™Ù[\˜™]ÙY[˜\›Ý[™]™[›XÝ™]Ú˜\Ù[[™XÙ[\‹\ØY™X[™\ØY™XKOJ
OO–ØÝ\[™Ù[\˜Ý™]ÚÙ[\‹\ØY™X[™\ØY™XKJ
OO–Ø]]Ø‹‹•

WKJ
OO–ÚŽK]]Ø[ØšØšÝØÝšZ[˜X^š]‹‹•

WKJ
OO–ÜËŽKØÜ™Y[˜[ØØÝØZ[˜X^š]‹‹•

WKOJ
OO–ÚŽKØÜ™Y[˜[ššÝšZ[˜X^š]‹‹•

WKJ
OO–ÙKŽKŽWKJ
OO–Ë‹‹ž

K™[‹[‹ÜÜÚ][ÛŽ–ÔŽKŽW_WKYOJ
OO–Ø›Ë\™\X]Ü™\X]–ØXÜXÙX›Ý[™_WKOJ
OO–Ø]]ØÛÝ™\˜ÛÛZ[˜Y[‹[‹ÜÚ^™N–ÔŽKŽW_WK™OJ
OO–Ü™[‹ŽKNWK™OJ
OO–Ø›Û™X[KŽKŽWKYOJ
OO–ØNKŽKNWKYOJ
OO–ØÛÛY\ÚYÝYÝX›XKJ
OO–Ø›Ü›X[][\XØÜ™Y[˜Ý™\›^X\šÙ[˜YÚ[˜ÛÛÜ‹YÙÙXÛÛÜ‹X\›˜\™[YÚÛÙ[YÚY™™\™[˜ÙX^Û\Ú[Û˜YXØ]\˜][Û˜ÛÛÜ˜[Z[›ÜÚ]XKÙOJ
OO–ÓNK™[‹™[‹[—KÙOJ
OO–Ø›Û™XŽKŽWKÙOJ
OO–Ø›Û™XNKŽKŽWKOJ
OO–Ø›Û™XNKŽKŽWKYOJ
OO–ÓNKŽKŽWKOJ
OO–ÚŽK[‹‹•

WNÜ™]\›žØØXÚTÚ^™NL[YNžØ[š[X]N–ØÜ[˜[™Ø[ÙX›Ý[˜ÙXK\ÜXÝ–ØšY[ØK›\Ž–ÔWKœ™XZÜÚ[–ÔWKÛÛÜŽ–ÚY[—KÛÛZ[™\Ž–ÔWK™›Ü\ÚYÝÈŽ–ÔWKX\ÙN–Ø[˜Ý][‹[Ý]K›Û–Û[—K™›Û]ÙZYÚŽ–Ø[˜^˜[YÚYÚ›Ü›X[YY][XÙ[ZX›Û›Û^˜X›Û›XÚØKš[œÙ]\ÚYÝÈŽ–ÔWKXY[™Î–Ø›Û™XYÚÛYØ›Ü›X[™[^YÛÜÙXK\œÜXÝ]™N–Ø˜[X]XØ™X\˜›Ü›X[ZY˜[™ÙX\Ý[›Û™XK˜Y]\Î–ÔWKÚYÝÎ–ÔWKÜXÚ[™Î–ØNWK^–ÔWK^\ÚYÝÈŽ–ÔWK˜XÚÚ[™Î–ØYÚ\˜YÚ›Ü›X[ÚYXÚY\˜ÚY\Ý_KÛ\ÜÑÜ›Ý\ÎžØ\ÜXÝ–ÞØ\ÜXÝ–Ø]]ØÜ]X\™XŽKŽKŽK×_WKÛÛZ[™\Ž–ØÛÛZ[™\˜K˜ÛÛZ[™\‹]\HŽ–ÞÈÛÛZ[™\ˆŽ–Ø›Ü›X[Ú^™XŽKŽW_WK˜ÛÛZ[™\‹[˜[YYŽ–ÝY[—KÛÛ[[œÎ–ÞØÛÛ[[œÎ–ÓNK]]ØŽKŽK×_WK˜œ™XZËXY\ˆŽ–ÞÈ˜œ™XZËXY\ˆŽ˜Š
_WK˜œ™XZËX™Y›Ü™HŽ–ÞÈ˜œ™XZËX™Y›Ü™HŽ˜Š
_WK˜œ™XZËZ[œÚYHŽ–ÞÈ˜œ™XZËZ[œÚYHŽ–Ø]]Ø]›ÚY]›ÚY\YÙX]›ÚYXÛÛ[[˜_WK˜›ÞYXÛÜ˜][ÛˆŽ–ÞÈ˜›ÞYXÛÜ˜][ÛˆŽ–ØÛXÙXÛÛ™X_WK›Þ–ÞØ›Þ–Ø›Ü™\˜ÛÛ[_WK\Ü^N–Ø›ØÚØ[›[™KX›ØÚØ[›[™X›^[›[™KY›^X›X[›[™K]X›XX›KXØ\[Û˜X›KXÙ[X›KXÛÛ[[˜X›KXÛÛ[[‹YÜ›Ý\X›KY›ÛÝ\‹YÜ›Ý\X›KZXY\‹YÜ›Ý\X›K\›ÝËYÜ›Ý\X›K\›ÝØ›ÝË\›ÛÝÜšY[›[™KYÜšYÛÛ[Ø\ÝZ][XY[˜KÜŽ–ØÜ‹[Û›X›Ý\Ü‹[Û›XK›Ø]–ÞÙ›Ø]–ØšYÚY›Û™XÝ\[™_WKÛX\Ž–ÞØÛX\Ž–ØYšYÚ›Ý›Û™XÝ\[™_WK\ÛÛ][ÛŽ–Ø\ÛÛ]X\ÛÛ][Û‹X]]ØK›Øš™XÝYš]Ž–ÞÛØš™XÝ–ØÛÛZ[˜ÛÝ™\˜š[›Û™XØØ[KYÝÛ˜_WK›Øš™XÝ\ÜÚ][ÛˆŽ–ÞÛØš™XÝ”Ê
_WKÝ™\™›ÝÎ–ÞÛÝ™\™›ÝÎÊ
_WK›Ý™\™›ÝË^Ž–ÞÈ›Ý™\™›ÝË^ŽÊ
_WK›Ý™\™›ÝË^HŽ–ÞÈ›Ý™\™›ÝË^HŽÊ
_WKÝ™\œØÜ›Û–ÞÛÝ™\œØÜ›ÛÊ
_WK›Ý™\œØÜ›Û^Ž–ÞÈ›Ý™\œØÜ›Û^ŽÊ
_WK›Ý™\œØÜ›Û^HŽ–ÞÈ›Ý™\œØÜ›Û^HŽÊ
_WKÜÚ][ÛŽ–ØÝ]XØš^YXœÛÛ]X™[]]™XÝXÚÞXK[œÙ]–ÞÚ[œÙ]‘J
_WKš[œÙ]^Ž–ÞÈš[œÙ]^Ž‘J
_WKš[œÙ]^HŽ–ÞÈš[œÙ]^HŽ‘J
_WKÝ\–ÞÈš[œÙ]\ÈŽ‘J
KÝ\‘J
_WK[™–ÞÈš[œÙ]YHŽ‘J
K[™‘J
_WKš[œÙ]XœÈŽ–ÞÈš[œÙ]XœÈŽ‘J
_WKš[œÙ]X™HŽ–ÞÈš[œÙ]X™HŽ‘J
_WKÜ–ÞÝÜ‘J
_WKšYÚ–ÞÜšYÚ‘J
_WK›ÝÛN–ÞØ›ÝÛN‘J
_WKY–ÞÛY‘J
_WKš\ÚXš[]N–Øš\ÚX›X[š\ÚX›XÛÛ\ÙXKŽ–ÞÞŽ–ÓŽK]]ØŽKŽW_WK˜\Ú\Î–ÞØ˜\Ú\Î–ÚŽK[]]ØË‹‹•

W_WK™›^Y\™XÝ[ÛˆŽ–ÞÙ›^–Ø›ÝØ›ÝË\™]™\œÙXÛÛÛÛ\™]™\œÙX_WK™›^]Ü˜\Ž–ÞÙ›^–Ø›ÝÜ˜\Ü˜\Ü˜\\™]™\œÙX_WK›^–ÞÙ›^–ÓNKŽK]]Ø[š]X[›Û™XŽW_WKÜ›ÝÎ–ÞÙÜ›ÝÎ–ØNKŽKŽW_WKÚš[šÎ–ÞÜÚš[šÎ–ØNKŽKŽW_WKÜ™\Ž–ÞÛÜ™\Ž–ÓŽKš\œÝ\Ý›Û™XŽKŽW_WK™ÜšYXÛÛÈŽ–ÞÈ™ÜšYXÛÛÈŽ‘

_WK˜ÛÛ\Ý\Y[™Ž–ÞØÛÛ“Ê
_WK˜ÛÛ\Ý\Ž–ÞÈ˜ÛÛ\Ý\ŽšÊ
_WK˜ÛÛY[™Ž–ÞÈ˜ÛÛY[™ŽšÊ
_WK™ÜšY\›ÝÜÈŽ–ÞÈ™ÜšY\›ÝÜÈŽ‘

_WKœ›ÝË\Ý\Y[™Ž–ÞÜ›ÝÎ“Ê
_WKœ›ÝË\Ý\Ž–ÞÈœ›ÝË\Ý\ŽšÊ
_WKœ›ÝËY[™Ž–ÞÈœ›ÝËY[™ŽšÊ
_WK™ÜšYY›ÝÈŽ–ÞÈ™ÜšYY›ÝÈŽ–Ø›ÝØÛÛ[œÙX›ÝËY[œÙXÛÛY[œÙX_WK˜]]ËXÛÛÈŽ–ÞÈ˜]]ËXÛÛÈŽJ
_WK˜]]Ë\›ÝÜÈŽ–ÞÈ˜]]Ë\›ÝÜÈŽJ
_WKØ\–ÞÙØ\•

_WK™Ø\^Ž–ÞÈ™Ø\^Ž•

_WK™Ø\^HŽ–ÞÈ™Ø\^HŽ•

_WKš\ÝYžKXÛÛ[Ž–ÞÚ\ÝYžN–Ë‹‹šŠ
K›Ü›X[_WKš\ÝYžKZ][\ÈŽ–ÞÈš\ÝYžKZ][\ÈŽ–Ë‹‹“J
K›Ü›X[_WKš\ÝYžK\Ù[ˆŽ–ÞÈš\ÝYžK\Ù[ˆŽ–Ø]]Ø‹‹“J
W_WK˜[YÛ‹XÛÛ[Ž–ÞØÛÛ[–Ø›Ü›X[‹‹šŠ
W_WK˜[YÛ‹Z][\ÈŽ–ÞÚ][\Î–Ë‹‹“J
KØ˜\Ù[[™N–Ø\Ý_W_WK˜[YÛ‹\Ù[ˆŽ–ÞÜÙ[Ž–Ø]]Ø‹‹“J
KØ˜\Ù[[™N–Ø\Ý_W_WKœXÙKXÛÛ[Ž–ÞÈœXÙKXÛÛ[ŽšŠ
_WKœXÙKZ][\ÈŽ–ÞÈœXÙKZ][\ÈŽ–Ë‹‹“J
K˜\Ù[[™X_WKœXÙK\Ù[ˆŽ–ÞÈœXÙK\Ù[ˆŽ–Ø]]Ø‹‹“J
W_WK–ÞÜ•

_WK–ÞÜ•

_WKN–ÞÜN•

_WKÎ–ÞÜÎ•

_WKN–ÞÜN•

_WKœÎ–ÞÜœÎ•

_WK™N–ÞÜ™N•

_WK–ÞÜ•

_WKŽ–ÞÜŽ•

_WKŽ–ÞÜŽ•

_WK–ÞÜ•

_WKN–ÞÛN“Š
_WK^–ÞÛ^“Š
_WK^N–ÞÛ^N“Š
_WK\Î–ÞÛ\Î“Š
_WKYN–ÞÛYN“Š
_WKXœÎ–ÞÛXœÎ“Š
_WKX™N–ÞÛX™N“Š
_WK]–ÞÛ]“Š
_WK\Ž–ÞÛ\Ž“Š
_WKXŽ–ÞÛXŽ“Š
_WK[–ÞÛ[“Š
_WKœÜXÙK^Ž–ÞÈœÜXÙK^Ž•

_WKœÜXÙK^\™]™\œÙHŽ–ØÜXÙK^\™]™\œÙXKœÜXÙK^HŽ–ÞÈœÜXÙK^HŽ•

_WKœÜXÙK^K\™]™\œÙHŽ–ØÜXÙK^K\™]™\œÙXKÚ^™N–ÞÜÚ^™N”

_WKš[›[™K\Ú^™HŽ–ÞÚ[›[™N–Ø]]Ø‹‹‘Š
W_WK›Z[‹Z[›[™K\Ú^™HŽ–ÞÈ›Z[‹Z[›[™HŽ–Ø]]Ø‹‹‘Š
W_WK›X^Z[›[™K\Ú^™HŽ–ÞÈ›X^Z[›[™HŽ–Ø›Û™X‹‹‘Š
W_WK˜›ØÚË\Ú^™HŽ–ÞØ›ØÚÎ–Ø]]Ø‹‹’J
W_WK›Z[‹X›ØÚË\Ú^™HŽ–ÞÈ›Z[‹X›ØÚÈŽ–Ø]]Ø‹‹’J
W_WK›X^X›ØÚË\Ú^™HŽ–ÞÈ›X^X›ØÚÈŽ–Ø›Û™X‹‹’J
W_WKÎ–ÞÝÎ–ÜËØÜ™Y[˜‹‹”

W_WK›Z[‹]ÈŽ–ÞÈ›Z[‹]ÈŽ–ÜËØÜ™Y[˜›Û™X‹‹”

W_WK›X^]ÈŽ–ÞÈ›X^]ÈŽ–ÜËØÜ™Y[˜›Û™X›ÜÙXÜØÜ™Y[Ž–Û×_K‹‹”

W_WK–ÞÚ–ØØÜ™Y[˜‹‹”

W_WK›Z[‹ZŽ–ÞÈ›Z[‹ZŽ–ØØÜ™Y[˜›Û™X‹‹”

W_WK›X^ZŽ–ÞÈ›X^ZŽ–ØØÜ™Y[˜›Û™X‹‹”

W_WK™›Û\Ú^™HŽ–ÞÝ^–Ø˜\ÙX‹ŽKNW_WK™›Û\Û[ÛÝ[™ÈŽ–Ø[X[X\ÙYÝXœ^[X[X[X\ÙYK™›Û\Ý[HŽ–Ø][XØ›ÝZ][XØK™›Û]ÙZYÚŽ–ÞÙ›Û–Ü‹[‹[—_WK™›Û\Ý™]ÚŽ–ÞÈ™›Û\Ý™]ÚŽ–Ø[˜KXÛÛ™[œÙY^˜KXÛÛ™[œÙYÛÛ™[œÙYÙ[ZKXÛÛ™[œÙY›Ü›X[Ù[ZKY^[™Y^[™Y^˜KY^[™Y[˜KY^[™Y™[‹ŽW_WK™›ÛY˜[Z[HŽ–ÞÙ›Û–×Ù[‹Y[‹_WK™›ÛY™X]\™\ÈŽ–ÞÈ™›ÛY™X]\™\ÈŽ–ÑŽW_WK™›‹[›Ü›X[Ž–Ø›Ü›X[[[\ØK™›‹[Ü™[˜[Ž–ØÜ™[˜[K™›‹\Û\ÚY^™\›ÈŽ–ØÛ\ÚY^™\›ØK™›‹YšYÝ\™HŽ–Ø[š[™Ë[[\ØÛÝ[K[[\ØK™›‹\ÜXÚ[™ÈŽ–Ø›ÜÜ[Û˜[[[\ØX[\‹[[\ØK™›‹Yœ˜XÝ[ÛˆŽ–ØXYÛÛ˜[Yœ˜XÝ[ÛœØÝXÚÙYYœ˜XÝ[ÛœØK˜XÚÚ[™Î–ÞÝ˜XÚÚ[™Î–ÚKŽKŽW_WK›[™KXÛ[\Ž–ÞÈ›[™KXÛ[\Ž–ÓNK›Û™XŽK™[—_WKXY[™Î–ÞÛXY[™Î–Ø›Û™XK‹‹•

W_WK›\ÝZ[XYÙHŽ–ÞÈ›\ÝZ[XYÙHŽ–Ø›Û™XŽKŽW_WK›\Ý\Ý[K\ÜÚ][ÛˆŽ–ÞÛ\Ý–Ø[œÚYXÝ]ÚYX_WK›\Ý\Ý[K]\HŽ–ÞÛ\Ý–Ø\ØØXÚ[X[›Û™XŽKŽW_WK^X[YÛ›Y[Ž–ÞÝ^–ØYÙ[\˜šYÚ\ÝYžXÝ\[™_WKœXÙZÛ\‹XÛÛÜˆŽ–ÞÜXÙZÛ\Ž“

_WK^XÛÛÜˆŽ–ÞÝ^“

_WK^YXÛÜ˜][ÛˆŽ–Ø[™\›[™XÝ™\›[™X[™K]›ÝYÚ›Ë][™\›[™XK^YXÛÜ˜][Û‹\Ý[HŽ–ÞÙXÛÜ˜][ÛŽ–Ë‹‹˜YJ
KØ]žX_WK^YXÛÜ˜][Û‹]XÚÛ™\ÜÈŽ–ÞÙXÛÜ˜][ÛŽ–ÓNKœ›ÛKY›Û]]ØŽKNW_WK^YXÛÜ˜][Û‹XÛÛÜˆŽ–ÞÙXÛÜ˜][ÛŽ“

_WK[™\›[™K[Ù™œÙ]Ž–ÞÈ[™\›[™K[Ù™œÙ]Ž–ÓNK]]ØŽKŽW_WK^]˜[œÙ›Ü›HŽ–Ø\\˜Ø\ÙXÝÙ\˜Ø\ÙXØ\][^™X›Ü›X[XØ\ÙXK^[Ý™\™›ÝÈŽ–Ø[˜Ø]X^Y[\Ú\Ø^XÛ\K^]Ü˜\Ž–ÞÝ^–ØÜ˜\›ÝÜ˜\˜[[˜ÙX™]X_WK[™[–ÞÚ[™[•

_WKX‹\Ú^™HŽ–ÞÝXŽ–ÓŽKŽKŽW_WK™\XØ[X[YÛˆŽ–ÞØ[YÛŽ–Ø˜\Ù[[™XÜZYX›ÝÛX^]Ü^X›ÝÛXÝX˜Ý\\˜ŽKŽW_WKÚ]\ÜXÙN–ÞÝÚ]\ÜXÙN–Ø›Ü›X[›ÝÜ˜\™X™K[[™X™K]Ü˜\œ™XZË\ÜXÙ\Ø_WKœ™XZÎ–ÞØœ™XZÎ–Ø›Ü›X[ÛÜ™Ø[ÙY\_WKÜ˜\–ÞÝÜ˜\–Øœ™XZË]ÛÜ™[ž]Ú\™X›Ü›X[_WK\[œÎ–ÞÚ\[œÎ–Ø›Û™XX[X[]]Ø_WKÛÛ[–ÞØÛÛ[–Ø›Û™XŽKŽW_WK˜™ËX]XÚY[Ž–ÞØ™Î–Øš^YØØ[ØÜ›Û_WK˜™ËXÛ\Ž–ÞÈ˜™ËXÛ\Ž–Ø›Ü™\˜Y[™ØÛÛ[^_WK˜™Ë[ÜšYÚ[ˆŽ–ÞÈ˜™Ë[ÜšYÚ[ˆŽ–Ø›Ü™\˜Y[™ØÛÛ[_WK˜™Ë\ÜÚ][ÛˆŽ–ÞØ™Î”Š
_WK˜™Ë\™\X]Ž–ÞØ™Î™YJ
_WK˜™Ë\Ú^™HŽ–ÞØ™ÎJ
_WK˜™ËZ[XYÙHŽ–ÞØ™Î–Ø›Û™XÛ[™X\Ž–ÞÝÎ–Ø˜˜œ˜˜›_KŽKŽKŽWK˜YX[–ØŽKŽWKÛÛšXÎ–ØŽKŽKŽW_K™[‹Ù[—_WK˜™ËXÛÛÜˆŽ–ÞØ™Î“

_WK™Ü˜YY[Yœ›ÛK\ÜÈŽ–ÞÙœ›ÛN›™J
_WK™Ü˜YY[]šXK\ÜÈŽ–ÞÝšXN›™J
_WK™Ü˜YY[]Ë\ÜÈŽ–ÞÝÎ›™J
_WK™Ü˜YY[Yœ›ÛHŽ–ÞÙœ›ÛN“

_WK™Ü˜YY[]šXHŽ–ÞÝšXN“

_WK™Ü˜YY[]ÈŽ–ÞÝÎ“

_WK›Ý[™Y–ÞÜ›Ý[™Yœ™J
_WKœ›Ý[™Y\ÈŽ–ÞÈœ›Ý[™Y\ÈŽœ™J
_WKœ›Ý[™YYHŽ–ÞÈœ›Ý[™YYHŽœ™J
_WKœ›Ý[™Y]Ž–ÞÈœ›Ý[™Y]Žœ™J
_WKœ›Ý[™Y\ˆŽ–ÞÈœ›Ý[™Y\ˆŽœ™J
_WKœ›Ý[™YXˆŽ–ÞÈœ›Ý[™YXˆŽœ™J
_WKœ›Ý[™Y[Ž–ÞÈœ›Ý[™Y[Žœ™J
_WKœ›Ý[™Y\ÜÈŽ–ÞÈœ›Ý[™Y\ÜÈŽœ™J
_WKœ›Ý[™Y\ÙHŽ–ÞÈœ›Ý[™Y\ÙHŽœ™J
_WKœ›Ý[™YYYHŽ–ÞÈœ›Ý[™YYYHŽœ™J
_WKœ›Ý[™YY\ÈŽ–ÞÈœ›Ý[™YY\ÈŽœ™J
_WKœ›Ý[™Y]Ž–ÞÈœ›Ý[™Y]Žœ™J
_WKœ›Ý[™Y]ˆŽ–ÞÈœ›Ý[™Y]ˆŽœ™J
_WKœ›Ý[™YXœˆŽ–ÞÈœ›Ý[™YXœˆŽœ™J
_WKœ›Ý[™YX›Ž–ÞÈœ›Ý[™YX›Žœ™J
_WK˜›Ü™\‹]ÈŽ–ÞØ›Ü™\ŽšYJ
_WK˜›Ü™\‹]Ë^Ž–ÞÈ˜›Ü™\‹^ŽšYJ
_WK˜›Ü™\‹]Ë^HŽ–ÞÈ˜›Ü™\‹^HŽšYJ
_WK˜›Ü™\‹]Ë\ÈŽ–ÞÈ˜›Ü™\‹\ÈŽšYJ
_WK˜›Ü™\‹]ËYHŽ–ÞÈ˜›Ü™\‹YHŽšYJ
_WK˜›Ü™\‹]ËXœÈŽ–ÞÈ˜›Ü™\‹XœÈŽšYJ
_WK˜›Ü™\‹]ËX™HŽ–ÞÈ˜›Ü™\‹X™HŽšYJ
_WK˜›Ü™\‹]Ë]Ž–ÞÈ˜›Ü™\‹]ŽšYJ
_WK˜›Ü™\‹]Ë\ˆŽ–ÞÈ˜›Ü™\‹\ˆŽšYJ
_WK˜›Ü™\‹]ËXˆŽ–ÞÈ˜›Ü™\‹XˆŽšYJ
_WK˜›Ü™\‹]Ë[Ž–ÞÈ˜›Ü™\‹[ŽšYJ
_WK™]šYK^Ž–ÞÈ™]šYK^ŽšYJ
_WK™]šYK^\™]™\œÙHŽ–Ø]šYK^\™]™\œÙXK™]šYK^HŽ–ÞÈ™]šYK^HŽšYJ
_WK™]šYK^K\™]™\œÙHŽ–Ø]šYK^K\™]™\œÙXK˜›Ü™\‹\Ý[HŽ–ÞØ›Ü™\Ž–Ë‹‹˜YJ
KY[˜›Û™X_WK™]šYK\Ý[HŽ–ÞÙ]šYN–Ë‹‹˜YJ
KY[˜›Û™X_WK˜›Ü™\‹XÛÛÜˆŽ–ÞØ›Ü™\Ž“

_WK˜›Ü™\‹XÛÛÜ‹^Ž–ÞÈ˜›Ü™\‹^Ž“

_WK˜›Ü™\‹XÛÛÜ‹^HŽ–ÞÈ˜›Ü™\‹^HŽ“

_WK˜›Ü™\‹XÛÛÜ‹\ÈŽ–ÞÈ˜›Ü™\‹\ÈŽ“

_WK˜›Ü™\‹XÛÛÜ‹YHŽ–ÞÈ˜›Ü™\‹YHŽ“

_WK˜›Ü™\‹XÛÛÜ‹XœÈŽ–ÞÈ˜›Ü™\‹XœÈŽ“

_WK˜›Ü™\‹XÛÛÜ‹X™HŽ–ÞÈ˜›Ü™\‹X™HŽ“

_WK˜›Ü™\‹XÛÛÜ‹]Ž–ÞÈ˜›Ü™\‹]Ž“

_WK˜›Ü™\‹XÛÛÜ‹\ˆŽ–ÞÈ˜›Ü™\‹\ˆŽ“

_WK˜›Ü™\‹XÛÛÜ‹XˆŽ–ÞÈ˜›Ü™\‹XˆŽ“

_WK˜›Ü™\‹XÛÛÜ‹[Ž–ÞÈ˜›Ü™\‹[Ž“

_WK™]šYKXÛÛÜˆŽ–ÞÙ]šYN“

_WK›Ý][™K\Ý[HŽ–ÞÛÝ][™N–Ë‹‹˜YJ
K›Û™XY[˜_WK›Ý][™K[Ù™œÙ]Ž–ÞÈ›Ý][™K[Ù™œÙ]Ž–ÓNKŽKŽW_WK›Ý][™K]ÈŽ–ÞÛÝ][™N–ØNKŽKNW_WK›Ý][™KXÛÛÜˆŽ–ÞÛÝ][™N“

_WKÚYÝÎ–ÞÜÚYÝÎ–Ø[›™\˜›Û™XŽKW_WKœÚYÝËXÛÛÜˆŽ–ÞÜÚYÝÎ“

_WKš[œÙ]\ÚYÝÈŽ–ÞÈš[œÙ]\ÚYÝÈŽ–Ø›Û™X‹ŽKW_WKš[œÙ]\ÚYÝËXÛÛÜˆŽ–ÞÈš[œÙ]\ÚYÝÈŽ“

_WKœš[™Ë]ÈŽ–ÞÜš[™ÎšYJ
_WKœš[™Ë]ËZ[œÙ]Ž–Øš[™ËZ[œÙ]Kœš[™ËXÛÛÜˆŽ–ÞÜš[™Î“

_WKœš[™Ë[Ù™œÙ]]ÈŽ–ÞÈœš[™Ë[Ù™œÙ]Ž–ÓNKNW_WKœš[™Ë[Ù™œÙ]XÛÛÜˆŽ–ÞÈœš[™Ë[Ù™œÙ]Ž“

_WKš[œÙ]\š[™Ë]ÈŽ–ÞÈš[œÙ]\š[™ÈŽšYJ
_WKš[œÙ]\š[™ËXÛÛÜˆŽ–ÞÈš[œÙ]\š[™ÈŽ“

_WK^\ÚYÝÈŽ–ÞÈ^\ÚYÝÈŽ–Ø›Û™XŽKW_WK^\ÚYÝËXÛÛÜˆŽ–ÞÈ^\ÚYÝÈŽ“

_WKÜXÚ]N–ÞÛÜXÚ]N–ÓNKŽKŽW_WK›Z^X›[™Ž–ÞÈ›Z^X›[™Ž–Ë‹‹žŠ
K\ËY\šÙ\˜\Ë[YÚ\˜_WK˜™ËX›[™Ž–ÞÈ˜™ËX›[™ŽžŠ
_WK›X\ÚËXÛ\Ž–ÞÈ›X\ÚËXÛ\Ž–Ø›Ü™\˜Y[™ØÛÛ[š[Ý›ÚÙXšY]Ø_KX\ÚË[›ËXÛ\K›X\ÚËXÛÛ\ÜÚ]HŽ–ÞÛX\ÚÎ–ØYÝX˜XÝ[\œÙXÝ^ÛYX_WK›X\ÚËZ[XYÙK[[™X\‹\ÜÈŽ–ÞÈ›X\ÚË[[™X\ˆŽ–ÓNW_WK›X\ÚËZ[XYÙK[[™X\‹Yœ›ÛK\ÜÈŽ–ÞÈ›X\ÚË[[™X\‹Yœ›ÛHŽ›ÙJ
_WK›X\ÚËZ[XYÙK[[™X\‹]Ë\ÜÈŽ–ÞÈ›X\ÚË[[™X\‹]ÈŽ›ÙJ
_WK›X\ÚËZ[XYÙK[[™X\‹Yœ›ÛKXÛÛÜˆŽ–ÞÈ›X\ÚË[[™X\‹Yœ›ÛHŽ“

_WK›X\ÚËZ[XYÙK[[™X\‹]ËXÛÛÜˆŽ–ÞÈ›X\ÚË[[™X\‹]ÈŽ“

_WK›X\ÚËZ[XYÙK]Yœ›ÛK\ÜÈŽ–ÞÈ›X\ÚË]Yœ›ÛHŽ›ÙJ
_WK›X\ÚËZ[XYÙK]]Ë\ÜÈŽ–ÞÈ›X\ÚË]]ÈŽ›ÙJ
_WK›X\ÚËZ[XYÙK]Yœ›ÛKXÛÛÜˆŽ–ÞÈ›X\ÚË]Yœ›ÛHŽ“

_WK›X\ÚËZ[XYÙK]]ËXÛÛÜˆŽ–ÞÈ›X\ÚË]]ÈŽ“

_WK›X\ÚËZ[XYÙK\‹Yœ›ÛK\ÜÈŽ–ÞÈ›X\ÚË\‹Yœ›ÛHŽ›ÙJ
_WK›X\ÚËZ[XYÙK\‹]Ë\ÜÈŽ–ÞÈ›X\ÚË\‹]ÈŽ›ÙJ
_WK›X\ÚËZ[XYÙK\‹Yœ›ÛKXÛÛÜˆŽ–ÞÈ›X\ÚË\‹Yœ›ÛHŽ“

_WK›X\ÚËZ[XYÙK\‹]ËXÛÛÜˆŽ–ÞÈ›X\ÚË\‹]ÈŽ“

_WK›X\ÚËZ[XYÙKX‹Yœ›ÛK\ÜÈŽ–ÞÈ›X\ÚËX‹Yœ›ÛHŽ›ÙJ
_WK›X\ÚËZ[XYÙKX‹]Ë\ÜÈŽ–ÞÈ›X\ÚËX‹]ÈŽ›ÙJ
_WK›X\ÚËZ[XYÙKX‹Yœ›ÛKXÛÛÜˆŽ–ÞÈ›X\ÚËX‹Yœ›ÛHŽ“

_WK›X\ÚËZ[XYÙKX‹]ËXÛÛÜˆŽ–ÞÈ›X\ÚËX‹]ÈŽ“

_WK›X\ÚËZ[XYÙK[Yœ›ÛK\ÜÈŽ–ÞÈ›X\ÚË[Yœ›ÛHŽ›ÙJ
_WK›X\ÚËZ[XYÙK[]Ë\ÜÈŽ–ÞÈ›X\ÚË[]ÈŽ›ÙJ
_WK›X\ÚËZ[XYÙK[Yœ›ÛKXÛÛÜˆŽ–ÞÈ›X\ÚË[Yœ›ÛHŽ“

_WK›X\ÚËZ[XYÙK[]ËXÛÛÜˆŽ–ÞÈ›X\ÚË[]ÈŽ“

_WK›X\ÚËZ[XYÙK^Yœ›ÛK\ÜÈŽ–ÞÈ›X\ÚË^Yœ›ÛHŽ›ÙJ
_WK›X\ÚËZ[XYÙK^]Ë\ÜÈŽ–ÞÈ›X\ÚË^]ÈŽ›ÙJ
_WK›X\ÚËZ[XYÙK^Yœ›ÛKXÛÛÜˆŽ–ÞÈ›X\ÚË^Yœ›ÛHŽ“

_WK›X\ÚËZ[XYÙK^]ËXÛÛÜˆŽ–ÞÈ›X\ÚË^]ÈŽ“

_WK›X\ÚËZ[XYÙK^KYœ›ÛK\ÜÈŽ–ÞÈ›X\ÚË^KYœ›ÛHŽ›ÙJ
_WK›X\ÚËZ[XYÙK^K]Ë\ÜÈŽ–ÞÈ›X\ÚË^K]ÈŽ›ÙJ
_WK›X\ÚËZ[XYÙK^KYœ›ÛKXÛÛÜˆŽ–ÞÈ›X\ÚË^KYœ›ÛHŽ“

_WK›X\ÚËZ[XYÙK^K]ËXÛÛÜˆŽ–ÞÈ›X\ÚË^K]ÈŽ“

_WK›X\ÚËZ[XYÙK\˜YX[Ž–ÞÈ›X\ÚË\˜YX[Ž–ÔŽKŽW_WK›X\ÚËZ[XYÙK\˜YX[Yœ›ÛK\ÜÈŽ–ÞÈ›X\ÚË\˜YX[Yœ›ÛHŽ›ÙJ
_WK›X\ÚËZ[XYÙK\˜YX[]Ë\ÜÈŽ–ÞÈ›X\ÚË\˜YX[]ÈŽ›ÙJ
_WK›X\ÚËZ[XYÙK\˜YX[Yœ›ÛKXÛÛÜˆŽ–ÞÈ›X\ÚË\˜YX[Yœ›ÛHŽ“

_WK›X\ÚËZ[XYÙK\˜YX[]ËXÛÛÜˆŽ–ÞÈ›X\ÚË\˜YX[]ÈŽ“

_WK›X\ÚËZ[XYÙK\˜YX[\Ú\HŽ–ÞÈ›X\ÚË\˜YX[Ž–ØÚ\˜ÛX[\ÙX_WK›X\ÚËZ[XYÙK\˜YX[\Ú^™HŽ–ÞÈ›X\ÚË\˜YX[Ž–ÞØÛÜÙ\Ý–ØÚYXÛÜ›™\˜K˜\\Ý–ØÚYXÛÜ›™\˜_W_WK›X\ÚËZ[XYÙK\˜YX[\ÜÈŽ–ÞÈ›X\ÚË\˜YX[X]Žž

_WK›X\ÚËZ[XYÙKXÛÛšXË\ÜÈŽ–ÞÈ›X\ÚËXÛÛšXÈŽ–ÓNW_WK›X\ÚËZ[XYÙKXÛÛšXËYœ›ÛK\ÜÈŽ–ÞÈ›X\ÚËXÛÛšXËYœ›ÛHŽ›ÙJ
_WK›X\ÚËZ[XYÙKXÛÛšXË]Ë\ÜÈŽ–ÞÈ›X\ÚËXÛÛšXË]ÈŽ›ÙJ
_WK›X\ÚËZ[XYÙKXÛÛšXËYœ›ÛKXÛÛÜˆŽ–ÞÈ›X\ÚËXÛÛšXËYœ›ÛHŽ“

_WK›X\ÚËZ[XYÙKXÛÛšXË]ËXÛÛÜˆŽ–ÞÈ›X\ÚËXÛÛšXË]ÈŽ“

_WK›X\ÚË[[ÙHŽ–ÞÛX\ÚÎ–Ø[X[Z[˜[˜ÙXX]Ú_WK›X\ÚË[ÜšYÚ[ˆŽ–ÞÈ›X\ÚË[ÜšYÚ[ˆŽ–Ø›Ü™\˜Y[™ØÛÛ[š[Ý›ÚÙXšY]Ø_WK›X\ÚË\ÜÚ][ÛˆŽ–ÞÛX\ÚÎ”Š
_WK›X\ÚË\™\X]Ž–ÞÛX\ÚÎ™YJ
_WK›X\ÚË\Ú^™HŽ–ÞÛX\ÚÎJ
_WK›X\ÚË]\HŽ–ÞÈ›X\ÚË]\HŽ–Ø[X[Z[˜[˜ÙX_WK›X\ÚËZ[XYÙHŽ–ÞÛX\ÚÎ–Ø›Û™XŽKŽW_WKš[\Ž–ÞÙš[\Ž–Ø›Û™XŽKŽW_WK›\Ž–ÞØ›\ŽœÙJ
_WKœšYÚ™\ÜÎ–ÞØœšYÚ™\ÜÎ–ÓNKŽKŽW_WKÛÛ˜\Ý–ÞØÛÛ˜\Ý–ÓNKŽKŽW_WK™›Ü\ÚYÝÈŽ–ÞÈ™›Ü\ÚYÝÈŽ–Ø›Û™XKŽKW_WK™›Ü\ÚYÝËXÛÛÜˆŽ–ÞÈ™›Ü\ÚYÝÈŽ“

_WKÜ˜^\ØØ[N–ÞÙÜ˜^\ØØ[N–ØNKŽKŽW_WKšYK\›Ý]HŽ–ÞÈšYK\›Ý]HŽ–ÓNKŽKŽW_WK[™\–ÞÚ[™\–ØNKŽKŽW_WKØ]\˜]N–ÞÜØ]\˜]N–ÓNKŽKŽW_WKÙ\XN–ÞÜÙ\XN–ØNKŽKŽW_WK˜˜XÚÙ›ÜYš[\ˆŽ–ÞÈ˜˜XÚÙ›ÜYš[\ˆŽ–Ø›Û™XŽKŽW_WK˜˜XÚÙ›ÜX›\ˆŽ–ÞÈ˜˜XÚÙ›ÜX›\ˆŽœÙJ
_WK˜˜XÚÙ›ÜXœšYÚ™\ÜÈŽ–ÞÈ˜˜XÚÙ›ÜXœšYÚ™\ÜÈŽ–ÓNKŽKŽW_WK˜˜XÚÙ›ÜXÛÛ˜\ÝŽ–ÞÈ˜˜XÚÙ›ÜXÛÛ˜\ÝŽ–ÓNKŽKŽW_WK˜˜XÚÙ›ÜYÜ˜^\ØØ[HŽ–ÞÈ˜˜XÚÙ›ÜYÜ˜^\ØØ[HŽ–ØNKŽKŽW_WK˜˜XÚÙ›ÜZYK\›Ý]HŽ–ÞÈ˜˜XÚÙ›ÜZYK\›Ý]HŽ–ÓNKŽKŽW_WK˜˜XÚÙ›ÜZ[™\Ž–ÞÈ˜˜XÚÙ›ÜZ[™\Ž–ØNKŽKŽW_WK˜˜XÚÙ›Ü[ÜXÚ]HŽ–ÞÈ˜˜XÚÙ›Ü[ÜXÚ]HŽ–ÓNKŽKŽW_WK˜˜XÚÙ›Ü\Ø]\˜]HŽ–ÞÈ˜˜XÚÙ›Ü\Ø]\˜]HŽ–ÓNKŽKŽW_WK˜˜XÚÙ›Ü\Ù\XHŽ–ÞÈ˜˜XÚÙ›Ü\Ù\XHŽ–ØNKŽKŽW_WK˜›Ü™\‹XÛÛ\ÙHŽ–ÞØ›Ü™\Ž–ØÛÛ\ÙXÙ\\˜]X_WK˜›Ü™\‹\ÜXÚ[™ÈŽ–ÞÈ˜›Ü™\‹\ÜXÚ[™ÈŽ•

_WK˜›Ü™\‹\ÜXÚ[™Ë^Ž–ÞÈ˜›Ü™\‹\ÜXÚ[™Ë^Ž•

_WK˜›Ü™\‹\ÜXÚ[™Ë^HŽ–ÞÈ˜›Ü™\‹\ÜXÚ[™Ë^HŽ•

_WKX›K[^[Ý]Ž–ÞÝX›N–Ø]]Øš^Y_WKØ\[ÛŽ–ÞØØ\[ÛŽ–ØÜ›ÝÛX_WK˜[œÚ][ÛŽ–ÞÝ˜[œÚ][ÛŽ–Ø[ÛÛÜœØÜXÚ]XÚYÝØ˜[œÙ›Ü›X›Û™XŽKŽW_WK˜[œÚ][Û‹X™Z]š[ÜˆŽ–ÞÝ˜[œÚ][ÛŽ–Ø›Ü›X[\ØÜ™]X_WK\˜][ÛŽ–ÞÙ\˜][ÛŽ–ÓNK[š]X[ŽKŽW_WKX\ÙN–ÞÙX\ÙN–Ø[™X\˜[š]X[‹ŽKŽW_WK[^N–ÞÙ[^N–ÓNKŽKŽW_WK[š[X]N–ÞØ[š[X]N–Ø›Û™XKŽKŽW_WK˜XÚÙ˜XÙN–ÞØ˜XÚÙ˜XÙN–ØY[˜š\ÚX›X_WK\œÜXÝ]™N–ÞÜ\œÜXÝ]™N–ÙËŽKŽW_WKœ\œÜXÝ]™K[ÜšYÚ[ˆŽ–ÞÈœ\œÜXÝ]™K[ÜšYÚ[ˆŽ”Ê
_WK›Ý]N–ÞÜ›Ý]N˜ÙJ
_WKœ›Ý]K^Ž–ÞÈœ›Ý]K^Ž˜ÙJ
_WKœ›Ý]K^HŽ–ÞÈœ›Ý]K^HŽ˜ÙJ
_WKœ›Ý]K^ˆŽ–ÞÈœ›Ý]K^ˆŽ˜ÙJ
_WKØØ[N–ÞÜØØ[N›J
_WKœØØ[K^Ž–ÞÈœØØ[K^Ž›J
_WKœØØ[K^HŽ–ÞÈœØØ[K^HŽ›J
_WKœØØ[K^ˆŽ–ÞÈœØØ[K^ˆŽ›J
_WKœØØ[KLÙŽ–ØØØ[KLÙKÚÙ]Î–ÞÜÚÙ]ÎYJ
_WKœÚÙ]Ë^Ž–ÞÈœÚÙ]Ë^ŽYJ
_WKœÚÙ]Ë^HŽ–ÞÈœÚÙ]Ë^HŽYJ
_WK˜[œÙ›Ü›N–ÞÝ˜[œÙ›Ü›N–ÔŽKŽK›Û™XÜXÜX_WK˜[œÙ›Ü›K[ÜšYÚ[ˆŽ–ÞÛÜšYÚ[Ž”Ê
_WK˜[œÙ›Ü›K\Ý[HŽ–ÞÝ˜[œÙ›Ü›N–ØÙ›]_WK˜[œÛ]N–ÞÝ˜[œÛ]N™J
_WK˜[œÛ]K^Ž–ÞÈ˜[œÛ]K^Ž™J
_WK˜[œÛ]K^HŽ–ÞÈ˜[œÛ]K^HŽ™J
_WK˜[œÛ]K^ˆŽ–ÞÈ˜[œÛ]K^ˆŽ™J
_WK˜[œÛ]K[›Û™HŽ–Ø˜[œÛ]K[›Û™XK›ÛÛN–ÞÞ›ÛÛN–ÓŽKŽKŽW_WKXØÙ[–ÞØXØÙ[“

_WK\X\˜[˜ÙN–ÞØ\X\˜[˜ÙN–Ø›Û™X]]Ø_WK˜Ø\™]XÛÛÜˆŽ–ÞØØ\™]“

_WK˜ÛÛÜ‹\ØÚ[YHŽ–ÞÜØÚ[YN–Ø›Ü›X[\šØYÚYÚY\šØÛ›KY\šØÛ›K[YÚ_WKÝ\œÛÜŽ–ÞØÝ\œÛÜŽ–Ø]]ØY˜][Ú[\˜ØZ]^[Ý™X[›ÝX[ÝÙY›Û™XÛÛ^[Y[X›ÙÜ™\ÜØÙ[Ü›ÜÜÚZ\˜™\XØ[]^[X\ØÛÜX›ËY›ÜÜ˜X˜Ü˜X˜š[™Ø[\ØÜ›ÛÛÛ\™\Ú^™X›ÝË\™\Ú^™X‹\™\Ú^™XK\™\Ú^™XË\™\Ú^™XË\™\Ú^™X™K\™\Ú^™XË\™\Ú^™XÙK\™\Ú^™XÝË\™\Ú^™X]Ë\™\Ú^™XœË\™\Ú^™X™\ÝË\™\Ú^™XÜÙK\™\Ú^™X›ÛÛKZ[˜›ÛÛK[Ý]ŽKŽW_WK™šY[\Ú^š[™ÈŽ–ÞÈ™šY[\Ú^š[™ÈŽ–Øš^YÛÛ[_WKœÚ[\‹Y]™[ÈŽ–ÞÈœÚ[\‹Y]™[ÈŽ–Ø]]Ø›Û™X_WK™\Ú^™N–ÞÜ™\Ú^™N–Ø›Û™XX_WKœØÜ›ÛX™Z]š[ÜˆŽ–ÞÜØÜ›Û–Ø]]ØÛ[ÛÝ_WKœØÜ›Û˜\‹][X‹XÛÛÜˆŽ–ÞÈœØÜ›Û˜\‹][XˆŽ“

_WKœØÜ›Û˜\‹]˜XÚËXÛÛÜˆŽ–ÞÈœØÜ›Û˜\‹]˜XÚÈŽ“

_WKœØÜ›Û˜\‹YÝ]\ˆŽ–ÞÈœØÜ›Û˜\‹YÝ]\ˆŽ–Ø]]ØÝX›X›Ý_WKœØÜ›Û˜\‹]ÈŽ–ÞÜØÜ›Û˜\Ž–Ø]]Ø[˜›Û™X_WKœØÜ›Û[HŽ–ÞÈœØÜ›Û[HŽ•

_WKœØÜ›Û[^Ž–ÞÈœØÜ›Û[^Ž•

_WKœØÜ›Û[^HŽ–ÞÈœØÜ›Û[^HŽ•

_WKœØÜ›Û[\ÈŽ–ÞÈœØÜ›Û[\ÈŽ•

_WKœØÜ›Û[YHŽ–ÞÈœØÜ›Û[YHŽ•

_WKœØÜ›Û[XœÈŽ–ÞÈœØÜ›Û[XœÈŽ•

_WKœØÜ›Û[X™HŽ–ÞÈœØÜ›Û[X™HŽ•

_WKœØÜ›Û[]Ž–ÞÈœØÜ›Û[]Ž•

_WKœØÜ›Û[\ˆŽ–ÞÈœØÜ›Û[\ˆŽ•

_WKœØÜ›Û[XˆŽ–ÞÈœØÜ›Û[XˆŽ•

_WKœØÜ›Û[[Ž–ÞÈœØÜ›Û[[Ž•

_WKœØÜ›Û\Ž–ÞÈœØÜ›Û\Ž•

_WKœØÜ›Û\Ž–ÞÈœØÜ›Û\Ž•

_WKœØÜ›Û\HŽ–ÞÈœØÜ›Û\HŽ•

_WKœØÜ›Û\ÈŽ–ÞÈœØÜ›Û\ÈŽ•

_WKœØÜ›Û\HŽ–ÞÈœØÜ›Û\HŽ•

_WKœØÜ›Û\œÈŽ–ÞÈœØÜ›Û\œÈŽ•

_WKœØÜ›Û\™HŽ–ÞÈœØÜ›Û\™HŽ•

_WKœØÜ›Û\Ž–ÞÈœØÜ›Û\Ž•

_WKœØÜ›Û\ˆŽ–ÞÈœØÜ›Û\ˆŽ•

_WKœØÜ›Û\ˆŽ–ÞÈœØÜ›Û\ˆŽ•

_WKœØÜ›Û\Ž–ÞÈœØÜ›Û\Ž•

_WKœÛ˜\X[YÛˆŽ–ÞÜÛ˜\–ØÝ\[™Ù[\˜[YÛ‹[›Û™X_WKœÛ˜\\ÝÜŽ–ÞÜÛ˜\–Ø›Ü›X[[Ø^\Ø_WKœÛ˜\]\HŽ–ÞÜÛ˜\–Ø›Û™XX›Ý_WKœÛ˜\\ÝšXÝ™\ÜÈŽ–ÞÜÛ˜\–ØX[™]ÜžX›Þ[Z]X_WKÝXÚ–ÞÝÝXÚ–Ø]]Ø›Û™XX[š\[][Û˜_WKÝXÚ^Ž–ÞÈÝXÚ\[ˆŽ–ØYšYÚ_WKÝXÚ^HŽ–ÞÈÝXÚ\[ˆŽ–ØX\ÝÛ˜_WKÝXÚ\ˆŽ–ØÝXÚ\[˜Ú^›ÛÛXKÙ[XÝ–ÞÜÙ[XÝ–Ø›Û™X^[]]Ø_WKÚ[XÚ[™ÙHŽ–ÞÈÚ[XÚ[™ÙHŽ–Ø]]ØØÜ›ÛÛÛ[Ø˜[œÙ›Ü›XŽKŽW_WKš[–ÞÙš[–Ø›Û™X‹‹“

W_WKœÝ›ÚÙK]ÈŽ–ÞÜÝ›ÚÙN–ÓNKŽKNK™[—_WKÝ›ÚÙN–ÞÜÝ›ÚÙN–Ø›Û™X‹‹“

W_WK™›Ü˜ÙYXÛÛÜ‹XY\ÝŽ–ÞÈ™›Ü˜ÙYXÛÛÜ‹XY\ÝŽ–Ø]]Ø›Û™X_W_KÛÛ™›XÝ[™ÐÛ\ÜÑÜ›Ý\ÎžÈ˜ÛÛZ[™\‹[˜[YYŽ–ØÛÛZ[™\‹]\XKÝ™\™›ÝÎ–ØÝ™\™›ÝË^Ý™\™›ÝË^XKÝ™\œØÜ›Û–ØÝ™\œØÜ›Û^Ý™\œØÜ›Û^XK[œÙ]–Ø[œÙ]^[œÙ]^X[œÙ]XœØ[œÙ]X™XÝ\[™ÜšYÚ›ÝÛXYKš[œÙ]^Ž–ØÝ\[™šYÚYKš[œÙ]^HŽ–Ø[œÙ]XœØ[œÙ]X™XÜ›ÝÛXK›^–Ø˜\Ú\ØÜ›ÝØÚš[šØKØ\–ØØ\^Ø\^XK–ØXØXœØ™X˜˜K–ØØX˜KN–ØœØ™X˜KN–Ø^^X\ØYXXœØX™X]\˜X˜[K^–Ø\ØYX\˜[K^N–ØXœØX™X]X˜KÚ^™N–ØØK™›Û\Ú^™HŽ–ØXY[™ØK™›‹[›Ü›X[Ž–Ø›‹[Ü™[˜[›‹\Û\ÚY^™\›Ø›‹YšYÝ\™X›‹\ÜXÚ[™Ø›‹Yœ˜XÝ[Û˜K™›‹[Ü™[˜[Ž–Ø›‹[›Ü›X[K™›‹\Û\ÚY^™\›ÈŽ–Ø›‹[›Ü›X[K™›‹YšYÝ\™HŽ–Ø›‹[›Ü›X[K™›‹\ÜXÚ[™ÈŽ–Ø›‹[›Ü›X[K™›‹Yœ˜XÝ[ÛˆŽ–Ø›‹[›Ü›X[K›[™KXÛ[\Ž–Ø\Ü^XÝ™\™›ÝØK›Ý[™Y–Ø›Ý[™Y\Ø›Ý[™YYX›Ý[™Y]›Ý[™Y\˜›Ý[™YX˜›Ý[™Y[›Ý[™Y\ÜØ›Ý[™Y\ÙX›Ý[™YYYX›Ý[™YY\Ø›Ý[™Y]›Ý[™Y]˜›Ý[™YXœ˜›Ý[™YX›Kœ›Ý[™Y\ÈŽ–Ø›Ý[™Y\ÜØ›Ý[™YY\ØKœ›Ý[™YYHŽ–Ø›Ý[™Y\ÙX›Ý[™YYYXKœ›Ý[™Y]Ž–Ø›Ý[™Y]›Ý[™Y]˜Kœ›Ý[™Y\ˆŽ–Ø›Ý[™Y]˜›Ý[™YXœ˜Kœ›Ý[™YXˆŽ–Ø›Ý[™YXœ˜›Ý[™YX›Kœ›Ý[™Y[Ž–Ø›Ý[™Y]›Ý[™YX›K˜›Ü™\‹\ÜXÚ[™ÈŽ–Ø›Ü™\‹\ÜXÚ[™Ë^›Ü™\‹\ÜXÚ[™Ë^XK˜›Ü™\‹]ÈŽ–Ø›Ü™\‹]Ë^›Ü™\‹]Ë^X›Ü™\‹]Ë\Ø›Ü™\‹]ËYX›Ü™\‹]ËXœØ›Ü™\‹]ËX™X›Ü™\‹]Ë]›Ü™\‹]Ë\˜›Ü™\‹]ËX˜›Ü™\‹]Ë[K˜›Ü™\‹]Ë^Ž–Ø›Ü™\‹]Ë\Ø›Ü™\‹]ËYX›Ü™\‹]Ë\˜›Ü™\‹]Ë[K˜›Ü™\‹]Ë^HŽ–Ø›Ü™\‹]ËXœØ›Ü™\‹]ËX™X›Ü™\‹]Ë]›Ü™\‹]ËX˜K˜›Ü™\‹XÛÛÜˆŽ–Ø›Ü™\‹XÛÛÜ‹^›Ü™\‹XÛÛÜ‹^X›Ü™\‹XÛÛÜ‹\Ø›Ü™\‹XÛÛÜ‹YX›Ü™\‹XÛÛÜ‹XœØ›Ü™\‹XÛÛÜ‹X™X›Ü™\‹XÛÛÜ‹]›Ü™\‹XÛÛÜ‹\˜›Ü™\‹XÛÛÜ‹X˜›Ü™\‹XÛÛÜ‹[K˜›Ü™\‹XÛÛÜ‹^Ž–Ø›Ü™\‹XÛÛÜ‹\Ø›Ü™\‹XÛÛÜ‹YX›Ü™\‹XÛÛÜ‹\˜›Ü™\‹XÛÛÜ‹[K˜›Ü™\‹XÛÛÜ‹^HŽ–Ø›Ü™\‹XÛÛÜ‹XœØ›Ü™\‹XÛÛÜ‹X™X›Ü™\‹XÛÛÜ‹]›Ü™\‹XÛÛÜ‹X˜K˜[œÛ]N–Ø˜[œÛ]K^˜[œÛ]K^X˜[œÛ]K[›Û™XK˜[œÛ]K[›Û™HŽ–Ø˜[œÛ]X˜[œÛ]K^˜[œÛ]K^X˜[œÛ]K^˜KœØÜ›Û[HŽ–ØØÜ›Û[^ØÜ›Û[^XØÜ›Û[\ØØÜ›Û[YXØÜ›Û[XœØØÜ›Û[X™XØÜ›Û[]ØÜ›Û[\˜ØÜ›Û[X˜ØÜ›Û[[KœØÜ›Û[^Ž–ØØÜ›Û[\ØØÜ›Û[YXØÜ›Û[\˜ØÜ›Û[[KœØÜ›Û[^HŽ–ØØÜ›Û[XœØØÜ›Û[X™XØÜ›Û[]ØÜ›Û[X˜KœØÜ›Û\Ž–ØØÜ›Û\ØÜ›Û\XØÜ›Û\ØØÜ›Û\XØÜ›Û\œØØÜ›Û\™XØÜ›Û\ØÜ›Û\˜ØÜ›Û\˜ØÜ›Û\KœØÜ›Û\Ž–ØØÜ›Û\ØØÜ›Û\XØÜ›Û\˜ØÜ›Û\KœØÜ›Û\HŽ–ØØÜ›Û\œØØÜ›Û\™XØÜ›Û\ØÜ›Û\˜KÝXÚ–ØÝXÚ^ÝXÚ^XÝXÚ\˜KÝXÚ^Ž–ØÝXÚKÝXÚ^HŽ–ØÝXÚKÝXÚ\ˆŽ–ØÝXÚ_KÛÛ™›XÝ[™ÐÛ\ÜÑÜ›Ý\[ÙYšY\œÎžÈ™›Û\Ú^™HŽ–ØXY[™Ø_KÜÝš^ÛÚÝ\Û\ÜÑÜ›Ý\Î–ØÛÛZ[™\‹]\XKÜ™\”Ù[œÚ]]™S[ÙYšY\œÎ–Ø
˜
Š˜Y\˜˜XÚÙ›Ü™Y›Ü™X]Z[ËXÛÛ[š[Xš\œÝ[]\˜š\œÝ[[™XX\šÙ\˜XÙZÛ\˜Ù[XÝ[Û˜__JNÙ[˜Ý[ÛˆNJ‹‹™J^Ü™]\›ˆY[Š]
JJ_]˜\ˆ™[\Ê
OOžÝ˜\ˆTÞ[X›Û™›ÜŠ™XXÝ˜[œÚ][Û˜[™[[Y[
KTÞ[X›Û™›ÜŠ™XXÝ™œ˜YÛY[
NÙ[˜Ý[ÛˆŠK‹Š^Ý˜\ˆO[[ÚYŠˆOO]›ÚY	‰ŠOX
ÜŠK‹šÙ^HOO]›ÚY	‰ŠOX
Û‹šÙ^JKÙ^X[ˆŠY›ÜŠ˜\ˆH[ˆ^ßKŠXHOOXÙ^X	‰Š–ØWO[–ØWJNÙ[ÙH[ŽÜ™]\›ˆ\‹œ™Y‹É	\[ÙŽ\N™KÙ^NšK™YŽ›OO]›ÚYÛ[›‹›ÜÎœŸ_YK‘œ˜YÛY[[‹KšœÞ\‹KšœÞÏ\ŸJJKÎO\Ê

K
OOžÝ™^ÜÏZ™[Š
_JJJ
KY[YÎ]
™[]]™HËY[›Ý[™Y^›Ü™\ˆ›Ü™\‹X›Ü™\ˆMˆKVÌŒœH^VÌŒHXY[™Ë\™[^YX^VÍŒNœVÌNHÉŽš\ÊœÝ™ÊWN™ÜšYÉŽš\ÊœÝ™ÊWN™ÜšYXÛÛËVÌÛZ[›X^
YœŠWHÉŽš\ÊœÝ™ÊWN™Ø\LËHÉœÝ™×N›]VÌÜHÉœÝ™×NœÚ^™KM˜Ý˜\šX[ÎžÝ˜\šX[žÙY˜][˜™ËX˜XÚÙÜ›Ý[™^Y›Ü™YÜ›Ý[™\ÝXÝ]™N˜›Ü™\‹Y\ÝXÝ]™KÍL^Y\ÝXÝ]™H\šÎ˜›Ü™\‹Y\ÝXÝ]™HÉœÝ™×N^Y\ÝXÝ]™X™]]˜[˜™Ë\ÙXÛÛ™\žH^Y›Ü™YÜ›Ý[™]]Y˜›Ü™\‹Y\ÚY™Ë\ÙXÛÛ™\žH^[]]YY›Ü™YÜ›Ý[™ÝXØÙ\ÜÎ˜›Ü™\‹\ÝXØÙ\ÜËÌŒ™Ë\ÝXØÙ\ÜË\Ý\™˜XÙH^\ÝXØÙ\ÜØØ\›š[™Î˜›Ü™\‹]Ø\›š[™ËÌŒ™Ë]Ø\›š[™Ë\Ý\™˜XÙH^]Ø\›š[™Ø[™Ù\Ž˜›Ü™\‹Y[™Ù\‹ÌŒ™ËY[™Ù\‹\Ý\™˜XÙH^Y[™Ù\˜_KY˜][˜\šX[ÎžÝ˜\šX[˜Y˜][_JK™[SÎK™›ÜØ\™™YŠ
ØÛ\ÜÓ˜[YN™K˜\šX[‹‹›ŸKŠOOŠÎKšœÞ
J]˜Ü™YŽœ‹™]K\ÛÝŽ˜[\›ÛN˜[\Û\ÜÓ˜[YN•NJY[ŠÝ˜\šX[JKJK‹‹›ŸJJNÓ™[‹™\Ü^S˜[YOX[\Ý˜\ˆ[SÎK™›ÜØ\™™YŠ
ØÛ\ÜÓ˜[YN™K‹‹KŠOOŠÎKšœÞ
JXÜ™YŽ›‹™]K\ÛÝŽ˜[\]]XÛ\ÜÓ˜[YN•NJKL^VÌŒœH›Û\Ù[ZX›ÛXY[™Ë\ÛYÈ˜XÚÚ[™Ë]YÚ^Z[š\š]JK‹‹JJNÔ[‹™\Ü^S˜[YOX[\]XÝ˜\ˆ™[SÎK™›ÜØ\™™YŠ
ØÛ\ÜÓ˜[YN™K‹‹KŠOOŠÎKšœÞ
J]˜Ü™YŽ›‹™]K\ÛÝŽ˜[\Y\ØÜš\[Û˜Û\ÜÓ˜[YN•NJ^VÌŒHÚ]\ÜXÙK\™K]Ü˜\É—ÜN›XY[™Ë\™[^YJK‹‹JJNÑ™[‹™\Ü^S˜[YOX[\\ØÜš\[Û˜Ý˜\ˆY[YÎ]
[›[™KY›^ËYš]X^]ËY[][\ËXÙ[\ˆÙ[‹\Ý\›Ý[™Y[Y›Ü™\ˆL‹HKVÌÜH^VÌMÜH›Û\Ù[ZX›ÛXY[™Ë[›Ü›X[Ý˜\šX[ÎžÝ˜\šX[žÙY˜][˜›Ü™\‹]˜[œÜ\™[™Ë\š[X\žH^\š[X\žKY›Ü™YÜ›Ý[™ÙXÛÛ™\žN˜›Ü™\‹]˜[œÜ\™[™Ë[]]Y^Y›Ü™YÜ›Ý[™\ÝXÝ]™N˜›Ü™\‹]˜[œÜ\™[™ËY\ÝXÝ]™H^Y\ÝXÝ]™KY›Ü™YÜ›Ý[™ÚYÝÈÝ™\Ž˜™ËY\ÝXÝ]™KÎÝ][™N˜^Y›Ü™YÜ›Ý[™KÛ™NžÛ™]]˜[˜ÝXØÙ\ÜÎ˜™Ë\ÝXØÙ\ÜË\Ý\™˜XÙH^\ÝXØÙ\ÜØØ\›š[™Î˜™Ë]Ø\›š[™Ë\Ý\™˜XÙH^]Ø\›š[™Ø[™Ù\Ž˜™ËY[™Ù\‹\Ý\™˜XÙH^Y[™Ù\˜_KÛÛ\Ý[™˜\šX[Î–ÞÝ˜\šX[˜Ý][™XÛ™N˜ÝXØÙ\ÜØÛ\ÜÓ˜[YN˜›Ü™\‹\ÝXØÙ\ÜËÌÌ™Ë]˜[œÜ\™[KÝ˜\šX[˜Ý][™XÛ™N˜Ø\›š[™ØÛ\ÜÓ˜[YN˜›Ü™\‹]Ø\›š[™ËÌÌ™Ë]˜[œÜ\™[KÝ˜\šX[˜Ý][™XÛ™N˜[™Ù\˜Û\ÜÓ˜[YN˜›Ü™\‹Y[™Ù\‹ÌÌ™Ë]˜[œÜ\™[KÝ˜\šX[˜Y˜][Û™N˜ÝXØÙ\ÜØÛ\ÜÓ˜[YN˜™Ë\ÝXØÙ\ÜÈ^\š[X\žKY›Ü™YÜ›Ý[™KÝ˜\šX[˜Y˜][Û™N˜Ø\›š[™ØÛ\ÜÓ˜[YN˜™Ë]Ø\›š[™È^\š[X\žKY›Ü™YÜ›Ý[™KÝ˜\šX[˜Y˜][Û™N˜[™Ù\˜Û\ÜÓ˜[YN˜™ËY[™Ù\ˆ^\š[X\žKY›Ü™YÜ›Ý[™WKY˜][˜\šX[ÎžÝ˜\šX[˜Y˜][Û™N˜™]]˜[_JNÙ[˜Ý[Ûˆ[ŠØÛ\ÜÓ˜[YN™K˜\šX[Û™N›‹‹‹œŸJ^Ü™]\›ŠÎKšœÞ
J]˜È™]K\ÛÝŽ˜˜YÙXÛ\ÜÓ˜[YN•NJY[ŠÝ˜\šX[Û™N›ŸJKJK‹‹œŸJ_]˜\ˆ™[YÎ]
Ü›Ý\ØØ\™›^Z[‹]ËL›^XÛÛØ\VÌŒœH›Ý[™YLž›Ü™\ˆ›Ü™\‹XØ\™XXØÙ[X›Ü™\ˆ^XØ\™Y›Ü™YÜ›Ý[™ÚYÝË^ÈKVÌŽHX^VÍŒNœKVÌŒœXÝ˜\šX[ÎžÜÝ\™˜XÙNžÛÝ][™N˜™ËXØ\™ÉŽ››Ý
Ù]K]Û™O[™]]˜[JWN˜›Ü™\‹]VÌÜHÉŽ››Ý
Ù]K]Û™O[™]]˜[JWN˜›Ü™\‹]XØ\™XXØÙ[]]Y˜™ËXØ\™XXØÙ[\Ý\™˜XÙHÚYÝË[›Û™XÚÜÝ˜›Ý[™Y[›Û™H›Ü™\‹L™Ë]˜[œÜ\™[KLÚYÝË[›Û™HX^VÍŒNœKLKÛ™NžÛ™]]˜[˜YXÛÛÜ‹[™]]˜[›YN˜YXÛÛÜ‹X›YX[Y\˜[˜YXÛÛÜ‹Y[Y\˜[š[Û]˜YXÛÛÜ‹]š[Û][X™\Ž˜YXÛÛÜ‹X[X™\˜›ÜÙN˜YXÛÛÜ‹\›ÜÙXÞX[Ž˜YXÛÛÜ‹XÞX[˜_KY˜][˜\šX[ÎžÜÝ\™˜XÙN˜Ý][™XÛ™N˜™]]˜[_JK™[XVÌŽHX^VÍŒNœVÌŒœHÜ›Ý\Y]KVÜÝ\™˜XÙOYÚÜÝKØØ\™œL™[SÎK™›ÜØ\™™YŠ
ØÛ\ÜÓ˜[YN™KÝ\™˜XÙNXÝ][™XÛ™N›X™]]˜[‹‹œŸKJOOŠÎKšœÞ
J]˜Ü™YŽšK™]K\ÛÝŽ˜Ø\™™]K\Ý\™˜XÙHŽ™]K]Û™HŽ›‹Û\ÜÓ˜[YN•NJ™[ŠÜÝ\™˜XÙNÛ™N›ŸJKJK‹‹œŸJJNÐ™[‹™\Ü^S˜[YOXØ\™Ý˜\ˆ™[SÎK™›ÜØ\™™YŠ
ØÛ\ÜÓ˜[YN™K‹‹KŠOOŠÎKšœÞ
J]˜Ü™YŽ›‹™]K\ÛÝŽ˜Ø\™ZXY\˜Û\ÜÓ˜[YN•NJ›^›^XÛÛØ\L‹X™[‹JK‹‹JJNÕ™[‹™\Ü^S˜[YOXØ\™XY\˜Ý˜\ˆ[SÎK™›ÜØ\™™YŠ
ØÛ\ÜÓ˜[YN™K‹‹KŠOOŠÎKšœÞ
J]˜Ü™YŽ›‹™]K\ÛÝŽ˜Ø\™]]XÛ\ÜÓ˜[YN•NJ›Û\Ù[ZX›ÛXY[™Ë\ÛYÈ˜XÚÚ[™Ë]YÚ^XØ\™XXØÙ[JK‹‹JJNÒ[‹™\Ü^S˜[YOXØ\™]XÝ˜\ˆY[SÎK™›ÜØ\™™YŠ
ØÛ\ÜÓ˜[YN™K‹‹KŠOOŠÎKšœÞ
J]˜Ü™YŽ›‹™]K\ÛÝŽ˜Ø\™Y\ØÜš\[Û˜Û\ÜÓ˜[YN•NJ^VÌŒH^[]]YY›Ü™YÜ›Ý[™JK‹‹JJNÕY[‹™\Ü^S˜[YOXØ\™\ØÜš\[Û˜Ý˜\ˆÙ[SÎK™›ÜØ\™™YŠ
ØÛ\ÜÓ˜[YN™K‹‹KŠOOŠÎKšœÞ
J]˜Ü™YŽ›‹™]K\ÛÝŽ˜Ø\™XÛÛ[Û\ÜÓ˜[YN•NJ™[‹JK‹‹JJNÕÙ[‹™\Ü^S˜[YOXØ\™ÛÛ[Ý˜\ˆÙ[SÎK™›ÜØ\™™YŠ
ØÛ\ÜÓ˜[YN™K‹‹KŠOOŠÎKšœÞ
J]˜Ü™YŽ›‹™]K\ÛÝŽ˜Ø\™Y›ÛÝ\˜Û\ÜÓ˜[YN•NJ›^][\ËXÙ[\ˆ›Ü™\‹]›Ü™\‹XØ\™XXØÙ[X›Ü™\ˆVÌNH^VÌNH^[]]YY›Ü™YÜ›Ý[™™[‹JK‹‹JJNÑÙ[‹™\Ü^S˜[YOXØ\™›ÛÝ\˜Ý˜\ˆÙ[SØš™XÝ™Yš[™T›Ü\KÎOJK
OO’Ù[ŠK˜[YXÝ˜[YNÛÛ™šYÝ\˜X›NˆLJNÙ[˜Ý[ÛˆY[ŠK
^Û]SÎK˜Ü™X]PÛÛ^

NÛ‹™\Ü^S˜[YOYJØÛÛ^Û]QÎJOOžÛ]ØÚ[™[Ž‹‹œŸOYKOSÎK\ÙSY[[Ê

OOœ‹Øš™XÝ˜[Y\ÊŠJNÜ™]\›ŠÎKšœÞ
J‹”›ÝšY\‹Ý˜[YNšKÚ[™[ŽJ_K›ÝšY\˜
NÜ‹™\Ü^S˜[YOYJØ›ÝšY\˜Ù[˜Ý[ÛˆJ‹O^ßJ^Û]ÛÜ[Û˜[˜OHL_OZKÏSÎK\ÙPÛÛ^
ŠNÚYŠÊ\™]\›ˆÎÚYŠOO]›ÚY
\™]\›ˆÚYŠXJ]›ÝÈ\œ›ÜŠ	ÜŸW]\Ý™H\ÙYÚ][ˆ	Ù_W
_\™]\›ˆÎJK\ÙPÛÛ^
KÜ‹W_QÎJY[‹Ü™X]PÛÛ^
NÙ[˜Ý[Ûˆ™[ŠKV×J^Û]V×NÙ[˜Ý[ÛˆŠŠ^Û]OSÎK˜Ü™X]PÛÛ^
ŠNÚK™\Ü^S˜[YO]
ØÛÛ^Û]O[‹›[™ÝÛVË‹‹›‹—NÛ]ÏQÎJOžÛ]ÜØÛÜN›‹Ú[™[Žœ‹‹‹›ßO]Ï[Ë–ÙWOË–ØW_KSÎK\ÙSY[[Ê

OO›ËØš™XÝ˜[Y\ÊÊJNÜ™]\›ŠÎKšœÞ
JË”›ÝšY\‹Ý˜[YN›Ú[™[ŽœŸJ_K›ÝšY\˜
NÛË™\Ü^S˜[YO]
Ø›ÝšY\˜Ù[˜Ý[ÛˆÊ‹ËÏ^ßJ^Û]ÛÜ[Û˜[›HL_O\ËO[ÏË–ÙWOË–ØW_KSÎK\ÙPÛÛ^
JNÚYŠ
\™]\›ˆÚYŠˆOO]›ÚY
\™]\›ˆŽÚYŠ[
]›ÝÈ\œ›ÜŠ	ÛŸW]\Ý™H\ÙYÚ][ˆ	ÝW
_\™]\›ˆÎJË\ÙPÛÛ^
KÛË×_QÎJ‹Ü™X]PÛÛ^
NÛ]OQÎJ

OOžÛ][‹›X\
OO“ÎK˜Ü™X]PÛÛ^
JJNÜ™]\›ˆÎJ[˜Ý[ÛŠŠ^Û][Ë–ÙW_Ü™]\›ˆÎK\ÙSY[[Ê

OOŠÖØ×ÜØÛÜIÙ_XNžË‹‹›‹ÙWNœŸ_JKÛ‹—J_K\ÙTØÛÜX
_KÜ™X]TØÛÜX
NÜ™]\›ˆKœØÛÜS˜[YOYKÜ‹Y[ŠK‹‹
W_QÎJ™[‹Ü™X]PÛÛ^ØÛÜX
NÙ[˜Ý[ÛˆY[Š‹‹™J^Û]YVÌNÚYŠK›[™ÝOOLJ\™]\›ˆÛ]QÎJ

OOžÛ]YK›X\
OOŠÝ\ÙTØÛÜN™J
KØÛÜS˜[YN™KœØÛÜS˜[Y_JJNÜ™]\›ˆÎJ[˜Ý[ÛŠJ^Û][‹œ™YXÙJ
Ý\ÙTØÛÜN›‹ØÛÜS˜[YNœŸJOOžÛ]O[ŠJVØ×ÜØÛÜIÜŸXNÜ™]\›žË‹‹‹‹š__KßJNÜ™]\›ˆÎK\ÙSY[[Ê

OOŠÖØ×ÜØÛÜIÝœØÛÜS˜[Y_XNœŸJKÜ—J_K\ÙPÛÛ\ÜÙYØÛÜ\Ø
_KÜ™X]TØÛÜX
NÜ™]\›ˆ‹œØÛÜS˜[YO]œØÛÜS˜[YKŸQÎJY[‹ÛÛ\ÜÙPÛÛ^ØÛÜ\Ø
NÝ˜\ˆ[SØš™XÝ™Yš[™T›Ü\KÎOJK
OO–[ŠK˜[YXÝ˜[YNÛÛ™šYÝ\˜X›NˆLJNÙ[˜Ý[Ûˆ™[ŠK
^ÚYŠ\[ÙˆOOX[˜Ý[Û˜
\™]\›ˆJ
NÙHO[[	‰ŠK˜Ý\œ™[]
_RÎJ™[‹Ù]™Y˜
NÙ[˜Ý[ÛˆY[Š‹‹™J^Ü™]\›ˆOžÛ]HLKYK›X\
OOžÛ]V™[ŠK
NÜ™]\›ˆ[‰‰\[ÙˆOX[˜Ý[Û˜	‰ŠHL
KŸJNÚYŠŠ\™]\›Š
OOžÙ›ÜŠ]LÝ‹›[™ÝÝ
ÊÊ^Û]\–ÝNÝ\[ÙˆOX[˜Ý[Û˜ÛŠ
N–™[ŠVÝK[
____RÎJY[‹ÛÛ\ÜÙT™YœØ
NÙ[˜Ý[Ûˆ	[Š‹‹™J^Ü™]\›ˆÎK\ÙPØ[˜XÚÊY[Š‹‹™JKJ_RÎJ	[‹\ÙPÛÛ\ÜÙY™YœØ
NÝ˜\ˆ]SØš™XÝ™Yš[™T›Ü\KNOJK
OO™]ŠK˜[YXÝ˜[YNÛÛ™šYÝ\˜X›NˆLJNÙ[˜Ý[ÛˆŠJ^Û]SÎK™›ÜØ\™™YŠ
ŠOOžÛ]ØÚ[™[Žœ‹‹‹š_O]O[[ÏHLKÏV×NÛŠŠI‰\[ÙˆŽOOX[˜Ý[Û˜	‰ŠRŽJ‹—Ü^[ØY
JKÎKÚ[™[‹™›Ü‘XXÚ
‹OOžÚYŠÝŠJJ^ÛÏHLÛ]YKXÚ[[ˆœ›ÜÏÝœ›ÜË˜Ú[œ›ÜË˜Ú[™[ŽÛŠŠI‰\[ÙˆŽOOX[˜Ý[Û˜	‰ŠRŽJ‹—Ü^[ØY
JKOZ]ŠŠKËœ\Ú
OËœ›ÜÏË˜Ú[™[Š_Y[ÙHËœ\Ú
J_JKOØOSÎK˜ÛÛ™Q[[Y[
K›ÚYÊNˆ[É‰“ÎKÚ[™[‹˜ÛÝ[
ŠOOOLI‰“ÎKš\Õ˜[Y[[Y[
ŠI‰ŠO\ŠNÛ]XOÛÝŠJN›ÚYOI[Š‹
NÚYŠXJ^ÚYŠŸOOL
]›ÝÈ\œ›ÜŠÏÜŠJN™ŠJJNÜ™]\›ˆŸ[]X]ŠKKœ›ÜÏÏÞßJNÜ™]\›ˆK\HOOSÎK‘œ˜YÛY[	‰Šœ™Y[ÝN›
KÎK˜ÛÛ™Q[[Y[
K
_JNÜ™]\›ˆ™\Ü^S˜[YOX	Ù_K”ÛÝ\NJ‹Ü™X]TÛÝ
NÝ˜\ˆTÞ[X›Û™›ÜŠ˜Y^œÛÝX›X
NÙ[˜Ý[ÛˆŠJ^Û]\NJOO˜Ú[[ˆOÙK˜Ú[™[ŠK˜Ú[
N™K˜Ú[™[‹ÛÝX›X
NÜ™]\›ˆ™\Ü^S˜[YOX	Ù_K”ÛÝX›X—×Ü˜Y^Y[‹\NJ‹Ü™X]TÛÝX›X
NÝ˜\ˆ]\NJ
K
OOžÚYŠÚ[[ˆKœ›ÜÊ^Û]YKœ›ÜË˜Ú[Ü™]\›ˆÎKš\Õ˜[Y[[Y[

OÓÎK˜ÛÛ™Q[[Y[
›ÚYKœ›ÜË˜Ú[™[Šœ›ÜË˜Ú[™[ŠJN›[\™]\›ˆÎKš\Õ˜[Y[[Y[

OÝ›[KÙ]ÛÝX›Q[[Y[œ›ÛTÛÝX›X
NÙ[˜Ý[Ûˆ]ŠK
^Û]^Ë‹‹NÙ›ÜŠ]ˆ[ˆ
^Û]OYVÜ—KO]Ü—NË×›Û–ÐKV—KË\Ý
ŠOÚI‰˜OÛ–Ü—OJ‹‹™JOOžÛ]XJ‹‹™JNÜ™]\›ˆJ‹‹™JKNšI‰Š–Ü—OZJNœOOXÝ[XÛ–Ü—O^Ë‹‹šK‹‹˜_NœOOXÛ\ÜÓ˜[YXÛ–Ü—OVÚKWK™š[\Š›ÛÛX[ŠKš›Ú[Š
NœOOX\šXKY\ØÜšX™YžX	‰Š–Ü—OYŠKJJ_\™]\›žË‹‹™K‹‹›Ÿ_\NJ]‹Y\™ÙT›ÜØ
NÙ[˜Ý[ÛˆÝŠJ^Û]SØš™XÝ™Ù]ÝÛ”›Ü\Q\ØÜš\ÜŠKœ›ÜË™Y˜
OË™Ù]]	‰˜\Ô™XXÝØ\›š[™Ø[ˆ	‰š\Ô™XXÝØ\›š[™ÎÜ™]\›ˆÙKœ™YŽŠSØš™XÝ™Ù]ÝÛ”›Ü\Q\ØÜš\ÜŠK™Y˜
OË™Ù]]	‰˜\Ô™XXÝØ\›š[™Ø[ˆ	‰š\Ô™XXÝØ\›š[™ËÙKœ›ÜËœ™YŽ™Kœ›ÜËœ™YŸKœ™YŠ_\NJÝ‹Ù][[Y[™Y˜
NÙ[˜Ý[ÛˆÝŠJ^Ü™]\›ˆÎKš\Õ˜[Y[[Y[
JI‰\[ÙˆK\OOX[˜Ý[Û˜	‰˜×Ü˜Y^Y[ˆK\I‰™K\K—×Ü˜Y^YOO[Ÿ\NJÝ‹\ÔÛÝX›X
NÝ˜\ˆÝTÞ[X›Û™›ÜŠ™XXÝ›^žX
NÙ[˜Ý[ÛˆŠJ^Ü™]\›ˆ\[ÙˆOOXØš™XÝ	‰ˆHYI‰˜		\[Ù˜[ˆI‰™K‰	\[ÙOOXÝ‰‰˜Ü^[ØY[ˆI‰]ŠK—Ü^[ØY
_\NJ‹\Ó^žPÛÛ\Û™[
NÙ[˜Ý[Ûˆ]ŠJ^Ü™]\›ˆ\[ÙˆOOXØš™XÝ	‰ˆHYI‰˜[˜[ˆ_\NJ]‹\Ô›ÛZ\ÙSZÙX
NÙ[˜Ý[ÛˆŠ‹‹™J^Û][™]ÈÙ]Ù›ÜŠ]ˆÙˆJZYŠ\[ÙˆOXÝš[™Ø
Y›ÜŠ]HÙˆÝš[™ÊŠKš[J
KœÜ]
×ÊËÊJYI‰˜Y
JNÜ™]\›ˆœÚ^™OŒÐ\œ˜^K™œ›ÛJ
Kš›Ú[Š
N›ÚY\NJ‹ÛÛ˜Ø]\šXQ\ØÜšX™YžX
NÝ˜\ˆ\NJOO˜	Ù_H˜Z[YÈÛÝÛÈ]ÈÚ[™[‹ˆ^XÝYHÚ[™ÛH™XXÝ[[Y[Ú[ÜˆÛÝX›W˜Ü™X]TÛÝ\œ›Ü˜
K\NJOO˜	Ù_H˜Z[YÈÛÝÛÈ]ÈÛÝX›Wˆ^XÝYÛÝX›WÈ™XÙZ]™HHÚ[™ÛH™XXÝ[[Y[Ú[˜Ü™X]TÛÝX›Q\œ›Ü˜
KŽOSÎK\ÙK]SØš™XÝ™Yš[™T›Ü\KJK
OO›]ŠK˜[YXÝ˜[YNÛÛ™šYÝ\˜X›NˆLJKÝVØX]Û˜]˜›Ü›X˜Ø[YØ[œ]X™[X˜]˜ÛÙ[XÝÜ[˜Ý™Ø[Kœ™YXÙJ
K
OOžÛ]]Šš[Z]]™K‰ÝX
KSÎK™›ÜØ\™™YŠ
KŠOOžÛ]Ø\ÐÚ[šK‹‹˜_OYKÏZOÛŽÜ™]\›ˆ\[ÙˆÚ[™ÝÏX	‰ŠÚ[™ÝÖÔÞ[X›Û™›ÜŠ˜Y^]ZX
WOHL
K
ÎKšœÞ
JËË‹‹˜K™YŽœŸJ_JNÜ™]\›ˆ‹™\Ü^S˜[YOXš[Z]]™K‰ÝXË‹‹™KÝNœŸ_KßJNÙ[˜Ý[ÛˆÝŠK
^ÙI‰N]™›\ÚÞ[˜Ê

OO™K™\Ü]Ú]™[

J_ZŠÝ‹\Ü]Ú\ØÜ™]PÝ\ÝÛQ]™[
NÝ˜\ˆSØš™XÝ™Yš[™T›Ü\KNOJK
OOŠK˜[YXÝ˜[YNÛÛ™šYÝ\˜X›NˆLJK]X›ÙÜ™\ÜØLLÞ‹Ý—OR™[Š]ŠKÐÝ‹Ý—O^Š]ŠKSÎK™›ÜØ\™™YŠNJ[˜Ý[ÛŠK
^Û]××ÜØÛÜT›ÙÜ™\ÜÎ›‹˜[YNœ[[X^šKÙ]˜[YSX™[˜OSÝ‹‹‹›ßOYNÊ_OOOL
I‰ˆP]ŠJI‰˜ÛÛœÛÛK™\œ›ÜŠ]Š	Ú_X›ÙÜ™\ÜØ
JNÛ]ÏP]ŠJOÚN˜ŽÜˆOO[[	‰ˆZŠ‹ÊI‰˜ÛÛœÛÛK™\œ›ÜŠŠ	ÜŸX›ÙÜ™\ÜØ
JNÛ]ZŠ‹ÊOÜŽ›[OVJ
OØJÊN›ÚYÜ™]\›ŠÎKšœÞ
JÝ‹ÜØÛÜN›‹˜[YN›X^œËÚ[™[ŽŠÎKšœÞ
JÝ‹™]‹È˜\šXK]˜[Y[X^ŽœË˜\šXK]˜[Y[Z[ˆŽŒ˜\šXK]˜[Y[›ÝÈŽ–J
OÛ›ÚY˜\šXK]˜[Y]^ŽK›ÛN˜›ÙÜ™\ÜØ˜\˜™]K\Ý]HŽšÝŠÊK™]K]˜[YHŽ›ÏÝ›ÚY™]K[X^ŽœË‹‹›Ë™YŽJ_J_K›ÙÜ™\ÜØ
JK]X›ÙÜ™\ÜÒ[™XØ]Ü˜SÎK™›ÜØ\™™YŠNJ[˜Ý[ÛŠK
^Û]××ÜØÛÜT›ÙÜ™\ÜÎ›‹‹‹œŸOYKO]ÝŠ]‹ŠNÜ™]\›ŠÎKšœÞ
JÝ‹™]‹È™]K\Ý]HŽšÝŠK˜[YKK›X^
K™]K]˜[YHŽšK˜[YOÏÝ›ÚY™]K[X^ŽšK›X^‹‹œ‹™YŽJ_K›ÙÜ™\ÜÒ[™XØ]Ü˜
JNÙ[˜Ý[ÛˆÝŠK
^Ü™]\›˜	ÓX]œ›Ý[™
KÝ
ŒL
_IXVNJÝ‹Y˜][Ù]˜[YSX™[
NÙ[˜Ý[ÛˆÝŠK
^Ü™]\›ˆOO[[Ø[™]\›Z[˜]X™OOO]ØÛÛ\]X˜ØY[™ØVNJÝ‹Ù]›ÙÜ™\ÜÔÝ]X
NÙ[˜Ý[ÛˆJJ^Ü™]\›ˆ\[ÙˆOOX[X™\˜VNJK\Ó[X™\˜
NÙ[˜Ý[Ûˆ]ŠJ^Ü™]\›ˆJJI‰ˆZ\Ó˜SŠJI‰™OŒVNJ]‹\Õ˜[YX^[X™\˜
NÙ[˜Ý[ÛˆŠK
^Ü™]\›ˆJJI‰ˆZ\Ó˜SŠJI‰™O]	‰™OLVNJ‹\Õ˜[Y˜[YS[X™\˜
NÙ[˜Ý[Ûˆ]ŠK
^Ü™]\›˜[˜[Y›ÜX^Ùˆ˜[YH	Ù_WÝ\YYÈ	ÝWˆÛ›H[X™\œÈÜ™X]\ˆ[ˆ\™H˜[YX^˜[Y\ËˆY˜][[™ÈÈ	ØŸW˜VNJ]‹Ù][˜[YX^\œ›Ü˜
NÙ[˜Ý[ÛˆŠK
^Ü™]\›˜[˜[Y›Ü˜[YWÙˆ˜[YH	Ù_WÝ\YYÈ	ÝWˆH˜[YW›Ü]\Ý™N‚ˆHHÜÚ]]™H[X™\‚ˆH\ÜÈ[ˆH˜[YH\ÜÙYÈX^
Üˆ	ØŸHYˆ›ÈX^›Ü\ÈÙ]
BˆH[Üˆ[™Yš[™YYˆH›ÙÜ™\ÜÈ\È[™]\›Z[˜]K‚‚‘Y˜][[™ÈÈ[˜VNJ‹Ù][˜[Y˜[YQ\œ›Ü˜
NÝ˜\ˆSÎK™›ÜØ\™™YŠ
ØÛ\ÜÓ˜[YN™K˜[YN‹‹›ŸKŠOOŠÎKšœÞ
J‹Ü™YŽœ‹™]K\ÛÝŽ˜›ÙÜ™\ÜØ˜[YNÛ\ÜÓ˜[YN•NJ™[]]™HLˆËY[Ý™\™›ÝËZY[ˆ›Ý[™YY[™Ë\š[X\žKÌŒJK‹‹›‹Ú[™[ŽŠÎKšœÞ
J‹È™]K\ÛÝŽ˜›ÙÜ™\ÜËZ[™XØ]Ü˜Û\ÜÓ˜[YN˜Y[ËY[›^LH™Ë\š[X\žXÝ[NžÝ˜[œÙ›Ü›N˜˜[œÛ]V
IÌLJ
_IJX_J_JJNÔ‹™\Ü^S˜[YOU‹™\Ü^S˜[YNÝ˜\ˆSØš™XÝ™Yš[™T›Ü\K]JK
OO‘ŠK˜[YXÝ˜[YNÛÛ™šYÝ\˜X›NˆLJK^ÒÜš^›Û[˜Üš^›Û[™\XØ[˜™\XØ[KS‹’Üš^›Û[SØš™XÝ˜[Y\ÊŠKSÎK™›ÜØ\™™YŠ]Š[˜Ý[ÛŠK
^Û]ÙXÛÜ˜]]™N›‹ÜšY[][ÛŽœT‹‹‹š_OYKOUŠŠOÜŽ”‹ÏXOOOS‹•™\XØ[ØN›ÚYÏ[ÞÜ›ÛN˜›Û™XNžÈ˜\šXK[ÜšY[][ÛˆŽ›Ë›ÛN˜Ù\\˜]Ü˜NÜ™]\›ŠÎKšœÞ
JÝ‹™]‹È™]K[ÜšY[][ÛˆŽ˜K‹‹œË‹‹šK™YŽJ_KÙ\\˜]Ü˜
JNÙ[˜Ý[ÛˆŠJ^Ü™]\›ˆ‹š[˜ÛY\ÊJ_R]Š‹\Õ˜[YÜšY[][Û˜
NÝ˜\ˆSÎK™›ÜØ\™™YŠ
ØÛ\ÜÓ˜[YN™KÜšY[][ÛŽXÜš^›Û[XÛÜ˜]]™N›HL‹‹œŸKJOOŠÎKšœÞ
J‹Ü™YŽšK™]K\ÛÝŽ˜Ù\\˜]Ü˜XÛÜ˜]]™N›‹ÜšY[][ÛŽÛ\ÜÓ˜[YN•NJÚš[šËL™ËX›Ü™\˜OOXÜš^›Û[ØVÌ\HËY[˜Y[ËVÌ\XJK‹‹œŸJJNÒ‹™\Ü^S˜[YOP‹™\Ü^S˜[YNÝ˜\ˆ]SÎK™›ÜØ\™™YŠ
ØÛ\ÜÓ˜[YN™K‹‹KŠOOŠÎKšœÞ
J]˜È™]K\ÛÝŽ˜X›KXÛÛZ[™\˜Û\ÜÓ˜[YN˜™[]]™HËY[Z[‹]ËLÝ™\™›ÝËZY[ˆ›Ý[™Y^›Ü™\ˆ›Ü™\‹X›Ü™\˜Ú[™[ŽŠÎKšœÞ
JX›XÜ™YŽ›‹™]K\ÛÝŽ˜X›XÛ\ÜÓ˜[YN•NJKLËY[^VÌŒ\HX^VÍŒN^VÌN\XJK‹‹J_JJNÕ]‹™\Ü^S˜[YOXX›XÝ˜\ˆÝSÎK™›ÜØ\™™YŠ
ØÛ\ÜÓ˜[YN™K‹‹KŠOOŠÎKšœÞ
JXYÜ™YŽ›‹Û\ÜÓ˜[YN•NJÉ—Ý—N˜›Ü™\‹X˜JK‹‹JJNÕÝ‹™\Ü^S˜[YOXX›RXY\˜Ý˜\ˆÝSÎK™›ÜØ\™™YŠ
ØÛ\ÜÓ˜[YN™K‹‹KŠOOŠÎKšœÞ
J›ÙXÜ™YŽ›‹Û\ÜÓ˜[YN•NJÉ—ÝŽ›\ÝXÚ[N˜›Ü™\‹LJK‹‹JJNÑÝ‹™\Ü^S˜[YOXX›P›ÙXÝ˜\ˆÝSÎK™›ÜØ\™™YŠ
ØÛ\ÜÓ˜[YN™K‹‹KŠOOŠÎKšœÞ
J›ÛÝÜ™YŽ›‹Û\ÜÓ˜[YN•NJ›Ü™\‹]™Ë[]]YÍL›Û[YY][HÉ—N›\Ý˜›Ü™\‹X‹LJK‹‹JJNÒÝ‹™\Ü^S˜[YOXX›Q›ÛÝ\˜Ý˜\ˆ]SÎK™›ÜØ\™™YŠ
ØÛ\ÜÓ˜[YN™K‹‹KŠOOŠÎKšœÞ
J˜Ü™YŽ›‹Û\ÜÓ˜[YN•NJ›Ü™\‹Xˆ˜[œÚ][Û‹XÛÛÜœÈÝ™\Ž˜™Ë[]]YÍL]KVÜÝ]O\Ù[XÝYN˜™Ë[]]YJK‹‹JJNÜ]‹™\Ü^S˜[YOXX›T›ÝØÝ˜\ˆSÎK™›ÜØ\™™YŠ
ØÛ\ÜÓ˜[YN™K‹‹KŠOOŠÎKšœÞ
JÜ™YŽ›‹Û\ÜÓ˜[YN•NJ™Ë[]]YÍŒM^[Y[YÛ‹]Ü^VÌNH›Û[YY][H^[]]YY›Ü™YÜ›Ý[™X^VÍŒNœL‹HX^VÍŒNœKLÈX^VÍŒN^VÌMÜXJK‹‹JJNÒ‹™\Ü^S˜[YOXX›RXYÝ˜\ˆ]SÎK™›ÜØ\™™YŠ
ØÛ\ÜÓ˜[YN™K‹‹KŠOOŠÎKšœÞ
JÜ™YŽ›‹Û\ÜÓ˜[YN•NJM[YÛ‹]ÜX^VÍŒNœL‹HX^VÍŒNœKLØJK‹‹JJNÖ]‹™\Ü^S˜[YOXX›PÙ[Ý˜\ˆSÎK™›ÜØ\™™YŠ
ØÛ\ÜÓ˜[YN™K‹‹KŠOOŠÎKšœÞ
JØ\[Û˜Ü™YŽ›‹™]K\ÛÝŽ˜X›KXØ\[Û˜Û\ÜÓ˜[YN•NJKL›Ü™\‹Xˆ›Ü™\‹X›Ü™\ˆ™Ë\ÙXÛÛ™\žHM^[Y^VÌNH^[]]YY›Ü™YÜ›Ý[™JK‹‹JJNÖ‹™\Ü^S˜[YOXX›PØ\[Û˜Ù[˜Ý[ÛˆŠØÛÛ™šYÎ™KØÝ[Y[HL_J^Ü™]\›ˆYK]I‰ˆYK™\ØÜš\[Û‰‰ˆYK™^YXœ›ÝÏÛ[ŠÎKšœÞÊJXY\˜ØÛ\ÜÓ˜[YN˜Y]ZKZXY\˜Ú[™[Ž–ÙK™^YXœ›ÝÉ‰ŠÎKšœÞ
J]˜ØÛ\ÜÓ˜[YN˜Y]ZKY^YXœ›ÝØÚ[™[Ž™K™^YXœ›ÝßJKK]I‰ŠÊÎKšœÞ
J˜ØÛ\ÜÓ˜[YN˜Y]ZK]]XÚ[™[Ž™K]_JNŠÎKšœÞ
JØØÛ\ÜÓ˜[YN˜Y]ZKXØ\™]]XÚ[™[Ž™K]_JJKK™\ØÜš\[Û‰‰ŠÎKšœÞ
JØÛ\ÜÓ˜[YN˜Y]ZKY\ØÜš\[Û˜Ú[™[Ž™K™\ØÜš\[ÛŸJW_J_Y[˜Ý[Ûˆ]ŠÜÝ]\Î™_J^Ü™]\›ŠÎKšœÞ
JÝ™ØÝšY]Ð›Þ˜š[˜›Û™XÝ›ÚÙN˜Ý\œ™[ÛÛÜ˜Ý›ÚÙUÚY˜K˜Ý›ÚÙS[™XØ\˜›Ý[™Ý›ÚÙS[™Z›Ú[Ž˜›Ý[™˜\šXKZY[ˆŽ˜YXÚ[™[ŽŠÎKšœÞ
J]Ù™OOOXÝXØÙ\ÜØØLŒHL˜NHHHKMMËSNL[KLL™OOOXØ\›š[™ØOOOX[™Ù\˜ØLLˆÈˆŒZŒLˆÖ›L[LÝ‹ŒX˜LŒHL˜NHHHKLNHHHN“LLˆL]›LLL‹ŒXJ_J_Y[˜Ý[Ûˆ	ŠØÛÛ™šYÎ™_J^Ü™]\›ŠÎKšœÞ
J]˜ØÛ\ÜÓ˜[YN˜Y]ZK\›ÜÙX[™Ù\›Ý\ÛTÙ][›™\’Sž××Ú[™Kœ™[™\™Y_J_Y[˜Ý[Ûˆ[›ŠÚ][N™_J^Ü™]\›˜\X[ˆOÊÎKšœÞ
J]˜ØÛ\ÜÓ˜[YN˜Y]ZKZ][KXÛÛ[Ú[™[ŽŠÎKšœÞ
J	‹ØÛÛ™šYÎ™_J_JNŠÎKšœÞÊJ]˜ØÛ\ÜÓ˜[YN˜Y]ZKZ][KXÛÛ[Ú[™[Ž–ÊÎKšœÞÊJ]˜ØÛ\ÜÓ˜[YN˜Y]ZKZ][KZXY\˜Ú[™[Ž–ÊÎKšœÞ
JÝ›Û™ØØÛ\ÜÓ˜[YN˜Y]ZKZ][K]]XÚ[™[Ž™K]_JKK›Y]I‰ŠÎKšœÞ
JÜ[˜ØÛ\ÜÓ˜[YN˜Y]ZKZ][K[Y]XÚ[™[Ž™K›Y]_JW_JKK™\ØÜš\[Û‰‰ŠÎKšœÞ
JØÛ\ÜÓ˜[YN˜Y]ZKY\ØÜš\[Û˜Ú[™[Ž™K™\ØÜš\[ÛŸJW_J_Y[˜Ý[ÛˆŽJÛ›Ù\Î™K™[™\™\œÎJ^Ü™]\›ˆK›X\

KŠOOŠÎKšœÞ
J[›‹ØÛÛ™šYÎ™K™[™\™\œÎKŠJ_Y[˜Ý[Ûˆ›ŠØÛÛ™šYÎ™_J^Û]X]X[ˆOÙK]N›ÚYYKœÛÝ\˜ÙWÝ\›
\›[ˆOÙK\›˜Î‹ËÝÝÝË›Ü[œÝ™Y]X\›Ü™ËØ
NÜ™]\›ŠÎKšœÞÊJšYÝ\™XØÛ\ÜÓ˜[YN˜Y]ZK[YYXHY[YYXKIÙK\_XÚ[™[Ž–Ý	‰ŠÎKšœÞ
JØØÛ\ÜÓ˜[YN˜Y]ZKXØ\™]]XÚ[™[ŽJKK›YYXWÙ]OÙK\OOOXYœ˜[YXÊÎKšœÞ
JYœ˜[YXØÛ\ÜÓ˜[YN˜Y]ZKYœ˜[YXØ[™›Þ˜]N™K]K™Y™\œ™\”ÛXÞN˜›Ë\™Y™\œ™\˜Ý[NžØ\ÜXÝ˜][Î˜	ÙK›YYXWÝÚYHÈ	ÙK›YYXWÚZYÚXKÜ˜ÑØÎ˜YØÝ\H[[XYY]HY\]Z]HÛÛ[TÙXÝ\š]KTÛXÞHˆÛÛ[H™Y˜][\Ü˜È	˜\ÜÎÛ›Û™I˜\ÜÎÎÈ[YË\Ü˜È]NŽÈÝ[K\Ü˜È	˜\ÜÎÝ[œØY™KZ[›[™I˜\ÜÎÈÝ[Oš[›Ù^ÛX\™Ú[ŽŒØ˜XÚÙÜ›Ý[™ˆÙ™™ŸZ[YÞÙ\Ü^N˜›ØÚÎÝÚYŒL	NÚZYÚ˜]]ßOÜÝ[OÚXY›ÙO[YÈ[HˆˆÜ˜ÏH˜
ÙK›YYXWÙ]JØØ›ÙOÚ[˜JNŠÎKšœÞ
J[YØØÛ\ÜÓ˜[YN•NJY]ZK\XÝ\™XK\OOOX[XYÙXØYYš]IÙK™š]ÛÛZ[˜HYX\ÜXÝIÙK˜\ÜXÝÜšYÚ[˜[X˜YYš]XÛÛZ[ˆYX\ÜXÝ[ÜšYÚ[˜[
KÜ˜Î™K›YYXWÙ]K[™K\OOOX[XYÙXÙK˜[9g,9fï˜ÚY™K›YYXWÝÚYZYÚ™K›YYXWÚZYÚJNŠÎKšœÞ
J™[‹Ý˜\šX[˜]]YÛ\ÜÓ˜[YN˜Y[YYXKY˜[˜XÚØÚ[™[ŽŠÎKšœÞ
J™[‹ØÚ[™[Ž™K›YYXWÙ\œ›ÜŸ9í(9§d9§*º ïyb¨:/o{ï#:+íù§éyç"ùc§údï¹£©xà ˜J_JKK˜Ø\[Û‰‰ŠÎKšœÞ
JšYØØ\[Û˜ØÛ\ÜÓ˜[YN˜Y]ZKY\ØÜš\[Û˜Ú[™[Ž™K˜Ø\[ÛŸJKK˜Ø\\™WÛ›ÝI‰ŠÎKšœÞ
J]˜ØÛ\ÜÓ˜[YN˜Y]ZKY\ØÜš\[Û˜Ú[™[Ž™K˜Ø\\™WÛ›Ý_JKK\OOOXX\	‰ŠÎKšœÞÊJ]˜ØÛ\ÜÓ˜[YN˜Y]ZK]\›Ú[™[Ž–ØÑÔÎ0­ÈK›]]YKK›Û™Ú]YK0­È0ªHÜ[”Ý™Y]X\ÛÛšX]ÜœØ_JK
ÎKšœÞ
J]˜ØÛ\ÜÓ˜[YN˜Y]ZK]\›Ú[™[Ž›ŸJW_J_Y[˜Ý[Ûˆ››ŠØÛÛ™šYÎ™_J^Û]YK˜ÛÛ[[—ÝÚYË]Ëœ™YXÙJ
K
OO™JÝ
_NÜ™]\›ŠÎKšœÞÊJ]‹ØÛ\ÜÓ˜[YN•NJY]ZK]X›X	‰˜Y]X›K]ÙZYÚY
KÚ[™[Ž–ÙK˜Ø\[Û‰‰ŠÎKšœÞ
J‹ØÚ[™[Ž™K˜Ø\[ÛŸJK	‰ŠÎKšœÞ
JÛÛÜ›Ý\ØÚ[™[Ž›X\

K
OOŠÎKšœÞ
JÛÛÜÝ[NžÝÚY˜	ÌL
™KÛŸIX_K
J_JK
ÎKšœÞ
JÝ‹ØÚ[™[ŽŠÎKšœÞ
J]‹ØÚ[™[Ž™K˜ÛÛ[[œË›X\

K
OOŠÎKšœÞ
J‹ÜØÛÜN˜ÛÛÚ[™[Ž™_K
J_J_JK
ÎKšœÞ
JÝ‹ØÚ[™[Ž™Kœ›ÝÜË›X\

K
OOŠÎKšœÞ
J]‹ØÚ[™[Ž™K›X\

K
OOŠÎKšœÞ
J]‹ØÚ[™[Ž™_K
J_K
J_JW_J_Y[˜Ý[Ûˆ››ŠØÛÛ™šYÎ™K™[™\™\œÎJ^Û]JÎK\ÙT™YŠJ[
NÜ™]\›ŠÎK\ÙS^[Ý]Y™™XÝ
J

OOžÛ][‹˜Ý\œ™[NÜ™]\›ˆK\OOOXÚ\ÚO]œ™[™\Ú\
‹K˜ÛÛ™šYÊN™K\OOOXÝ]ØÝœ™[™\”Ý]Ê‹K˜ÛÛ™šYÊNœ™[™\•[Y[[™J‹K˜ÛÛ™šYÊK

OOžÚOËŠ
K‹œ™\XÙPÚ[™[Š
__KÙKJK
ÎKšœÞ
J]˜ØÛ\ÜÓ˜[YN˜Y]ZKY]X™YŽ›ŸJ_Y[˜Ý[Ûˆ[›ŠØÛÛ™šYÎ™K™[™\™\œÎJ^ÜÝÚ]Ú
K\J^ØØ\ÙX›ÝØ˜Ø\ÙXÛÛ[[˜˜Ø\ÙXÜšYœ™]\›ŠÎKšœÞ
J]˜ØÛ\ÜÓ˜[YN˜Y]ZKIÙK\_HYYØ\IÙK™Ø\YXÝ[N™K\OOOXÜšYÞÈ‹K[Y]ZKXÛÛ[[œÈŽ™K˜ÛÛ[[œßŸN›ÚYÚ[™[ŽŠÎKšœÞ
JŽKÛ›Ù\Î™K˜Ú[™[‹™[™\™\œÎJ_JNØØ\ÙXØ\™œ™]\›ŠÎKšœÞÊJ™[‹ÜÝ\™˜XÙN™K˜\šX[Ý][™XÛ™N™K˜ÛÛÜŸ™]]˜[Û\ÜÓ˜[YN˜Y]ZKXØ\™YXØ\™IÙK˜\šX[Ý][™XHYXÛÛÜ‹IÙK˜ÛÛÜŸ™]]˜[XÚ[™[Ž–ÊK]_K™\ØÜš\[ÛŸK™^YXœ›ÝÊI‰ŠÎKšœÞÊJ™[‹ØÛ\ÜÓ˜[YN˜Y]ZKZXY\˜Ú[™[Ž–ÙK™^YXœ›ÝÉ‰ŠÎKšœÞ
J]˜ØÛ\ÜÓ˜[YN˜Y]ZKY^YXœ›ÝØÚ[™[Ž™K™^YXœ›ÝßJKK]I‰ŠÎKšœÞ
J[‹ØÛ\ÜÓ˜[YN˜Y]ZKXØ\™]]XÚ[™[Ž™K]_JKK™\ØÜš\[Û‰‰ŠÎKšœÞ
JY[‹ØÛ\ÜÓ˜[YN˜Y]ZKY\ØÜš\[Û˜Ú[™[Ž™K™\ØÜš\[ÛŸJW_JK
ÎKšœÞ
JÙ[‹ØÛ\ÜÓ˜[YN˜Y]ZKXÛÛ[Ú[™[ŽŠÎKšœÞ
JŽKÛ›Ù\Î™K˜Ú[™[‹™[™\™\œÎJ_JKK™›ÛÝ\‰‰ŠÎKšœÞ
JÙ[‹ØÛ\ÜÓ˜[YN˜Y]ZKXØ\™Y›ÛÝ\˜Ú[™[Ž™K™›ÛÝ\ŸJW_JNØØ\ÙXÙXÝ[Û˜œ™]\›ŠÎKšœÞÊJÙXÝ[Û˜ØÛ\ÜÓ˜[YN˜Y]ZK\ÙXÝ[Û˜Ú[™[Ž–ÊÎKšœÞ
J‹ØÛÛ™šYÎ™_JK
ÎKšœÞ
J]˜ØÛ\ÜÓ˜[YN˜Y]ZKXÛÛ[Ú[™[ŽŠÎKšœÞ
JŽKÛ›Ù\Î™K˜Ú[™[‹™[™\™\œÎJ_JW_JNØØ\ÙXXY[™Øœ™]\›ŠÎKšœÞ
JØØÛ\ÜÓ˜[YN˜Y]ZKZXY[™ØÚ[™[Ž™K^JNØØ\ÙX^œ™]\›ŠÎKšœÞ
JØÛ\ÜÓ˜[YN˜Y]ZK]^Y]^IÙK˜\šX[›ÙXXÚ[™[Ž™K^JNØØ\ÙX›ÜÙXœ™]\›ŠÎKšœÞ
J	‹ØÛÛ™šYÎ™_JNØØ\ÙX˜YÙXœ™]\›ŠÎKšœÞ
J[‹Ý˜\šX[™K˜\šX[OOXÛÛYØY˜][™K˜\šX[ÙXÛÛ™\žXÛ™N™KœÝ]\ß™]]˜[Û\ÜÓ˜[YN˜Y]ZKX˜YÙHY\Ý]\ËIÙKœÝ]\ß™]]˜[XÚ[™[Ž™K^JNØØ\ÙXØ[Ý]˜Ø\ÙX[\œ™]\›ŠÎKšœÞÊJ™[‹Ý˜\šX[™KœÝ]\ß™]]˜[›ÛN˜›ÝXÛ\ÜÓ˜[YN˜Y]ZKX[\Y\Ý]\ËIÙKœÝ]\ß™]]˜[XÚ[™[Ž–ÊÎKšœÞ
J]‹ÜÝ]\Î™KœÝ]\ß™]]˜[JK
ÎKšœÞÊJ]˜ØÛ\ÜÓ˜[YN˜Y]ZKX[\X›ÙXÚ[™[Ž–ÙK]I‰ŠÎKšœÞ
J[‹ØÛ\ÜÓ˜[YN˜Y]ZKX[\]]XÚ[™[Ž™K]_JK
ÎKšœÞ
J™[‹ØÛ\ÜÓ˜[YN˜Y]ZK]^Ú[™[Ž™K^JW_JW_JNØØ\ÙX[šØœ™]\›ŠÎKšœÞÊJ]˜ØÛ\ÜÓ˜[YN˜Y]ZK[[šØÚ[™[Ž–ÊÎKšœÞ
JÝ›Û™ØØÚ[™[Ž™K›X™[JK
ÎKšœÞ
J]˜ØÛ\ÜÓ˜[YN˜Y]ZK]\›Ú[™[Ž™K\›JW_JNØØ\ÙXÛÝ\˜Ù\Øœ™]\›ŠÎKšœÞ
JÛØÛ\ÜÓ˜[YN˜Y]ZK\ÛÝ\˜Ù\ØÚ[™[Ž™Kš][\Ë›X\

K
OOŠÎKšœÞÊJXØÚ[™[Ž–ÊÎKšœÞ
JÝ›Û™ØØÛ\ÜÓ˜[YN˜Y]ZK\ÛÝ\˜ÙK[X™[Ú[™[Ž™K›X™[JKK™\ØÜš\[Û‰‰ŠÎKšœÞ
JØÛ\ÜÓ˜[YN˜Y]ZKY\ØÜš\[Û˜Ú[™[Ž™K™\ØÜš\[ÛŸJK
ÎKšœÞ
J]˜ØÛ\ÜÓ˜[YN˜Y]ZK]\›Ú[™[Ž™K\›JW_K
J_JNØØ\ÙX[XYÙX˜Ø\ÙXX\˜Ø\ÙXYœ˜[YXœ™]\›ŠÎKšœÞ
J›‹ØÛÛ™šYÎ™_JNØØ\ÙXÛÙXœ™]\›ŠÎKšœÞ
J™XØÛ\ÜÓ˜[YN˜Y]ZKXÛÙXÚ[™[ŽŠÎKšœÞ
JÛÙXØÚ[™[Ž™K^J_JNØØ\ÙXY\›XZYœ™]\›ŠÎKšœÞ
J]˜ØÛ\ÜÓ˜[YN˜Y\›XZYÚ[™[Ž™K^JNØØ\ÙXÝ\Ø˜Ø\ÙX\Ýœ™]\›ŠÎKšœÞ
JK\OOOXÝ\ØØÛ˜[ØÛ\ÜÓ˜[YN™K\OOOXÝ\ØØY]ZK\Ý\Ø˜Y]ZK[\ÝY[\ÝIÙK˜\šX[Z[˜XÚ[™[Ž™Kš][\Ë›X\

ŠOOŠÎKšœÞÊJXØÛ\ÜÓ˜[YN˜Y]ZKZ][XÚ[™[Ž–ÙK\OOOXÝ\Ø	‰ŠÎKšœÞ
JÜ[˜ØÛ\ÜÓ˜[YN˜Y]ZK\Ý\[[X™\˜Ú[™[Ž›ŠÌ_JK
ÎKšœÞ
J[›‹Ú][N\[ÙˆOXÝš[™ØÞÝ]NNJW_KŠJ_JNØØ\ÙX˜XÝØœ™]\›ŠÎKšœÞ
JØÛ\ÜÓ˜[YN˜Y]ZKY˜XÝØÝ[NžÈ‹K[YY˜XÝXÛÛ[[œÈŽ™K˜ÛÛ[[œß_KÚ[™[Ž™Kš][\Ë›X\

K
OOŠÎKšœÞÊJ]˜ØÛ\ÜÓ˜[YN˜Y]ZKY˜XÝÚ[™[Ž–ÊÎKšœÞ
JØÚ[™[Ž™K›X™[JK
ÎKšœÞ
JØÚ[™[Ž™K˜[Y_JW_K
J_JNØØ\ÙXÙ\\˜]Ü˜œ™]\›ŠÎKšœÞÊJ]˜ØÛ\ÜÓ˜[YN˜Y]ZK\Ù\\˜]Ü˜Ú[™[Ž–ÊÎKšœÞ
J‹ØÛ\ÜÓ˜[YN˜Z[‹]ËL›^LXXÛÜ˜]]™NˆHYK›X™[JKK›X™[	‰ŠÎKšœÞÊJÎK‘œ˜YÛY[ØÚ[™[Ž–ÊÎKšœÞ
JÜ[˜ØÚ[™[Ž™K›X™[JK
ÎKšœÞ
J‹ØÛ\ÜÓ˜[YN˜Z[‹]ËL›^LXJW_JW_JNØØ\ÙX][ÝXœ™]\›ŠÎKšœÞÊJ›ØÚÜ][ÝXØÛ\ÜÓ˜[YN˜Y]ZK\][ÝXÚ[™[Ž–ÊÎKšœÞ
JØÚ[™[Ž™K^JKK˜]šX][Û‰‰ŠÎKšœÞ
JÚ]XØÚ[™[Ž™K˜]šX][ÛŸJW_JNØØ\ÙX›ÙÜ™\ÜØœ™]\›ŠÎKšœÞÊJ]˜ØÛ\ÜÓ˜[YN˜Y]ZK\›ÙÜ™\ÜØÚ[™[Ž–ÊÎKšœÞÊJ]˜ØÛ\ÜÓ˜[YN˜Y]ZKZ][KZXY\˜Ú[™[Ž–ÊÎKšœÞ
JÝ›Û™ØØÚ[™[Ž™K›X™[JK
ÎKšœÞÊJÜ[˜ØÛ\ÜÓ˜[YN˜Y]ZKZ][K[Y]XÚ[™[Ž–ÙK˜[YK	X_JW_JK
ÎKšœÞ
J‹Ý˜[YN™K˜[YK˜\šXK[X™[Ž™K›X™[JKK™]Z[	‰ŠÎKšœÞ
JØÛ\ÜÓ˜[YN˜Y]ZKY\ØÜš\[Û˜Ú[™[Ž™K™]Z[JW_JNØØ\ÙXX›Xœ™]\›ŠÎKšœÞ
J››‹ØÛÛ™šYÎ™_JNØØ\ÙXÚ\˜Ø\ÙXÝ]Ø˜Ø\ÙX[Y[[™Xœ™]\›ŠÎKšœÞ
J››‹ØÛÛ™šYÎ™K™[™\™\œÎJNÙY˜][›ÝÈ\œ›ÜŠ[œÝ\ÜYRHÛÛ\Û™[
__]˜\ˆ[›XÛ\ÜÈ^[™ÈÎKÛÛ\Û™[ÜÝ]O^Ù˜Z[YˆL_NÜÝ]XÈÙ]\š]™YÝ]Qœ›ÛQ\œ›ÜŠ
^Ü™]\›žÙ˜Z[YˆL_XÛÛ\Û™[YØ]Ú
J^Ý\Ëœ›ÜË›Û‘\œ›ÜŠJ_\™[™\Š
^Ü™]\›ˆ\ËœÝ]K™˜Z[YÊÎKšœÞ
J]˜ØÛ\ÜÓ˜[YN˜Y\šXÚY\œ›Ü˜Ú[™[Ž˜9h§¹o.¹a¡yk®y®,¹§äùi,z-){ï#9mì¹/çyåfyam¹/fya¡yk®xà ˜JN\Ëœ›ÜË˜Ú[™[Ÿ_KÛ›[™]ÈÙXZÓX\Ù[˜Ý[ÛˆÛ›ŠKŠ^ÙK˜Û\ÜÓ\Ý˜Y
Y]ZKYØÝ[Y[
KK™]\Ù]›Y\ÜØYÙQ[™Ú[™OX™XXÝÛ][Û›‹™Ù]
JNÜŸ
^Ü›ÛÝŠ]˜Ü™X]T›ÛÝ
JKÛÛØ]YÚ\œ›ÜŽŠ
OOžß_JK™]š\Ú[ÛŽŒKÛ›‹œÙ]
KŠJNÛ]Ü›ÛÝš_O\ŽÊN]™›\ÚÞ[˜ÊJ

OOšKœ™[™\Š
ÎKšœÞÊJ[›‹ÛÛ‘\œ›ÜŽ›‹›Û‘\œ›Ü‹Ú[™[Ž–ÊÎKšœÞ
J‹ØÛÛ™šYÎØÝ[Y[ˆLJK
ÎKšœÞ
JŽKÛ›Ù\Î˜Ú[™[‹™[™\™\œÎ›ŸJW_K
ÊÜ‹œ™]š\Ú[ÛŠJJ_T×Ê×ØÙKØYKØÙKÚKZKšKWÙWJNÝ˜\ˆÛ›VØÌNNX˜ÍŒÍ™ŒXØLXLXXXÌNMŽXÙMÍÌ˜ÍÍ˜Ø™LLŒØØÌLXŒ˜K›^ÜÝ]N˜[™[™Ø\œ›ÜœÎ–×_NÝÚ[™ÝË—×Ñ”“Ó•QT—Ô‘S‘T—×Ï[›ŽÙ[˜Ý[ÛˆNJKŠ^Û]YØÝ[Y[˜Ü™X]Q[[Y[
JNÜ™]\›ˆ	‰Š‹˜Û\ÜÓ˜[YO]
KˆO[[	‰Š‹^ÛÛ[TÝš[™ÊŠJKŸY[˜Ý[Ûˆ	JK
^Û]][œÝ[˜Ù[Ùˆ\œ›ÜÝ›Y\ÜØYÙN”Ýš[™Ê
NÛ›‹™\œ›ÜœËœ\Ú
ÚÚ[™™KY\ÜØYÙN›ŸJKÛÛœÛÛKØ\›Š	Ù_H™[™\š[™È˜Z[Y˜
_Y[˜Ý[Ûˆ[›ŠK
^ÚYŠ]]J\™]\›ŽÛ]TNJ]˜Y\šXÚ]]X]JNÝ[š]	‰›‹˜\[™
NJÜ[˜Y\šXÚ][š]9cey/c{ï&‰Ý[š]X
JKK˜\[™
Š_Y[˜Ý[Ûˆ›ŠJ^Û]SX]›X^
‹‹™K›X\
OO”Ýš[™ÊJK›[™Ý
JNÜ™]\›žÚ[\˜[™K›[™ÝŒÓX]˜ÙZ[
K›[™ÝÌLŠKLNŒ›Ý]N™K›[™ÝŒLŸŽÌÌŒYSÝ™\›\ˆL_Y[˜Ý[Ûˆ››ŠJ^Û]^Ø[š[X][ÛŽˆLK\šXNžÙ[˜X›YˆLX™[žÙ\ØÜš\[ÛŽ™K]_9¥l9£k¹fïº(j_KÛÛÜŽ˜Û›‹^Ý[NžÙ›Û˜[Z[N˜›ÝÈØ[œÈÒ’ÈÐËZXÜ›ÜÛÙXRZKØ[œË\Ù\šY˜›ÛÚ^™NŒNÛÛÜŽ˜ÍLLX˜KÛÛ›ÞžÜÚÝÎˆL_KÛÛ\žÜÚÝÎˆL__NÜ™]\›ˆK\OOOXYXÞË‹‹YÙ[™™KœÚÝ×ÛYÙ[™ÞÝ\N˜Z[˜›ÝÛNŒ^Ý[NžÙ›ÛÚ^™NŒMŸ_NžÜÚÝÎˆL_KÙ\šY\Î–ÞÝ\N˜YX˜Y]\Î–ØÍ	XŽ	XKÙ[\Ž–ØL	X‰XK]N™K™]KX™[žÙ›Ü›X]\Ž˜ØŸNˆÙIXÝ™\™›ÝÎ˜[˜Ø]X›ÛÚ^™NŒMŸK]›ÚYX™[Ý™\›\ˆLÚ[[ˆLW_NžË‹‹ÜšYžÛYšYÚŒŽÜŒŽ›ÝÛN™KœÚÝ×ÛYÙ[™ÎŽNÛÛZ[“X™[ˆLKYÙ[™™KœÚÝ×ÛYÙ[™ÞØ›ÝÛNŒ^Ý[NžÙ›ÛÚ^™NŒMŸ_NžÜÚÝÎˆL_K^\ÎžÝ\N˜Ø]YÛÜžX]N™K›X™[Ë^\ÓX™[žË‹‹™›ŠK›X™[ÊK›ÛÚ^™NŒMŸK^\ÕXÚÎžØ[YÛ•Ú]X™[ˆL_KP^\ÎžÝ\N˜˜[YX˜[YN™K[š]ØØ[N™K\OOOX[™X^\ÓX™[žÙ›ÛÚ^™NŒMŸKÜ][™NžÛ[™TÝ[NžØÛÛÜŽ˜ÙMMMØ__KÙ\šY\Î™KœÙ\šY\Ë›X\
OŠÛ˜[YN›˜[YK\N™K\K]N˜[Y\Ë˜\“X^ÚY™K\OOOX˜\˜Í›ÚYÚÝÔÞ[X›Û™K\OOOX[™X	‰™K›X™[Ë›[™ÝLÌÞ[X›ÛÚ^™NËÛ[ÛÝˆLKÚ[[ˆLJJ__Y[˜Ý[Ûˆ›ŠK
^Û]TNJX›XYXÚ\Y˜[˜XÚØ
KTNJXY
KOTNJ˜
KOTNJ›ÙX
NÝ\OOOXYXÊK˜\[™
NJ[:hnyæë˜
KNJ[9¥l9`/	Ý[š]Ø;ï"	Ý[š]{ï"X˜X
JK™]K™›Ü‘XXÚ
OOžÛ]TNJ˜
NÝ˜\[™
NJ[K›˜[YJKNJ[K˜[YJJKK˜\[™

_JJNŠK˜\[™
NJ[:hnyæë˜
K‹‹œÙ\šY\Ë›X\
OO”NJ[K›˜[YJJJK›X™[Ë™›Ü‘XXÚ

KŠOOžÛ]TNJ˜
NÜ‹˜\[™
NJ[JK‹‹œÙ\šY\Ë›X\
OO”NJ[K˜[Y\ÖÛ—JJJKK˜\[™
Š_JJK‹˜\[™
JK‹˜\[™
‹JKK˜\[™
Š_Y[˜Ý[Ûˆ[›ŠK
^Ý[›ŠK
NÛ]TNJ]˜YXÚ\XØ[˜\Ø
NÛ‹œÙ]]šX]J›ÛX[YØ
K‹œÙ]]šX]J\šXK[X™[]_9¥l9£k¹fïº(j
KK˜\[™
ŠNÝž^Û]VY™J‹[Ü™[™\™\Ž˜Ý™ØJNÜ™]\›ˆ‹œÙ]Ü[ÛŠ››Š
KÛ›ÝY\™ÙNˆL^žU\]NˆL_JK‹œ™\Ú^™J
KK™]\Ù]˜Ú\™[™\™YXYX

OOœ‹™\ÜÜÙJ
_XØ]Ú
Š^Û‹œ™[[Ý™J
K›ŠK
KK™]\Ù]˜Ú\™[™\™YX˜[˜XÚØ	JÚ\Š__Y[˜Ý[Ûˆ›ŠK
^Ý[›ŠK
NÛ]TNJ]˜Y\Ý]ËYÜšYY\Ý]ËIÝ˜\šX[Z[˜X
NÛ‹œÝ[KœÙ]›Ü\JK[Y\Ý]ËXÛÛ[[œØÝš[™Ê˜ÛÛ[[œÊJKš][\Ë™›Ü‘XXÚ
OOžÛ]TNJÙXÝ[Û˜Y\Ý]XØ\™Y\Ý]\ËIÙKœÝ]\ßX
NÝ˜\[™
NJ]˜Y\Ý][X™[K›X™[
JNÛ]TNJ]˜Y\Ý]]˜[YXK˜[YJNÙK[š]	‰œ‹˜\[™
NJÜ[˜Y\Ý]][š]K[š]
JK˜\[™
ŠKK™]Z[	‰˜\[™
NJ]˜Y\Ý]Y]Z[K™]Z[
JK‹˜\[™

_JKK˜\[™
Š_Y[˜Ý[ÛˆÛ›ŠK
^Ý[›ŠK
NÛ]TNJ]˜Y][Y[[™X
NÝš][\Ë™›Ü‘XXÚ
OOžÛ]TNJÙXÝ[Û˜Y][Y[[™KZ][HY\Ý]\ËIÙKœÝ]\ßX
NÝ˜\[™
NJÜ[˜Y][Y[[™K[X\šÙ\˜
JNÛ]TNJ]˜Y][Y[[™KX›ÙX
NÜ‹˜\[™
NJ]˜Y][Y[[™K][YXK[YJJK‹˜\[™
NJ]˜Y][Y[[™K]]XK]JJKK˜ÛÛ[	‰œ‹˜\[™
NJ]˜Y][Y[[™KXÛÛ[K˜ÛÛ[
JK˜\[™
ŠK‹˜\[™

_JKK˜\[™
Š_Y[˜Ý[ÛˆÛ›Š
^ÙØÝ[Y[œ]Y\žTÙ[XÝÜ[
›Y\šXÚX›ØÚØ
K™›Ü‘XXÚ
OOžÝž^Û]YK™]\Ù]œšXÚÚ[™R”ÓÓ‹œ\œÙJK™]\Ù]œšXÚÛÛ™šYÊNÚYŠOOXÚ\
[[›ŠKŠNÙ[ÙHYŠOOXÝ]Ø
Z›ŠKŠNÙ[ÙHYŠOOX[Y[[™X
YÛ›ŠKŠNÙ[ÙHYŠOOXZX
\Û›ŠK‹Ü™[™\Ú\›[›‹™[™\”Ý]Îš›‹™[™\•[Y[[™N™Û›‹Û‘\œ›ÜŽOžÙK™]\Ù]œšXÚ™[™\™YX˜[˜XÚØ	JšXÚ
__JNÙ[ÙH›ÝÈ\œ›ÜŠ[œÝ\ÜYšXÚ›ØÚÎˆ	ÝX
NÙK™]\Ù]œšXÚ™[™\™YOOX˜[˜XÚØ	‰ŠK™]\Ù]œšXÚ™[™\™YXYX
_XØ]Ú

^ÙKœ™\XÙPÚ[™[ŠNJ]˜Y\šXÚY\œ›Ü˜9h§¹o.¹a¡yk®y®,¹§äùi,z-){ï#9mì¹/çyåfyam¹/fya¡yk®xà ˜
JKK™]\Ù]œšXÚ™[™\™YX˜[˜XÚØ	JšXÚ
__J_Y[˜Ý[Ûˆ››ŠOYØÝ[Y[˜›ÙKHLJ^×ÞJKÙ[[Z]\œÎ–ÞÛY˜		šYÚ˜		\Ü^NˆLKÛY˜	šYÚ˜	\Ü^NˆL_KÛY˜
šYÚ˜
X\Ü^NˆL_KÛY˜ØšYÚ˜X\Ü^NˆLWK›ÝÓÛ‘\œ›ÜŽˆLKÝšXÝˆLK\ÝˆLKYÛ›Ü™YÛ\ÜÙ\ÎÖØY\›XZYN–ØY\›XZYY\šXÚX›ØÚØKXXÜ›ÜÎžÈ—”ˆŽ˜X]˜žÔŸX—“ˆŽ˜X]˜žÓŸX—–ˆŽ˜X]˜žÖŸX—THŽ˜X]˜žÔ_X—ÐÈŽ˜X]˜žÐßX_J_X\Þ[˜È[˜Ý[Ûˆ[›Š
^ÙN]š[š]X[^™JÜÝ\Û“ØYˆLKÙXÝ\š]S]™[˜ÝšXÝ[X™[ÎˆLK[YN˜™]]˜[JNÙ›ÜŠ]HÙˆØÝ[Y[œ]Y\žTÙ[XÝÜ[
›Y\›XZY
J^Û]YK^ÛÛ[Ýž^Ø]ØZ]N]œ[ŠÛ›Ù\Î–ÙWKÝ\™\ÜÑ\œ›ÜœÎˆL_JKK™]\Ù]›Y\›XZY™[™\™YXYXXØ]Ú
Š^Û]TNJ™XY[Y\›XZYY˜[˜XÚØ
NÜ‹˜\[™
NJÛÙX[™ÝXYÙK[Y\›XZY
JKKœ™\XÙUÚ]
ŠK	JY\›XZYŠ___Y[˜Ý[Ûˆ››Š
^Ü™]\›ˆ™]È›ÛZ\ÙJOOœ™\]Y\Ý[š[X][Û‘œ˜[YJ

OO™J
JJ_X\Þ[˜È[˜Ý[Ûˆ›Š
^Ýž^ÙØÝ[Y[™›ÛÏËœ™XYI‰˜]ØZ]ØÝ[Y[™›ÛËœ™XYKÛ›Š
K]ØZ]›ÛZ\ÙK˜[Ù]Y
ÖØX]

OOžÝ››Š
KØÝ[Y[œ]Y\žTÙ[XÝÜ[
›Y]ZK\›ÜÙX
K™›Ü‘XXÚ
OO››ŠKL
J_WKØY\›XZY[›—KØYÚYÚ

OO]™Y˜][šYÚYÚ[

WWK›X\
\Þ[˜ÊÙKJOOžÝž^Ø]ØZ]

_XØ]Ú

^ÉJK
__JJK]ØZ]›ÛZ\ÙK˜[Ù]Y
Ë‹‹™ØÝ[Y[œ]Y\žTÙ[XÝÜ[
›Y]ZK\XÝ\™X
WK›X\
OO™K™XÛÙJ
JJK]ØZ]›ÛZ\ÙK˜[Ù]Y
Ë‹‹™ØÝ[Y[œ]Y\žTÙ[XÝÜ[
›Y]ZKYœ˜[YX
WK›X\
OO›™]È›ÛZ\ÙJOžÙK˜Y]™[\Ý[™\ŠØYÛÛ˜ÙNˆLJKÙ][Y[Ý]
ML
_JJJK]ØZ]››Š
K]ØZ]››Š
_Yš[˜[^Û›‹œÝ]OX™XYXØÝ[Y[™ØÝ[Y[[[Y[™]\Ù]™œ›ÛY\”™XYOXYX_YØÝ[Y[œ™XYTÝ]OOOXØY[™ØÙØÝ[Y[˜Y]™[\Ý[™\ŠÓPÛÛ[ØYY

OO›ÚY›Š
KÛÛ˜ÙNˆLJNž›Š
_JJ
N