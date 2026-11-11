function e(e,t,i,a){var r,n=arguments.length,s=n<3?t:null===a?a=Object.getOwnPropertyDescriptor(t,i):a;if("object"==typeof Reflect&&"function"==typeof Reflect.decorate)s=Reflect.decorate(e,t,i,a);else for(var o=e.length-1;o>=0;o--)(r=e[o])&&(s=(n<3?r(s):n>3?r(t,i,s):r(t,i))||s);return n>3&&s&&Object.defineProperty(t,i,s),s}"function"==typeof SuppressedError&&SuppressedError;var t="M18.92 2C18.72 1.42 18.16 1 17.5 1H6.5C5.84 1 5.29 1.42 5.08 2L3 8V16C3 16.55 3.45 17 4 17H5C5.55 17 6 16.55 6 16V15H18V16C18 16.55 18.45 17 19 17H20C20.55 17 21 16.55 21 16V8L18.92 2M6.5 12C5.67 12 5 11.33 5 10.5S5.67 9 6.5 9 8 9.67 8 10.5 7.33 12 6.5 12M17.5 12C16.67 12 16 11.33 16 10.5S16.67 9 17.5 9 19 9.67 19 10.5 18.33 12 17.5 12M5 7L6.5 2.5H17.5L19 7H5M7 20H11V18L17 21H13V23L7 20Z",i="M21 11H3V9H21V11M21 13H3V15H21V13Z",a="M19.77,7.23L19.78,7.22L16.06,3.5L15,4.56L17.11,6.67C16.17,7.03 15.5,7.93 15.5,9A2.5,2.5 0 0,0 18,11.5C18.36,11.5 18.69,11.42 19,11.29V18.5A1,1 0 0,1 18,19.5A1,1 0 0,1 17,18.5V14A2,2 0 0,0 15,12H14V5A2,2 0 0,0 12,3H6A2,2 0 0,0 4,5V21H14V13.5H15.5V18.5A2.5,2.5 0 0,0 18,21A2.5,2.5 0 0,0 20.5,18.5V9C20.5,8.31 20.22,7.68 19.77,7.23M18,10A1,1 0 0,1 17,9A1,1 0 0,1 18,8A1,1 0 0,1 19,9A1,1 0 0,1 18,10M8,18V13.5H6L10,6V11H12L8,18Z",r="M11 15H6L13 1V9H18L11 23V15Z",n="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z",s="M6,2H18V8H18V8L14,12L18,16V16H18V22H6V16H6V16L10,12L6,8V8H6V2M16,16.5L12,12.5L8,16.5V20H16V16.5M12,11.5L16,7.5V4H8V7.5L12,11.5M10,6H14V6.75L12,8.75L10,6.75V6Z";const o=globalThis,l=o.ShadowRoot&&(void 0===o.ShadyCSS||o.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,c=Symbol(),d=new WeakMap;let h=class{constructor(e,t,i){if(this._$cssResult$=!0,i!==c)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=e,this.t=t}get styleSheet(){let e=this.o;const t=this.t;if(l&&void 0===e){const i=void 0!==t&&1===t.length;i&&(e=d.get(t)),void 0===e&&((this.o=e=new CSSStyleSheet).replaceSync(this.cssText),i&&d.set(t,e))}return e}toString(){return this.cssText}};const p=e=>new h("string"==typeof e?e:e+"",void 0,c),g=(e,...t)=>{const i=1===e.length?e[0]:t.reduce((t,i,a)=>t+(e=>{if(!0===e._$cssResult$)return e.cssText;if("number"==typeof e)return e;throw Error("Value passed to 'css' function must be a 'css' function result: "+e+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(i)+e[a+1],e[0]);return new h(i,e,c)},u=l?e=>e:e=>e instanceof CSSStyleSheet?(e=>{let t="";for(const i of e.cssRules)t+=i.cssText;return p(t)})(e):e,{is:v,defineProperty:m,getOwnPropertyDescriptor:f,getOwnPropertyNames:_,getOwnPropertySymbols:y,getPrototypeOf:b}=Object,w=globalThis,$=w.trustedTypes,k=$?$.emptyScript:"",x=w.reactiveElementPolyfillSupport,A=(e,t)=>e,C={toAttribute(e,t){switch(t){case Boolean:e=e?k:null;break;case Object:case Array:e=null==e?e:JSON.stringify(e)}return e},fromAttribute(e,t){let i=e;switch(t){case Boolean:i=null!==e;break;case Number:i=null===e?null:Number(e);break;case Object:case Array:try{i=JSON.parse(e)}catch(e){i=null}}return i}},E=(e,t)=>!v(e,t),z={attribute:!0,type:String,converter:C,reflect:!1,useDefault:!1,hasChanged:E};Symbol.metadata??=Symbol("metadata"),w.litPropertyMetadata??=new WeakMap;let S=class extends HTMLElement{static addInitializer(e){this._$Ei(),(this.l??=[]).push(e)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(e,t=z){if(t.state&&(t.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(e)&&((t=Object.create(t)).wrapped=!0),this.elementProperties.set(e,t),!t.noAccessor){const i=Symbol(),a=this.getPropertyDescriptor(e,i,t);void 0!==a&&m(this.prototype,e,a)}}static getPropertyDescriptor(e,t,i){const{get:a,set:r}=f(this.prototype,e)??{get(){return this[t]},set(e){this[t]=e}};return{get:a,set(t){const n=a?.call(this);r?.call(this,t),this.requestUpdate(e,n,i)},configurable:!0,enumerable:!0}}static getPropertyOptions(e){return this.elementProperties.get(e)??z}static _$Ei(){if(this.hasOwnProperty(A("elementProperties")))return;const e=b(this);e.finalize(),void 0!==e.l&&(this.l=[...e.l]),this.elementProperties=new Map(e.elementProperties)}static finalize(){if(this.hasOwnProperty(A("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(A("properties"))){const e=this.properties,t=[..._(e),...y(e)];for(const i of t)this.createProperty(i,e[i])}const e=this[Symbol.metadata];if(null!==e){const t=litPropertyMetadata.get(e);if(void 0!==t)for(const[e,i]of t)this.elementProperties.set(e,i)}this._$Eh=new Map;for(const[e,t]of this.elementProperties){const i=this._$Eu(e,t);void 0!==i&&this._$Eh.set(i,e)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(e){const t=[];if(Array.isArray(e)){const i=new Set(e.flat(1/0).reverse());for(const e of i)t.unshift(u(e))}else void 0!==e&&t.push(u(e));return t}static _$Eu(e,t){const i=t.attribute;return!1===i?void 0:"string"==typeof i?i:"string"==typeof e?e.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(e=>this.enableUpdating=e),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(e=>e(this))}addController(e){(this._$EO??=new Set).add(e),void 0!==this.renderRoot&&this.isConnected&&e.hostConnected?.()}removeController(e){this._$EO?.delete(e)}_$E_(){const e=new Map,t=this.constructor.elementProperties;for(const i of t.keys())this.hasOwnProperty(i)&&(e.set(i,this[i]),delete this[i]);e.size>0&&(this._$Ep=e)}createRenderRoot(){const e=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return((e,t)=>{if(l)e.adoptedStyleSheets=t.map(e=>e instanceof CSSStyleSheet?e:e.styleSheet);else for(const i of t){const t=document.createElement("style"),a=o.litNonce;void 0!==a&&t.setAttribute("nonce",a),t.textContent=i.cssText,e.appendChild(t)}})(e,this.constructor.elementStyles),e}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(e=>e.hostConnected?.())}enableUpdating(e){}disconnectedCallback(){this._$EO?.forEach(e=>e.hostDisconnected?.())}attributeChangedCallback(e,t,i){this._$AK(e,i)}_$ET(e,t){const i=this.constructor.elementProperties.get(e),a=this.constructor._$Eu(e,i);if(void 0!==a&&!0===i.reflect){const r=(void 0!==i.converter?.toAttribute?i.converter:C).toAttribute(t,i.type);this._$Em=e,null==r?this.removeAttribute(a):this.setAttribute(a,r),this._$Em=null}}_$AK(e,t){const i=this.constructor,a=i._$Eh.get(e);if(void 0!==a&&this._$Em!==a){const e=i.getPropertyOptions(a),r="function"==typeof e.converter?{fromAttribute:e.converter}:void 0!==e.converter?.fromAttribute?e.converter:C;this._$Em=a;const n=r.fromAttribute(t,e.type);this[a]=n??this._$Ej?.get(a)??n,this._$Em=null}}requestUpdate(e,t,i,a=!1,r){if(void 0!==e){const n=this.constructor;if(!1===a&&(r=this[e]),i??=n.getPropertyOptions(e),!((i.hasChanged??E)(r,t)||i.useDefault&&i.reflect&&r===this._$Ej?.get(e)&&!this.hasAttribute(n._$Eu(e,i))))return;this.C(e,t,i)}!1===this.isUpdatePending&&(this._$ES=this._$EP())}C(e,t,{useDefault:i,reflect:a,wrapped:r},n){i&&!(this._$Ej??=new Map).has(e)&&(this._$Ej.set(e,n??t??this[e]),!0!==r||void 0!==n)||(this._$AL.has(e)||(this.hasUpdated||i||(t=void 0),this._$AL.set(e,t)),!0===a&&this._$Em!==e&&(this._$Eq??=new Set).add(e))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(e){Promise.reject(e)}const e=this.scheduleUpdate();return null!=e&&await e,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(const[e,t]of this._$Ep)this[e]=t;this._$Ep=void 0}const e=this.constructor.elementProperties;if(e.size>0)for(const[t,i]of e){const{wrapped:e}=i,a=this[t];!0!==e||this._$AL.has(t)||void 0===a||this.C(t,void 0,i,a)}}let e=!1;const t=this._$AL;try{e=this.shouldUpdate(t),e?(this.willUpdate(t),this._$EO?.forEach(e=>e.hostUpdate?.()),this.update(t)):this._$EM()}catch(t){throw e=!1,this._$EM(),t}e&&this._$AE(t)}willUpdate(e){}_$AE(e){this._$EO?.forEach(e=>e.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(e)),this.updated(e)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(e){return!0}update(e){this._$Eq&&=this._$Eq.forEach(e=>this._$ET(e,this[e])),this._$EM()}updated(e){}firstUpdated(e){}};S.elementStyles=[],S.shadowRootOptions={mode:"open"},S[A("elementProperties")]=new Map,S[A("finalized")]=new Map,x?.({ReactiveElement:S}),(w.reactiveElementVersions??=[]).push("2.1.2");const V=globalThis,H=e=>e,M=V.trustedTypes,L=M?M.createPolicy("lit-html",{createHTML:e=>e}):void 0,T="$lit$",P=`lit$${Math.random().toFixed(9).slice(2)}$`,N="?"+P,j=`<${N}>`,D=document,O=()=>D.createComment(""),W=e=>null===e||"object"!=typeof e&&"function"!=typeof e,R=Array.isArray,I="[ \t\n\f\r]",F=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,U=/-->/g,B=/>/g,q=RegExp(`>|${I}(?:([^\\s"'>=/]+)(${I}*=${I}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`,"g"),K=/'/g,Z=/"/g,G=/^(?:script|style|textarea|title)$/i,J=e=>(t,...i)=>({_$litType$:e,strings:t,values:i}),X=J(1),Q=J(2),Y=Symbol.for("lit-noChange"),ee=Symbol.for("lit-nothing"),te=new WeakMap,ie=D.createTreeWalker(D,129);function ae(e,t){if(!R(e)||!e.hasOwnProperty("raw"))throw Error("invalid template strings array");return void 0!==L?L.createHTML(t):t}class re{constructor({strings:e,_$litType$:t},i){let a;this.parts=[];let r=0,n=0;const s=e.length-1,o=this.parts,[l,c]=((e,t)=>{const i=e.length-1,a=[];let r,n=2===t?"<svg>":3===t?"<math>":"",s=F;for(let t=0;t<i;t++){const i=e[t];let o,l,c=-1,d=0;for(;d<i.length&&(s.lastIndex=d,l=s.exec(i),null!==l);)d=s.lastIndex,s===F?"!--"===l[1]?s=U:void 0!==l[1]?s=B:void 0!==l[2]?(G.test(l[2])&&(r=RegExp("</"+l[2],"g")),s=q):void 0!==l[3]&&(s=q):s===q?">"===l[0]?(s=r??F,c=-1):void 0===l[1]?c=-2:(c=s.lastIndex-l[2].length,o=l[1],s=void 0===l[3]?q:'"'===l[3]?Z:K):s===Z||s===K?s=q:s===U||s===B?s=F:(s=q,r=void 0);const h=s===q&&e[t+1].startsWith("/>")?" ":"";n+=s===F?i+j:c>=0?(a.push(o),i.slice(0,c)+T+i.slice(c)+P+h):i+P+(-2===c?t:h)}return[ae(e,n+(e[i]||"<?>")+(2===t?"</svg>":3===t?"</math>":"")),a]})(e,t);if(this.el=re.createElement(l,i),ie.currentNode=this.el.content,2===t||3===t){const e=this.el.content.firstChild;e.replaceWith(...e.childNodes)}for(;null!==(a=ie.nextNode())&&o.length<s;){if(1===a.nodeType){if(a.hasAttributes())for(const e of a.getAttributeNames())if(e.endsWith(T)){const t=c[n++],i=a.getAttribute(e).split(P),s=/([.?@])?(.*)/.exec(t);o.push({type:1,index:r,name:s[2],strings:i,ctor:"."===s[1]?ce:"?"===s[1]?de:"@"===s[1]?he:le}),a.removeAttribute(e)}else e.startsWith(P)&&(o.push({type:6,index:r}),a.removeAttribute(e));if(G.test(a.tagName)){const e=a.textContent.split(P),t=e.length-1;if(t>0){a.textContent=M?M.emptyScript:"";for(let i=0;i<t;i++)a.append(e[i],O()),ie.nextNode(),o.push({type:2,index:++r});a.append(e[t],O())}}}else if(8===a.nodeType)if(a.data===N)o.push({type:2,index:r});else{let e=-1;for(;-1!==(e=a.data.indexOf(P,e+1));)o.push({type:7,index:r}),e+=P.length-1}r++}}static createElement(e,t){const i=D.createElement("template");return i.innerHTML=e,i}}function ne(e,t,i=e,a){if(t===Y)return t;let r=void 0!==a?i._$Co?.[a]:i._$Cl;const n=W(t)?void 0:t._$litDirective$;return r?.constructor!==n&&(r?._$AO?.(!1),void 0===n?r=void 0:(r=new n(e),r._$AT(e,i,a)),void 0!==a?(i._$Co??=[])[a]=r:i._$Cl=r),void 0!==r&&(t=ne(e,r._$AS(e,t.values),r,a)),t}class se{constructor(e,t){this._$AV=[],this._$AN=void 0,this._$AD=e,this._$AM=t}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(e){const{el:{content:t},parts:i}=this._$AD,a=(e?.creationScope??D).importNode(t,!0);ie.currentNode=a;let r=ie.nextNode(),n=0,s=0,o=i[0];for(;void 0!==o;){if(n===o.index){let t;2===o.type?t=new oe(r,r.nextSibling,this,e):1===o.type?t=new o.ctor(r,o.name,o.strings,this,e):6===o.type&&(t=new pe(r,this,e)),this._$AV.push(t),o=i[++s]}n!==o?.index&&(r=ie.nextNode(),n++)}return ie.currentNode=D,a}p(e){let t=0;for(const i of this._$AV)void 0!==i&&(void 0!==i.strings?(i._$AI(e,i,t),t+=i.strings.length-2):i._$AI(e[t])),t++}}class oe{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(e,t,i,a){this.type=2,this._$AH=ee,this._$AN=void 0,this._$AA=e,this._$AB=t,this._$AM=i,this.options=a,this._$Cv=a?.isConnected??!0}get parentNode(){let e=this._$AA.parentNode;const t=this._$AM;return void 0!==t&&11===e?.nodeType&&(e=t.parentNode),e}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(e,t=this){e=ne(this,e,t),W(e)?e===ee||null==e||""===e?(this._$AH!==ee&&this._$AR(),this._$AH=ee):e!==this._$AH&&e!==Y&&this._(e):void 0!==e._$litType$?this.$(e):void 0!==e.nodeType?this.T(e):(e=>R(e)||"function"==typeof e?.[Symbol.iterator])(e)?this.k(e):this._(e)}O(e){return this._$AA.parentNode.insertBefore(e,this._$AB)}T(e){this._$AH!==e&&(this._$AR(),this._$AH=this.O(e))}_(e){this._$AH!==ee&&W(this._$AH)?this._$AA.nextSibling.data=e:this.T(D.createTextNode(e)),this._$AH=e}$(e){const{values:t,_$litType$:i}=e,a="number"==typeof i?this._$AC(e):(void 0===i.el&&(i.el=re.createElement(ae(i.h,i.h[0]),this.options)),i);if(this._$AH?._$AD===a)this._$AH.p(t);else{const e=new se(a,this),i=e.u(this.options);e.p(t),this.T(i),this._$AH=e}}_$AC(e){let t=te.get(e.strings);return void 0===t&&te.set(e.strings,t=new re(e)),t}k(e){R(this._$AH)||(this._$AH=[],this._$AR());const t=this._$AH;let i,a=0;for(const r of e)a===t.length?t.push(i=new oe(this.O(O()),this.O(O()),this,this.options)):i=t[a],i._$AI(r),a++;a<t.length&&(this._$AR(i&&i._$AB.nextSibling,a),t.length=a)}_$AR(e=this._$AA.nextSibling,t){for(this._$AP?.(!1,!0,t);e!==this._$AB;){const t=H(e).nextSibling;H(e).remove(),e=t}}setConnected(e){void 0===this._$AM&&(this._$Cv=e,this._$AP?.(e))}}class le{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(e,t,i,a,r){this.type=1,this._$AH=ee,this._$AN=void 0,this.element=e,this.name=t,this._$AM=a,this.options=r,i.length>2||""!==i[0]||""!==i[1]?(this._$AH=Array(i.length-1).fill(new String),this.strings=i):this._$AH=ee}_$AI(e,t=this,i,a){const r=this.strings;let n=!1;if(void 0===r)e=ne(this,e,t,0),n=!W(e)||e!==this._$AH&&e!==Y,n&&(this._$AH=e);else{const a=e;let s,o;for(e=r[0],s=0;s<r.length-1;s++)o=ne(this,a[i+s],t,s),o===Y&&(o=this._$AH[s]),n||=!W(o)||o!==this._$AH[s],o===ee?e=ee:e!==ee&&(e+=(o??"")+r[s+1]),this._$AH[s]=o}n&&!a&&this.j(e)}j(e){e===ee?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,e??"")}}class ce extends le{constructor(){super(...arguments),this.type=3}j(e){this.element[this.name]=e===ee?void 0:e}}class de extends le{constructor(){super(...arguments),this.type=4}j(e){this.element.toggleAttribute(this.name,!!e&&e!==ee)}}class he extends le{constructor(e,t,i,a,r){super(e,t,i,a,r),this.type=5}_$AI(e,t=this){if((e=ne(this,e,t,0)??ee)===Y)return;const i=this._$AH,a=e===ee&&i!==ee||e.capture!==i.capture||e.once!==i.once||e.passive!==i.passive,r=e!==ee&&(i===ee||a);a&&this.element.removeEventListener(this.name,this,i),r&&this.element.addEventListener(this.name,this,e),this._$AH=e}handleEvent(e){"function"==typeof this._$AH?this._$AH.call(this.options?.host??this.element,e):this._$AH.handleEvent(e)}}class pe{constructor(e,t,i){this.element=e,this.type=6,this._$AN=void 0,this._$AM=t,this.options=i}get _$AU(){return this._$AM._$AU}_$AI(e){ne(this,e)}}const ge={I:oe},ue=V.litHtmlPolyfillSupport;ue?.(re,oe),(V.litHtmlVersions??=[]).push("3.3.3");const ve=globalThis;let me=class extends S{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){const e=super.createRenderRoot();return this.renderOptions.renderBefore??=e.firstChild,e}update(e){const t=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(e),this._$Do=((e,t,i)=>{const a=i?.renderBefore??t;let r=a._$litPart$;if(void 0===r){const e=i?.renderBefore??null;a._$litPart$=r=new oe(t.insertBefore(O(),e),e,void 0,i??{})}return r._$AI(e),r})(t,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return Y}};me._$litElement$=!0,me.finalized=!0,ve.litElementHydrateSupport?.({LitElement:me});const fe=ve.litElementPolyfillSupport;fe?.({LitElement:me}),(ve.litElementVersions??=[]).push("4.2.2");const _e=e=>(t,i)=>{void 0!==i?i.addInitializer(()=>{customElements.define(e,t)}):customElements.define(e,t)},ye={attribute:!0,type:String,converter:C,reflect:!1,hasChanged:E},be=(e=ye,t,i)=>{const{kind:a,metadata:r}=i;let n=globalThis.litPropertyMetadata.get(r);if(void 0===n&&globalThis.litPropertyMetadata.set(r,n=new Map),"setter"===a&&((e=Object.create(e)).wrapped=!0),n.set(i.name,e),"accessor"===a){const{name:a}=i;return{set(i){const r=t.get.call(this);t.set.call(this,i),this.requestUpdate(a,r,e,!0,i)},init(t){return void 0!==t&&this.C(a,void 0,e,t),t}}}if("setter"===a){const{name:a}=i;return function(i){const r=this[a];t.call(this,i),this.requestUpdate(a,r,e,!0,i)}}throw Error("Unsupported decorator location: "+a)};function we(e){return(t,i)=>"object"==typeof i?be(e,t,i):((e,t,i)=>{const a=t.hasOwnProperty(i);return t.constructor.createProperty(i,e),a?Object.getOwnPropertyDescriptor(t,i):void 0})(e,t,i)}function $e(e){return we({...e,state:!0,attribute:!1})}const ke=1,xe=2,Ae=3,Ce=4,Ee=e=>(...t)=>({_$litDirective$:e,values:t});let ze=class{constructor(e){}get _$AU(){return this._$AM._$AU}_$AT(e,t,i){this._$Ct=e,this._$AM=t,this._$Ci=i}_$AS(e,t){return this.update(e,t)}update(e,t){return this.render(...t)}};const{I:Se}=ge,Ve=e=>e,He=()=>document.createComment(""),Me=(e,t,i)=>{const a=e._$AA.parentNode,r=void 0===t?e._$AB:t._$AA;if(void 0===i){const t=a.insertBefore(He(),r),n=a.insertBefore(He(),r);i=new Se(t,n,e,e.options)}else{const t=i._$AB.nextSibling,n=i._$AM,s=n!==e;if(s){let t;i._$AQ?.(e),i._$AM=e,void 0!==i._$AP&&(t=e._$AU)!==n._$AU&&i._$AP(t)}if(t!==r||s){let e=i._$AA;for(;e!==t;){const t=Ve(e).nextSibling;Ve(a).insertBefore(e,r),e=t}}}return i},Le=(e,t,i=e)=>(e._$AI(t,i),e),Te={},Pe=(e,t=Te)=>e._$AH=t,Ne=e=>{e._$AR(),e._$AA.remove()},je=Ee(class extends ze{constructor(e){if(super(e),e.type!==Ae&&e.type!==ke&&e.type!==Ce)throw Error("The `live` directive is not allowed on child or event bindings");if(!(e=>void 0===e.strings)(e))throw Error("`live` bindings can only contain a single expression")}render(e){return e}update(e,[t]){if(t===Y||t===ee)return t;const i=e.element,a=e.name;if(e.type===Ae){if(t===i[a])return Y}else if(e.type===Ce){if(!!t===i.hasAttribute(a))return Y}else if(e.type===ke&&i.getAttribute(a)===t+"")return Y;return Pe(e),t}}),De=Symbol.for(""),Oe=e=>{if(e?.r===De)return e?._$litStatic$},We=(e,...t)=>({_$litStatic$:t.reduce((t,i,a)=>t+(e=>{if(void 0!==e._$litStatic$)return e._$litStatic$;throw Error(`Value passed to 'literal' function must be a 'literal' result: ${e}. Use 'unsafeStatic' to pass non-literal values, but\n            take care to ensure page security.`)})(i)+e[a+1],e[0]),r:De}),Re=new Map,Ie=(e=>(t,...i)=>{const a=i.length;let r,n;const s=[],o=[];let l,c=0,d=!1;for(;c<a;){for(l=t[c];c<a&&void 0!==(n=i[c],r=Oe(n));)l+=r+t[++c],d=!0;c!==a&&o.push(n),s.push(l),c++}if(c===a&&s.push(t[a]),d){const e=s.join("$$lit$$");void 0===(t=Re.get(e))&&(s.raw=s,Re.set(e,t=s)),i=o}return e(t,...i)})(X);function Fe(e){return"object"==typeof e&&null!==e&&"code"in e&&"message"in e}function Ue(e){return Fe(e)?e.message:String(e)}let Be=class extends me{constructor(){super(...arguments),this.open=!1,this.heading="",this.text="",this.confirmText="",this.cancelText="",this.confirmed=!1}render(){return X`
      <ha-dialog .open=${this.open} .headerTitle=${this.heading} @closed=${this.closed}>
        <p>${this.text}</p>
        <div slot="footer">
          <ha-button appearance="plain" @click=${this.cancel}>${this.cancelText}</ha-button>
          <ha-button variant="danger" @click=${this.confirm}>${this.confirmText}</ha-button>
        </div>
      </ha-dialog>
    `}confirm(){this.confirmed=!0,this.open=!1}cancel(){this.open=!1}closed(e){e.stopPropagation();const t=this.confirmed?"confirm":"cancel";this.confirmed=!1,this.open=!1,this.dispatchEvent(new CustomEvent(t))}};e([we({type:Boolean})],Be.prototype,"open",void 0),e([we()],Be.prototype,"heading",void 0),e([we()],Be.prototype,"text",void 0),e([we()],Be.prototype,"confirmText",void 0),e([we()],Be.prototype,"cancelText",void 0),Be=e([_e("kraftvakt-confirm-dialog")],Be);let qe=class extends me{constructor(){super(...arguments),this.running=!1,this.appearance="plain",this.disabled=!1,this.changing=!1}render(){return this.running?X`
          <ha-button
            variant="danger"
            appearance=${this.appearance}
            .disabled=${this.disabled||this.changing}
            @click=${this.toggle}
          >
            <ha-svg-icon slot="start" .path=${"M18,18H6V6H18V18Z"}></ha-svg-icon>
            ${this.localize("status.stop")}
          </ha-button>
        `:X`
          <ha-button .disabled=${this.disabled||this.changing} @click=${this.toggle}>
            <ha-svg-icon slot="start" .path=${"M8,5.14V19.14L19,12.14L8,5.14Z"}></ha-svg-icon>
            ${this.localize("status.start")}
          </ha-button>
        `}async toggle(){this.changing=!0,this.fireError(void 0);try{await(e=this.hass,t=!this.running,e.callWS({type:"kraftvakt/regulation/set_running",running:t}))}catch(e){this.fireError(Fe(e)&&"config_incomplete"===e.code?this.localize("status.start_refused"):this.localize("panel.error",{message:Ue(e)}))}finally{this.changing=!1}var e,t}fireError(e){this.dispatchEvent(new CustomEvent("running-error",{detail:e}))}static{this.styles=g`
    ha-button::part(base) {
      white-space: nowrap;
    }
  `}};e([we({attribute:!1})],qe.prototype,"hass",void 0),e([we({attribute:!1})],qe.prototype,"localize",void 0),e([we({type:Boolean})],qe.prototype,"running",void 0),e([we()],qe.prototype,"appearance",void 0),e([we({type:Boolean})],qe.prototype,"disabled",void 0),e([$e()],qe.prototype,"changing",void 0),qe=e([_e("kraftvakt-running-button")],qe);let Ke=class extends me{constructor(){super(...arguments),this.narrow=!1}render(){return X`
      <ha-alert alert-type="warning" .title=${this.localize("locked.title")} .narrow=${this.narrow}>
        <ha-svg-icon slot="icon" .path=${"M12,17A2,2 0 0,0 14,15C14,13.89 13.1,13 12,13A2,2 0 0,0 10,15A2,2 0 0,0 12,17M18,8A2,2 0 0,1 20,10V20A2,2 0 0,1 18,22H6A2,2 0 0,1 4,20V10C4,8.89 4.9,8 6,8H7V6A5,5 0 0,1 12,1A5,5 0 0,1 17,6V8H18M12,3A3,3 0 0,0 9,6V8H15V6A3,3 0 0,0 12,3Z"}></ha-svg-icon>
        ${this.localize("locked.text")}
        ${this.error?X`<div class="error">${this.error}</div>`:ee}
        <kraftvakt-running-button
          slot="action"
          .hass=${this.hass}
          .localize=${this.localize}
          running
          appearance="outlined"
          @running-error=${e=>this.error=e.detail}
        ></kraftvakt-running-button>
      </ha-alert>
    `}static{this.styles=g`
    :host {
      display: block;
      margin-bottom: 16px;
    }
    .error {
      margin-top: 8px;
      color: var(--error-color);
    }
  `}};e([we({attribute:!1})],Ke.prototype,"hass",void 0),e([we({attribute:!1})],Ke.prototype,"localize",void 0),e([we({type:Boolean})],Ke.prototype,"narrow",void 0),e([$e()],Ke.prototype,"error",void 0),Ke=e([_e("kraftvakt-locked-banner")],Ke);let Ze=class extends me{constructor(){super(...arguments),this.errorCount=0,this.saving=!1}render(){const e=this.errorCount>0?this.localize("config.fix_before_saving"):this.message;return X`
      <div class="bar" role="region" aria-label=${this.localize("config.unsaved")}>
        <div class="text">
          <div class="title">${this.localize("config.unsaved")}</div>
          ${e?X`<div class="error">${e}</div>`:ee}
        </div>
        <ha-button appearance="plain" .disabled=${this.saving} @click=${()=>this.fire("discard")}>
          ${this.localize("config.discard")}
        </ha-button>
        <ha-button .disabled=${this.saving||this.errorCount>0} @click=${()=>this.fire("save")}>
          <ha-svg-icon slot="start" .path=${"M15,9H5V5H15M12,19A3,3 0 0,1 9,16A3,3 0 0,1 12,13A3,3 0 0,1 15,16A3,3 0 0,1 12,19M17,3H5C3.89,3 3,3.9 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V7L17,3Z"}></ha-svg-icon>
          ${this.localize("config.save")}
        </ha-button>
      </div>
    `}fire(e){this.dispatchEvent(new CustomEvent(e))}static{this.styles=g`
    :host {
      display: block;
      position: sticky;
      bottom: 0;
      z-index: 2;
      padding: 8px 0 16px;
    }
    .bar {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px;
      padding: 8px 8px 8px 16px;
      border-radius: var(--ha-card-border-radius, 12px);
      background: var(--card-background-color);
      box-shadow: var(--ha-card-box-shadow, 0 2px 8px rgba(0, 0, 0, 0.25));
      border: 1px solid var(--divider-color);
    }
    .text {
      flex: 1;
      min-width: 160px;
    }
    .title {
      font-weight: 500;
    }
    .error {
      color: var(--error-color);
      font-size: var(--ha-font-size-s, 12px);
    }
  `}};e([we({attribute:!1})],Ze.prototype,"localize",void 0),e([we({type:Number})],Ze.prototype,"errorCount",void 0),e([we({type:Boolean})],Ze.prototype,"saving",void 0),e([we()],Ze.prototype,"message",void 0),Ze=e([_e("kraftvakt-save-bar")],Ze);const Ge="draft-changed";function Je(){const e=crypto.getRandomValues(new Uint8Array(6));return Array.from(e,e=>e.toString(16).padStart(2,"0")).join("")}function Xe(e,t,i){const a=[...e],[r]=a.splice(t,1);return a.splice(i,0,r),a}function Qe(e){return"ev_charging"===e.type?"ev_charging":`${e.appliance_id}/${e.variant_id??""}`}function Ye(e){const t=function(e){const t=e.appliances.flatMap(e=>[{type:"appliance",appliance_id:e.id,variant_id:null},...e.variants.map(t=>({type:"appliance",appliance_id:e.id,variant_id:t.id}))]);e.charging.enabled&&t.push({type:"ev_charging"});return t}(e),i=new Set(t.map(Qe)),a=new Set,r=e.priority.filter(e=>{const t=Qe(e);return!(!i.has(t)||a.has(t))&&(a.add(t),!0)}),n=t.filter(e=>!a.has(Qe(e)));return{...e,priority:[...r,...n]}}const et={en:{panel:{title:"Kraftvakt",not_loaded:"Kraftvakt is not loaded. Check the integration under Settings → Devices & services.",error:"Something went wrong: {message}"},tabs:{status:"Status",general:"General",appliances:"Appliances",charging:"EV charging",advanced:"Advanced"},status:{regulation:"Regulation",running:"Running",stopped:"Stopped",start:"Start regulation",stop:"Stop regulation",stopped_info:"The regulation is stopped, and all regulated appliances and EV chargers are turned off. The configuration can be changed. When the regulation starts, the appliances are turned on again one by one.",incomplete_title:"The configuration is not complete",start_refused:"The regulation cannot start before the configuration is complete.",safe_state_title:"Safe state",safe_state_text:"The power sensor {sensor} gives no valid measurement. All regulated appliances and EV chargers are turned off. The regulation starts again by itself when the sensor gives a valid value again.",penalty_title:"Penalty period",penalty_text:"The average consumption has been above the power limit. All regulated appliances and EV chargers are kept off until the overconsumption is recovered.",overconsumption_left:"Overconsumption left: {energy} kWh",recovery_started:"recovery has started",recovery_not_started:"recovery has not started",regulation_average:"Regulation average",capacity_average:"Average consumption",average_over_seconds:"over {seconds} s",average_over_hour:"over 1 hour",power_now:"Consumption now",momentary:"momentary value",power_limit:"Power limit",safe_state_chip:"Safe state",safe_state_back_text:"The power sensor {sensor} gives a valid value again. The regulation starts again with everything off at the next decision.",penalty_chip:"Penalty period",next_decision:"Next decision",next_decision_at:"Next decision at {time}",priority_list:"Priority list",ev_charging:"EV charging",no_chargers:"No EV chargers are configured.",no_appliances:"No appliances are configured.",on:"On",off:"Off",activated:"Activated",deactivated:"Deactivated",waiting_ends_at:"Turns on at the decision at {time}",delayed_turn_on:"Delayed turn-on",charging_at:"Charging at {current}A",first_decision:"Waiting for the first decision",bypassed:"Bypassed: not charging",bypassed_no_car:"Bypassed: no car connected",waiting_charger:"Waiting: another EV charger is charging",excluded:"Excluded from the regulation",outside_window:"Outside the charging window ({start}–{end})",next_ampere_at:"One more ampere at the decision at {time}",amperes:"{current} A",chargers_charging:"{charging} of {total} EV chargers are charging",activated_not_charging:"Activated, but not charging yet",window_overridden:"The charging window is overridden",chip_charging:"Charging",chip_not_charging:"Not charging",chip_no_car:"No car connected",chip_queued:"Queued",chip_excluded:"Excluded",chip_window:"{start}–{end}",chip_override:"Override",chip_first_decision:"First decision",free_power:"{power} kW ({share}) free",power_runs_out:"The power runs out here. What is below waits for free power."},missing:{missing_power_sensor:"The power sensor is not chosen.",missing_entity:"{item}: the entity is not chosen.",missing_action:"{item}: the action to {action} is missing.",missing_actively_charging:"{item}: «actively charging» is missing.",missing_car_connected:"{item}: «car connected» is missing. It is required when only one EV charger may charge at a time.",unknown:"{item}: {code}",appliance_without_entity:"An appliance without an entity",charger_without_entity:"An EV charger without an entity",actions:{turn_on:"turn it on",turn_off:"turn it off",activate:"activate it",deactivate:"deactivate it",set_current:"set the charging current"}},config:{save:"Save",discard:"Discard",unsaved:"Unsaved changes",fix_before_saving:"Fix the marked settings before saving.",not_saved:"The configuration was not saved. Fix the marked settings.",save_refused_running:"The configuration cannot be saved while the regulation runs.",leave_title:"Discard unsaved changes?",leave_text:"The changes on the configuration pages are not saved. They are lost if you leave.",stay:"Keep editing",leave:"Discard changes"},locked:{title:"The configuration is locked",text:"The regulation runs. Stop the regulation to change the configuration. When the regulation stops, all regulated appliances and EV chargers are turned off."},warning:{appliances_title:"Do not turn regulated appliances on or off outside Kraftvakt",chargers_title:"Do not turn EV chargers on or off outside Kraftvakt",text:"Manual control and automations can disturb the regulation, affect appliances with higher priority and trigger a penalty."},errors:{required:"Required.",car_connected_required:"Required when only one EV charger may charge at a time.",out_of_range:"Must be between {min} and {max}.",at_least:"Must be at least {min}.",invalid_resolution:"Must be in steps of {step}.",not_integer:"Must be a whole number.",invalid_entity_id:"Not a valid entity ID.",empty_label:"The label cannot be empty.",duplicate_label:"The label must be unique for the appliance.",min_current_above_max:"The minimum current cannot be above the maximum current.",invalid_time:"Give both start and end.",window_start_equals_end:"Start and end cannot be the same.",duplicate_entity:"The entity is already used by another appliance or EV charger.",invalid_action:"Home Assistant cannot read the action.",invalid_template:"The template has a syntax error.",default_action_unavailable:"The entity has no standard action. Choose a custom action.",unsupported_entity_domain:"The entity cannot be used. Choose a number entity.",domain_action_unavailable:"The action is not available for the entity. Choose another action.",unsupported_option:"The entity does not support this value.",outside_entity_range:"Outside the range of the entity.",unknown:"Invalid value ({code})."},dialog:{ok:"OK",cancel:"Cancel",close:"Close"},general:{measurement:"Measurement",regulation:"Regulation",penalty:"Penalty",capacity_window_info:"The capacity window is fixed at one hour and cannot be changed.",interval_option:"{count} × the regulation window",fields:{power_sensor:{label:"Power sensor",helper:"The sensor that measures the total power of the house, in W or kW."},regulation_window_s:{label:"Regulation window",helper:"The period the regulation average is calculated over. {min}–{max} s, default {default} s."},power_limit_w:{label:"Power limit",helper:"The highest allowed average consumption per hour. {min}–{max} W, default {default} W."},turn_on_margin_w:{label:"Turn-on margin",helper:"How far below the power limit the regulation average must be before an appliance is turned on. {min}–{max} W, default {default} W."},regulation_interval:{label:"Regulation interval",helper:"A decision every {seconds} seconds. Default {default} ×."},wait_at_limit_s:{label:"Waiting time at the power limit",helper:"How long an appliance waits before it is turned on when the regulation average is at the power limit. Shorter when the average is lower. {min}–{max} s, default {default} s."},penalty_threshold_w:{label:"Penalty threshold",helper:"How much the average consumption may exceed the power limit before a penalty starts. {min}–{max} W, default {default} W."},wait_curve_steepness:{label:"Steepness"},wait_curve_pivot:{label:"Pivot point"},appliance_cycling_step_factor:{label:"Step",helper:"How much the waiting time grows each time, as a share of the waiting time at the power limit. Default × {default}."},appliance_cycling_steps:{label:"Number of steps",helper:"How many times the waiting time grows. {min}–{max}, default {default}."},charger_cycling_step_factor:{label:"Step",helper:"How much the waiting time grows each time, as a share of the waiting time at the power limit. Default × {default}."},charger_cycling_steps:{label:"Number of steps",helper:"How many times the waiting time grows. {min}–{max}, default {default}."}}},advanced:{wait_curve:"Waiting time curve",wait_curve_info:"How much of the waiting time at the power limit an appliance waits, by how much power is free: the power limit minus the regulation average. The appliance is turned on at the first decision after the waiting time, so the actual waiting time is rounded up to the regulation interval.",free_power_kw:"Free power kW",waiting_minutes:"Waiting time min:s",actual_waiting_minutes:"Actual waiting time min:s",cycling:"Waiting time on repeated turn-on",cycling_info:"When the regulation turns the same appliance, or one more ampere for an EV charger, on over and over again, because it has to be switched off again each time and nothing else is switched in between, the waiting time grows. The first two times, the waiting time follows the curve. After that, it is the waiting time at the power limit, and it grows by one step each time until the number of steps is reached. For the first two, the table shows the waiting time at the pivot point.",turn_on_in_a_row:"Turn-on in a row",appliances:"Appliances",chargers:"EV chargers"},list:{drag:"Drag to change the order",edit:"Edit",view:"Show"},appliances:{priority_title:"Priority list",priority_sub:"Top = highest priority, turned off last",add:"Add appliance",empty:"No appliances yet. Add the appliances Kraftvakt may turn off when the consumption is too high.",ev_charging:"EV charging",ev_charging_sub:"EV chargers: {count} · configured under",power_reserve:"power reserve {power} W",variant_count:"variants: {count}",variant_entity:"Variant · entity {entity}",variant_template:"Variant · template"},appliance:{add_title:"Add appliance",edit_title:"Edit appliance",view_title:"Appliance",actions:"Actions",variants:"Variants",variants_info:"A variant gives the appliance another place in the priority list while its expression is true. The top true expression applies. A new variant is put at the bottom of the priority list.",add_variant:"Add variant",remove_variant:"Remove variant",delete:"Delete appliance",fields:{entity_id:{label:"Entity",helper:"The name in Home Assistant becomes the name of the appliance. The entity is available as entity_id and entity (the state object) in templates and actions."},turn_on:{label:"Turn on"},turn_off:{label:"Turn off"},power_reserve_w:{label:"Power reserve (optional)",helper:"Free power that must be available before the appliance is turned on. Use it for appliances that draw a lot as soon as they are turned on."},label:{label:"Label"}}},action:{default:"Standard",custom:"Custom",entity:"Entity",domain_actions:{climate_hvac_mode:"HVAC mode",climate_temperature:"Temperature",climate_hvac_mode_and_temperature:"HVAC mode and temperature"},default_runs:"Runs {service} for the entity.",entity_runs:"Runs {service} for the chosen entity with the current as value.",no_default:"The entity type has no standard action, so the action must be custom.",choose_entity:"Choose the entity to use the standard action.",choose_action_entity:"Choose the entity to set the value of.",variables:"Variables: {variables}.",parameters:{hvac_mode:"HVAC mode",temperature:"Target temperature"},parameter_range:"{min}–{max} {unit} for the entity."},condition:{none:"Not set",entity:"Entity",template:"Template",entity_label:"Boolean entity",template_label:"Template",entity_helper:"True only when the entity is on. Unavailable counts as false.",template_helper:"True only when the template gives the boolean value true. Variables: entity_id, entity.",now:"Now: {value}",true:"true",false:"false",error:"Error: {message}",not_boolean:"The template gives {value}, which is not true or false, so it counts as false."},actively_charging:{power_sensor:"Charging power",entity:"Entity",template:"Template",power_sensor_label:"Sensor for charging power",entity_label:"Boolean entity",template_label:"Template",power_sensor_helper:"Above 100 W, in W or kW, counts as charging. Unavailable counts as charging.",entity_helper:"Off counts as not charging. On and unavailable count as charging.",template_helper:"Only the boolean value false counts as not charging. Anything else, also an error, counts as charging. Variables: entity_id, entity.",true:"charging",false:"not charging",not_boolean:"The template gives {value}, which is not true or false, so it counts as charging."},charging:{shared:"Shared settings",enabled:"EV charging control",enabled_sub:"When it is off, the EV chargers are left to themselves and «EV charging» is removed from the priority list.",one_at_a_time:"One EV charger at a time",one_at_a_time_sub:"An EV charger that charges may continue until the car is full or disconnected. The others wait.",disabled_info:"EV charging control is off. The EV chargers below are kept, but Kraftvakt sends no commands to them.",chargers:"EV chargers",chargers_sub:"Charging priority, highest at the top",add:"Add EV charger",empty:"No EV chargers yet.",switches_info:"For each EV charger Kraftvakt makes two switches that can also be used while the regulation runs: «‹charger› excluded from regulation» and «‹charger› override charging window».",currents:"{min}–{max} A",reserve:"reserve {power} W",window:"charging window {start}–{end}",always_allowed:"always allowed to charge",car_from:"car connected from {source}",car_template:"car connected from a template",charging_from:"actively charging from {source}",charging_template:"actively charging from a template"},charger:{add_title:"Add EV charger",edit_title:"Edit EV charger",view_title:"EV charger",allowed_charging:"Allowed charging",charging_current:"Charging current",actively_charging:"Actively charging",minimum_first:"The charging current is always set to the minimum before the EV charger is activated or deactivated.",car_connected_required:"Car connected",car_connected_optional:"Car connected (optional)",delete:"Delete EV charger",fields:{entity_id:{label:"Entity for allowed charging",helper:"Normally the charger's switch for allowing charging. The name in Home Assistant becomes the name of the EV charger. The entity is available as entity_id and entity in templates and actions."},activate:{label:"Activate"},deactivate:{label:"Deactivate"},min_current_a:{label:"Minimum charging current"},max_current_a:{label:"Maximum charging current",helper:"Whole amperes. The minimum cannot be above the maximum."},set_current:{label:"Set charging current"},power_reserve_w:{label:"Power reserve",helper:"The power the EV charger draws when charging starts at the minimum current. {min}–{max} W, default {default} W (about 6 A on three phases, 400 V)."},car_connected:{helper:"The car counts as connected only when the value is true. Unavailable counts as not connected."},actively_charging:{helper:"How Kraftvakt sees that the car is charging. Without evidence that it is not charging, for example an unavailable entity or a template that fails, it counts as charging."},charging_window:{label:"Charging window (optional)",helper:"Can span midnight. Start and end cannot be the same. Without a charging window, the EV charger is always allowed to charge."},start:{label:"Start"},end:{label:"End"}}}},nb:{panel:{title:"Kraftvakt",not_loaded:"Kraftvakt er ikke lastet. Sjekk integrasjonen under Innstillinger → Enheter og tjenester.",error:"Noe gikk galt: {message}"},tabs:{status:"Status",general:"Generelt",appliances:"Apparater",charging:"Billading",advanced:"Avansert"},status:{regulation:"Regulering",running:"Kjører",stopped:"Stoppet",start:"Start regulering",stop:"Stopp regulering",stopped_info:"Reguleringen er stoppet, og alle regulerte apparater og elbilladere er slått av. Konfigurasjonen kan endres. Når reguleringen startes, slås apparatene på igjen ett og ett.",incomplete_title:"Konfigurasjonen er ikke fullstendig",start_refused:"Reguleringen kan ikke startes før konfigurasjonen er fullstendig.",safe_state_title:"Sikker tilstand",safe_state_text:"Effektsensoren {sensor} gir ingen gyldig måling. Alle regulerte apparater og elbilladere er slått av. Reguleringen starter på nytt av seg selv når sensoren gir en gyldig verdi igjen.",penalty_title:"Straffeperiode pågår",penalty_text:"Snittforbruket har vært over effektgrensen. Alle regulerte apparater og elbilladere holdes av til overforbruket er hentet inn.",overconsumption_left:"Overforbruk igjen: {energy} kWh",recovery_started:"innhenting har startet",recovery_not_started:"innhenting har ikke startet",regulation_average:"Reguleringssnitt",capacity_average:"Snittforbruk",average_over_seconds:"over {seconds} s",average_over_hour:"over 1 time",power_now:"Forbruk nå",momentary:"øyeblikksverdi",power_limit:"Effektgrense",safe_state_chip:"Sikker tilstand",safe_state_back_text:"Effektsensoren {sensor} gir en gyldig verdi igjen. Reguleringen starter på nytt med alt avslått ved neste avgjørelse.",penalty_chip:"Straffeperiode",next_decision:"Neste avgjørelse",next_decision_at:"Neste avgjørelse kl. {time}",priority_list:"Prioritetsliste",ev_charging:"Elbillading",no_chargers:"Ingen elbilladere er konfigurert.",no_appliances:"Ingen apparater er konfigurert.",on:"På",off:"Av",activated:"Aktivert",deactivated:"Deaktivert",waiting_ends_at:"Slås på ved avgjørelsen kl. {time}",delayed_turn_on:"Forsinket innkobling",charging_at:"Lader med {current}A",first_decision:"Venter på første avgjørelse",bypassed:"Forbigått: lader ikke",bypassed_no_car:"Forbigått: ingen bil tilkoblet",waiting_charger:"Ventende: en annen elbillader lader",excluded:"Utenfor regulering",outside_window:"Utenfor ladetidsrom ({start}–{end})",next_ampere_at:"Én ampere til ved avgjørelsen kl. {time}",amperes:"{current} A",chargers_charging:"{charging} av {total} elbilladere lader",activated_not_charging:"Aktivert, men lader ikke ennå",window_overridden:"Ladetidsrommet er overstyrt",chip_charging:"Lader",chip_not_charging:"Lader ikke",chip_no_car:"Ingen bil tilkoblet",chip_queued:"Ventende",chip_excluded:"Utenfor regulering",chip_window:"{start}–{end}",chip_override:"Overstyrt",chip_first_decision:"Første avgjørelse",free_power:"{power} kW ({share}) ledig",power_runs_out:"Her er effekten brukt opp. Det som står under, venter på ledig effekt."},missing:{missing_power_sensor:"Effektsensor er ikke valgt.",missing_entity:"{item}: entitet er ikke valgt.",missing_action:"{item}: handling for å {action} mangler.",missing_actively_charging:"{item}: «lader aktivt» mangler.",missing_car_connected:"{item}: «bil tilkoblet» mangler. Den er påkrevd når bare én elbillader kan lade om gangen.",unknown:"{item}: {code}",appliance_without_entity:"Et apparat uten entitet",charger_without_entity:"En elbillader uten entitet",actions:{turn_on:"slå på",turn_off:"slå av",activate:"aktivere",deactivate:"deaktivere",set_current:"sette ladestrøm"}},config:{save:"Lagre",discard:"Forkast",unsaved:"Ulagrede endringer",fix_before_saving:"Rett de merkede innstillingene før du lagrer.",not_saved:"Konfigurasjonen ble ikke lagret. Rett de merkede innstillingene.",save_refused_running:"Konfigurasjonen kan ikke lagres mens reguleringen kjører.",leave_title:"Forkaste ulagrede endringer?",leave_text:"Endringene på konfigurasjonssidene er ikke lagret. De går tapt hvis du går videre.",stay:"Fortsett å redigere",leave:"Forkast endringer"},locked:{title:"Konfigurasjonen er låst",text:"Reguleringen kjører. Stopp reguleringen for å endre konfigurasjonen. Når reguleringen stoppes, slås alle regulerte apparater og elbilladere av."},warning:{appliances_title:"Ikke slå regulerte apparater av eller på utenom Kraftvakt",chargers_title:"Ikke slå elbilladere av eller på utenom Kraftvakt",text:"Manuell styring og automasjoner kan forstyrre reguleringen, gå ut over apparater med høyere prioritet og utløse straff."},errors:{required:"Påkrevd.",car_connected_required:"Påkrevd når bare én elbillader kan lade om gangen.",out_of_range:"Må være mellom {min} og {max}.",at_least:"Må være minst {min}.",invalid_resolution:"Må være i steg på {step}.",not_integer:"Må være et helt tall.",invalid_entity_id:"Ikke en gyldig entitets-ID.",empty_label:"Merkelappen kan ikke være tom.",duplicate_label:"Merkelappen må være unik for apparatet.",min_current_above_max:"Minste ladestrøm kan ikke være større enn største.",invalid_time:"Angi både start og slutt.",window_start_equals_end:"Start og slutt kan ikke være like.",duplicate_entity:"Entiteten brukes allerede av et annet apparat eller en elbillader.",invalid_action:"Home Assistant kan ikke lese handlingen.",invalid_template:"Malen har en syntaksfeil.",default_action_unavailable:"Entiteten har ingen standardhandling. Velg egendefinert handling.",unsupported_entity_domain:"Entiteten kan ikke brukes. Velg en tallentitet.",domain_action_unavailable:"Handlingen er ikke tilgjengelig for entiteten. Velg en annen handling.",unsupported_option:"Entiteten støtter ikke denne verdien.",outside_entity_range:"Utenfor området til entiteten.",unknown:"Ugyldig verdi ({code})."},dialog:{ok:"OK",cancel:"Avbryt",close:"Lukk"},general:{measurement:"Måling",regulation:"Regulering",penalty:"Straff",capacity_window_info:"Kapasitetsvinduet er fast én time og kan ikke endres.",interval_option:"{count} × reguleringsvinduet",fields:{power_sensor:{label:"Effektsensor",helper:"Sensoren som måler husets totale momentane effekt, i W eller kW."},regulation_window_s:{label:"Reguleringsvindu",helper:"Tidsrommet reguleringssnittet beregnes over. {min}–{max} s, standard {default} s."},power_limit_w:{label:"Effektgrense",helper:"Høyeste tillatte snittforbruk per time. {min}–{max} W, standard {default} W."},turn_on_margin_w:{label:"Innkoblingsmargin",helper:"Hvor langt under effektgrensen reguleringssnittet må være før et apparat slås på. {min}–{max} W, standard {default} W."},regulation_interval:{label:"Reguleringsintervall",helper:"Avgjørelse hvert {seconds}. sekund. Standard {default} ×."},wait_at_limit_s:{label:"Ventetid ved effektgrensen",helper:"Hvor lenge et apparat venter før det slås på når reguleringssnittet er ved effektgrensen. Kortere når snittet er lavere. {min}–{max} s, standard {default} s."},penalty_threshold_w:{label:"Straffeterskel",helper:"Hvor mye snittforbruket kan overstige effektgrensen før straff starter. {min}–{max} W, standard {default} W."},wait_curve_steepness:{label:"Bratthet"},wait_curve_pivot:{label:"Vendepunkt"},appliance_cycling_step_factor:{label:"Steg",helper:"Hvor mye ventetiden øker hver gang, som andel av ventetiden ved effektgrensen. Standard × {default}."},appliance_cycling_steps:{label:"Antall steg",helper:"Hvor mange ganger ventetiden øker. {min}–{max}, standard {default}."},charger_cycling_step_factor:{label:"Steg",helper:"Hvor mye ventetiden øker hver gang, som andel av ventetiden ved effektgrensen. Standard × {default}."},charger_cycling_steps:{label:"Antall steg",helper:"Hvor mange ganger ventetiden øker. {min}–{max}, standard {default}."}}},advanced:{wait_curve:"Ventetidskurve",wait_curve_info:"Hvor stor del av ventetiden ved effektgrensen et apparat venter, etter hvor mye effekt som er ledig: effektgrensen minus reguleringssnittet. Apparatet slås på ved første avgjørelse etter ventetiden, så reell ventetid er rundet opp til reguleringsintervallet.",free_power_kw:"Ledig effekt kW",waiting_minutes:"Ventetid min:s",actual_waiting_minutes:"Reell ventetid min:s",cycling:"Ventetid ved gjentatt innkobling",cycling_info:"Når reguleringen slår på det samme apparatet, eller én ampere til for en elbillader, gang på gang, fordi det må slås av igjen hver gang og ingenting annet slås av eller på imellom, øker ventetiden. De to første gangene følger ventetiden kurven. Deretter er den lik ventetiden ved effektgrensen, og den øker med ett steg hver gang til antall steg er nådd. For de to første viser tabellen ventetiden ved vendepunktet.",turn_on_in_a_row:"Innkobling på rad",appliances:"Apparater",chargers:"Elbilladere"},list:{drag:"Dra for å endre rekkefølgen",edit:"Rediger",view:"Vis"},appliances:{priority_title:"Prioritetsliste",priority_sub:"Øverst = høyest prioritet, slås av sist",add:"Legg til apparat",empty:"Ingen apparater ennå. Legg til apparatene Kraftvakt kan slå av når forbruket blir for høyt.",ev_charging:"Elbillading",ev_charging_sub:"elbilladere: {count} · konfigureres under",power_reserve:"effektreserve {power} W",variant_count:"varianter: {count}",variant_entity:"Variant · entitet {entity}",variant_template:"Variant · mal"},appliance:{add_title:"Legg til apparat",edit_title:"Rediger apparat",view_title:"Apparat",actions:"Handlinger",variants:"Varianter",variants_info:"En variant gir apparatet en annen plass i prioritetslisten mens uttrykket er sant. Det øverste sanne uttrykket gjelder. En ny variant legges nederst i prioritetslisten.",add_variant:"Legg til variant",remove_variant:"Fjern variant",delete:"Slett apparat",fields:{entity_id:{label:"Entitet",helper:"Navnet i Home Assistant blir apparatets navn. Entiteten er tilgjengelig som entity_id og entity (tilstandsobjektet) i maler og handlinger."},turn_on:{label:"Slå på"},turn_off:{label:"Slå av"},power_reserve_w:{label:"Effektreserve (valgfri)",helper:"Ledig effekt som må finnes før apparatet slås på. Bruk den for apparater som trekker mye straks de slås på."},label:{label:"Merkelapp"}}},action:{default:"Standard",custom:"Egendefinert",entity:"Entitet",domain_actions:{climate_hvac_mode:"HVAC-modus",climate_temperature:"Temperatur",climate_hvac_mode_and_temperature:"HVAC-modus og temperatur"},default_runs:"Kjører {service} for entiteten.",entity_runs:"Kjører {service} for den valgte entiteten med ladestrømmen som verdi.",no_default:"Entitetstypen har ingen standardhandling, så handlingen må være egendefinert.",choose_entity:"Velg entitet for å bruke standardhandlingen.",choose_action_entity:"Velg entiteten som skal få verdien.",variables:"Variabler: {variables}.",parameters:{hvac_mode:"HVAC-modus",temperature:"Måltemperatur"},parameter_range:"{min}–{max} {unit} for entiteten."},condition:{none:"Ikke angitt",entity:"Entitet",template:"Mal",entity_label:"Boolsk entitet",template_label:"Mal",entity_helper:"Sann bare når entiteten er på. Utilgjengelig regnes som usann.",template_helper:"Sann bare når malen gir den boolske verdien sann. Variabler: entity_id, entity.",now:"Nå: {value}",true:"sann",false:"usann",error:"Feil: {message}",not_boolean:"Malen gir {value}, som ikke er sann eller usann, og regnes derfor som usann."},actively_charging:{power_sensor:"Ladeeffekt",entity:"Entitet",template:"Mal",power_sensor_label:"Sensor for ladeeffekt",entity_label:"Boolsk entitet",template_label:"Mal",power_sensor_helper:"Over 100 W, i W eller kW, regnes som lading. Utilgjengelig regnes som lading.",entity_helper:"Av regnes som ikke lading. På og utilgjengelig regnes som lading.",template_helper:"Bare den boolske verdien usann regnes som ikke lading. Alt annet, også en feil, regnes som lading. Variabler: entity_id, entity.",true:"lader",false:"lader ikke",not_boolean:"Malen gir {value}, som ikke er sann eller usann, og regnes derfor som lading."},charging:{shared:"Felles innstillinger",enabled:"Billadestyring",enabled_sub:"Når den er av, overlates elbilladerne til seg selv og «Elbillading» fjernes fra prioritetslisten.",one_at_a_time:"Én elbillader om gangen",one_at_a_time_sub:"En elbillader som lader, får fortsette til bilen er fulladet eller koblet fra. Andre venter.",disabled_info:"Billadestyring er av. Elbilladerne nedenfor beholdes, men Kraftvakt sender ingen kommandoer til dem.",chargers:"Elbilladere",chargers_sub:"Ladeprioritering, høyest øverst",add:"Legg til elbillader",empty:"Ingen elbilladere ennå.",switches_info:"For hver elbillader lager Kraftvakt to brytere som kan brukes også mens reguleringen kjører: «‹lader› utenfor regulering» og «‹lader› overstyr ladetidsrom».",currents:"{min}–{max} A",reserve:"reserve {power} W",window:"ladetidsrom {start}–{end}",always_allowed:"alltid lov til å lade",car_from:"bil tilkoblet fra {source}",car_template:"bil tilkoblet fra mal",charging_from:"lader aktivt fra {source}",charging_template:"lader aktivt fra mal"},charger:{add_title:"Legg til elbillader",edit_title:"Rediger elbillader",view_title:"Elbillader",allowed_charging:"Tillatt lading",charging_current:"Ladestrøm",actively_charging:"Lader aktivt",minimum_first:"Ladestrømmen settes alltid til minste ladestrøm før elbilladeren aktiveres eller deaktiveres.",car_connected_required:"Bil tilkoblet",car_connected_optional:"Bil tilkoblet (valgfri)",delete:"Slett elbillader",fields:{entity_id:{label:"Entitet for tillatt lading",helper:"Normalt laderens bryter for å tillate lading. Navnet i Home Assistant blir elbilladerens navn. Entiteten er tilgjengelig som entity_id og entity i maler og handlinger."},activate:{label:"Aktiver"},deactivate:{label:"Deaktiver"},min_current_a:{label:"Minste ladestrøm"},max_current_a:{label:"Største ladestrøm",helper:"Hele ampere. Minste kan ikke være større enn største."},set_current:{label:"Sett ladestrøm"},power_reserve_w:{label:"Effektreserve",helper:"Effekten elbilladeren trekker når lading starter på minste ladestrøm. {min}–{max} W, standard {default} W (ca. 6 A på tre faser, 400 V)."},car_connected:{helper:"Bilen regnes som tilkoblet bare når verdien er sann. Utilgjengelig regnes som ikke tilkoblet."},actively_charging:{helper:"Hvordan Kraftvakt ser at bilen lader. Uten bevis for at den ikke lader, for eksempel en utilgjengelig entitet eller en mal som feiler, regnes den som ladende."},charging_window:{label:"Ladetidsrom (valgfritt)",helper:"Kan gå over midnatt. Start og slutt kan ikke være like. Uten ladetidsrom har elbilladeren alltid lov til å lade."},start:{label:"Start"},end:{label:"Slutt"}}}}};function tt(e){const t=et[e]??et[e.split("-")[0]]??et.en;return(e,i={})=>(it(t,e)??it(et.en,e)??e).replace(/\{(\w+)\}/g,(e,t)=>t in i?String(i[t]):e)}function it(e,t){let i=e;for(const e of t.split("."))i=i?.[e];return"string"==typeof i?i:void 0}const at=["status","general","appliances","charging","advanced"],rt="/kraftvakt";function nt(e,t={}){const i=`${rt}/${e}`;t.replace?history.replaceState(null,"",i):history.pushState(null,"",i),window.dispatchEvent(new CustomEvent("location-changed",{detail:{replace:t.replace??!1}}))}function st(e,t,i){return new Intl.NumberFormat(e,{minimumFractionDigits:i,maximumFractionDigits:i}).format(t)}function ot(e,t){return null===t?"–":st(e,t/1e3,2)}function lt(e){if(null===e)return"–";const t=Math.round(e);return`${Math.floor(t/60)}:${String(t%60).padStart(2,"0")}`}function ct(e,t){return new Intl.NumberFormat(e,{style:"percent",maximumFractionDigits:0}).format(t)}function dt(e,t){return new Date(t).toLocaleTimeString(e)}function ht(e){return Math.min(1,Math.max(0,(e-.5)/.5))}function pt(e,t){const i=Math.min(ht(t/100),.8**(1/e)*.999)**e,a=i*(1-.8)/(.8-i);return t=>{const i=ht(t)**e;return 0===i?0:i*(1+a)/(i+a)}}const gt=(e,t,i)=>{const a=new Map;for(let r=t;r<=i;r++)a.set(e[r],r);return a},ut=Ee(class extends ze{constructor(e){if(super(e),e.type!==xe)throw Error("repeat() can only be used in text expressions")}dt(e,t,i){let a;void 0===i?i=t:void 0!==t&&(a=t);const r=[],n=[];let s=0;for(const t of e)r[s]=a?a(t,s):s,n[s]=i(t,s),s++;return{values:n,keys:r}}render(e,t,i){return this.dt(e,t,i).values}update(e,[t,i,a]){const r=(e=>e._$AH)(e),{values:n,keys:s}=this.dt(t,i,a);if(!Array.isArray(r))return this.ut=s,n;const o=this.ut??=[],l=[];let c,d,h=0,p=r.length-1,g=0,u=n.length-1;for(;h<=p&&g<=u;)if(null===r[h])h++;else if(null===r[p])p--;else if(o[h]===s[g])l[g]=Le(r[h],n[g]),h++,g++;else if(o[p]===s[u])l[u]=Le(r[p],n[u]),p--,u--;else if(o[h]===s[u])l[u]=Le(r[h],n[u]),Me(e,l[u+1],r[h]),h++,u--;else if(o[p]===s[g])l[g]=Le(r[p],n[g]),Me(e,r[h],r[p]),p--,g++;else if(void 0===c&&(c=gt(s,g,u),d=gt(o,h,p)),c.has(o[h]))if(c.has(o[p])){const t=d.get(s[g]),i=void 0!==t?r[t]:null;if(null===i){const t=Me(e,r[h]);Le(t,n[g]),l[g]=t}else l[g]=Le(i,n[g]),Me(e,r[h],i),r[t]=null;g++}else Ne(r[p]),p--;else Ne(r[h]),h++;for(;g<=u;){const t=Me(e,l[u+1]);Le(t,n[g]),l[g++]=t}for(;h<=p;){const e=r[h++];null!==e&&Ne(e)}return this.ut=s,Pe(e,l),Y}});let vt=class extends me{constructor(){super(...arguments),this.rows=[],this.locked=!1}render(){return X`
      <ha-sortable handle-selector=".handle" .disabled=${this.locked} @item-moved=${this.itemMoved}>
        <div class="list">${ut(this.rows,e=>e.key,(e,t)=>this.renderRow(e,t))}</div>
      </ha-sortable>
    `}renderRow(e,t){return X`
      <div class="row">
        ${this.locked?ee:X`<ha-svg-icon class="handle" .path=${i} title=${this.localize("list.drag")}></ha-svg-icon>`}
        <span class="rank">${t+1}</span>
        ${e.iconPath?X`<ha-svg-icon class="icon" .path=${e.iconPath}></ha-svg-icon>`:ee}
        <div class="main">
          <div class="title">${e.title}${e.tag?X`<span class="tag">${e.tag}</span>`:ee}</div>
          ${e.details.length>0?X`<div class="details">${a=e.details,a.map((e,t)=>X`${t>0?" · ":""}${e}`)}</div>`:ee}
          ${e.errors.map(e=>X`<div class="error">${e}</div>`)}
        </div>
        ${e.openable?X`
              <ha-icon-button
                .path=${this.locked?"M12,9A3,3 0 0,0 9,12A3,3 0 0,0 12,15A3,3 0 0,0 15,12A3,3 0 0,0 12,9M12,17A5,5 0 0,1 7,12A5,5 0 0,1 12,7A5,5 0 0,1 17,12A5,5 0 0,1 12,17M12,4.5C7,4.5 2.73,7.61 1,12C2.73,16.39 7,19.5 12,19.5C17,19.5 21.27,16.39 23,12C21.27,7.61 17,4.5 12,4.5Z":"M20.71,7.04C21.1,6.65 21.1,6 20.71,5.63L18.37,3.29C18,2.9 17.35,2.9 16.96,3.29L15.12,5.12L18.87,8.87M3,17.25V21H6.75L17.81,9.93L14.06,6.18L3,17.25Z"}
                .label=${this.localize(this.locked?"list.view":"list.edit")}
                @click=${()=>this.dispatchEvent(new CustomEvent("open-row",{detail:e.key}))}
              ></ha-icon-button>
            `:ee}
      </div>
    `;var a}itemMoved(e){e.stopPropagation(),this.dispatchEvent(new CustomEvent("item-moved",{detail:e.detail}))}static{this.styles=g`
    :host {
      display: block;
    }
    .row {
      display: flex;
      align-items: center;
      gap: 12px;
      min-height: 56px;
      padding: 6px 8px 6px 16px;
      border-top: 1px solid var(--divider-color);
      box-sizing: border-box;
      background: var(--card-background-color);
    }
    .handle {
      flex: none;
      cursor: grab;
      color: var(--secondary-text-color);
    }
    .rank {
      flex: none;
      min-width: 20px;
      text-align: center;
      color: var(--secondary-text-color);
    }
    .icon {
      flex: none;
      color: var(--state-icon-color, var(--secondary-text-color));
    }
    .main {
      flex: 1;
      min-width: 0;
    }
    .title {
      overflow-wrap: anywhere;
    }
    .tag {
      display: inline-block;
      margin-inline-start: 6px;
      padding: 0 8px;
      border-radius: 999px;
      font-size: var(--ha-font-size-s, 12px);
      background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.16);
      color: var(--primary-color);
    }
    .details,
    .error {
      font-size: var(--ha-font-size-s, 12px);
      overflow-wrap: anywhere;
    }
    .details {
      color: var(--secondary-text-color);
    }
    .details a {
      color: var(--primary-color);
    }
    .error {
      color: var(--error-color);
    }
  `}};e([we({attribute:!1})],vt.prototype,"localize",void 0),e([we({attribute:!1})],vt.prototype,"rows",void 0),e([we({type:Boolean})],vt.prototype,"locked",void 0),vt=e([_e("kraftvakt-sortable-list")],vt);const mt={missing_power_sensor:"missing.missing_power_sensor",missing_entity:"missing.missing_entity",missing_action:"missing.missing_action",missing_actively_charging:"missing.missing_actively_charging",missing_car_connected:"missing.missing_car_connected"},ft={turn_on:"missing.actions.turn_on",turn_off:"missing.actions.turn_off",activate:"missing.actions.activate",deactivate:"missing.actions.deactivate",set_current:"missing.actions.set_current"},_t={general:"general",appliances:"appliances",priority:"appliances",charging:"charging",chargers:"charging"},yt=new Set(["wait_curve_steepness","wait_curve_pivot","appliance_cycling_step_factor","appliance_cycling_steps","charger_cycling_step_factor","charger_cycling_steps"]);function bt(e,t,i){const a="chargers"===e.section?t?.config.charging.chargers:t?.config.appliances,r=a?.find(t=>t.id===e.target)?.entity_id;return r?t?.entity_names[r]??r:i("chargers"===e.section?"missing.charger_without_entity":"missing.appliance_without_entity")}const wt={required:"errors.required",missing_power_sensor:"errors.required",missing_entity:"errors.required",missing_action:"errors.required",missing_actively_charging:"errors.required",missing_car_connected:"errors.car_connected_required",not_integer:"errors.not_integer",invalid_entity_id:"errors.invalid_entity_id",empty_label:"errors.empty_label",duplicate_label:"errors.duplicate_label",min_current_above_max:"errors.min_current_above_max",invalid_time:"errors.invalid_time",window_start_equals_end:"errors.window_start_equals_end",duplicate_entity:"errors.duplicate_entity",invalid_action:"errors.invalid_action",invalid_template:"errors.invalid_template",default_action_unavailable:"errors.default_action_unavailable",unsupported_entity_domain:"errors.unsupported_entity_domain",domain_action_unavailable:"errors.domain_action_unavailable",unsupported_option:"errors.unsupported_option",outside_entity_range:"errors.outside_entity_range"},$t={general:"general",appliances:"appliances",chargers:"chargers"};function kt(e,t,i,a){const r=$t[e.section],n=r&&e.field?i?.limits[r][e.field]:void 0,s=e=>null===e?"":new Intl.NumberFormat(a).format(e);return"out_of_range"===e.code&&n?null===n.max?t("errors.at_least",{min:s(n.min)}):t("errors.out_of_range",{min:s(n.min),max:s(n.max)}):"invalid_resolution"===e.code&&n?t("errors.invalid_resolution",{step:s(n.step)}):t(wt[e.code]??"errors.unknown",{code:e.code})}function xt(e,t,i){const a={};for(const r of e)r.field?.startsWith(t)&&(a[r.field.slice(t.length)]??=i(r));return a}class At extends me{constructor(){super(...arguments),this.narrow=!1,this.entityNames={},this.issues=[],this.saveErrors=[],this.locked=!1,this.describeIssue=e=>kt(e,this.localize,this.capabilities,this.hass.language)}changeConfig(e){!function(e,t){e.dispatchEvent(new CustomEvent(Ge,{detail:t,bubbles:!0,composed:!0}))}(this,e)}formErrors(e,t,i=""){return xt(this.issues.filter(i=>i.section===e&&i.target===t),i,this.describeIssue)}entitiesUsedBesides(e){return[...this.config.appliances,...this.config.charging.chargers].filter(t=>t.id!==e&&t.entity_id).map(e=>e.entity_id)}renderListCard(e,t=""){return X`
      <ha-card class=${e.locked?"locked":""}>
        <div class="card-header">
          <div class="heading">
            <span>${this.localize(e.title)}</span>
            <span class="sub">${this.localize(e.sub)}</span>
          </div>
          <ha-button .disabled=${e.locked} @click=${e.onAdd}>
            <ha-svg-icon slot="start" .path=${n}></ha-svg-icon>
            ${this.localize(e.add)}
          </ha-button>
        </div>
        ${0===e.rows.length?X`<div class="empty">${this.localize(e.empty)}</div>`:X`
              <kraftvakt-sortable-list
                .localize=${this.localize}
                .rows=${e.rows}
                .locked=${e.locked}
                @item-moved=${e.onMoved}
                @open-row=${e.onOpen}
              ></kraftvakt-sortable-list>
            `}
        ${t}
      </ha-card>
    `}static{this.styles=g`
    :host {
      display: grid;
      gap: 16px;
    }
    :host([narrow]) {
      gap: 8px;
    }
    /* HA's number field keeps its full text colour when disabled. */
    :host([locked]) ha-form {
      opacity: 0.6;
    }
    .card-content {
      padding: 0 16px 16px;
    }
    .card-header {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
      padding: 12px 16px;
    }
    .heading {
      flex: 1;
      display: flex;
      flex-wrap: wrap;
      align-items: baseline;
      gap: 4px 12px;
      font-size: var(--ha-font-size-xl, 20px);
    }
    .sub {
      font-size: var(--ha-font-size-m, 14px);
      color: var(--secondary-text-color);
    }
    .empty {
      padding: 0 16px 16px;
      color: var(--secondary-text-color);
    }
    .locked kraftvakt-sortable-list {
      opacity: 0.6;
    }
  `}}e([we({attribute:!1})],At.prototype,"hass",void 0),e([we({attribute:!1})],At.prototype,"localize",void 0),e([we({type:Boolean,reflect:!0})],At.prototype,"narrow",void 0),e([we({attribute:!1})],At.prototype,"config",void 0),e([we({attribute:!1})],At.prototype,"entityNames",void 0),e([we({attribute:!1})],At.prototype,"capabilities",void 0),e([we({attribute:!1})],At.prototype,"issues",void 0),e([we({attribute:!1})],At.prototype,"saveErrors",void 0),e([we({type:Boolean,reflect:!0})],At.prototype,"locked",void 0);const Ct={power_limit_w:"W",turn_on_margin_w:"W",regulation_window_s:"s",wait_at_limit_s:"s",penalty_threshold_w:"W"},Et=new Set(["regulation_interval","appliance_cycling_step_factor","appliance_cycling_steps","charger_cycling_step_factor","charger_cycling_steps"]);class zt extends At{constructor(){super(...arguments),this.computeLabel=e=>this.localize(`general.fields.${e.name}.label`),this.computeHelper=e=>{const t=this.range(e.name),i=this.capabilities.defaults.general,a=e=>null==e?"":new Intl.NumberFormat(this.hass.language).format(e),r=this.config.general.regulation_window_s;return this.localize(`general.fields.${e.name}.helper`,{min:a(t?.min),max:a(t?.max),default:a(i[e.name]),seconds:a(r*this.config.general.regulation_interval)})}}renderForm(e){return X`
      <ha-form
        .hass=${this.hass}
        .data=${this.formData}
        .schema=${e}
        .error=${this.formErrors("general")}
        .disabled=${this.locked}
        .computeLabel=${this.computeLabel}
        .computeHelper=${this.computeHelper}
        .computeError=${e=>e}
        @value-changed=${this.valueChanged}
      ></ha-form>
    `}numberField(e){const t=this.range(e);return{name:e,required:!0,selector:{number:{min:t.min??void 0,max:t.max??void 0,step:t.step,mode:"box",unit_of_measurement:Ct[e]}}}}selectField(e,t){const i=this.range(e),a=[];for(let e=i.min??i.step;e<=(i.max??e);e+=i.step)a.push({value:String(e),label:t(e)});return{name:e,required:!0,selector:{select:{mode:"dropdown",options:a}}}}range(e){return this.capabilities.limits.general[e]}get formData(){const e=this.config.general;return Object.fromEntries(Object.entries(e).map(([e,t])=>[e,Et.has(e)&&null!==t?String(t):t]))}valueChanged(e){const t=e.detail.value,i={...this.config.general};for(const e of Object.keys(i)){const a=t[e];i[e]=Et.has(e)&&void 0!==a?Number(a):a??null}this.changeConfig({...this.config,general:i})}static{this.styles=[At.styles,g`
      .card-content {
        display: grid;
        gap: 16px;
      }
      .description {
        margin: 0;
        color: var(--secondary-text-color);
      }
    `]}}const St=["wait_curve_steepness","wait_curve_pivot"],Vt=[50,40,30,25,20,15,10,7,4,1],Ht=60,Mt=[.1,.2,.5,1,2,5,10];function Lt(e,t){return Math.max(0,Math.ceil(e/t-1e-9))*t}const Tt={wait_curve_steepness:!1,wait_curve_pivot:!0};let Pt=class extends zt{render(){return X`${this.renderWaitCurveCard()} ${this.renderCyclingCard()}`}renderWaitCurveCard(){return X`
      <ha-card .header=${this.localize("advanced.wait_curve")}>
        <div class="card-content">
          <p class="description">${this.localize("advanced.wait_curve_info")}</p>
          <div class="sliders">${St.map(e=>this.renderSlider(e))}</div>
          ${this.renderWaitCurve()}
        </div>
      </ha-card>
    `}renderCyclingCard(){return X`
      <ha-card .header=${this.localize("advanced.cycling")}>
        <div class="card-content">
          <p class="description">${this.localize("advanced.cycling_info")}</p>
          ${this.renderCyclingSection("advanced.appliances","appliance_cycling_step_factor","appliance_cycling_steps")}
          ${this.renderCyclingSection("advanced.chargers","charger_cycling_step_factor","charger_cycling_steps")}
        </div>
      </ha-card>
    `}renderCyclingSection(e,t,i){const a=this.hass.language;return X`
      <h3>${this.localize(e)}</h3>
      ${this.renderForm([this.selectField(t,e=>`× ${new Intl.NumberFormat(a).format(e)}`),this.selectField(i,e=>String(e))])}
      ${this.narrow?ee:this.renderCyclingTable(this.config.general[t],this.config.general[i])}
    `}renderCyclingTable(e,t){const i=this.config.general,a=i.wait_at_limit_s,r=this.decisionInterval,n=pt(i.wait_curve_steepness,i.wait_curve_pivot)(i.wait_curve_pivot/100),s=Array.from({length:t+2+1},(e,t)=>t+1),o=(t,i)=>{if(null===a||i&&null===r)return"–";const s=t<=2?a*n:a*(1+e*(t-2-1));return lt(i?Lt(s,r):s)};return X`
      <table class="curve-table">
        <tr>
          <th>${this.localize("advanced.turn_on_in_a_row")}</th>
          ${s.map(e=>X`<td>${e}${e===s.length?"+":""}</td>`)}
        </tr>
        <tr>
          <th>${this.localize("advanced.waiting_minutes")}</th>
          ${s.map(e=>X`<td>${o(e,!1)}</td>`)}
        </tr>
        <tr>
          <th>${this.localize("advanced.actual_waiting_minutes")}</th>
          ${s.map(e=>X`<td>${o(e,!0)}</td>`)}
        </tr>
      </table>
    `}get decisionInterval(){const e=this.config.general.regulation_window_s;return null===e?null:e*this.config.general.regulation_interval}renderSlider(e){const t=this.range(e),i=this.config.general[e],a=Tt[e]?100-i:i,r=this.localize(`general.fields.${e}.label`),n=Tt[e]?" %":"";return X`
      <span class="slider-label">${r}</span>
      <ha-slider
        aria-label=${r}
        .min=${t.min}
        .max=${t.max}
        .step=${t.step}
        .value=${i}
        .withTooltip=${!1}
        ?disabled=${this.locked}
        @input=${t=>this.changeCurve(e,Number(t.target.value))}
      ></ha-slider>
      <span class="slider-value">${new Intl.NumberFormat(this.hass.language).format(a)}${n}</span>
    `}changeCurve(e,t){t!==this.config.general[e]&&this.changeConfig({...this.config,general:{...this.config.general,[e]:t}})}renderWaitCurve(){const e=this.config.general,t=pt(e.wait_curve_steepness,e.wait_curve_pivot),i=e=>t(1-e/100),a=this.hass.language,r=e.power_limit_w,n=e.wait_at_limit_s,s=this.decisionInterval,o=e=>null===n?null:n*i(e),l=(e,t)=>X`
      <tr>
        <th>${this.localize(e)}</th>
        ${Vt.map(e=>X`<td>${t(e)}</td>`)}
      </tr>
    `;return X`
      ${this.narrow?ee:X`<table class="curve-table">
            ${l("advanced.free_power_kw",e=>ot(a,null===r?null:r*e/100))}
            ${l("advanced.waiting_minutes",e=>lt(o(e)))}
            ${l("advanced.actual_waiting_minutes",e=>lt((e=>{const t=o(e);return null===t||null===s?null:Lt(t,s)})(e)))}
          </table>`}
      ${this.renderCurveGraph(i,r)}
    `}renderCurveGraph(e,t){const i=this.hass.language,[a,r]=this.narrow?[320,200]:[900,260],[n,s,o,l]=[44,24,8,38],c=e=>n+(a-n-s)*(Ht-e)/Ht,d=e=>o+(r-o-l)*(100-e)/100,h=`M${Array.from({length:201},(t,i)=>{const a=Ht-i*Ht/200;return`${c(a)},${d(100*e(a))}`}).join("L")}`,p=null===t?0:t/1e3,g=p*Ht/100,u=(v=g,m=this.narrow?4:10,Mt.find(e=>v/e<=m)??Mt[Mt.length-1]);var v,m;const f=g>0?Array.from({length:Math.floor(g/u+1e-9)+1},(e,t)=>t*u):[],_=u<1?1:0;return X`
      <svg class="curve" viewBox="0 0 ${a} ${r}" role="img" aria-label=${this.localize("advanced.wait_curve")}>
        ${[0,20,40,60,80,100].map(e=>Q`
            <line class="grid" x1=${n} x2=${a-s} y1=${d(e)} y2=${d(e)}></line>
            <text x=${n-6} y=${d(e)+4} text-anchor="end">${st(i,e,0)} %</text>
          `)}
        ${f.map(e=>Q`<text x=${c(100*e/p)} y=${r-l+18} text-anchor="middle">${st(i,e,_)}</text>`)}
        <text x=${c(30)} y=${r-4} text-anchor="middle">${this.localize("advanced.free_power_kw")}</text>
        <path class="area" d="${h}L${c(0)},${d(0)}L${c(Ht)},${d(0)}Z"></path>
        <path class="line" d=${h}></path>
      </svg>
    `}static{this.styles=[zt.styles,g`
      h3 {
        margin: 0 0 -8px;
        font-size: var(--ha-font-size-m, 14px);
        font-weight: 500;
      }
      .sliders {
        display: grid;
        grid-template-columns: auto minmax(0, 1fr) 3em;
        align-items: center;
        gap: 8px 16px;
      }
      .sliders ha-slider {
        width: 100%;
      }
      :host([locked]) .sliders {
        opacity: 0.6;
      }
      .slider-value {
        text-align: end;
        font-variant-numeric: tabular-nums;
      }
      .curve-table {
        width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
      }
      .curve-table th {
        width: 180px;
        text-align: start;
        font-weight: normal;
        color: var(--secondary-text-color);
        white-space: nowrap;
      }
      .curve-table th,
      .curve-table td {
        padding: 6px 0;
        border-bottom: 1px solid var(--divider-color);
      }
      .curve-table td {
        text-align: center;
        font-variant-numeric: tabular-nums;
      }
      .curve {
        display: block;
        width: 100%;
        height: auto;
      }
      .curve .grid {
        stroke: var(--divider-color);
      }
      .curve text {
        fill: var(--secondary-text-color);
        font-size: 12px;
      }
      .curve .line {
        fill: none;
        stroke: var(--primary-color);
        stroke-width: 2;
      }
      .curve .area {
        fill: var(--primary-color);
        opacity: 0.12;
      }
    `]}};function Nt(e,t,i,a){const r=e.domain_actions[t][i],n=a?.split(".")[0];return Object.fromEntries(Object.entries(r).filter(([,e])=>e.domain===n))}function jt(e,t,i,a,r){return r?.domain_action?Nt(e,t,i,a)[r.domain_action]:void 0}function Dt(e,t,i={}){return Object.fromEntries(e.parameters.map(e=>[e.name,i[e.name]??Rt(e,t)]))}function Ot(e,t){return{min:Ft(t,e.min_attribute),max:Ft(t,e.max_attribute),step:Ft(t,e.step_attribute)}}function Wt(e,t,i){if(null===t)return;if("option"===e.type){const a=It(i,e.options_attribute);return Array.isArray(a)&&!a.includes(t)?"unsupported_option":void 0}const{min:a,max:r}=Ot(e,i);return"number"==typeof t&&(void 0!==a&&t<a||void 0!==r&&t>r)?"outside_entity_range":void 0}function Rt(e,t){if("option"===e.type){const i=It(t,e.options_attribute),a=Array.isArray(i)?i:e.preferred_options;return e.preferred_options.find(e=>a.includes(e))??null}return e.default}function It(e,t){return t?e?.attributes[t]:void 0}function Ft(e,t){const i=It(e,t);return"number"==typeof i?i:void 0}Pt=e([_e("kraftvakt-advanced-page")],Pt);const Ut=["turn_on","turn_off"],Bt=["activate","deactivate","set_current"];function qt(e){const t=[];return e.general.power_sensor||t.push({code:"missing_power_sensor",section:"general",field:"power_sensor"}),t.push(...e.appliances.flatMap(Kt)),e.charging.enabled&&t.push(...e.charging.chargers.flatMap(t=>Zt(t,e.charging.one_at_a_time))),t}function Kt(e){return ri("appliances",e,Ut)}function Zt(e,t){const i=ri("chargers",e,Bt);return e.actively_charging||i.push({code:"missing_actively_charging",section:"chargers",target:e.id,field:"actively_charging"}),t&&!e.car_connected&&i.push({code:"missing_car_connected",section:"chargers",target:e.id,field:"car_connected"}),i}function Gt(e,t,i){return e.default_actions[t][i]}function Jt(e,t,i,a,r){switch(r?.mode){case"default":return Xt(e,t,i,a);case"domain":return void 0!==jt(e,t,i,a,r);default:return!0}}function Xt(e,t,i,a){return null!==a&&Gt(e,t,i).domains.includes(a.split(".")[0])}function Qt(e,t,i){const a=e.variants.map(e=>e.label.trim());return[...ii("appliances",e.id,e,t.limits.appliances,!1),...ai("appliances",e,Ut,t,i),...e.variants.flatMap((t,i)=>{const r=`variants.${t.id}.`,n=[];return""===a[i]?n.push(ei(e,"empty_label",`${r}label`)):a.filter(e=>e===a[i]).length>1&&n.push(ei(e,"duplicate_label",`${r}label`)),[...n,...ti("appliances",e.id,`${r}condition`,t.condition)]})]}function Yt(e,t,i){const a=(t,i)=>({code:t,section:"chargers",target:e.id,field:i}),r=[...ii("chargers",e.id,e,t.limits.chargers,!0),...ai("chargers",e,Bt,t,i)];e.min_current_a>e.max_current_a&&r.push(a("min_current_above_max","min_current_a"));for(const t of["car_connected","actively_charging"]){const i=e[t];i&&r.push(...ti("chargers",e.id,t,i))}const n=e.charging_window;return!n||n.start&&n.end?n&&n.start===n.end&&r.push(a("window_start_equals_end","charging_window")):r.push(a("invalid_time","charging_window")),r}function ei(e,t,i){return{code:t,section:"appliances",target:e.id,field:i}}function ti(e,t,i,a){return""===a.value.trim()?[{code:"required",section:e,target:t,field:i}]:[]}function ii(e,t,i,a,r){const n=i;return Object.entries(a).flatMap(([i,a])=>{const s=n[i],o="number"!=typeof s||Number.isNaN(s)?r?"required":void 0:function(e,t){if(null!==t.min&&e<t.min||null!==t.max&&e>t.max)return"out_of_range";const i=e/t.step;return Math.abs(i-Math.round(i))<1e-6?void 0:"invalid_resolution"}(s,a);return o?[{code:o,section:e,target:t,field:i}]:[]})}function ai(e,t,i,a,r){const n=t,s=t.entity_id;return null===s?[]:i.flatMap(i=>{const o=n[i],l=(a,r)=>({code:a,section:e,target:t.id,field:r?`${i}.${r}`:i});if(!Jt(a,e,i,s,o))return[l("default"===o?.mode?"default_action_unavailable":"domain_action_unavailable")];const c=jt(a,e,i,s,o);return c?Object.entries(function(e,t,i){const a={};for(const r of e.parameters){const e=r.name in t?Wt(r,t[r.name],i):"required";e&&(a[r.name]=e)}return a}(c,o?.data??{},r[s])).map(([e,t])=>l(t,e)):[]})}function ri(e,t,i){const a=t;return[...t.entity_id?[]:[{code:"missing_entity",section:e,target:t.id,field:"entity_id"}],...i.filter(e=>function(e){return null===e||"custom"===e.mode&&0===(e.action??[]).length||"entity"===e.mode&&!e.entity_id||"domain"===e.mode&&Object.values(e.data??{}).includes(null)}(a[e])).map(i=>({code:"missing_action",section:e,target:t.id,field:i}))]}function ni(e,t,i){return t[i]??e.states[i]?.attributes.friendly_name??i}function si(e,t,i){const a=e.entities?.[i]?.device_id,r=a?e.devices?.[a]:void 0;return t[i]??r?.name_by_user??r?.name??ni(e,t,i)}function oi(e){return Object.values(e.entities??{}).filter(e=>"kraftvakt"===e.platform).map(e=>e.entity_id)}function li(e,t){const i=e.states[t],a=Number(i?.state);if(!i||""===i.state.trim()||!Number.isFinite(a))return null;const r=i.attributes.unit_of_measurement,n="kW"===r?1e3:r&&"W"!==r?null:1;return null===n?null:Math.max(0,a)*n}const ci=["binary_sensor","input_boolean","switch","schedule"],di={condition:["entity","template"],actively_charging:["power_sensor","entity","template"]};let hi=class extends me{constructor(){super(...arguments),this.value=null,this.entityId=null,this.optional=!1,this.kind="condition",this.disabled=!1,this.computeLabel=e=>"value"===e.name?this.text(`${this.shownType()}_label`):"",this.computeHelper=e=>"value"===e.name?this.text(`${this.shownType()}_helper`):""}disconnectedCallback(){super.disconnectedCallback(),this.stopPreview()}updated(e){(e.has("value")||e.has("entityId"))&&this.schedulePreview()}render(){const e=this.shownType();return X`
      <ha-form
        .hass=${this.hass}
        .data=${{type:e,value:this.value?.value??""}}
        .schema=${this.schema(e)}
        .disabled=${this.disabled}
        .computeLabel=${this.computeLabel}
        .computeHelper=${this.computeHelper}
        @value-changed=${this.valueChanged}
      ></ha-form>
      ${this.renderPreview()} ${this.error?X`<div class="error">${this.error}</div>`:ee}
    `}shownType(){return this.value?.type??(this.optional?"none":di[this.kind][0])}schema(e){return[{name:"type",selector:{select:{mode:"list",options:[...this.optional?["none"]:[],...di[this.kind]].map(e=>({value:e,label:this.text(e)}))}}},...this.valueField(e)]}valueField(e){switch(e){case"entity":return[{name:"value",required:!0,selector:{entity:{filter:{domain:ci}}}}];case"power_sensor":return[{name:"value",required:!0,selector:{entity:{filter:{domain:"sensor",device_class:"power"},exclude_entities:oi(this.hass)}}}];case"template":return[{name:"value",required:!0,selector:{template:{}}}];default:return[]}}renderPreview(){if(!this.value?.value)return ee;if("template"===this.value.type&&void 0!==this.preview?.error)return X`<div class="preview error">${this.localize("condition.error",{message:this.preview.error})}</div>`;if("template"===this.value.type&&!this.preview)return ee;const e=this.evidence(this.value),t="actively_charging"===this.kind?!1!==e:!0===e;return X`
      ${this.renderNow(t)}
      ${"template"===this.value.type&&null===e?X`<div class="warning">${this.text("not_boolean",{value:JSON.stringify(this.preview?.result)})}</div>`:ee}
    `}evidence(e){switch(e.type){case"template":return"boolean"==typeof this.preview?.result?this.preview.result:null;case"power_sensor":{const t=li(this.hass,e.value);return null===t?null:t>100}default:{const t=this.hass.states[e.value]?.state;return"on"===t||"off"!==t&&null}}}renderNow(e){const t=this.text(e?"true":"false");return X`<div class="preview">${this.localize("condition.now",{value:""})}<b>${t}</b></div>`}text(e,t){return this.localize(`${this.kind}.${e}`,t)}valueChanged(e){e.stopPropagation();const{type:t,value:i}=e.detail.value,a=t===this.shownType(),r="none"===t?null:{type:t,value:a?i??"":""};this.dispatchEvent(new CustomEvent("value-changed",{detail:{value:r}}))}schedulePreview(){if(this.stopPreview(),"template"!==this.value?.type||!this.value.value.trim())return void(this.preview=void 0);const e=this.value.value;this.previewTimer=window.setTimeout(()=>this.startPreview(e),500)}startPreview(e){const t=this.entityId?this.hass.states[this.entityId]??null:null;this.unsubscribePreview=this.hass.connection.subscribeMessage(e=>this.preview=e,{type:"render_template",template:e,variables:{entity_id:this.entityId,entity:t},report_errors:!0}),this.unsubscribePreview.catch(e=>{this.preview={error:String(e instanceof Object&&"message"in e?e.message:e)}})}stopPreview(){window.clearTimeout(this.previewTimer),this.unsubscribePreview?.then(e=>e()).catch(()=>{}),this.unsubscribePreview=void 0}static{this.styles=g`
    :host {
      display: block;
    }
    .preview {
      margin-top: 4px;
      font-size: var(--ha-font-size-s, 12px);
      color: var(--secondary-text-color);
    }
    .error {
      margin-top: 4px;
      font-size: var(--ha-font-size-s, 12px);
      color: var(--error-color);
    }
    .warning {
      margin-top: 4px;
      font-size: var(--ha-font-size-s, 12px);
      color: var(--warning-color);
    }
  `}};e([we({attribute:!1})],hi.prototype,"hass",void 0),e([we({attribute:!1})],hi.prototype,"localize",void 0),e([we({attribute:!1})],hi.prototype,"value",void 0),e([we({attribute:!1})],hi.prototype,"entityId",void 0),e([we({type:Boolean})],hi.prototype,"optional",void 0),e([we()],hi.prototype,"kind",void 0),e([we()],hi.prototype,"error",void 0),e([we({type:Boolean})],hi.prototype,"disabled",void 0),e([$e()],hi.prototype,"preview",void 0),hi=e([_e("kraftvakt-condition-field")],hi);let pi=class extends me{constructor(){super(...arguments),this.label="",this.value=null,this.entityId=null,this.defaultAvailable=!1,this.entityDomains=[],this.domainActions={},this.parameterErrors={},this.variables=[],this.disabled=!1}render(){const e=this.value?.mode,t=this.domainAction;return X`
      <div class="field ${this.error?"invalid":""}">
        <div class="label">${this.label}</div>
        <ha-form
          .hass=${this.hass}
          .data=${{mode:"domain"===e?this.value?.domain_action:e,action:this.value?.action??[],entity_id:this.value?.entity_id??void 0}}
          .schema=${this.schema(e)}
          .disabled=${this.disabled}
          .computeLabel=${()=>""}
          @value-changed=${this.valueChanged}
        ></ha-form>
        ${t?this.renderParameters(t):ee}
        <div class="helper">${this.helperText(e)}</div>
        ${this.error?X`<div class="error">${this.error}</div>`:ee}
      </div>
    `}renderParameters(e){const t=this.value?.data??{};return X`
      <ha-form
        .hass=${this.hass}
        .data=${Object.fromEntries(Object.entries(t).map(([e,t])=>[e,t??void 0]))}
        .schema=${e.parameters.map(e=>this.parameterField(e))}
        .error=${this.parameterErrors}
        .disabled=${this.disabled}
        .computeLabel=${e=>this.localize(`action.parameters.${e.name}`)}
        .computeHelper=${t=>this.parameterHelper(e,t.name)}
        @value-changed=${this.parametersChanged}
      ></ha-form>
    `}parameterField(e){const t=this.stateObj;if("option"===e.type){const i=function(e,t){const i=It(t,e.options_attribute);return Array.isArray(i)?i.map(String):e.preferred_options}(e,t).map(e=>({value:e,label:t?this.hass.formatEntityState(t,e):e}));return{name:e.name,required:!0,selector:{select:{mode:"dropdown",options:i}}}}const{min:i,max:a,step:r}=Ot(e,t),n=this.hass.config.unit_system.temperature;return{name:e.name,required:!0,selector:{number:{min:i,max:a,step:r??"any",mode:"box",unit_of_measurement:n}}}}parameterHelper(e,t){const i=e.parameters.find(e=>e.name===t),{min:a,max:r}=i?Ot(i,this.stateObj):{};if(void 0===a||void 0===r)return"";const n=e=>new Intl.NumberFormat(this.hass.language).format(e);return this.localize("action.parameter_range",{min:n(a),max:n(r),unit:this.hass.config.unit_system.temperature})}schema(e){return[{name:"mode",selector:{select:{mode:"list",options:[...this.defaultAvailable?[{value:"default",label:this.localize("action.default")}]:[],...Object.keys(this.domainActions).map(e=>({value:e,label:this.localize(`action.domain_actions.${e}`)})),...this.entityDomains.length?[{value:"entity",label:this.localize("action.entity")}]:[],{value:"custom",label:this.localize("action.custom")}]}}},..."entity"===e?[{name:"entity_id",selector:{entity:{filter:{domain:this.entityDomains}}}}]:[],..."custom"===e?[{name:"action",selector:{action:{}}}]:[]]}helperText(e){if("custom"===e)return this.localize("action.variables",{variables:this.variables.join(", ")});if("domain"===e){const e=this.domainAction;return e?this.localize("action.default_runs",{service:`${e.domain}.${e.service}`}):""}if("entity"===e){const e=this.value?.entity_id;return e?this.localize("action.entity_runs",{service:this.defaultService(e)}):this.localize("action.choose_action_entity")}return this.defaultAvailable&&this.entityId?this.localize("action.default_runs",{service:this.defaultService(this.entityId)}):this.localize(this.entityId?"action.no_default":"action.choose_entity")}valueChanged(e){e.stopPropagation();const{mode:t,action:i,entity_id:a}=e.detail.value,r=t?this.domainActions[t]:void 0,n=r?{mode:"domain",domain_action:t,data:Dt(r,this.stateObj,this.value?.data)}:"default"===t?{mode:t}:"entity"===t?{mode:t,entity_id:a||null}:"custom"===t?{mode:t,action:"custom"===this.value?.mode?gi(i):this.defaultSteps()}:null;this.fireChanged(n)}parametersChanged(e){e.stopPropagation();const t=Object.fromEntries((this.domainAction?.parameters??[]).map(({name:t})=>[t,e.detail.value[t]??null]));this.fireChanged({...this.value,data:t})}fireChanged(e){this.dispatchEvent(new CustomEvent("value-changed",{detail:{value:e}}))}get domainAction(){return"domain"===this.value?.mode&&this.value.domain_action?this.domainActions[this.value.domain_action]:void 0}get stateObj(){return this.entityId?this.hass.states[this.entityId]:void 0}defaultSteps(){if(!this.defaultAvailable||!this.entityId)return[];const e=this.defaultAction?.data??{};return[{action:this.defaultService(this.entityId),target:{entity_id:this.entityId},...Object.keys(e).length?{data:e}:{}}]}defaultService(e){return`${e.split(".")[0]}.${this.defaultAction?.service}`}static{this.styles=g`
    .field {
      padding: 12px;
      border: 1px solid var(--divider-color);
      border-radius: var(--ha-border-radius-md, 8px);
    }
    .field.invalid {
      border-color: var(--error-color);
    }
    .label {
      font-weight: 500;
    }
    .helper {
      margin-top: 4px;
      font-size: var(--ha-font-size-s, 12px);
      color: var(--secondary-text-color);
    }
    .error {
      margin-top: 4px;
      font-size: var(--ha-font-size-s, 12px);
      color: var(--error-color);
    }
  `}};function gi(e){return Array.isArray(e)?e:e&&"object"==typeof e?[e]:[]}e([we({attribute:!1})],pi.prototype,"hass",void 0),e([we({attribute:!1})],pi.prototype,"localize",void 0),e([we()],pi.prototype,"label",void 0),e([we({attribute:!1})],pi.prototype,"value",void 0),e([we({attribute:!1})],pi.prototype,"entityId",void 0),e([we({attribute:!1})],pi.prototype,"defaultAction",void 0),e([we({type:Boolean})],pi.prototype,"defaultAvailable",void 0),e([we({attribute:!1})],pi.prototype,"entityDomains",void 0),e([we({attribute:!1})],pi.prototype,"domainActions",void 0),e([we({attribute:!1})],pi.prototype,"parameterErrors",void 0),e([we({attribute:!1})],pi.prototype,"variables",void 0),e([we()],pi.prototype,"error",void 0),e([we({type:Boolean})],pi.prototype,"disabled",void 0),pi=e([_e("kraftvakt-action-field")],pi);class ui extends me{constructor(){super(...arguments),this.isNew=!1,this.usedEntities=[],this.saveErrors=[],this.locked=!1,this.open=!0,this.describe=e=>kt(e,this.localize,this.capabilities,this.hass.language)}willUpdate(e){e.has("item")&&(this.draft=structuredClone(this.item))}render(){const e=this.errors(),t=[...e,...this.isNew?[]:this.missing(),...this.saveErrors];return X`
      <ha-dialog .open=${this.open} .headerTitle=${this.heading} prevent-scrim-close @closed=${this.closed}>
        <div class="content">${this.renderFields(t)}</div>
        <div slot="footer">${this.renderButtons(e.length>0)}</div>
      </ha-dialog>
    `}renderEntity(e){const t=[{name:"entity_id",required:!0,selector:{entity:{exclude_entities:this.usedEntities}}}];return this.renderForm(t,e,e=>this.entityChanged(e.entity_id||null))}renderAction(e,t,i,a=!1){const r=t.find(t=>t.field===e),n=xt(t,`${e}.`,this.describe),s=Gt(this.capabilities,this.section,e);return X`
      <kraftvakt-action-field
        .hass=${this.hass}
        .localize=${this.localize}
        .label=${this.label(e)}
        .value=${this.draft[e]}
        .entityId=${this.draft.entity_id}
        .defaultAction=${s}
        .defaultAvailable=${Xt(this.capabilities,this.section,e,this.draft.entity_id)}
        .entityDomains=${a?s.domains:[]}
        .domainActions=${Nt(this.capabilities,this.section,e,this.draft.entity_id)}
        .variables=${i}
        .error=${r?this.describe(r):void 0}
        .parameterErrors=${n}
        .disabled=${this.locked}
        @value-changed=${t=>this.changeDraft({[e]:t.detail.value})}
      ></kraftvakt-action-field>
    `}renderForm(e,t,i,a=this.draft){const r=e.map(e=>e.name);return X`
      <ha-form
        .hass=${this.hass}
        .data=${a}
        .schema=${e}
        .error=${xt(t.filter(e=>void 0!==e.field&&r.includes(e.field)),"",this.describe)}
        .disabled=${this.locked}
        .computeLabel=${e=>this.label(e.name)}
        .computeHelper=${e=>this.helper(e.name)}
        @value-changed=${e=>{e.stopPropagation(),i(e.detail.value)}}
      ></ha-form>
    `}numberField(e,t,i){const a=this.capabilities.limits[this.section][e];return{name:e,required:i,selector:{number:{min:a.min??void 0,max:a.max??void 0,step:a.step,mode:"box",unit_of_measurement:t}}}}label(e){return this.localize(`${this.texts}.fields.${e}.label`)}helper(e){const t=`${this.texts}.fields.${e}.helper`;if(this.localize(t)===t)return"";const i=this.capabilities.limits[this.section][e],a=this.capabilities.defaults[this.section],r=e=>"number"==typeof e?new Intl.NumberFormat(this.hass.language).format(e):"";return this.localize(t,{min:r(i?.min),max:r(i?.max),default:r(a[e])})}renderSection(e){return X`<div class="section">${this.localize(e)}</div>`}changeDraft(e){this.draft={...this.draft,...e}}entityChanged(e){const t=this.draft,i={entity_id:e};for(const a of this.actionFields){const r=t[a];null===r&&Xt(this.capabilities,this.section,a,e)?i[a]={mode:"default"}:null===e||Jt(this.capabilities,this.section,a,e,r)||(i[a]={mode:"custom",action:[]})}this.changeDraft(i)}renderButtons(e){return this.locked?X`<ha-button @click=${this.close}>${this.localize("dialog.close")}</ha-button>`:X`
      ${this.isNew?ee:X`<ha-button variant="danger" appearance="plain" @click=${this.delete}>
            ${this.localize(`${this.texts}.delete`)}
          </ha-button>`}
      <span class="spacer"></span>
      <ha-button appearance="plain" @click=${this.close}>${this.localize("dialog.cancel")}</ha-button>
      <ha-button .disabled=${e} @click=${this.confirm}>${this.localize("dialog.ok")}</ha-button>
    `}get heading(){return this.locked?this.localize(`${this.texts}.view_title`):this.localize(this.isNew?`${this.texts}.add_title`:`${this.texts}.edit_title`)}confirm(){this.dispatchEvent(new CustomEvent("item-changed",{detail:this.draft})),this.close()}delete(){this.dispatchEvent(new CustomEvent("item-deleted",{detail:this.draft.id})),this.close()}close(){this.open=!1}closed(e){e.stopPropagation(),this.dispatchEvent(new CustomEvent("closed"))}static{this.styles=g`
    .content {
      display: grid;
      gap: 16px;
    }
    .section {
      margin-top: 8px;
      font-size: var(--ha-font-size-l, 16px);
      font-weight: 500;
    }
    .info {
      margin-top: -8px;
      font-size: var(--ha-font-size-s, 12px);
      color: var(--secondary-text-color);
    }
    .spacer {
      flex: 1;
    }
    div[slot="footer"] {
      display: flex;
      align-items: center;
    }
  `}}e([we({attribute:!1})],ui.prototype,"hass",void 0),e([we({attribute:!1})],ui.prototype,"localize",void 0),e([we({attribute:!1})],ui.prototype,"capabilities",void 0),e([we({attribute:!1})],ui.prototype,"item",void 0),e([we({type:Boolean})],ui.prototype,"isNew",void 0),e([we({attribute:!1})],ui.prototype,"usedEntities",void 0),e([we({attribute:!1})],ui.prototype,"saveErrors",void 0),e([we({type:Boolean})],ui.prototype,"locked",void 0),e([$e()],ui.prototype,"open",void 0),e([$e()],ui.prototype,"draft",void 0);const vi=["entity_id","entity"];let mi=class extends ui{constructor(){super(...arguments),this.section="appliances",this.texts="appliance",this.actionFields=["turn_on","turn_off"]}errors(){return Qt(this.draft,this.capabilities,this.hass.states)}missing(){return Kt(this.draft)}renderFields(e){return X`
      ${this.renderEntity(e)} ${this.renderSection("appliance.actions")}
      ${this.actionFields.map(t=>this.renderAction(t,e,vi))}
      ${this.renderForm([this.numberField("power_reserve_w","W",!1)],e,e=>this.changeDraft({power_reserve_w:e.power_reserve_w??null}))}
      ${this.renderVariants(e)}
    `}renderVariants(e){return X`
      ${this.renderSection("appliance.variants")}
      <div class="info">${this.localize("appliance.variants_info")}</div>
      <ha-sortable handle-selector=".handle" .disabled=${this.locked} @item-moved=${this.variantMoved}>
        <div class="variants">
          ${ut(this.draft.variants,e=>e.id,(t,i)=>this.renderVariant(t,i,e))}
        </div>
      </ha-sortable>
      ${this.locked?ee:X`
            <div>
              <ha-button appearance="outlined" @click=${this.addVariant}>
                <ha-svg-icon slot="start" .path=${n}></ha-svg-icon>
                ${this.localize("appliance.add_variant")}
              </ha-button>
            </div>
          `}
    `}renderVariant(e,t,a){const r=`variants.${e.id}.`,n=a.filter(e=>e.field?.startsWith(r)).map(e=>({...e,field:e.field?.slice(r.length)})),s=n.find(e=>"condition"===e.field);return X`
      <div class="variant">
        <div class="variant-header">
          ${this.locked?ee:X`<ha-svg-icon class="handle" .path=${i}></ha-svg-icon>`}
          <b>${t+1}.</b>
          <span class="spacer"></span>
          ${this.locked?ee:X`
                <ha-icon-button
                  .path=${"M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"}
                  .label=${this.localize("appliance.remove_variant")}
                  @click=${()=>this.removeVariant(e.id)}
                ></ha-icon-button>
              `}
        </div>
        ${this.renderForm(fi,n,t=>this.changeVariant(e.id,{label:t.label??""}),e)}
        <kraftvakt-condition-field
          .hass=${this.hass}
          .localize=${this.localize}
          .value=${e.condition}
          .entityId=${this.draft.entity_id}
          .error=${s?this.describe(s):void 0}
          .disabled=${this.locked}
          @value-changed=${t=>t.detail.value&&this.changeVariant(e.id,{condition:t.detail.value})}
        ></kraftvakt-condition-field>
      </div>
    `}addVariant(){const e={id:Je(),label:"",condition:{type:"template",value:""}};this.changeDraft({variants:[...this.draft.variants,e]})}removeVariant(e){this.changeDraft({variants:this.draft.variants.filter(t=>t.id!==e)})}changeVariant(e,t){this.changeDraft({variants:this.draft.variants.map(i=>i.id===e?{...i,...t}:i)})}variantMoved(e){e.stopPropagation(),this.changeDraft({variants:Xe(this.draft.variants,e.detail.oldIndex,e.detail.newIndex)})}static{this.styles=[ui.styles,g`
      .variants {
        display: grid;
        gap: 12px;
      }
      .variant {
        display: grid;
        gap: 8px;
        padding: 8px 12px 12px;
        border: 1px solid var(--divider-color);
        border-radius: var(--ha-border-radius-md, 8px);
        background: var(--card-background-color);
      }
      .variant-header {
        display: flex;
        align-items: center;
        gap: 8px;
        min-height: 40px;
      }
      .handle {
        cursor: grab;
        color: var(--secondary-text-color);
      }
    `]}};mi=e([_e("kraftvakt-appliance-dialog")],mi);const fi=[{name:"label",required:!0,selector:{text:{}}}];let _i=class extends me{constructor(){super(...arguments),this.kind="appliances",this.narrow=!1}render(){return X`
      <ha-alert alert-type="warning" .title=${this.localize(`warning.${this.kind}_title`)} .narrow=${this.narrow}>
        ${this.localize("warning.text")}
      </ha-alert>
    `}static{this.styles=g`
    :host {
      display: block;
    }
  `}};e([we({attribute:!1})],_i.prototype,"localize",void 0),e([we()],_i.prototype,"kind",void 0),e([we({type:Boolean})],_i.prototype,"narrow",void 0),_i=e([_e("kraftvakt-manual-control-warning")],_i);const yi=["entity_id","turn_on","turn_off","power_reserve_w","label","condition"];let bi=class extends At{render(){const e=this.config.priority.map(e=>this.row(e));return X`
      ${this.renderListCard({title:"appliances.priority_title",sub:"appliances.priority_sub",add:"appliances.add",empty:"appliances.empty",rows:e,locked:this.locked,onAdd:this.addAppliance,onMoved:this.entryMoved,onOpen:this.openRow})}
      ${0===this.config.appliances.length?X`
            <kraftvakt-manual-control-warning
              .localize=${this.localize}
              .narrow=${this.narrow}
              kind="appliances"
            ></kraftvakt-manual-control-warning>
          `:ee}
      ${this.editing?this.renderDialog(this.editing.appliance,this.editing.isNew):""}
    `}renderDialog(e,t){return X`
      <kraftvakt-appliance-dialog
        .hass=${this.hass}
        .localize=${this.localize}
        .capabilities=${this.capabilities}
        .item=${e}
        .isNew=${t}
        .usedEntities=${this.entitiesUsedBesides(e.id)}
        .saveErrors=${this.saveErrors.filter(t=>"appliances"===t.section&&t.target===e.id)}
        .locked=${this.locked}
        @item-changed=${this.applianceChanged}
        @item-deleted=${this.applianceDeleted}
        @closed=${()=>this.editing=void 0}
      ></kraftvakt-appliance-dialog>
    `}row(e){if("ev_charging"===e.type)return{key:Qe(e),title:this.localize("appliances.ev_charging"),iconPath:a,details:[X`${this.localize("appliances.ev_charging_sub",{count:this.config.charging.chargers.length})}
            <a href="${rt}/charging" @click=${this.openChargingPage}>${this.localize("tabs.charging")}</a>`],errors:[],openable:!1};const t=this.config.appliances.find(t=>t.id===e.appliance_id),i=t?.variants.find(t=>t.id===e.variant_id),r=this.issues.filter(t=>"appliances"===t.section&&t.target===e.appliance_id&&(i?t.field?.startsWith(`variants.${i.id}.`):!t.field?.startsWith("variants.")));return{key:Qe(e),title:t?this.applianceName(t):"",tag:i?.label,details:t?i?[this.variantSource(i.condition)]:this.applianceDetails(t):[],errors:r.map(e=>`${this.fieldLabel(e)}: ${this.describeIssue(e)}`),openable:!0}}applianceName(e){return e.entity_id?ni(this.hass,this.entityNames,e.entity_id):this.localize("missing.appliance_without_entity")}applianceDetails(e){const t=e.entity_id?[e.entity_id]:[];return null!==e.power_reserve_w&&t.push(this.localize("appliances.power_reserve",{power:st(this.hass.language,e.power_reserve_w,0)})),e.variants.length>0&&t.push(this.localize("appliances.variant_count",{count:e.variants.length})),t}variantSource(e){return"entity"===e.type?this.localize("appliances.variant_entity",{entity:e.value}):this.localize("appliances.variant_template")}fieldLabel(e){const t=e.field?.split(".").at(-1)??"";return yi.includes(t)?this.localize(`appliance.fields.${t}.label`):t}entryMoved(e){const{oldIndex:t,newIndex:i}=e.detail;this.changeConfig({...this.config,priority:Xe(this.config.priority,t,i)})}addAppliance(){const e={id:Je(),entity_id:null,turn_on:null,turn_off:null,power_reserve_w:this.capabilities.defaults.appliances.power_reserve_w,variants:[]};this.editing={appliance:e,isNew:!0}}openRow(e){const t=this.config.priority.find(t=>Qe(t)===e.detail),i="appliance"===t?.type?this.config.appliances.find(e=>e.id===t.appliance_id):void 0;i&&(this.editing={appliance:i,isNew:!1})}applianceChanged(e){const t=e.detail,i=this.config.appliances.some(e=>e.id===t.id)?this.config.appliances.map(e=>e.id===t.id?t:e):[...this.config.appliances,t];this.changeConfig({...this.config,appliances:i})}applianceDeleted(e){this.changeConfig({...this.config,appliances:this.config.appliances.filter(t=>t.id!==e.detail)})}openChargingPage(e){e.preventDefault(),nt("charging")}static{this.styles=At.styles}};e([$e()],bi.prototype,"editing",void 0),bi=e([_e("kraftvakt-appliances-page")],bi);const wi=["entity_id","entity"],$i=["current","min_current","max_current",...wi];let ki=class extends ui{constructor(){super(...arguments),this.section="chargers",this.texts="charger",this.actionFields=["activate","deactivate","set_current"],this.oneAtATime=!1}errors(){return Yt(this.draft,this.capabilities,this.hass.states)}missing(){return Zt(this.draft,this.oneAtATime)}renderFields(e){return X`
      ${this.renderEntity(e)} ${this.renderSection("charger.allowed_charging")}
      ${this.renderAction("activate",e,wi)}
      ${this.renderAction("deactivate",e,wi)}
      <div class="info">${this.localize("charger.minimum_first")}</div>
      ${this.renderSection("charger.charging_current")}
      ${this.renderForm([this.numberField("min_current_a","A",!0),this.numberField("max_current_a","A",!0)],e,e=>this.changeDraft({min_current_a:e.min_current_a,max_current_a:e.max_current_a}))}
      ${this.renderAction("set_current",e,$i,!0)}
      ${this.renderForm([this.numberField("power_reserve_w","W",!0)],e,e=>this.changeDraft({power_reserve_w:e.power_reserve_w}))}
      ${this.renderConditionGroup("car_connected",this.oneAtATime?"charger.car_connected_required":"charger.car_connected_optional",e)}
      ${this.renderConditionGroup("actively_charging","charger.actively_charging",e)}
      ${this.renderChargingWindow(e)}
    `}renderConditionGroup(e,t,i){const a=i.find(t=>t.field===e),r="actively_charging"===e;return X`
      <div class="group">
        <div class="group-title">${this.localize(t)}</div>
        <div class="info">${this.helper(e)}</div>
        <kraftvakt-condition-field
          .hass=${this.hass}
          .localize=${this.localize}
          .value=${this.draft[e]}
          .entityId=${this.draft.entity_id}
          .kind=${r?"actively_charging":"condition"}
          .optional=${!r}
          .error=${a?this.describe(a):void 0}
          .disabled=${this.locked}
          @value-changed=${t=>this.changeDraft({[e]:t.detail.value})}
        ></kraftvakt-condition-field>
      </div>
    `}renderChargingWindow(e){const t=this.draft.charging_window,i=[{name:"charging_window",selector:{boolean:{}}},...t?[{type:"grid",name:"",schema:[{name:"start",required:!0,selector:{time:{no_second:!0}}},{name:"end",required:!0,selector:{time:{no_second:!0}}}]}]:[]],a={charging_window:null!==t,start:t?.start??"",end:t?.end??""};return X`
      <div class="group">
        ${this.renderForm(i,e,e=>this.changeDraft({charging_window:e.charging_window?{start:xi(e.start),end:xi(e.end)}:null}),a)}
      </div>
    `}static{this.styles=[ui.styles,g`
      .group {
        display: grid;
        gap: 8px;
        padding: 12px;
        border: 1px solid var(--divider-color);
        border-radius: var(--ha-border-radius-md, 8px);
      }
      .group-title {
        font-weight: 500;
      }
      .group .info {
        margin-top: 0;
      }
    `]}};function xi(e){return"string"==typeof e?e.slice(0,5):""}e([we({type:Boolean})],ki.prototype,"oneAtATime",void 0),ki=e([_e("kraftvakt-charger-dialog")],ki);const Ai=["entity_id","activate","deactivate","set_current","min_current_a","max_current_a","power_reserve_w","car_connected","actively_charging","charging_window"];let Ci=class extends At{render(){const e=this.config.charging;return X`
      <ha-card .header=${this.localize("charging.shared")}>
        <div class="card-content">
          <ha-form
            .hass=${this.hass}
            .data=${e}
            .schema=${this.sharedSchema}
            .disabled=${this.locked}
            .computeLabel=${e=>this.localize(`charging.${e.name}`)}
            .computeHelper=${e=>this.localize(`charging.${e.name}_sub`)}
            @value-changed=${this.sharedChanged}
          ></ha-form>
        </div>
      </ha-card>
      ${e.enabled?ee:X`<ha-alert alert-type="info">${this.localize("charging.disabled_info")}</ha-alert>`}
      ${this.renderChargers()} ${this.editing?this.renderDialog(this.editing.charger,this.editing.isNew):ee}
    `}renderChargers(){const e=this.config.charging;return X`
      ${this.renderListCard({title:"charging.chargers",sub:"charging.chargers_sub",add:"charging.add",empty:"charging.empty",rows:e.chargers.map(e=>this.row(e)),locked:this.locked||!e.enabled,onAdd:this.addCharger,onMoved:this.chargerMoved,onOpen:this.openRow},X`<div class="switches-info">${this.localize("charging.switches_info")}</div>`)}
      ${0===e.chargers.length?X`
            <kraftvakt-manual-control-warning
              .localize=${this.localize}
              .narrow=${this.narrow}
              kind="chargers"
            ></kraftvakt-manual-control-warning>
          `:ee}
    `}renderDialog(e,t){return X`
      <kraftvakt-charger-dialog
        .hass=${this.hass}
        .localize=${this.localize}
        .capabilities=${this.capabilities}
        .item=${e}
        .isNew=${t}
        .oneAtATime=${this.config.charging.one_at_a_time}
        .usedEntities=${this.entitiesUsedBesides(e.id)}
        .saveErrors=${this.saveErrors.filter(t=>"chargers"===t.section&&t.target===e.id)}
        .locked=${this.locked||!this.config.charging.enabled}
        @item-changed=${this.chargerChanged}
        @item-deleted=${this.chargerDeleted}
        @closed=${()=>this.editing=void 0}
      ></kraftvakt-charger-dialog>
    `}get sharedSchema(){return[{name:"enabled",selector:{boolean:{}}},...this.config.charging.enabled?[{name:"one_at_a_time",selector:{boolean:{}}}]:[]]}row(e){const t=this.hass.language,i=[this.localize("charging.currents",{min:e.min_current_a,max:e.max_current_a}),this.localize("charging.reserve",{power:st(t,e.power_reserve_w,0)}),e.charging_window?this.localize("charging.window",{...e.charging_window}):this.localize("charging.always_allowed")];e.car_connected&&i.push("entity"===e.car_connected.type?this.localize("charging.car_from",{source:e.car_connected.value}):this.localize("charging.car_template")),e.actively_charging&&i.push("template"===e.actively_charging.type?this.localize("charging.charging_template"):this.localize("charging.charging_from",{source:e.actively_charging.value}));const r=this.issues.filter(t=>"chargers"===t.section&&t.target===e.id);return{key:e.id,title:e.entity_id?si(this.hass,this.entityNames,e.entity_id):this.localize("missing.charger_without_entity"),iconPath:a,details:i,errors:r.map(e=>`${this.fieldLabel(e)}: ${this.describeIssue(e)}`),openable:!0}}fieldLabel(e){const t=e.field??"";return Ai.includes(t)?this.localize(`charger.fields.${t}.label`):t}sharedChanged(e){const{enabled:t,one_at_a_time:i}=e.detail.value,a=this.config.charging;this.changeConfig({...this.config,charging:{...a,enabled:t??!1,one_at_a_time:i??a.one_at_a_time}})}chargerMoved(e){const{oldIndex:t,newIndex:i}=e.detail,a=this.config.charging;this.changeConfig({...this.config,charging:{...a,chargers:Xe(a.chargers,t,i)}})}addCharger(){const e=this.capabilities.defaults.chargers,t={id:Je(),entity_id:null,activate:null,deactivate:null,set_current:null,min_current_a:e.min_current_a,max_current_a:e.max_current_a,power_reserve_w:e.power_reserve_w,car_connected:null,actively_charging:null,charging_window:null};this.editing={charger:t,isNew:!0}}openRow(e){const t=this.config.charging.chargers.find(t=>t.id===e.detail);t&&(this.editing={charger:t,isNew:!1})}chargerChanged(e){const t=e.detail,i=this.config.charging.chargers,a=i.some(e=>e.id===t.id);this.changeChargers(a?i.map(e=>e.id===t.id?t:e):[...i,t])}chargerDeleted(e){this.changeChargers(this.config.charging.chargers.filter(t=>t.id!==e.detail))}changeChargers(e){this.changeConfig({...this.config,charging:{...this.config.charging,chargers:e}})}static{this.styles=[At.styles,g`
      .switches-info {
        padding: 12px 16px;
        border-top: 1px solid var(--divider-color);
        font-size: var(--ha-font-size-s, 12px);
        color: var(--secondary-text-color);
      }
    `]}};e([$e()],Ci.prototype,"editing",void 0),Ci=e([_e("kraftvakt-charging-page")],Ci);let Ei=class extends zt{render(){return X`
      ${this.renderCard("general.measurement",[this.entityField("power_sensor"),this.numberField("regulation_window_s")])}
      ${this.renderCard("general.regulation",[this.numberField("power_limit_w"),this.numberField("turn_on_margin_w"),this.intervalField(),this.numberField("wait_at_limit_s")])}
      ${this.renderCard("general.penalty",[this.numberField("penalty_threshold_w")],X`<ha-alert alert-type="info">${this.localize("general.capacity_window_info")}</ha-alert>`)}
    `}renderCard(e,t,i){return X`
      <ha-card .header=${this.localize(e)}>
        <div class="card-content">${this.renderForm(t)} ${i??""}</div>
      </ha-card>
    `}entityField(e){return{name:e,required:!0,selector:{entity:{filter:{domain:"sensor",device_class:"power"},exclude_entities:oi(this.hass)}}}}intervalField(){return this.selectField("regulation_interval",e=>this.localize("general.interval_option",{count:e}))}};Ei=e([_e("kraftvakt-general-page")],Ei);const zi=2*Math.PI*7;class Si extends me{constructor(){super(...arguments),this.start=0,this.end=0}connectedCallback(){super.connectedCallback(),this.hasUpdated&&this.startCountdown()}disconnectedCallback(){this.countdown?.cancel(),super.disconnectedCallback()}updated(e){(e.has("start")||e.has("end"))&&this.startCountdown()}startCountdown(){this.countdown?.cancel();const e=this.renderRoot.querySelector(".fill");if(!e)return;const t=Math.max(0,this.end-Date.now()),i=Math.min(1,t/Math.max(1,this.end-this.start));this.countdown=e.animate(this.keyframes(i),{duration:t,easing:"linear",fill:"forwards"})}}e([we({type:Number})],Si.prototype,"start",void 0),e([we({type:Number})],Si.prototype,"end",void 0);let Vi=class extends Si{render(){return X`
      <svg viewBox="0 0 18 18" aria-hidden="true">
        ${Q`
          <circle class="track" cx="9" cy="9" r=${7}></circle>
          <circle class="fill" cx="9" cy="9" r=${7} stroke-dasharray=${zi} transform="rotate(-90 9 9)"></circle>
        `}
      </svg>
    `}keyframes(e){return[{strokeDashoffset:""+zi*(1-e)},{strokeDashoffset:`${zi}`}]}static{this.styles=g`
    :host {
      display: inline-block;
      width: 20px;
      height: 20px;
    }
    svg {
      display: block;
      width: 100%;
      height: 100%;
    }
    circle {
      fill: none;
      stroke-width: 3;
    }
    .track {
      stroke: rgba(127, 127, 127, 0.24);
    }
    .fill {
      stroke: var(--primary-color);
    }
  `}};Vi=e([_e("kraftvakt-countdown-ring")],Vi);let Hi=class extends Si{render(){return X`<div class="fill"></div>`}keyframes(e){return[{transform:`scaleX(${e})`},{transform:"scaleX(0)"}]}static{this.styles=g`
    :host {
      display: block;
      height: 6px;
      border-radius: 3px;
      overflow: hidden;
      background: rgba(127, 127, 127, 0.24);
    }
    .fill {
      height: 100%;
      background: var(--primary-text-color);
      transform-origin: right;
    }
  `}};Hi=e([_e("kraftvakt-countdown-bar")],Hi);const Mi={kind:"on"},Li={kind:"off"},Ti={kind:"on",icon:r},Pi={kind:"warning",icon:"M20.84 22.73L15.31 17.2L14.5 18V21H9.5V18L6 14.5V9C6 8.7 6.1 8.41 6.25 8.14L1.11 3L2.39 1.73L22.11 21.46L20.84 22.73M18 14.5V9C18 8 17 7 16 7V3H14V7H10.2L17.85 14.65L18 14.5M10 3H8V4.8L10 6.8V3Z"},Ni={kind:"warning",icon:"M20.5,19.85L6.41,5.76L2.41,1.76L1.11,3L4.57,6.46L3,11V19A1,1 0 0,0 4,20H5A1,1 0 0,0 6,19V18H16.11L20.84,22.73L22.11,21.46L20.5,19.85M6.5,15A1.5,1.5 0 0,1 5,13.5A1.5,1.5 0 0,1 6.5,12A1.5,1.5 0 0,1 8,13.5A1.5,1.5 0 0,1 6.5,15M5,10L5.78,7.67L8.11,10H5M17.5,5.5L19,10H13.2L16.12,12.92C16.5,12.17 17.37,11.86 18.12,12.21C18.87,12.57 19.18,13.47 18.83,14.21C18.68,14.5 18.43,14.77 18.12,14.92L21,17.8V11L18.92,5C18.71,4.4 18.14,4 17.5,4H7.2L8.7,5.5H17.5Z"},ji={kind:"off",icon:s},Di={kind:"outline",icon:"M12 2C17.5 2 22 6.5 22 12S17.5 22 12 22 2 17.5 2 12 6.5 2 12 2M12 4C10.1 4 8.4 4.6 7.1 5.7L18.3 16.9C19.3 15.5 20 13.8 20 12C20 7.6 16.4 4 12 4M16.9 18.3L5.7 7.1C4.6 8.4 4 10.1 4 12C4 16.4 7.6 20 12 20C13.9 20 15.6 19.4 16.9 18.3Z"},Oi={kind:"outline",icon:"M12,20A8,8 0 0,0 20,12A8,8 0 0,0 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22C6.47,22 2,17.5 2,12A10,10 0 0,1 12,2M12.5,7V12.25L17,14.92L16.25,16.15L11,13V7H12.5Z"},Wi={kind:"info",icon:"M15,4A8,8 0 0,1 23,12A8,8 0 0,1 15,20A8,8 0 0,1 7,12A8,8 0 0,1 15,4M15,6A6,6 0 0,0 9,12A6,6 0 0,0 15,18A6,6 0 0,0 21,12A6,6 0 0,0 15,6M14,8H15.5V11.78L17.83,14.11L16.77,15.17L14,12.4V8M2,18A1,1 0 0,1 1,17A1,1 0 0,1 2,16H5.83C6.14,16.71 6.54,17.38 7,18H2M3,13A1,1 0 0,1 2,12A1,1 0 0,1 3,11H5.05L5,12L5.05,13H3M4,8A1,1 0 0,1 3,7A1,1 0 0,1 4,6H7C6.54,6.62 6.14,7.29 5.83,8H4Z"},Ri={kind:"off",icon:s};function Ii(e){return e.endsWith(":00")?e.slice(0,-3):e}const Fi=[1,2,5,10,20,50];let Ui=class extends me{constructor(){super(...arguments),this.narrow=!1}render(){if(!this.status)return ee;const e=this.status;return X`
      <div class="cards">
        ${this.renderRegulationCard(e)} ${e.running?this.renderPriorityCard(e):ee}
      </div>
    `}renderRegulationCard(e){return X`
      <ha-card class="regulation">
        <div class="card-header">
          <span>${this.localize("status.regulation")}</span>
          <span class="chip ${e.running?"running":"off"}">
            <span class="dot"></span>
            ${this.localize(e.running?"status.running":"status.stopped")}
          </span>
          ${e.running&&e.safe_state?X`<span class="chip alarm">${this.localize("status.safe_state_chip")}</span>`:ee}
          ${e.running&&e.penalty.active?X`<span class="chip alarm">${this.localize("status.penalty_chip")}</span>`:ee}
          <span class="spacer"></span>
          ${e.running&&e.next_decision_at?this.renderNextDecision(e,e.next_decision_at):ee}
        </div>
        <div class="card-content">
          ${this.runningError?X`<ha-alert alert-type="error">${this.runningError}</ha-alert>`:ee}
          ${e.running?this.renderRunning(e):this.renderStopped(e)}
        </div>
        <div class="card-actions">${this.renderStartStop(e)}</div>
      </ha-card>
    `}renderStartStop(e){return X`
      <kraftvakt-running-button
        .hass=${this.hass}
        .localize=${this.localize}
        .running=${e.running}
        .disabled=${!e.running&&e.missing.length>0}
        @running-error=${e=>this.runningError=e.detail}
      ></kraftvakt-running-button>
    `}renderRunning(e){const t=this.hass.language,i=li(this.hass,this.config?.config.general.power_sensor??"");return X`
      ${e.safe_state?this.renderSafeState(null!==i):ee} ${e.penalty.active?this.renderPenalty(e):ee}
      <div class="stats">
        ${this.renderStat("power-now","status.power_now",ot(t,i),this.localize("status.momentary"))}
        ${this.renderStat("regulation-average","status.regulation_average",ot(t,e.regulation_average_w),this.localize("status.average_over_seconds",{seconds:e.regulation_window_s}))}
        ${this.renderStat("capacity-average","status.capacity_average",ot(t,e.capacity_average_w),this.localize("status.average_over_hour"),(a=e.capacity_average_w,null!==a&&a>e.power_limit_w))}
        ${this.renderStat("power-limit","status.power_limit",ot(t,e.power_limit_w))}
      </div>
      ${this.renderMeter(e,i)}
    `;var a}renderNextDecision(e,t){const i=Date.parse(t),a=e.regulation_window_s*e.regulation_interval*1e3,r=dt(this.hass.language,t);return X`
      <span class="next-decision" title=${this.localize("status.next_decision_at",{time:r})}>
        ${this.narrow?ee:this.localize("status.next_decision")}
        <kraftvakt-countdown-ring .start=${i-a} .end=${i}></kraftvakt-countdown-ring>
      </span>
    `}renderSafeState(e){const t=this.config?.config.general.power_sensor??"",i=this.hass.states[t]?.attributes.friendly_name??t;return X`
      <ha-alert alert-type=${e?"info":"error"} .title=${this.localize("status.safe_state_title")}>
        ${this.localize(e?"status.safe_state_back_text":"status.safe_state_text",{sensor:i})}
      </ha-alert>
    `}renderPenalty(e){const t=(i=this.hass.language,a=Math.max(0,e.penalty.overconsumption_wh),st(i,a/1e3,2));var i,a;const r=e.penalty.recovery_started?"status.recovery_started":"status.recovery_not_started";return X`
      <ha-alert alert-type="warning" .title=${this.localize("status.penalty_title")}>
        ${this.localize("status.penalty_text")}
        <div class="penalty-details">${this.localize("status.overconsumption_left",{energy:t})} · ${this.localize(r)}</div>
      </ha-alert>
    `}renderStat(e,t,i,a,r=!1){return X`
      <div class="stat">
        <div class="stat-label">${e?X`<span class="swatch ${e}"></span>`:ee}${this.localize(t)}</div>
        <div class="stat-value ${r?"alarm":""}">${i} <small>kW</small></div>
        ${a?X`<div class="stat-period">${a}</div>`:ee}
      </div>
    `}renderMeter(e,t){const i=e=>null===e?null:e/1e3,a=e.power_limit_w/1e3,r=i(t),n=i(e.capacity_average_w),s=i(e.regulation_average_w),o=[r,n,s],{step:l,end:c}=function(e){const t=Fi.find(t=>e/t<=15)??Fi[Fi.length-1];return{step:t,end:Math.ceil(e/t)*t}}(Math.max(1.2*a,...o.map(e=>e??0))),d=e=>100*Math.min(e,c)/c+"%",h=this.hass.language,p=Array.from({length:c/l+1},(e,t)=>t*l),g=this.narrow?3:2,u=p.filter((e,t)=>t%g===0),v=(e,t,i)=>null===i?ee:X`<span
            class="marker ${e}"
            style="left: ${d(i)}"
            title="${this.localize(t)} ${st(h,i,2)} kW"
          ></span>`;return X`
      <div class="meter">
        <div class="markers">
          ${v("power-limit","status.power_limit",a)}
          ${v("capacity-average","status.capacity_average",n)}
          ${v("regulation-average","status.regulation_average",s)}
        </div>
        <div class="bar">
          ${null===r?ee:X`<div class="fill power-now" style="width: ${d(r)}"></div>`}
        </div>
        <div class="ticks">${p.map(e=>X`<span style="left: ${d(e)}"></span>`)}</div>
        <div class="scale">
          ${u.map((e,t)=>X`<span class=${0===e?"start":e===c?"end":""} style="left: ${d(e)}"
                >${st(h,e,0)}${t===u.length-1?" kW":""}</span
              >`)}
        </div>
      </div>
    `}renderPriorityCard(e){const t=function(e){const t=e.appliances.map(e=>({kind:"appliance",appliance:e,on:e.on}));if(null!==e.ev_charging_position){const i=e.chargers,a=i.some(e=>e.activated&&!e.bypassed);t.splice(e.ev_charging_position,0,{kind:"ev_charging",chargers:i,on:a})}return t}(e),i=function(e){const t=e.map(e=>e.on).lastIndexOf(!0),i=e.slice(t+1).some(e=>"ev_charging"===e.kind||!e.appliance.excluded);return t>=0&&i?t:-1}(t);return X`
      <ha-card>
        <div class="card-header">
          <span>${this.localize("status.priority_list")}</span>
        </div>
        ${0===t.length?X`<div class="card-content empty">${this.localize("status.no_appliances")}</div>`:X`<div class="list">
              ${t.map((t,a)=>X`
                  ${"appliance"===t.kind?this.renderApplianceRow(t.appliance,a+1):this.renderEvCharging(t.chargers,a+1)}
                  ${a===i?this.renderCutOff(e):ee}
                `)}
            </div>`}
      </ha-card>
    `}renderApplianceRow(e,t){return X`
      <div class="row ${e.on?"":"off"} ${e.excluded?"excluded":""}">
        <span class="rank">${t}</span>
        <div class="row-title">
          ${this.renderApplianceIcon(e)}<span class="name">${e.name}</span>
          ${e.variant?X`<span class="variant">${e.variant}</span>`:ee}
        </div>
        <span></span>
        ${this.renderWaiting(e,"M12,20A7,7 0 0,1 5,13A7,7 0 0,1 12,6A7,7 0 0,1 19,13A7,7 0 0,1 12,20M19.03,7.39L20.45,5.97C20,5.46 19.55,5 19.04,4.56L17.62,6C16.07,4.74 14.12,4 12,4A9,9 0 0,0 3,13A9,9 0 0,0 12,22C17,22 21,17.97 21,13C21,10.88 20.26,8.93 19.03,7.39M11,14H13V8H11M15,1H9V3H15V1Z","status.delayed_turn_on","status.waiting_ends_at")}
        ${this.renderApplianceChip(e)}
      </div>
    `}renderApplianceChip(e){return e.excluded?this.renderChip(Di,"status.chip_excluded","status.excluded"):e.on?this.renderChip(Mi,"status.on","status.on"):this.renderChip(Li,"status.off","status.off")}renderApplianceIcon(e){const t=this.config?.config.appliances.find(t=>t.id===e.id)?.entity_id,i=t?this.hass.states[t]:void 0,a=e.on?"on":"";return i?X`<ha-state-icon class="device-icon ${a}" .hass=${this.hass} .stateObj=${i}></ha-state-icon>`:X`<ha-svg-icon class="device-icon ${a}" .path=${"M7,2V13H10V22L17,10H13L17,2H7Z"}></ha-svg-icon>`}renderEvCharging(e,i){const s=e.filter(e=>e.charging).length;return X`
      <div class="row group">
        <span class="rank">${i}</span>
        <div class="row-title">
          <ha-svg-icon class="ev-icon" .path=${t}></ha-svg-icon>
          <span class="name">${this.localize("status.ev_charging")}</span>
          ${0===e.length?X`<span class="row-sub">${this.localize("status.no_chargers")}</span>`:ee}
        </div>
        ${0===e.length?X`<span></span>`:X`<span
              class="charging-count"
              title=${this.localize("status.chargers_charging",{charging:s,total:e.length})}
            >
              <ha-svg-icon .path=${r}></ha-svg-icon>${s} / ${e.length}
            </span>`}
      </div>
      ${e.map(e=>X`
          <div class="row charger ${e.activated?"":"off"}">
            <span class="rank"></span>
            <div class="row-title">
              <ha-svg-icon class="device-icon ev ${e.activated?"on":""}" .path=${a}></ha-svg-icon>
              <span class="name">${e.name}</span>
            </div>
            ${this.renderAmperes(e)}
            ${this.renderWaiting(e,n,"status.delayed_turn_on","status.next_ampere_at")}
            ${this.renderChargerChip(e)}
          </div>
        `)}
    `}renderWaiting(e,t,i,a){if(this.narrow)return ee;if(!e.waiting_since||!e.waiting_ends_at)return X`<span></span>`;const r=dt(this.hass.language,e.waiting_ends_at);return X`
      <span class="waiting" title="${this.localize(i)}: ${this.localize(a,{time:r})}">
        <ha-svg-icon .path=${t}></ha-svg-icon>
        <kraftvakt-countdown-bar
          .start=${Date.parse(e.waiting_since)}
          .end=${Date.parse(e.waiting_ends_at)}
        ></kraftvakt-countdown-bar>
      </span>
    `}renderAmperes(e){const t=this.chargerConfig(e);if(!t)return X`<span></span>`;const i=t.max_current_a-t.min_current_a+1,a=null===e.current_a?0:e.current_a-t.min_current_a+1,r=e.bypassed?"on bypassed":"on";return X`
      <span class="amperes">
        ${this.narrow?ee:X`<span class="current ${null===e.current_a?"none":""}"
              >${null===e.current_a?"–":this.localize("status.amperes",{current:e.current_a})}</span
            >`}
        <span class="ampere-steps ${i>16?"small":""}">
          ${Array.from({length:i},(e,t)=>X`<span class="ampere ${t<a?r:""}"></span>`)}
        </span>
      </span>
    `}renderChargerChip(e){const t=this.chargerConfig(e)?.charging_window;if(null===e.excluded)return this.renderChip(Ri,"status.chip_first_decision","status.first_decision");if(e.excluded)return this.renderChip(Di,"status.chip_excluded","status.excluded");if(!e.allowed&&t){const e={start:Ii(t.start),end:Ii(t.end)};return this.renderChip(Oi,"status.chip_window","status.outside_window",e,{...t})}if(e.bypassed&&!1===e.car_connected)return this.renderChip(Ni,"status.chip_no_car","status.bypassed_no_car");if(e.bypassed)return this.renderChip(Pi,"status.chip_not_charging","status.bypassed");if(e.waiting)return this.renderChip(ji,"status.chip_queued","status.waiting_charger");if(e.window_overridden&&e.activated)return this.renderChip(Wi,"status.chip_override","status.window_overridden");if(e.charging){const t={current:e.current_a??0};return this.renderChip(Ti,"status.chip_charging","status.charging_at",{},t)}return e.activated?this.renderChip(Mi,"status.activated","status.activated_not_charging"):this.renderChip(Li,"status.deactivated","status.deactivated")}renderChip(e,t,i,a={},r=a){return X`
      <span class="state chip ${e.kind}" title=${this.localize(i,r)}>
        ${e.icon?X`<ha-svg-icon .path=${e.icon}></ha-svg-icon>`:X`<span class="dot"></span>`}
        ${this.localize(t,a)}
      </span>
    `}renderCutOff(e){const t=this.hass.language,i=e.regulation_average_w,a=null===i?0:e.power_limit_w-i;return X`
      <div class="cut-off" title=${this.localize("status.power_runs_out")}>
        <ha-svg-icon .path=${"M11,4H13V16L18.5,10.5L19.92,11.92L12,19.84L4.08,11.92L5.5,10.5L11,16V4Z"}></ha-svg-icon>
        ${a>0?this.localize("status.free_power",{power:ot(t,a),share:ct(t,a/e.power_limit_w)}):ee}
      </div>
    `}chargerConfig(e){return this.config?.config.charging.chargers.find(t=>t.id===e.id)}renderStopped(e){return 0===e.missing.length?X`<ha-alert alert-type="info">${this.localize("status.stopped_info")}</ha-alert>`:X`
      <ha-alert alert-type="warning" .title=${this.localize("status.incomplete_title")}>
        <ul class="missing">
          ${e.missing.map(e=>{const t=function(e){return"general"===e.section&&e.field&&yt.has(e.field)?"advanced":_t[e.section]}(e);return X`
              <li>
                ${function(e,t,i){const a={item:bt(e,t,i),action:e.field&&ft[e.field]?i(ft[e.field]):e.field??"",code:e.code};return i(mt[e.code]??"missing.unknown",a)}(e,this.config,this.localize)}
                <a href="${rt}/${t}" @click=${e=>this.openPage(e,t)}>
                  ${this.localize(`tabs.${t}`)}
                </a>
              </li>
            `})}
        </ul>
      </ha-alert>
    `}openPage(e,t){e.preventDefault(),nt(t)}static{this.styles=g`
    :host {
      display: block;
      --kraftvakt-grid-color: var(--energy-grid-consumption-color, #488fc2);
      --kraftvakt-now-color: var(--secondary-text-color);
      --kraftvakt-ev-color: var(--teal-color, #009688);
      --kraftvakt-on-color: var(--state-active-color, var(--amber-color, #ffc107));
    }
    .cards {
      display: grid;
      grid-template-columns: minmax(0, 1fr);
      gap: 16px;
    }
    :host([narrow]) .cards {
      gap: 8px;
    }
    .card-header {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
      min-height: 40px;
      padding: 12px 16px;
      font-size: var(--ha-font-size-xl, 20px);
    }
    .spacer {
      flex: 1;
    }
    .card-content {
      display: grid;
      gap: 16px;
      padding: 0 16px 16px;
    }
    .card-content:empty {
      display: none;
    }
    .card-actions {
      display: flex;
      justify-content: flex-end;
      padding: 8px 16px;
      border-top: 1px solid var(--divider-color);
    }
    .chip {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 2px 10px;
      border-radius: 999px;
      font-size: var(--ha-font-size-s, 12px);
      font-weight: 500;
      line-height: 20px;
      white-space: nowrap;
      background: var(--kraftvakt-chip-off-background, rgba(127, 127, 127, 0.16));
      color: var(--secondary-text-color);
    }
    .chip .dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: currentColor;
    }
    .chip.running,
    .chip.on {
      background: rgba(var(--rgb-success-color, 67, 160, 71), 0.16);
      color: var(--success-color, #43a047);
    }
    .chip.alarm {
      background: rgba(var(--rgb-error-color, 219, 68, 55), 0.16);
      color: var(--error-color, #db4437);
    }
    .stats {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 12px;
    }
    .stat {
      padding: 10px 12px;
      border-radius: var(--ha-border-radius-lg, 12px);
      background: var(--secondary-background-color);
    }
    .stat-label {
      display: flex;
      align-items: center;
      gap: 6px;
      color: var(--secondary-text-color);
      font-size: var(--ha-font-size-s, 12px);
    }
    .stat-value {
      font-size: 26px;
    }
    .stat-period {
      color: var(--secondary-text-color);
      font-size: var(--ha-font-size-s, 12px);
    }
    .stat-value small {
      font-size: var(--ha-font-size-m, 14px);
      color: var(--secondary-text-color);
    }
    :host([narrow]) .stats {
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
    }
    :host([narrow]) .stat {
      padding: 8px;
    }
    :host([narrow]) .stat-value {
      font-size: 20px;
    }
    .stat-value.alarm {
      color: var(--error-color);
    }
    .swatch {
      display: inline-block;
      flex: none;
    }
    .swatch.power-now {
      width: 12px;
      height: 8px;
      border-radius: 4px;
      background: var(--kraftvakt-now-color);
    }
    .swatch:not(.power-now),
    .meter .marker {
      width: 0;
      height: 0;
      border-inline: 5px solid transparent;
      border-top: 7px solid var(--marker-color);
    }
    .capacity-average {
      --marker-color: var(--kraftvakt-grid-color);
    }
    .regulation-average {
      --marker-color: var(--primary-text-color);
    }
    .power-limit {
      --marker-color: var(--error-color);
    }
    .meter .markers {
      position: relative;
      height: 9px;
    }
    .meter .marker {
      position: absolute;
      top: 0;
      transform: translateX(-50%);
      transition: left 0.6s ease;
    }
    .meter .bar {
      position: relative;
      height: 12px;
      overflow: hidden;
      border-radius: 6px;
      background: var(--secondary-background-color);
    }
    .meter .fill {
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      border-radius: 6px;
      background: var(--kraftvakt-now-color);
      transition: width 0.6s ease;
    }
    .meter .ticks {
      position: relative;
      height: 5px;
      margin-top: 2px;
    }
    .meter .ticks span {
      position: absolute;
      top: 0;
      width: 1px;
      height: 100%;
      margin-left: -0.5px;
      background: var(--secondary-text-color);
      opacity: 0.6;
    }
    .meter .scale {
      position: relative;
      height: 18px;
      margin-top: 2px;
      font-size: var(--ha-font-size-s, 12px);
      color: var(--secondary-text-color);
    }
    .meter .scale span {
      position: absolute;
      transform: translateX(-50%);
      white-space: nowrap;
    }
    .meter .scale .start {
      transform: none;
    }
    .meter .scale .end {
      transform: translateX(-100%);
    }
    .penalty-details {
      margin-top: 8px;
    }
    .empty {
      color: var(--secondary-text-color);
    }
    .list {
      display: grid;
      grid-template-columns: 24px minmax(0, 2fr) minmax(max-content, 1.3fr) ${p(120)}px max-content;
      column-gap: 12px;
    }
    :host([narrow]) .list {
      grid-template-columns: 20px minmax(0, 1fr) max-content max-content;
      column-gap: 8px;
    }
    .row {
      grid-column: 1 / -1;
      display: grid;
      grid-template-columns: subgrid;
      align-items: center;
      min-height: 48px;
      padding: 4px 16px;
      border-top: 1px solid var(--divider-color);
      box-sizing: border-box;
    }
    :host([narrow]) .row {
      padding: 4px 12px;
    }
    .row.group,
    .row.charger {
      background: color-mix(in srgb, var(--kraftvakt-ev-color) 7%, transparent);
    }
    .row.charger {
      min-height: 44px;
      border-top-style: dashed;
    }
    .row.off .name {
      color: var(--secondary-text-color);
    }
    .row.excluded .row-title {
      opacity: 0.5;
    }
    .row.charger .row-title {
      padding-inline-start: 24px;
    }
    :host([narrow]) .row.charger .row-title {
      padding-inline-start: 16px;
    }
    .rank {
      text-align: center;
      color: var(--secondary-text-color);
    }
    .row > .chip {
      justify-self: start;
    }
    :host([narrow]) .row > .chip {
      justify-self: end;
    }
    .chip ha-svg-icon {
      --mdc-icon-size: 16px;
    }
    .chip.warning {
      background: rgba(var(--rgb-warning-color, 255, 166, 0), 0.16);
      color: var(--warning-color, #ffa600);
    }
    .chip.outline {
      background: none;
      box-shadow: inset 0 0 0 1px var(--divider-color);
    }
    .chip.info {
      background: rgba(var(--rgb-info-color, 3, 155, 229), 0.16);
      color: var(--info-color, #039be5);
    }
    .cut-off {
      grid-column: 1 / -1;
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 4px 16px;
      border-top: 1px solid var(--divider-color);
      color: var(--primary-color);
      font-size: var(--ha-font-size-s, 12px);
      white-space: nowrap;
    }
    .cut-off::before,
    .cut-off::after {
      content: "";
      flex: 1;
      border-top: 2px dashed var(--primary-color);
    }
    .cut-off ha-svg-icon {
      --mdc-icon-size: 14px;
    }
    .next-decision {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      font-size: var(--ha-font-size-m, 14px);
      color: var(--secondary-text-color);
    }
    .waiting {
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .waiting kraftvakt-countdown-bar {
      flex: 1;
    }
    .waiting ha-svg-icon,
    .charging-count ha-svg-icon {
      flex: none;
      --mdc-icon-size: 16px;
      color: var(--secondary-text-color);
    }
    .charging-count {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      color: var(--secondary-text-color);
      font-size: var(--ha-font-size-s, 12px);
    }
    .charging-count ha-svg-icon {
      color: var(--kraftvakt-ev-color);
    }
    .amperes {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .amperes .current {
      min-width: 40px;
      text-align: end;
      font-weight: 500;
    }
    .amperes .current.none {
      color: var(--secondary-text-color);
      font-weight: normal;
    }
    .ampere-steps {
      display: inline-flex;
      gap: 2px;
    }
    .ampere {
      width: 3px;
      height: 14px;
      border-radius: 1px;
      background: rgba(127, 127, 127, 0.32);
    }
    .ampere-steps.small {
      gap: 1px;
    }
    .ampere-steps.small .ampere {
      width: 2px;
    }
    .ampere.on {
      background: var(--kraftvakt-ev-color);
    }
    .ampere.on.bypassed {
      background: repeating-linear-gradient(
        45deg,
        var(--secondary-text-color) 0 2px,
        rgba(127, 127, 127, 0.16) 2px 4px
      );
    }
    :host([narrow]) .ampere-steps {
      gap: 1px;
    }
    :host([narrow]) .ampere {
      width: 2px;
      height: 12px;
    }
    .row-title {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 6px 10px;
      overflow-wrap: anywhere;
    }
    .row-title ha-svg-icon,
    .row-title ha-state-icon {
      flex: none;
      --mdc-icon-size: 20px;
      color: var(--state-inactive-color, var(--secondary-text-color));
    }
    .row-title .device-icon.on {
      color: var(--kraftvakt-on-color);
    }
    .row-title .device-icon.ev.on,
    .row-title .ev-icon {
      color: var(--kraftvakt-ev-color);
    }
    .row.group .name {
      font-weight: 500;
    }
    .row-sub {
      color: var(--secondary-text-color);
      font-size: var(--ha-font-size-s, 12px);
    }
    .variant {
      display: inline-block;
      padding: 0 8px;
      border-radius: 999px;
      font-size: var(--ha-font-size-s, 12px);
      background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.16);
      color: var(--primary-color);
    }
    ul.missing {
      margin: 6px 0 0;
      padding-inline-start: 18px;
    }
    ul.missing a {
      color: var(--primary-color);
    }
  `}};e([we({attribute:!1})],Ui.prototype,"hass",void 0),e([we({attribute:!1})],Ui.prototype,"localize",void 0),e([we({type:Boolean,reflect:!0})],Ui.prototype,"narrow",void 0),e([we({attribute:!1})],Ui.prototype,"status",void 0),e([we({attribute:!1})],Ui.prototype,"config",void 0),e([$e()],Ui.prototype,"runningError",void 0),Ui=e([_e("kraftvakt-status-page")],Ui);const Bi={status:"M3,13H5.79L10.1,4.79L11.28,13.75L14.5,9.66L17.83,13H21V15H17L14.67,12.67L9.92,18.73L8.94,11.31L7,15H3V13Z",general:"M12,15.5A3.5,3.5 0 0,1 8.5,12A3.5,3.5 0 0,1 12,8.5A3.5,3.5 0 0,1 15.5,12A3.5,3.5 0 0,1 12,15.5M19.43,12.97C19.47,12.65 19.5,12.33 19.5,12C19.5,11.67 19.47,11.34 19.43,11L21.54,9.37C21.73,9.22 21.78,8.95 21.66,8.73L19.66,5.27C19.54,5.05 19.27,4.96 19.05,5.05L16.56,6.05C16.04,5.66 15.5,5.32 14.87,5.07L14.5,2.42C14.46,2.18 14.25,2 14,2H10C9.75,2 9.54,2.18 9.5,2.42L9.13,5.07C8.5,5.32 7.96,5.66 7.44,6.05L4.95,5.05C4.73,4.96 4.46,5.05 4.34,5.27L2.34,8.73C2.21,8.95 2.27,9.22 2.46,9.37L4.57,11C4.53,11.34 4.5,11.67 4.5,12C4.5,12.33 4.53,12.65 4.57,12.97L2.46,14.63C2.27,14.78 2.21,15.05 2.34,15.27L4.34,18.73C4.46,18.95 4.73,19.03 4.95,18.95L7.44,17.94C7.96,18.34 8.5,18.68 9.13,18.93L9.5,21.58C9.54,21.82 9.75,22 10,22H14C14.25,22 14.46,21.82 14.5,21.58L14.87,18.93C15.5,18.67 16.04,18.34 16.56,17.94L19.05,18.95C19.27,19.03 19.54,18.95 19.66,18.73L21.66,15.27C21.78,15.05 21.73,14.78 21.54,14.63L19.43,12.97Z",appliances:"M7,13V11H21V13H7M7,19V17H21V19H7M7,7V5H21V7H7M3,8V5H2V4H4V8H3M2,17V16H5V20H2V19H4V18.5H3V17.5H4V17H2M4.25,10A0.75,0.75 0 0,1 5,10.75C5,10.95 4.92,11.14 4.79,11.27L3.12,13H5V14H2V13.08L4,11H2V10H4.25Z",charging:t,advanced:"M3,17V19H9V17H3M3,5V7H13V5H3M13,21V19H21V17H13V15H11V21H13M7,9V11H3V13H7V15H9V9H7M21,13V11H11V13H21M15,9H17V7H21V5H17V3H15V9Z"},qi={general:We`kraftvakt-general-page`,appliances:We`kraftvakt-appliances-page`,charging:We`kraftvakt-charging-page`,advanced:We`kraftvakt-advanced-page`};let Ki=class extends me{constructor(){super(...arguments),this.narrow=!1,this.haElementsReady=!1,this.saveErrors=[],this.saving=!1,this.localize=tt("en"),this.warnBeforeUnload=e=>{this.dirty&&e.preventDefault()}}connectedCallback(){super.connectedCallback(),window.addEventListener("beforeunload",this.warnBeforeUnload),customElements.whenDefined("ha-form").then(()=>{this.haElementsReady=!0}),this.hass&&this.subscribe()}disconnectedCallback(){super.disconnectedCallback(),window.removeEventListener("beforeunload",this.warnBeforeUnload),this.unsubscribe()}willUpdate(e){e.has("hass")&&this.hass?.language!==e.get("hass")?.language&&(this.localize=tt(this.hass?.language??"en"),this.hass?.loadFragmentTranslation("config")),e.has("hass")&&this.hass&&!this.unsubscribeStatus&&this.subscribe()}updated(e){e.has("route")&&this.openAppliancesFromConfigureButton()}render(){if(!this.hass||!this.haElementsReady)return X``;const e=this.currentPage;return X`
      <div class="toolbar">
        <ha-menu-button .hass=${this.hass} .narrow=${this.narrow}></ha-menu-button>
        <div class="title">${this.localize("panel.title")}</div>
        <ha-tab-group @wa-tab-show=${this.tabShown}>
          ${Object.entries(Bi).map(([t,i])=>X`
              <ha-tab-group-tab
                slot="nav"
                panel=${t}
                .active=${je(t===e)}
                title=${this.tabLabel(t)}
              >
                <ha-svg-icon .path=${i}></ha-svg-icon>
                <span class="tab-label">${this.tabLabel(t)}</span>
              </ha-tab-group-tab>
            `)}
        </ha-tab-group>
      </div>
      <div class="content" @draft-changed=${this.draftChanged}>${this.renderLoadError()} ${this.renderPage(e)}</div>
      <kraftvakt-confirm-dialog
        .open=${void 0!==this.leavingTo}
        .heading=${this.localize("config.leave_title")}
        .text=${this.localize("config.leave_text")}
        .confirmText=${this.localize("config.leave")}
        .cancelText=${this.localize("config.stay")}
        @confirm=${this.leaveConfirmed}
        @cancel=${this.leaveCancelled}
      ></kraftvakt-confirm-dialog>
    `}renderLoadError(){if(void 0===this.loadError)return"";const e=Fe(this.loadError)&&"not_loaded"===this.loadError.code?this.localize("panel.not_loaded"):this.localize("panel.error",{message:Ue(this.loadError)});return X`<ha-alert alert-type="error">${e}</ha-alert>`}renderPage(e){switch(e){case"status":return X`
          <kraftvakt-status-page
            .hass=${this.hass}
            .localize=${this.localize}
            .narrow=${this.narrow}
            .status=${this.status}
            .config=${this.config}
          ></kraftvakt-status-page>
        `;case"general":case"appliances":case"charging":case"advanced":return this.renderConfigPage(e)}}renderConfigPage(e){if(!(this.hass&&this.status&&this.config&&this.draft&&this.capabilities))return"";const t=this.status.running,i=t?[]:function(e,t,i){return[...ii("general",void 0,e.general,t.limits.general,!0),...e.appliances.flatMap(e=>Qt(e,t,i)),...e.charging.chargers.flatMap(e=>Yt(e,t,i))]}(this.draft,this.capabilities,this.hass.states),a=!t&&(this.dirty||this.saveErrors.length>0),r=t?[]:this.pageIssues(i);return X`
      ${t?X`<kraftvakt-locked-banner
            .hass=${this.hass}
            .localize=${this.localize}
            .narrow=${this.narrow}
          ></kraftvakt-locked-banner>`:""}
      ${this.renderConfigPageContent(e,t?this.config.config:this.draft,r,t)}
      ${a?X`
            <kraftvakt-save-bar
              .localize=${this.localize}
              .errorCount=${i.length}
              .saving=${this.saving}
              .message=${this.saveMessage}
              @save=${this.save}
              @discard=${this.discard}
            ></kraftvakt-save-bar>
          `:""}
    `}renderConfigPageContent(e,t,i,a){const r=qi[e];return Ie`
      <${r}
        .hass=${this.hass}
        .localize=${this.localize}
        .narrow=${this.narrow}
        .config=${t}
        .entityNames=${this.config?.entity_names??{}}
        .capabilities=${this.capabilities}
        .issues=${i}
        .saveErrors=${this.saveErrors}
        .locked=${a}
      ></${r}>
    `}pageIssues(e){return this.draft?[...e,...this.saveErrors,...qt(this.draft)]:[]}get dirty(){return void 0!==this.draft&&(e=this.draft,t=this.savedConfig,!(JSON.stringify(e)===JSON.stringify(t)));var e,t}get savedConfig(){return this.config&&Ye(this.config.config)}draftChanged(e){e.type!==Ge||this.status?.running||(this.draft=Ye(e.detail))}async save(){if(this.hass&&this.draft){this.saving=!0,this.saveMessage=void 0;try{const e=await((e,t)=>e.callWS({type:"kraftvakt/config/save",config:t}))(this.hass,this.draft);e.saved?(this.saveErrors=[],await this.loadConfig({resetDraft:!0})):(this.saveErrors=e.errors,this.saveMessage=this.localize("config.not_saved"))}catch(e){this.saveMessage=Fe(e)&&"regulation_running"===e.code?this.localize("config.save_refused_running"):this.localize("panel.error",{message:Ue(e)})}finally{this.saving=!1}}}discard(){this.resetDraft()}resetDraft(){this.draft=this.savedConfig,this.saveErrors=[],this.saveMessage=void 0}leaveConfirmed(){const e=this.leavingTo;this.leavingTo=void 0,this.resetDraft(),e&&nt(e)}leaveCancelled(){this.leavingTo=void 0}get currentPage(){return function(e){const t=e.split("/")[1]??"";return at.includes(t)?t:"status"}(this.route?.path??"")}tabLabel(e){return this.localize(`tabs.${e}`)}tabShown(e){const t=e.detail.name;t!==this.currentPage&&("status"===t&&this.dirty?this.leavingTo=t:nt(t))}subscribe(){var e,t;this.hass&&(this.unsubscribeStatus=(e=this.hass,t=e=>this.statusReceived(e),e.connection.subscribeMessage(t,{type:"kraftvakt/status/subscribe"})),this.unsubscribeStatus.catch(e=>{this.loadError=e,this.unsubscribeStatus=void 0}),(e=>e.callWS({type:"kraftvakt/capabilities"}))(this.hass).then(e=>this.capabilities=e).catch(e=>this.loadError=e))}unsubscribe(){this.unsubscribeStatus?.then(e=>e()).catch(()=>{}),this.unsubscribeStatus=void 0}statusReceived(e){const t=this.status;this.status=e,this.loadError=void 0,void 0!==t&&t.running===e.running&&t.power_limit_w===e.power_limit_w&&JSON.stringify(t.missing)===JSON.stringify(e.missing)||this.loadConfig()}async loadConfig(e={}){var t;if(this.hass)try{const i=this.dirty&&!e.resetDraft&&!this.status?.running;this.config=await(t=this.hass,t.callWS({type:"kraftvakt/config/get"})),i||this.resetDraft()}catch(e){this.loadError=e}}openAppliancesFromConfigureButton(){new URLSearchParams(window.location.search).has("config_entry")&&nt("appliances",{replace:!0})}static{this.styles=g`
    :host {
      display: block;
      min-height: 100vh;
      background: var(--primary-background-color);
      color: var(--primary-text-color);
    }
    .toolbar {
      display: flex;
      align-items: center;
      gap: 8px;
      height: var(--header-height, 56px);
      padding: 0 12px;
      box-sizing: border-box;
      background: var(--app-header-background-color, var(--primary-color));
      color: var(--app-header-text-color, var(--text-primary-color));
      border-bottom: var(--app-header-border-bottom, none);
    }
    .title {
      font-size: var(--ha-font-size-xl, 20px);
      margin-inline-end: 16px;
    }
    ha-tab-group {
      flex: 1;
      min-width: 0;
      align-self: stretch;
      --ha-tab-active-text-color: var(--app-header-text-color, var(--text-primary-color));
      --ha-tab-indicator-color: var(--app-header-text-color, var(--text-primary-color));
      --ha-tab-track-color: transparent;
    }
    ha-tab-group-tab {
      height: 100%;
    }
    .tab-label {
      margin-inline-start: 8px;
    }
    :host([narrow]) .title {
      display: none;
    }
    :host([narrow]) .tab-label {
      display: none;
    }
    .content {
      max-width: 1040px;
      margin: 0 auto;
      padding: 16px;
    }
    :host([narrow]) .content {
      padding: 8px;
    }
  `}};e([we({attribute:!1})],Ki.prototype,"hass",void 0),e([we({type:Boolean,reflect:!0})],Ki.prototype,"narrow",void 0),e([we({attribute:!1})],Ki.prototype,"route",void 0),e([$e()],Ki.prototype,"haElementsReady",void 0),e([$e()],Ki.prototype,"status",void 0),e([$e()],Ki.prototype,"config",void 0),e([$e()],Ki.prototype,"loadError",void 0),e([$e()],Ki.prototype,"capabilities",void 0),e([$e()],Ki.prototype,"draft",void 0),e([$e()],Ki.prototype,"saveErrors",void 0),e([$e()],Ki.prototype,"saveMessage",void 0),e([$e()],Ki.prototype,"saving",void 0),e([$e()],Ki.prototype,"leavingTo",void 0),Ki=e([_e("kraftvakt-panel")],Ki);export{Ki as KraftvaktPanel};
