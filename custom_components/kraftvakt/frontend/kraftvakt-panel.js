function e(e,t,i,r){var a,n=arguments.length,s=n<3?t:null===r?r=Object.getOwnPropertyDescriptor(t,i):r;if("object"==typeof Reflect&&"function"==typeof Reflect.decorate)s=Reflect.decorate(e,t,i,r);else for(var o=e.length-1;o>=0;o--)(a=e[o])&&(s=(n<3?a(s):n>3?a(t,i,s):a(t,i))||s);return n>3&&s&&Object.defineProperty(t,i,s),s}"function"==typeof SuppressedError&&SuppressedError;var t="M18.92 2C18.72 1.42 18.16 1 17.5 1H6.5C5.84 1 5.29 1.42 5.08 2L3 8V16C3 16.55 3.45 17 4 17H5C5.55 17 6 16.55 6 16V15H18V16C18 16.55 18.45 17 19 17H20C20.55 17 21 16.55 21 16V8L18.92 2M6.5 12C5.67 12 5 11.33 5 10.5S5.67 9 6.5 9 8 9.67 8 10.5 7.33 12 6.5 12M17.5 12C16.67 12 16 11.33 16 10.5S16.67 9 17.5 9 19 9.67 19 10.5 18.33 12 17.5 12M5 7L6.5 2.5H17.5L19 7H5M7 20H11V18L17 21H13V23L7 20Z",i="M21 11H3V9H21V11M21 13H3V15H21V13Z",r="M19.77,7.23L19.78,7.22L16.06,3.5L15,4.56L17.11,6.67C16.17,7.03 15.5,7.93 15.5,9A2.5,2.5 0 0,0 18,11.5C18.36,11.5 18.69,11.42 19,11.29V18.5A1,1 0 0,1 18,19.5A1,1 0 0,1 17,18.5V14A2,2 0 0,0 15,12H14V5A2,2 0 0,0 12,3H6A2,2 0 0,0 4,5V21H14V13.5H15.5V18.5A2.5,2.5 0 0,0 18,21A2.5,2.5 0 0,0 20.5,18.5V9C20.5,8.31 20.22,7.68 19.77,7.23M18,10A1,1 0 0,1 17,9A1,1 0 0,1 18,8A1,1 0 0,1 19,9A1,1 0 0,1 18,10M8,18V13.5H6L10,6V11H12L8,18Z",a="M12,9A3,3 0 0,0 9,12A3,3 0 0,0 12,15A3,3 0 0,0 15,12A3,3 0 0,0 12,9M12,17A5,5 0 0,1 7,12A5,5 0 0,1 12,7A5,5 0 0,1 17,12A5,5 0 0,1 12,17M12,4.5C7,4.5 2.73,7.61 1,12C2.73,16.39 7,19.5 12,19.5C17,19.5 21.27,16.39 23,12C21.27,7.61 17,4.5 12,4.5Z",n="M11 15H6L13 1V9H18L11 23V15Z",s="M20.71,7.04C21.1,6.65 21.1,6 20.71,5.63L18.37,3.29C18,2.9 17.35,2.9 16.96,3.29L15.12,5.12L18.87,8.87M3,17.25V21H6.75L17.81,9.93L14.06,6.18L3,17.25Z",o="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z",l="M6,2H18V8H18V8L14,12L18,16V16H18V22H6V16H6V16L10,12L6,8V8H6V2M16,16.5L12,12.5L8,16.5V20H16V16.5M12,11.5L16,7.5V4H8V7.5L12,11.5M10,6H14V6.75L12,8.75L10,6.75V6Z";const d=globalThis,c=d.ShadowRoot&&(void 0===d.ShadyCSS||d.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,h=Symbol(),p=new WeakMap;let u=class{constructor(e,t,i){if(this._$cssResult$=!0,i!==h)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=e,this.t=t}get styleSheet(){let e=this.o;const t=this.t;if(c&&void 0===e){const i=void 0!==t&&1===t.length;i&&(e=p.get(t)),void 0===e&&((this.o=e=new CSSStyleSheet).replaceSync(this.cssText),i&&p.set(t,e))}return e}toString(){return this.cssText}};const g=(e,...t)=>{const i=1===e.length?e[0]:t.reduce((t,i,r)=>t+(e=>{if(!0===e._$cssResult$)return e.cssText;if("number"==typeof e)return e;throw Error("Value passed to 'css' function must be a 'css' function result: "+e+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(i)+e[r+1],e[0]);return new u(i,e,h)},f=c?e=>e:e=>e instanceof CSSStyleSheet?(e=>{let t="";for(const i of e.cssRules)t+=i.cssText;return(e=>new u("string"==typeof e?e:e+"",void 0,h))(t)})(e):e,{is:m,defineProperty:v,getOwnPropertyDescriptor:_,getOwnPropertyNames:y,getOwnPropertySymbols:w,getPrototypeOf:b}=Object,$=globalThis,k=$.trustedTypes,x=k?k.emptyScript:"",A=$.reactiveElementPolyfillSupport,C=(e,t)=>e,E={toAttribute(e,t){switch(t){case Boolean:e=e?x:null;break;case Object:case Array:e=null==e?e:JSON.stringify(e)}return e},fromAttribute(e,t){let i=e;switch(t){case Boolean:i=null!==e;break;case Number:i=null===e?null:Number(e);break;case Object:case Array:try{i=JSON.parse(e)}catch(e){i=null}}return i}},z=(e,t)=>!m(e,t),S={attribute:!0,type:String,converter:E,reflect:!1,useDefault:!1,hasChanged:z};Symbol.metadata??=Symbol("metadata"),$.litPropertyMetadata??=new WeakMap;let V=class extends HTMLElement{static addInitializer(e){this._$Ei(),(this.l??=[]).push(e)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(e,t=S){if(t.state&&(t.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(e)&&((t=Object.create(t)).wrapped=!0),this.elementProperties.set(e,t),!t.noAccessor){const i=Symbol(),r=this.getPropertyDescriptor(e,i,t);void 0!==r&&v(this.prototype,e,r)}}static getPropertyDescriptor(e,t,i){const{get:r,set:a}=_(this.prototype,e)??{get(){return this[t]},set(e){this[t]=e}};return{get:r,set(t){const n=r?.call(this);a?.call(this,t),this.requestUpdate(e,n,i)},configurable:!0,enumerable:!0}}static getPropertyOptions(e){return this.elementProperties.get(e)??S}static _$Ei(){if(this.hasOwnProperty(C("elementProperties")))return;const e=b(this);e.finalize(),void 0!==e.l&&(this.l=[...e.l]),this.elementProperties=new Map(e.elementProperties)}static finalize(){if(this.hasOwnProperty(C("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(C("properties"))){const e=this.properties,t=[...y(e),...w(e)];for(const i of t)this.createProperty(i,e[i])}const e=this[Symbol.metadata];if(null!==e){const t=litPropertyMetadata.get(e);if(void 0!==t)for(const[e,i]of t)this.elementProperties.set(e,i)}this._$Eh=new Map;for(const[e,t]of this.elementProperties){const i=this._$Eu(e,t);void 0!==i&&this._$Eh.set(i,e)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(e){const t=[];if(Array.isArray(e)){const i=new Set(e.flat(1/0).reverse());for(const e of i)t.unshift(f(e))}else void 0!==e&&t.push(f(e));return t}static _$Eu(e,t){const i=t.attribute;return!1===i?void 0:"string"==typeof i?i:"string"==typeof e?e.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(e=>this.enableUpdating=e),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(e=>e(this))}addController(e){(this._$EO??=new Set).add(e),void 0!==this.renderRoot&&this.isConnected&&e.hostConnected?.()}removeController(e){this._$EO?.delete(e)}_$E_(){const e=new Map,t=this.constructor.elementProperties;for(const i of t.keys())this.hasOwnProperty(i)&&(e.set(i,this[i]),delete this[i]);e.size>0&&(this._$Ep=e)}createRenderRoot(){const e=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return((e,t)=>{if(c)e.adoptedStyleSheets=t.map(e=>e instanceof CSSStyleSheet?e:e.styleSheet);else for(const i of t){const t=document.createElement("style"),r=d.litNonce;void 0!==r&&t.setAttribute("nonce",r),t.textContent=i.cssText,e.appendChild(t)}})(e,this.constructor.elementStyles),e}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(e=>e.hostConnected?.())}enableUpdating(e){}disconnectedCallback(){this._$EO?.forEach(e=>e.hostDisconnected?.())}attributeChangedCallback(e,t,i){this._$AK(e,i)}_$ET(e,t){const i=this.constructor.elementProperties.get(e),r=this.constructor._$Eu(e,i);if(void 0!==r&&!0===i.reflect){const a=(void 0!==i.converter?.toAttribute?i.converter:E).toAttribute(t,i.type);this._$Em=e,null==a?this.removeAttribute(r):this.setAttribute(r,a),this._$Em=null}}_$AK(e,t){const i=this.constructor,r=i._$Eh.get(e);if(void 0!==r&&this._$Em!==r){const e=i.getPropertyOptions(r),a="function"==typeof e.converter?{fromAttribute:e.converter}:void 0!==e.converter?.fromAttribute?e.converter:E;this._$Em=r;const n=a.fromAttribute(t,e.type);this[r]=n??this._$Ej?.get(r)??n,this._$Em=null}}requestUpdate(e,t,i,r=!1,a){if(void 0!==e){const n=this.constructor;if(!1===r&&(a=this[e]),i??=n.getPropertyOptions(e),!((i.hasChanged??z)(a,t)||i.useDefault&&i.reflect&&a===this._$Ej?.get(e)&&!this.hasAttribute(n._$Eu(e,i))))return;this.C(e,t,i)}!1===this.isUpdatePending&&(this._$ES=this._$EP())}C(e,t,{useDefault:i,reflect:r,wrapped:a},n){i&&!(this._$Ej??=new Map).has(e)&&(this._$Ej.set(e,n??t??this[e]),!0!==a||void 0!==n)||(this._$AL.has(e)||(this.hasUpdated||i||(t=void 0),this._$AL.set(e,t)),!0===r&&this._$Em!==e&&(this._$Eq??=new Set).add(e))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(e){Promise.reject(e)}const e=this.scheduleUpdate();return null!=e&&await e,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(const[e,t]of this._$Ep)this[e]=t;this._$Ep=void 0}const e=this.constructor.elementProperties;if(e.size>0)for(const[t,i]of e){const{wrapped:e}=i,r=this[t];!0!==e||this._$AL.has(t)||void 0===r||this.C(t,void 0,i,r)}}let e=!1;const t=this._$AL;try{e=this.shouldUpdate(t),e?(this.willUpdate(t),this._$EO?.forEach(e=>e.hostUpdate?.()),this.update(t)):this._$EM()}catch(t){throw e=!1,this._$EM(),t}e&&this._$AE(t)}willUpdate(e){}_$AE(e){this._$EO?.forEach(e=>e.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(e)),this.updated(e)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(e){return!0}update(e){this._$Eq&&=this._$Eq.forEach(e=>this._$ET(e,this[e])),this._$EM()}updated(e){}firstUpdated(e){}};V.elementStyles=[],V.shadowRootOptions={mode:"open"},V[C("elementProperties")]=new Map,V[C("finalized")]=new Map,A?.({ReactiveElement:V}),($.reactiveElementVersions??=[]).push("2.1.2");const M=globalThis,H=e=>e,T=M.trustedTypes,L=T?T.createPolicy("lit-html",{createHTML:e=>e}):void 0,P="$lit$",D=`lit$${Math.random().toFixed(9).slice(2)}$`,I="?"+D,F=`<${I}>`,N=document,O=()=>N.createComment(""),W=e=>null===e||"object"!=typeof e&&"function"!=typeof e,j=Array.isArray,R="[ \t\n\f\r]",U=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,B=/-->/g,q=/>/g,G=RegExp(`>|${R}(?:([^\\s"'>=/]+)(${R}*=${R}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`,"g"),Z=/'/g,K=/"/g,J=/^(?:script|style|textarea|title)$/i,Q=e=>(t,...i)=>({_$litType$:e,strings:t,values:i}),X=Q(1),Y=Q(2),ee=Symbol.for("lit-noChange"),te=Symbol.for("lit-nothing"),ie=new WeakMap,re=N.createTreeWalker(N,129);function ae(e,t){if(!j(e)||!e.hasOwnProperty("raw"))throw Error("invalid template strings array");return void 0!==L?L.createHTML(t):t}class ne{constructor({strings:e,_$litType$:t},i){let r;this.parts=[];let a=0,n=0;const s=e.length-1,o=this.parts,[l,d]=((e,t)=>{const i=e.length-1,r=[];let a,n=2===t?"<svg>":3===t?"<math>":"",s=U;for(let t=0;t<i;t++){const i=e[t];let o,l,d=-1,c=0;for(;c<i.length&&(s.lastIndex=c,l=s.exec(i),null!==l);)c=s.lastIndex,s===U?"!--"===l[1]?s=B:void 0!==l[1]?s=q:void 0!==l[2]?(J.test(l[2])&&(a=RegExp("</"+l[2],"g")),s=G):void 0!==l[3]&&(s=G):s===G?">"===l[0]?(s=a??U,d=-1):void 0===l[1]?d=-2:(d=s.lastIndex-l[2].length,o=l[1],s=void 0===l[3]?G:'"'===l[3]?K:Z):s===K||s===Z?s=G:s===B||s===q?s=U:(s=G,a=void 0);const h=s===G&&e[t+1].startsWith("/>")?" ":"";n+=s===U?i+F:d>=0?(r.push(o),i.slice(0,d)+P+i.slice(d)+D+h):i+D+(-2===d?t:h)}return[ae(e,n+(e[i]||"<?>")+(2===t?"</svg>":3===t?"</math>":"")),r]})(e,t);if(this.el=ne.createElement(l,i),re.currentNode=this.el.content,2===t||3===t){const e=this.el.content.firstChild;e.replaceWith(...e.childNodes)}for(;null!==(r=re.nextNode())&&o.length<s;){if(1===r.nodeType){if(r.hasAttributes())for(const e of r.getAttributeNames())if(e.endsWith(P)){const t=d[n++],i=r.getAttribute(e).split(D),s=/([.?@])?(.*)/.exec(t);o.push({type:1,index:a,name:s[2],strings:i,ctor:"."===s[1]?ce:"?"===s[1]?he:"@"===s[1]?pe:de}),r.removeAttribute(e)}else e.startsWith(D)&&(o.push({type:6,index:a}),r.removeAttribute(e));if(J.test(r.tagName)){const e=r.textContent.split(D),t=e.length-1;if(t>0){r.textContent=T?T.emptyScript:"";for(let i=0;i<t;i++)r.append(e[i],O()),re.nextNode(),o.push({type:2,index:++a});r.append(e[t],O())}}}else if(8===r.nodeType)if(r.data===I)o.push({type:2,index:a});else{let e=-1;for(;-1!==(e=r.data.indexOf(D,e+1));)o.push({type:7,index:a}),e+=D.length-1}a++}}static createElement(e,t){const i=N.createElement("template");return i.innerHTML=e,i}}function se(e,t,i=e,r){if(t===ee)return t;let a=void 0!==r?i._$Co?.[r]:i._$Cl;const n=W(t)?void 0:t._$litDirective$;return a?.constructor!==n&&(a?._$AO?.(!1),void 0===n?a=void 0:(a=new n(e),a._$AT(e,i,r)),void 0!==r?(i._$Co??=[])[r]=a:i._$Cl=a),void 0!==a&&(t=se(e,a._$AS(e,t.values),a,r)),t}class oe{constructor(e,t){this._$AV=[],this._$AN=void 0,this._$AD=e,this._$AM=t}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(e){const{el:{content:t},parts:i}=this._$AD,r=(e?.creationScope??N).importNode(t,!0);re.currentNode=r;let a=re.nextNode(),n=0,s=0,o=i[0];for(;void 0!==o;){if(n===o.index){let t;2===o.type?t=new le(a,a.nextSibling,this,e):1===o.type?t=new o.ctor(a,o.name,o.strings,this,e):6===o.type&&(t=new ue(a,this,e)),this._$AV.push(t),o=i[++s]}n!==o?.index&&(a=re.nextNode(),n++)}return re.currentNode=N,r}p(e){let t=0;for(const i of this._$AV)void 0!==i&&(void 0!==i.strings?(i._$AI(e,i,t),t+=i.strings.length-2):i._$AI(e[t])),t++}}class le{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(e,t,i,r){this.type=2,this._$AH=te,this._$AN=void 0,this._$AA=e,this._$AB=t,this._$AM=i,this.options=r,this._$Cv=r?.isConnected??!0}get parentNode(){let e=this._$AA.parentNode;const t=this._$AM;return void 0!==t&&11===e?.nodeType&&(e=t.parentNode),e}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(e,t=this){e=se(this,e,t),W(e)?e===te||null==e||""===e?(this._$AH!==te&&this._$AR(),this._$AH=te):e!==this._$AH&&e!==ee&&this._(e):void 0!==e._$litType$?this.$(e):void 0!==e.nodeType?this.T(e):(e=>j(e)||"function"==typeof e?.[Symbol.iterator])(e)?this.k(e):this._(e)}O(e){return this._$AA.parentNode.insertBefore(e,this._$AB)}T(e){this._$AH!==e&&(this._$AR(),this._$AH=this.O(e))}_(e){this._$AH!==te&&W(this._$AH)?this._$AA.nextSibling.data=e:this.T(N.createTextNode(e)),this._$AH=e}$(e){const{values:t,_$litType$:i}=e,r="number"==typeof i?this._$AC(e):(void 0===i.el&&(i.el=ne.createElement(ae(i.h,i.h[0]),this.options)),i);if(this._$AH?._$AD===r)this._$AH.p(t);else{const e=new oe(r,this),i=e.u(this.options);e.p(t),this.T(i),this._$AH=e}}_$AC(e){let t=ie.get(e.strings);return void 0===t&&ie.set(e.strings,t=new ne(e)),t}k(e){j(this._$AH)||(this._$AH=[],this._$AR());const t=this._$AH;let i,r=0;for(const a of e)r===t.length?t.push(i=new le(this.O(O()),this.O(O()),this,this.options)):i=t[r],i._$AI(a),r++;r<t.length&&(this._$AR(i&&i._$AB.nextSibling,r),t.length=r)}_$AR(e=this._$AA.nextSibling,t){for(this._$AP?.(!1,!0,t);e!==this._$AB;){const t=H(e).nextSibling;H(e).remove(),e=t}}setConnected(e){void 0===this._$AM&&(this._$Cv=e,this._$AP?.(e))}}class de{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(e,t,i,r,a){this.type=1,this._$AH=te,this._$AN=void 0,this.element=e,this.name=t,this._$AM=r,this.options=a,i.length>2||""!==i[0]||""!==i[1]?(this._$AH=Array(i.length-1).fill(new String),this.strings=i):this._$AH=te}_$AI(e,t=this,i,r){const a=this.strings;let n=!1;if(void 0===a)e=se(this,e,t,0),n=!W(e)||e!==this._$AH&&e!==ee,n&&(this._$AH=e);else{const r=e;let s,o;for(e=a[0],s=0;s<a.length-1;s++)o=se(this,r[i+s],t,s),o===ee&&(o=this._$AH[s]),n||=!W(o)||o!==this._$AH[s],o===te?e=te:e!==te&&(e+=(o??"")+a[s+1]),this._$AH[s]=o}n&&!r&&this.j(e)}j(e){e===te?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,e??"")}}class ce extends de{constructor(){super(...arguments),this.type=3}j(e){this.element[this.name]=e===te?void 0:e}}class he extends de{constructor(){super(...arguments),this.type=4}j(e){this.element.toggleAttribute(this.name,!!e&&e!==te)}}class pe extends de{constructor(e,t,i,r,a){super(e,t,i,r,a),this.type=5}_$AI(e,t=this){if((e=se(this,e,t,0)??te)===ee)return;const i=this._$AH,r=e===te&&i!==te||e.capture!==i.capture||e.once!==i.once||e.passive!==i.passive,a=e!==te&&(i===te||r);r&&this.element.removeEventListener(this.name,this,i),a&&this.element.addEventListener(this.name,this,e),this._$AH=e}handleEvent(e){"function"==typeof this._$AH?this._$AH.call(this.options?.host??this.element,e):this._$AH.handleEvent(e)}}class ue{constructor(e,t,i){this.element=e,this.type=6,this._$AN=void 0,this._$AM=t,this.options=i}get _$AU(){return this._$AM._$AU}_$AI(e){se(this,e)}}const ge={I:le},fe=M.litHtmlPolyfillSupport;fe?.(ne,le),(M.litHtmlVersions??=[]).push("3.3.3");const me=globalThis;let ve=class extends V{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){const e=super.createRenderRoot();return this.renderOptions.renderBefore??=e.firstChild,e}update(e){const t=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(e),this._$Do=((e,t,i)=>{const r=i?.renderBefore??t;let a=r._$litPart$;if(void 0===a){const e=i?.renderBefore??null;r._$litPart$=a=new le(t.insertBefore(O(),e),e,void 0,i??{})}return a._$AI(e),a})(t,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return ee}};ve._$litElement$=!0,ve.finalized=!0,me.litElementHydrateSupport?.({LitElement:ve});const _e=me.litElementPolyfillSupport;_e?.({LitElement:ve}),(me.litElementVersions??=[]).push("4.2.2");const ye=e=>(t,i)=>{void 0!==i?i.addInitializer(()=>{customElements.define(e,t)}):customElements.define(e,t)},we={attribute:!0,type:String,converter:E,reflect:!1,hasChanged:z},be=(e=we,t,i)=>{const{kind:r,metadata:a}=i;let n=globalThis.litPropertyMetadata.get(a);if(void 0===n&&globalThis.litPropertyMetadata.set(a,n=new Map),"setter"===r&&((e=Object.create(e)).wrapped=!0),n.set(i.name,e),"accessor"===r){const{name:r}=i;return{set(i){const a=t.get.call(this);t.set.call(this,i),this.requestUpdate(r,a,e,!0,i)},init(t){return void 0!==t&&this.C(r,void 0,e,t),t}}}if("setter"===r){const{name:r}=i;return function(i){const a=this[r];t.call(this,i),this.requestUpdate(r,a,e,!0,i)}}throw Error("Unsupported decorator location: "+r)};function $e(e){return(t,i)=>"object"==typeof i?be(e,t,i):((e,t,i)=>{const r=t.hasOwnProperty(i);return t.constructor.createProperty(i,e),r?Object.getOwnPropertyDescriptor(t,i):void 0})(e,t,i)}function ke(e){return $e({...e,state:!0,attribute:!1})}const xe=1,Ae=2,Ce=3,Ee=4,ze=e=>(...t)=>({_$litDirective$:e,values:t});let Se=class{constructor(e){}get _$AU(){return this._$AM._$AU}_$AT(e,t,i){this._$Ct=e,this._$AM=t,this._$Ci=i}_$AS(e,t){return this.update(e,t)}update(e,t){return this.render(...t)}};const{I:Ve}=ge,Me=e=>e,He=()=>document.createComment(""),Te=(e,t,i)=>{const r=e._$AA.parentNode,a=void 0===t?e._$AB:t._$AA;if(void 0===i){const t=r.insertBefore(He(),a),n=r.insertBefore(He(),a);i=new Ve(t,n,e,e.options)}else{const t=i._$AB.nextSibling,n=i._$AM,s=n!==e;if(s){let t;i._$AQ?.(e),i._$AM=e,void 0!==i._$AP&&(t=e._$AU)!==n._$AU&&i._$AP(t)}if(t!==a||s){let e=i._$AA;for(;e!==t;){const t=Me(e).nextSibling;Me(r).insertBefore(e,a),e=t}}}return i},Le=(e,t,i=e)=>(e._$AI(t,i),e),Pe={},De=(e,t=Pe)=>e._$AH=t,Ie=e=>{e._$AR(),e._$AA.remove()},Fe=ze(class extends Se{constructor(e){if(super(e),e.type!==Ce&&e.type!==xe&&e.type!==Ee)throw Error("The `live` directive is not allowed on child or event bindings");if(!(e=>void 0===e.strings)(e))throw Error("`live` bindings can only contain a single expression")}render(e){return e}update(e,[t]){if(t===ee||t===te)return t;const i=e.element,r=e.name;if(e.type===Ce){if(t===i[r])return ee}else if(e.type===Ee){if(!!t===i.hasAttribute(r))return ee}else if(e.type===xe&&i.getAttribute(r)===t+"")return ee;return De(e),t}}),Ne=Symbol.for(""),Oe=e=>{if(e?.r===Ne)return e?._$litStatic$},We=(e,...t)=>({_$litStatic$:t.reduce((t,i,r)=>t+(e=>{if(void 0!==e._$litStatic$)return e._$litStatic$;throw Error(`Value passed to 'literal' function must be a 'literal' result: ${e}. Use 'unsafeStatic' to pass non-literal values, but\n            take care to ensure page security.`)})(i)+e[r+1],e[0]),r:Ne}),je=new Map,Re=(e=>(t,...i)=>{const r=i.length;let a,n;const s=[],o=[];let l,d=0,c=!1;for(;d<r;){for(l=t[d];d<r&&void 0!==(n=i[d],a=Oe(n));)l+=a+t[++d],c=!0;d!==r&&o.push(n),s.push(l),d++}if(d===r&&s.push(t[r]),c){const e=s.join("$$lit$$");void 0===(t=je.get(e))&&(s.raw=s,je.set(e,t=s)),i=o}return e(t,...i)})(X),Ue=["manual","charging_stopped","car_disconnected"];function Be(e){return"object"==typeof e&&null!==e&&"code"in e&&"message"in e}function qe(e){return Be(e)?e.message:String(e)}let Ge=class extends ve{constructor(){super(...arguments),this.open=!1,this.heading="",this.text="",this.confirmText="",this.cancelText="",this.confirmed=!1}render(){return X`
      <ha-dialog .open=${this.open} .headerTitle=${this.heading} @closed=${this.closed}>
        <p>${this.text}</p>
        <div slot="footer">
          <ha-button appearance="plain" @click=${this.cancel}>${this.cancelText}</ha-button>
          <ha-button variant="danger" @click=${this.confirm}>${this.confirmText}</ha-button>
        </div>
      </ha-dialog>
    `}confirm(){this.confirmed=!0,this.open=!1}cancel(){this.open=!1}closed(e){e.stopPropagation();const t=this.confirmed?"confirm":"cancel";this.confirmed=!1,this.open=!1,this.dispatchEvent(new CustomEvent(t))}};e([$e({type:Boolean})],Ge.prototype,"open",void 0),e([$e()],Ge.prototype,"heading",void 0),e([$e()],Ge.prototype,"text",void 0),e([$e()],Ge.prototype,"confirmText",void 0),e([$e()],Ge.prototype,"cancelText",void 0),Ge=e([ye("kraftvakt-confirm-dialog")],Ge);let Ze=class extends ve{constructor(){super(...arguments),this.running=!1,this.appearance="plain",this.disabled=!1,this.changing=!1}render(){return this.running?X`
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
        `}async toggle(){this.changing=!0,this.fireError(void 0);try{await(e=this.hass,t=!this.running,e.callWS({type:"kraftvakt/regulation/set_running",running:t}))}catch(e){this.fireError(Be(e)&&"config_incomplete"===e.code?this.localize("status.start_refused"):this.localize("panel.error",{message:qe(e)}))}finally{this.changing=!1}var e,t}fireError(e){this.dispatchEvent(new CustomEvent("running-error",{detail:e}))}static{this.styles=g`
    ha-button::part(base) {
      white-space: nowrap;
    }
  `}};e([$e({attribute:!1})],Ze.prototype,"hass",void 0),e([$e({attribute:!1})],Ze.prototype,"localize",void 0),e([$e({type:Boolean})],Ze.prototype,"running",void 0),e([$e()],Ze.prototype,"appearance",void 0),e([$e({type:Boolean})],Ze.prototype,"disabled",void 0),e([ke()],Ze.prototype,"changing",void 0),Ze=e([ye("kraftvakt-running-button")],Ze);let Ke=class extends ve{constructor(){super(...arguments),this.narrow=!1}render(){return X`
      <ha-alert alert-type="warning" .title=${this.localize("locked.title")} .narrow=${this.narrow}>
        <ha-svg-icon slot="icon" .path=${"M12,17A2,2 0 0,0 14,15C14,13.89 13.1,13 12,13A2,2 0 0,0 10,15A2,2 0 0,0 12,17M18,8A2,2 0 0,1 20,10V20A2,2 0 0,1 18,22H6A2,2 0 0,1 4,20V10C4,8.89 4.9,8 6,8H7V6A5,5 0 0,1 12,1A5,5 0 0,1 17,6V8H18M12,3A3,3 0 0,0 9,6V8H15V6A3,3 0 0,0 12,3Z"}></ha-svg-icon>
        ${this.localize("locked.text")}
        ${this.error?X`<div class="error">${this.error}</div>`:te}
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
  `}};e([$e({attribute:!1})],Ke.prototype,"hass",void 0),e([$e({attribute:!1})],Ke.prototype,"localize",void 0),e([$e({type:Boolean})],Ke.prototype,"narrow",void 0),e([ke()],Ke.prototype,"error",void 0),Ke=e([ye("kraftvakt-locked-banner")],Ke);let Je=class extends ve{constructor(){super(...arguments),this.errorCount=0,this.saving=!1}render(){const e=this.errorCount>0?this.localize("config.fix_before_saving"):this.message;return X`
      <div class="bar" role="region" aria-label=${this.localize("config.unsaved")}>
        <div class="text">
          <div class="title">${this.localize("config.unsaved")}</div>
          ${e?X`<div class="error">${e}</div>`:te}
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
  `}};e([$e({attribute:!1})],Je.prototype,"localize",void 0),e([$e({type:Number})],Je.prototype,"errorCount",void 0),e([$e({type:Boolean})],Je.prototype,"saving",void 0),e([$e()],Je.prototype,"message",void 0),Je=e([ye("kraftvakt-save-bar")],Je);const Qe="draft-changed";function Xe(){const e=crypto.getRandomValues(new Uint8Array(6));return Array.from(e,e=>e.toString(16).padStart(2,"0")).join("")}function Ye(e,t,i){const r=[...e],[a]=r.splice(t,1);return r.splice(i,0,a),r}function et(e){return"charger_group"===e.type?`group/${e.group_id}`:`${e.appliance_id}/${e.variant_id??""}`}function tt(e){const t=function(e){const t=e.appliances.flatMap(e=>[{type:"appliance",appliance_id:e.id,variant_id:null},...e.variants.map(t=>({type:"appliance",appliance_id:e.id,variant_id:t.id}))]);return t.push(...e.charger_groups.map(e=>({type:"charger_group",group_id:e.id}))),t}(e),i=new Set(t.map(et)),r=new Set,a=e.priority.filter(e=>{const t=et(e);return!(!i.has(t)||r.has(t))&&(r.add(t),!0)}),n=t.filter(e=>!r.has(et(e))),s=new Set(e.appliances.filter(e=>e.essential).map(e=>e.id)),o=e=>"appliance"===e.type&&s.has(e.appliance_id),l=[...a,...n];return{...e,priority:[...l.filter(o),...l.filter(e=>!o(e))]}}function it(e){return e.charger_groups.flatMap(e=>e.chargers)}const rt={en:{panel:{title:"Kraftvakt",not_loaded:"Kraftvakt is not loaded. Check the integration under Settings → Devices & services.",error:"Something went wrong: {message}"},tabs:{status:"Status",general:"General",appliances:"Appliances",charging:"EV charging",advanced:"Advanced"},status:{regulation:"Regulation",running:"Running",stopped:"Stopped",start:"Start regulation",stop:"Stop regulation",stopped_info:"The regulation is stopped, and all regulated appliances and EV chargers are turned off. The configuration can be changed. When the regulation starts, the appliances are turned on again one by one.",incomplete_title:"The configuration is not complete",start_refused:"The regulation cannot start before the configuration is complete.",safe_state_title:"Safe state",safe_state_text:"The power sensor {sensor} gives no valid measurement. All regulated appliances and EV chargers are turned off. The regulation starts again by itself when the sensor gives a valid value again.",penalty_title:"Penalty period",penalty_text:"The tariff average has been above the power limit. All regulated appliances and EV chargers are kept off until the overconsumption is recovered.",overconsumption_left:"Overconsumption left: {energy} kWh",recovery_started:"recovery has started",recovery_not_started:"recovery has not started",regulation_average:"Regulation average",tariff_average:"Tariff average",average_over_seconds:"over {seconds} s",average_over_hour:"over 1 hour",power_now:"Consumption now",momentary:"momentary value",power_limit:"Power limit",safe_state_chip:"Safe state",safe_state_back_text:"The power sensor {sensor} gives a valid value again. The regulation starts again with everything off at the next decision.",penalty_chip:"Penalty period",next_decision:"Next decision",next_decision_at:"Next decision at {time}",appliances_and_chargers:"Appliances and EV chargers",power:"Power",temperature:"Temperature",no_chargers:"No EV chargers in the group.",no_appliances:"No appliances are configured.",on:"On",off:"Off",activated:"Activated",deactivated:"Deactivated",waiting_ends_at:"Turns on at the decision at {time}",delayed_turn_on:"Delayed turn-on",charging_at:"Charging at {current} A",first_decision:"Waiting for the first decision",bypassed_no_car:"Bypassed: no car connected",waiting_charger:"Queued: another EV charger in the group has its turn",starting_until:"Waiting until {time} for the car to start charging. Its power at minimum current is kept free until then.",excluded:"Excluded from the regulation",outside_window:"Outside the charging window ({start}–{end})",next_ampere_at:"One more ampere at the decision at {time}",amperes:"{current} A",chargers_charging:"{charging} of {total} EV chargers are charging",activated_not_charging:"Activated: the car does not draw power, so it waits at the minimum current",window_overridden:"The charging window is overridden",finishing_at:"Finishing the charging that went on when the charging window ended, at {current} A",chip_charging:"Charging",chip_no_car:"No car connected",chip_queued:"Queued",chip_starting:"Starting",chip_excluded:"Excluded",chip_window:"{start}–{end}",chip_override:"Override",chip_finishing:"Finishing",chip_first_decision:"First decision",chip_fault:"Fault",fault:"A fault flag shows a fault, so the EV charger is deactivated until the fault clears",free_power:"{power} kW ({share}) free",power_runs_out:"The power runs out here. What is below waits for free power.",queued_for_room:"Queued: waiting for room beside the EV chargers that charge"},missing:{missing_power_sensor:"The power sensor is not chosen.",missing_device:"{item}: the device is not chosen.",missing_entity:"{item}: the entity is not chosen.",missing_action:"{item}: the action to {action} is missing.",missing_condition:"{item}: the expression is missing.",missing_car_connected:"{item}: «car connected» is missing.",missing_fault_flag:"{item}: «fault flag» is missing.",unknown:"{item}: {code}",appliance_without_entity:"An appliance without an entity",charger_without_entity:"An EV charger without an entity",actions:{turn_on:"turn it on",turn_off:"turn it off",activate:"activate it",deactivate:"deactivate it",set_current:"set the charging current"},missing_charging_power:"{item}: «charging power» is missing."},config:{save:"Save",restore_defaults:"Restore defaults",discard:"Discard",unsaved:"Unsaved changes",fix_before_saving:"Fix the marked settings before saving.",not_saved:"The configuration was not saved. Fix the marked settings.",save_refused_running:"The configuration cannot be saved while the regulation runs.",leave_title:"Discard unsaved changes?",leave_text:"The changes on the configuration pages are not saved. They are lost if you leave.",stay:"Keep editing",leave:"Discard changes"},locked:{title:"The configuration is locked",text:"The regulation runs. Stop the regulation to change the configuration. When the regulation stops, all regulated appliances and EV chargers are turned off."},warning:{appliances_title:"Do not turn regulated appliances on or off outside Kraftvakt",chargers_title:"Do not turn EV chargers on or off outside Kraftvakt",text:"Manual control and automations can disturb the regulation, affect appliances with higher priority and trigger a penalty. Kraftvakt also sets them back when it repeats its commands."},errors:{required:"Required.",fault_flag_required:"Choose a fault flag, or turn the setting off.",out_of_range:"Must be between {min} and {max}.",at_least:"Must be at least {min}.",invalid_resolution:"Must be a multiple of {resolution}.",not_integer:"Must be a whole number.",invalid_entity_id:"Not a valid entity ID.",empty_label:"The label cannot be empty.",duplicate_label:"The label must be unique for the appliance.",empty_name:"The name cannot be empty.",duplicate_name:"The name is already used by another group.",min_current_above_max:"The minimum current cannot be above the maximum current.",invalid_time:"Give both start and end.",window_start_equals_end:"Start and end cannot be the same.",duplicate_entity:"The entity is already used by another appliance or EV charger.",unknown_device:"The device no longer exists in Home Assistant.",entity_not_on_device:"The entity does not belong to the device of the EV charger, or of the appliance's entity.",invalid_action:"Home Assistant cannot read the action.",invalid_template:"The template has a syntax error.",default_action_unavailable:"The entity has no standard action. Choose a custom action.",unsupported_entity_domain:"The entity cannot be used. Choose a number entity.",domain_action_unavailable:"The action is not available for the entity. Choose another action.",unsupported_option:"The entity does not support this value.",outside_entity_range:"Outside the range of the entity.",unknown:"Invalid value ({code}).",current_off_unsupported:"The entity cannot be set to 0 A, which stops an EV charger turned on and off by the current.",essential_with_variants:"An essential appliance cannot have variants. Delete them, or turn the setting off.",essential_with_power_reserve:"An essential appliance has no power reserve. Turn the setting off, or turn off Fixed load first.",essential_not_at_top:"An essential appliance must be above every other entry in the priority list.",not_a_thermostat:"Choose a thermostat, a climate entity."},dialog:{ok:"OK",cancel:"Cancel",close:"Close"},general:{measurement:"Measurement",regulation:"Regulation",penalty:"Penalty",interval_option:"{count} × the regulation window",fields:{power_sensor:{label:"Power sensor",helper:"The total power of the house now, usually from the HAN port of the electricity meter. W or kW."},regulation_window_s:{label:"Regulation window",helper:"Decisions use the average over this period. Longer evens out short peaks, shorter reacts faster. {min}–{max} s, default {default} s."},power_limit_w:{label:"Power limit",helper:"The step in the capacity tariff you want to stay below. The average over the last hour is kept below it. {min}–{max} W, default {default} W."},turn_on_margin_w:{label:"Turn-on margin",helper:"Appliances are turned on only this far below the power limit, so they are not turned off again at once. {min}–{max} W, default {default} W."},regulation_interval:{label:"Decide every",helper:"Now every {seconds} seconds. Default {default} ×."},wait_at_limit_s:{label:"Waiting time at the power limit",helper:"How long an appliance waits before it is turned on when little power is free. The more power is free, the shorter it waits. {min}–{max} s, default {default} s."},penalty_threshold_w:{label:"Penalty threshold",helper:"How far the average over the last hour may go above the power limit before everything is turned off. {min}–{max} W, default {default} W."},wait_curve_steepness:{label:"Steepness"},wait_curve_pivot:{label:"Pivot point"},appliance_repeat_increment_factor:{label:"Increase each time",helper:"Share of the waiting time at the power limit. Default × {default}."},appliance_repeat_increments:{label:"Most increases",helper:"{min}–{max}, default {default}."},charger_repeat_increment_factor:{label:"Increase each time",helper:"Share of the waiting time at the power limit. Default × {default}."},charger_repeat_increments:{label:"Most increases",helper:"{min}–{max}, default {default}."},command_repeat_interval_min:{label:"Repeat the command after",helper:"{min}–{max} min, default {default} min."},action_timeout_s:{label:"Action timeout",helper:"An action that takes longer is stopped and counts as failed. {min}–{max} s, default {default} s."},power_sensor_timeout_s:{label:"Power sensor timeout",helper:"A power sensor that reports nothing for this long counts as lost, and everything is turned off. A HAN reader usually reports every 10 seconds. {min}–{max} s, default {default} s."}},penalty_info:"A safety valve that should never be needed: if the average over the last hour still goes above the power limit, everything is kept off until the overconsumption is paid back."},advanced:{wait_curve:"Waiting time curve",wait_curve_info:"How long an appliance waits, by how much power is free. The actual waiting time is rounded up to the next decision.",free_power_kw:"Free power kW",waiting_minutes:"Waiting time min:s",actual_waiting_minutes:"Actual waiting time min:s",repeated_turn_on:"Waiting time on repeated turn-on",repeated_turn_on_info:"When the same appliance, or the same ampere of an EV charger, is turned on again and again with nothing else switched in between, the waiting time grows from the third time. The first two follow the curve; the table shows them at the pivot point.",turn_on_in_a_row:"Turn-on in a row",appliances:"Appliances",chargers:"EV chargers",command_repeat:"Command repeat",command_repeat_info:"An appliance or EV charger can change state by itself, for example after a power cut. When it has had no command for this long, it gets the last one again. Excluded ones are left alone.",timeouts:"Timeouts",timeouts_info:"Guards against an action that never finishes and a power sensor that stops reporting."},list:{drag:"Drag to change the order",edit:"Edit",view:"Show"},appliances:{priority_title:"Priority list",priority_sub:"Turned on from the top, off from the bottom. Drag to change the order.",add:"Add appliance",empty:"No appliances yet. Add the appliances Kraftvakt may turn off when the consumption is too high.",charger_group_sub:"EV chargers: {count} · configured under",power_reserve:"power reserve {power} W",essential:"Essential",variant_count:"variants: {count}",variant_entity:"Variant · entity {entity}",variant_template:"Variant · template",variant_own_actions:"own actions",variant_own_turn_on:"own action to turn on",variant_own_turn_off:"own action to turn off"},appliance:{add_title:"Add appliance",edit_title:"Edit appliance",view_title:"Appliance",variants:"Variants",variants_info:"Give the appliance another place in the priority list at certain times or conditions, for example a higher place for the water heater in the morning. The top variant that applies wins.",add_variant:"Add variant",display_values:"Display values",display_values_info:"Optional, and not used by the regulation. Shown on the status page for convenience.",delete:"Delete appliance",fields:{entity_id:{label:"Entity",helper:"What Kraftvakt turns on and off, for example the switch of a water heater. Its name becomes the name of the appliance."},essential:{label:"Essential appliance",helper:"For an appliance that must always run, such as a freezer. It is kept on, and turned off only during a penalty period. Not for an appliance with variants."},turn_on:{label:"Action to turn on",helper:"Standard works for most entities."},turn_off:{label:"Action to turn off",helper:"Standard works for most entities."},fixed_load:{label:"Fixed load",helper:"Only for an appliance that always draws the same power while it is on, such as a ceiling fan. Never for one with a thermostat or other control of its own: the regulation then works worse."},power_reserve_w:{label:"Power reserve",helper:"What the appliance draws while it is on. Applies to every variant."},label:{label:"Label"},condition:{label:"Expression"},override_turn_on:{label:"Own action to turn on",helper:"For example another HVAC mode."},override_turn_off:{label:"Own action to turn off",helper:"For example frost protection."},display_power:{label:"Power"},display_temperature:{label:"Temperature"}}},variant:{edit_title:"Edit variant {name}",view_title:"Variant {name}",condition:"Expression",delete:"Delete variant",condition_info:"The variant applies while the expression is true, for example between 05 and 08. Otherwise the appliance keeps its usual place."},action:{default:"Standard",custom:"Custom",entity:"Entity",domain_actions:{climate_hvac_mode:"HVAC mode",climate_temperature:"Temperature",climate_hvac_mode_and_temperature:"HVAC mode and temperature"},default_runs:"Runs {service} for the entity.",entity_runs:"Runs {service} for the chosen entity with the current as value.",no_default:"The entity type has no standard action, so the action must be custom.",choose_entity:"Choose the entity to use the standard action.",choose_action_entity:"Choose the entity to set the value of.",variables:"Variables: {variables}.",parameters:{hvac_mode:"HVAC mode",temperature:"Target temperature"},parameter_range:"{min}–{max} {unit} for the entity."},condition:{entity:"Entity",template:"Template",entity_label:"Boolean entity",template_label:"Template",entity_helper:"True only when it is on. Unavailable counts as false.",state:"State",state_label:"Entity with a state",state_helper:"For example a status sensor of the EV charger.",states_label:"States",states_helper:"Choose or type the states. Every other state counts as the opposite, except unavailable, which counts as false.",template_helper:"True only when it gives true. Variables: entity_id, entity.",now:"Now: {value}",true:"true",false:"false",error:"Error: {message}",invalid:"The template gives {value}, which is not true or false, so it counts as false."},actively_charging:{type_label:"Charging on/off from",entity:"Entity",template:"Template",entity_label:"Boolean entity",template_label:"Template",entity_helper:"On while the car charges. Unavailable counts as not charging.",state:"State",state_label:"Entity with a state",state_helper:"For example a status sensor of the EV charger.",states_label:"States",states_helper:"Choose or type the states. Every other state counts as the opposite, except unavailable, which counts as not charging.",template_helper:"True means charging, anything else not charging. Variables: entity_id, entity.",true:"charging",false:"not charging",invalid:"The template gives {value}, which is not true or false, so it counts as not charging."},charging_power:{type_label:"Charging power from",power_sensor:"Sensor",template:"Template",power_sensor_label:"Sensor for charging power",template_label:"Template for charging power",power_sensor_helper:"Above 100 W counts as charging. W or kW.",template_helper:"The power in W; above 100 W counts as charging. Variables: entity_id, entity.",true:"charging",false:"not charging",invalid:"The template gives {value}, which is not a number, so it counts as not charging."},display_power:{type_label:"Power from",power_sensor:"Sensor",template:"Template",power_sensor_label:"Power",template_label:"Template for power",power_sensor_helper:"A sensor of the same device as the entity. W or kW.",template_helper:"The power in W, also from another device. Variables: entity_id, entity.",no_value:"no value",invalid:"The template gives {value}, which is not a number, so nothing is shown."},display_temperature:{type_label:"Temperature from",temperature_sensor:"Entity",template:"Template",current_temperature:"{name}: current temperature",target_temperature:"{name}: set temperature",temperature_sensor_label:"Temperature",template_label:"Template for temperature",temperature_sensor_helper:"A temperature sensor of the same device as the entity, or a thermostat's current or set temperature.",template_helper:"A temperature in the unit of Home Assistant, also from another device. Variables: entity_id, entity.",no_value:"no value",invalid:"The template gives {value}, which is not a number, so nothing is shown."},fault:{entity:"Entity",template:"Template",entity_label:"Boolean entity",template_label:"Template",entity_helper:"On means a fault. Unavailable is no fault.",state:"State",state_label:"Entity with a state",state_helper:"For example a status sensor of the EV charger.",states_label:"States",states_helper:"Choose or type the states. Every other state counts as the opposite, except unavailable, which is no fault.",template_helper:"True means a fault, anything else no fault. Variables: entity_id, entity.",true:"fault",false:"no fault",invalid:"The template gives {value}, which is not true or false, so it counts as no fault."},charging:{name:"Name",name_sub:"Shown in the priority list and on the status page.",one_at_a_time:"One EV charger at a time",one_at_a_time_sub:"Only one car in the group charges at a time. While none charges, every car may wait at the minimum current, and the first that draws power gets the turn.",dynamic_order:"Dynamic charging order",dynamic_order_sub:"Off: the charging priority below always applies, so a car higher up that draws power takes over from one charging below it.\nOn: EV chargers that charge go first, and the others wait their turn.",chargers:"Charging priority",chargers_sub:"Highest at the top. Drag an EV charger to another group to move it.",add:"Add EV charger",empty:"No EV chargers yet.",no_groups:"No groups of EV chargers yet. Add a group, and then its EV chargers.",add_group:"Add group",new_group_name:"EV chargers",unnamed_group:"Group without a name",delete_group:"Delete group",delete_group_not_empty:"Move or delete its EV chargers to delete the group.",switches_info:"Each EV charger gets three switches you can use while the regulation runs: «‹charger› excluded from regulation», «‹charger› override charging window» and «‹charger› finish charging after charging window».",currents:"{min}–{max} A",min_current_power:"{power} W at minimum current",window:"charging window {start}–{end}",finishes_after_window:"finishes ongoing charging after the window",always_allowed:"always allowed to charge",car_from:"car connected from {source}",car_template:"car connected from a template",charging_from:"actively charging from {source}",charging_template:"actively charging from a template",power_from:"charging power from {source}",power_template:"charging power from a template",deactivated_on_fault:"deactivated on fault",switched_by_current:"turned on and off by the current"},charger:{add_title:"Add EV charger",edit_title:"Edit EV charger",view_title:"EV charger",charging_current:"Charging current",profile_applied:"Filled in from the charger profile {profile}. Check every field before you save.",override_ends:{manual:"When I turn it off",charging_stopped:"When the car no longer charges",car_disconnected:"When the car is disconnected"},delete:"Delete EV charger",fields:{device_id:{label:"Device",helper:"The EV charger in Home Assistant. Its entities are chosen below, and filled in when Kraftvakt knows the charger."},entity_id:{label:"Charger entity",helper:"Usually the switch that allows charging."},activate:{label:"Action to activate",helper:"Standard works for most entities."},deactivate:{label:"Action to deactivate",helper:"Standard works for most entities."},min_current_a:{label:"Minimum charging current"},max_current_a:{label:"Maximum charging current"},set_current:{label:"Set charging current"},min_current_power_w:{label:"Power at minimum current",helper:"What the car draws at the minimum current, about 1400 W on one phase. The car starts charging only when this much power is free. {min}–{max} W, default {default} W, 6 A on three phases."},car_connected:{label:"Car connected",helper:"An EV charger without a car is not activated. Unavailable counts as not connected."},actively_charging:{label:"Actively charging",helper:"The charging power is required, and tells how much the car draws. The charging on/off is optional, and may tell sooner that the car charges."},charging_power:{label:"Charging power"},cloud_controlled:{label:"Cloud-controlled EV charger",helper:"For an EV charger controlled over the internet. It gets fewer repeated commands, and its power is kept free while the car starts charging."},start_delay_s:{label:"Start delay",helper:"How long the car may take to start charging after the EV charger is activated. Its power at minimum current is kept free meanwhile. {min}–{max} s, default {default} s."},deactivate_on_fault:{label:"Deactivate on fault",helper:"While a fault flag shows a fault, the EV charger is stopped and the others in the group may charge. Unavailable is no fault."},fault_flag:{label:"Fault flag"},charging_window:{label:"Charging window",helper:"The EV charger charges only within this time each day, for example at night. Off: it may always charge."},start:{label:"Start"},end:{label:"End"},finish_after_window:{label:"Finish charging after the charging window",helper:"A car that is charging when the charging window ends may go on until it stops. It then waits for the next charging window."},override_ends:{label:"End the override",helper:"When the switch «‹charger› override charging window» turns itself off. It can be turned on before the car arrives."},switched_by_current:{label:"Charging is turned on and off by",helper:"Choose the current for an EV charger that has no way to turn charging on and off: 0 A stops it."}},charging_current_info:"The current is raised and lowered one ampere at a time by the free power. The minimum is the lowest current the car charges with, usually 6 A, and the maximum what the EV charger and its fuse allow.",state_choices:{car_connected:{true:"States for connected",false:"States for disconnected"},actively_charging:{true:"States for charging",false:"States for not charging"},fault_flag:{true:"States for a fault",false:"States for no fault"}},switched_by:{actions:"Actions to activate and deactivate",current:"The charging current"}}},nb:{panel:{title:"Kraftvakt",not_loaded:"Kraftvakt er ikke lastet. Sjekk integrasjonen under Innstillinger → Enheter og tjenester.",error:"Noe gikk galt: {message}"},tabs:{status:"Status",general:"Generelt",appliances:"Apparater",charging:"Billading",advanced:"Avansert"},status:{regulation:"Regulering",running:"Kjører",stopped:"Stoppet",start:"Start regulering",stop:"Stopp regulering",stopped_info:"Reguleringen er stoppet, og alle regulerte apparater og elbilladere er slått av. Konfigurasjonen kan endres. Når reguleringen startes, slås apparatene på igjen ett og ett.",incomplete_title:"Konfigurasjonen er ikke fullstendig",start_refused:"Reguleringen kan ikke startes før konfigurasjonen er fullstendig.",safe_state_title:"Sikker tilstand",safe_state_text:"Effektsensoren {sensor} gir ingen gyldig måling. Alle regulerte apparater og elbilladere er slått av. Reguleringen starter på nytt av seg selv når sensoren gir en gyldig verdi igjen.",penalty_title:"Straffeperiode pågår",penalty_text:"Tariffsnittet har vært over effektgrensen. Alle regulerte apparater og elbilladere holdes av til overforbruket er hentet inn.",overconsumption_left:"Overforbruk igjen: {energy} kWh",recovery_started:"innhenting har startet",recovery_not_started:"innhenting har ikke startet",regulation_average:"Reguleringssnitt",tariff_average:"Tariffsnitt",average_over_seconds:"over {seconds} s",average_over_hour:"over 1 time",power_now:"Forbruk nå",momentary:"øyeblikksverdi",power_limit:"Effektgrense",safe_state_chip:"Sikker tilstand",safe_state_back_text:"Effektsensoren {sensor} gir en gyldig verdi igjen. Reguleringen starter på nytt med alt avslått ved neste avgjørelse.",penalty_chip:"Straffeperiode",next_decision:"Neste avgjørelse",next_decision_at:"Neste avgjørelse kl. {time}",appliances_and_chargers:"Apparater og elbilladere",power:"Effekt",temperature:"Temperatur",no_chargers:"Ingen elbilladere i gruppen.",no_appliances:"Ingen apparater er konfigurert.",on:"På",off:"Av",activated:"Aktivert",deactivated:"Deaktivert",waiting_ends_at:"Slås på ved avgjørelsen kl. {time}",delayed_turn_on:"Forsinket innkobling",charging_at:"Lader med {current} A",first_decision:"Venter på første avgjørelse",bypassed_no_car:"Forbigått: ingen bil tilkoblet",waiting_charger:"I kø: en annen elbillader i gruppen har tur",starting_until:"Venter til {time} på at bilen begynner å lade. Effekten ved minste ladestrøm holdes ledig så lenge.",excluded:"Utenfor regulering",outside_window:"Utenfor ladetidsrom ({start}–{end})",next_ampere_at:"Én ampere til ved avgjørelsen kl. {time}",amperes:"{current} A",chargers_charging:"{charging} av {total} elbilladere lader",activated_not_charging:"Aktivert: bilen trekker ikke effekt, så den venter på minste ladestrøm",window_overridden:"Ladetidsrommet er overstyrt",finishing_at:"Fullfører ladingen som pågikk da ladetidsrommet sluttet, med {current} A",chip_charging:"Lader",chip_no_car:"Ingen bil tilkoblet",chip_queued:"I kø",chip_starting:"Starter",chip_excluded:"Utenfor regulering",chip_window:"{start}–{end}",chip_override:"Overstyrt",chip_finishing:"Fullfører",chip_first_decision:"Første avgjørelse",chip_fault:"Feil",fault:"Et feilflagg viser feil, så elbilladeren er deaktivert til feilen er borte",free_power:"{power} kW ({share}) ledig",power_runs_out:"Her er effekten brukt opp. Det som står under, venter på ledig effekt.",queued_for_room:"I kø: venter på plass ved siden av elbilladerne som lader"},missing:{missing_power_sensor:"Effektsensor er ikke valgt.",missing_device:"{item}: enheten er ikke valgt.",missing_entity:"{item}: entitet er ikke valgt.",missing_action:"{item}: handling for å {action} mangler.",missing_condition:"{item}: uttrykket mangler.",missing_car_connected:"{item}: «bil tilkoblet» mangler.",missing_fault_flag:"{item}: «feilflagg» mangler.",unknown:"{item}: {code}",appliance_without_entity:"Et apparat uten entitet",charger_without_entity:"En elbillader uten entitet",actions:{turn_on:"slå på",turn_off:"slå av",activate:"aktivere",deactivate:"deaktivere",set_current:"sette ladestrøm"},missing_charging_power:"{item}: «ladeeffekt» mangler."},config:{save:"Lagre",restore_defaults:"Gjenopprett standardinnstillinger",discard:"Forkast",unsaved:"Ulagrede endringer",fix_before_saving:"Rett de merkede innstillingene før du lagrer.",not_saved:"Konfigurasjonen ble ikke lagret. Rett de merkede innstillingene.",save_refused_running:"Konfigurasjonen kan ikke lagres når reguleringen kjører.",leave_title:"Forkaste ulagrede endringer?",leave_text:"Endringene på konfigurasjonssidene er ikke lagret. De går tapt hvis du går videre.",stay:"Fortsett å redigere",leave:"Forkast endringer"},locked:{title:"Konfigurasjonen er låst",text:"Reguleringen kjører. Stopp reguleringen for å endre konfigurasjonen. Når reguleringen stoppes, slås alle regulerte apparater og elbilladere av."},warning:{appliances_title:"Ikke slå regulerte apparater av eller på utenom Kraftvakt",chargers_title:"Ikke slå elbilladere av eller på utenom Kraftvakt",text:"Manuell styring og automasjoner kan forstyrre reguleringen, gå ut over apparater med høyere prioritet og utløse straff. Kraftvakt setter dem også tilbake når den gjentar kommandoene sine."},errors:{required:"Påkrevd.",fault_flag_required:"Velg et feilflagg, eller slå innstillingen av.",out_of_range:"Må være mellom {min} og {max}.",at_least:"Må være minst {min}.",invalid_resolution:"Må være et multiplum av {resolution}.",not_integer:"Må være et helt tall.",invalid_entity_id:"Ikke en gyldig entitets-ID.",empty_label:"Merkelappen kan ikke være tom.",duplicate_label:"Merkelappen må være unik for apparatet.",empty_name:"Navnet kan ikke være tomt.",duplicate_name:"Navnet brukes allerede av en annen gruppe.",min_current_above_max:"Minste ladestrøm kan ikke være større enn største.",invalid_time:"Angi både start og slutt.",window_start_equals_end:"Start og slutt kan ikke være like.",duplicate_entity:"Entiteten brukes allerede av et annet apparat eller en elbillader.",unknown_device:"Enheten finnes ikke lenger i Home Assistant.",entity_not_on_device:"Entiteten hører ikke til enheten til elbilladeren, eller til apparatets entitet.",invalid_action:"Home Assistant kan ikke lese handlingen.",invalid_template:"Malen har en syntaksfeil.",default_action_unavailable:"Entiteten har ingen standardhandling. Velg egendefinert handling.",unsupported_entity_domain:"Entiteten kan ikke brukes. Velg en tallentitet.",domain_action_unavailable:"Handlingen er ikke tilgjengelig for entiteten. Velg en annen handling.",unsupported_option:"Entiteten støtter ikke denne verdien.",outside_entity_range:"Utenfor området til entiteten.",unknown:"Ugyldig verdi ({code}).",current_off_unsupported:"Entiteten kan ikke settes til 0 A, som stopper en elbillader som slås på og av med strømmen.",essential_with_variants:"Et nødvendig apparat kan ikke ha varianter. Slett dem, eller slå av innstillingen.",essential_with_power_reserve:"Et nødvendig apparat har ingen effektreserve. Slå av innstillingen, eller slå av Fast last først.",essential_not_at_top:"Et nødvendig apparat må stå over alle andre i prioritetslisten.",not_a_thermostat:"Velg en termostat, en climate-entitet."},dialog:{ok:"OK",cancel:"Avbryt",close:"Lukk"},general:{measurement:"Måling",regulation:"Regulering",penalty:"Straff",interval_option:"{count} × reguleringsvinduet",fields:{power_sensor:{label:"Effektsensor",helper:"Husets totale effekt nå, vanligvis fra HAN-porten på strømmåleren. W eller kW."},regulation_window_s:{label:"Reguleringsvindu",helper:"Avgjørelsene bruker snittet over dette tidsrommet. Lengre jevner ut korte topper, kortere reagerer raskere. {min}–{max} s, standard {default} s."},power_limit_w:{label:"Effektgrense",helper:"Trinnet i kapasitetsleddet du vil holde deg under. Snittet den siste timen holdes under grensen. {min}–{max} W, standard {default} W."},turn_on_margin_w:{label:"Innkoblingsmargin",helper:"Apparater slås på bare så langt under effektgrensen, så de ikke slås av igjen med en gang. {min}–{max} W, standard {default} W."},regulation_interval:{label:"Avgjør hver",helper:"Nå hvert {seconds}. sekund. Standard {default} ×."},wait_at_limit_s:{label:"Ventetid ved effektgrensen",helper:"Hvor lenge et apparat venter før det slås på når lite effekt er ledig. Jo mer effekt som er ledig, jo kortere venter det. {min}–{max} s, standard {default} s."},penalty_threshold_w:{label:"Straffeterskel",helper:"Hvor langt snittet den siste timen kan gå over effektgrensen før alt slås av. {min}–{max} W, standard {default} W."},wait_curve_steepness:{label:"Bratthet"},wait_curve_pivot:{label:"Vendepunkt"},appliance_repeat_increment_factor:{label:"Økning hver gang",helper:"Andel av ventetiden ved effektgrensen. Standard × {default}."},appliance_repeat_increments:{label:"Flest økninger",helper:"{min}–{max}, standard {default}."},charger_repeat_increment_factor:{label:"Økning hver gang",helper:"Andel av ventetiden ved effektgrensen. Standard × {default}."},charger_repeat_increments:{label:"Flest økninger",helper:"{min}–{max}, standard {default}."},command_repeat_interval_min:{label:"Gjenta kommandoen etter",helper:"{min}–{max} min, standard {default} min."},action_timeout_s:{label:"Tidsavbrudd for handling",helper:"En handling som tar lengre tid, stoppes og regnes som mislykket. {min}–{max} s, standard {default} s."},power_sensor_timeout_s:{label:"Tidsavbrudd for effektsensor",helper:"En effektsensor som ikke rapporterer på så lenge, regnes som tapt, og alt slås av. En HAN-leser rapporterer vanligvis hvert 10. sekund. {min}–{max} s, standard {default} s."}},penalty_info:"En sikkerhetsventil som aldri skal trenges: hvis snittet den siste timen likevel går over effektgrensen, holdes alt av til overforbruket er tatt igjen."},advanced:{wait_curve:"Ventetidskurve",wait_curve_info:"Hvor lenge et apparat venter, etter hvor mye effekt som er ledig. Reell ventetid er rundet opp til neste avgjørelse.",free_power_kw:"Ledig effekt kW",waiting_minutes:"Ventetid min:s",actual_waiting_minutes:"Reell ventetid min:s",repeated_turn_on:"Ventetid ved gjentatt innkobling",repeated_turn_on_info:"Når det samme apparatet, eller den samme amperen på en elbillader, slås på gang på gang uten at noe annet slås av eller på imellom, øker ventetiden fra tredje gang. De to første følger kurven; tabellen viser dem ved vendepunktet.",turn_on_in_a_row:"Innkobling på rad",appliances:"Apparater",chargers:"Elbilladere",command_repeat:"Gjentatt kommando",command_repeat_info:"Et apparat eller en elbillader kan endre tilstand av seg selv, for eksempel etter et strømbrudd. Når det ikke har fått kommando på så lenge, får det den siste på nytt. De som er utenfor regulering, får være i fred.",timeouts:"Tidsavbrudd",timeouts_info:"Beskytter mot en handling som aldri blir ferdig, og en effektsensor som slutter å rapportere."},list:{drag:"Dra for å endre rekkefølgen",edit:"Rediger",view:"Vis"},appliances:{priority_title:"Prioritetsliste",priority_sub:"Slås på ovenfra og av nedenfra. Dra for å endre rekkefølgen.",add:"Legg til apparat",empty:"Ingen apparater ennå. Legg til apparatene Kraftvakt kan slå av når forbruket blir for høyt.",charger_group_sub:"elbilladere: {count} · konfigureres under",power_reserve:"effektreserve {power} W",essential:"Nødvendig",variant_count:"varianter: {count}",variant_entity:"Variant · entitet {entity}",variant_template:"Variant · mal",variant_own_actions:"egne handlinger",variant_own_turn_on:"egen handling for å slå på",variant_own_turn_off:"egen handling for å slå av"},appliance:{add_title:"Legg til apparat",edit_title:"Rediger apparat",view_title:"Apparat",variants:"Varianter",variants_info:"Gi apparatet en annen plass i prioritetslisten til bestemte tider eller forhold, for eksempel høyere plass for varmtvannsberederen om morgenen. Den øverste varianten som gjelder, vinner.",add_variant:"Legg til variant",display_values:"Visningsverdier",display_values_info:"Valgfrie, og ikke brukt av reguleringen. Vises på statussiden for oversiktens skyld.",delete:"Slett apparat",fields:{entity_id:{label:"Entitet",helper:"Det Kraftvakt slår på og av, for eksempel bryteren til en varmtvannsbereder. Navnet blir apparatets navn."},essential:{label:"Nødvendig apparat",helper:"For et apparat som alltid må gå, som en fryser. Det holdes på, og slås av bare i en straffeperiode. Ikke for et apparat med varianter."},turn_on:{label:"Handling for å slå på",helper:"Standard passer for de fleste entiteter."},turn_off:{label:"Handling for å slå av",helper:"Standard passer for de fleste entiteter."},fixed_load:{label:"Fast last",helper:"Bare for et apparat som alltid bruker samme effekt mens det er på, som en takvifte. Aldri for et apparat med termostat eller annen egen styring: da virker reguleringen dårligere."},power_reserve_w:{label:"Effektreserve",helper:"Det apparatet bruker mens det er på. Gjelder alle varianter."},label:{label:"Merkelapp"},condition:{label:"Uttrykk"},override_turn_on:{label:"Egen handling for å slå på",helper:"For eksempel en annen HVAC-modus."},override_turn_off:{label:"Egen handling for å slå av",helper:"For eksempel frostsikring."},display_power:{label:"Effekt"},display_temperature:{label:"Temperatur"}}},variant:{edit_title:"Rediger variant {name}",view_title:"Variant {name}",condition:"Uttrykk",delete:"Slett variant",condition_info:"Varianten gjelder når uttrykket er sant, for eksempel mellom 05 og 08. Ellers har apparatet sin vanlige plass."},action:{default:"Standard",custom:"Egendefinert",entity:"Entitet",domain_actions:{climate_hvac_mode:"HVAC-modus",climate_temperature:"Temperatur",climate_hvac_mode_and_temperature:"HVAC-modus og temperatur"},default_runs:"Kjører {service} for entiteten.",entity_runs:"Kjører {service} for den valgte entiteten med ladestrømmen som verdi.",no_default:"Entitetstypen har ingen standardhandling, så handlingen må være egendefinert.",choose_entity:"Velg entitet for å bruke standardhandlingen.",choose_action_entity:"Velg entiteten som skal få verdien.",variables:"Variabler: {variables}.",parameters:{hvac_mode:"HVAC-modus",temperature:"Måltemperatur"},parameter_range:"{min}–{max} {unit} for entiteten."},condition:{entity:"Entitet",template:"Mal",entity_label:"Boolsk entitet",template_label:"Mal",entity_helper:"Sann bare når den er på. Utilgjengelig regnes som usann.",state:"Tilstand",state_label:"Entitet med tilstand",state_helper:"For eksempel en statussensor på elbilladeren.",states_label:"Tilstander",states_helper:"Velg eller skriv inn tilstandene. Alle andre tilstander regnes som det motsatte, unntatt utilgjengelig, som regnes som usann.",template_helper:"Sann bare når den gir sann. Variabler: entity_id, entity.",now:"Nå: {value}",true:"sann",false:"usann",error:"Feil: {message}",invalid:"Malen gir {value}, som ikke er sann eller usann, og regnes derfor som usann."},actively_charging:{type_label:"Lading på/av fra",entity:"Entitet",template:"Mal",entity_label:"Boolsk entitet",template_label:"Mal",entity_helper:"På mens bilen lader. Utilgjengelig regnes ikke som lading.",state:"Tilstand",state_label:"Entitet med tilstand",state_helper:"For eksempel en statussensor på elbilladeren.",states_label:"Tilstander",states_helper:"Velg eller skriv inn tilstandene. Alle andre tilstander regnes som det motsatte, unntatt utilgjengelig, som ikke regnes som lading.",template_helper:"Sann betyr lading, alt annet ikke lading. Variabler: entity_id, entity.",true:"lader",false:"lader ikke",invalid:"Malen gir {value}, som ikke er sann eller usann, og regnes derfor ikke som lading."},charging_power:{type_label:"Ladeeffekt fra",power_sensor:"Sensor",template:"Mal",power_sensor_label:"Sensor for ladeeffekt",template_label:"Mal for ladeeffekt",power_sensor_helper:"Over 100 W regnes som lading. W eller kW.",template_helper:"Effekten i W; over 100 W regnes som lading. Variabler: entity_id, entity.",true:"lader",false:"lader ikke",invalid:"Malen gir {value}, som ikke er et tall, og regnes derfor ikke som lading."},display_power:{type_label:"Effekt fra",power_sensor:"Sensor",template:"Mal",power_sensor_label:"Effekt",template_label:"Mal for effekt",power_sensor_helper:"En sensor på samme enhet som entiteten. W eller kW.",template_helper:"Effekten i W, også fra en annen enhet. Variabler: entity_id, entity.",no_value:"ingen verdi",invalid:"Malen gir {value}, som ikke er et tall, så ingenting vises."},display_temperature:{type_label:"Temperatur fra",temperature_sensor:"Entitet",template:"Mal",current_temperature:"{name}: nåværende temperatur",target_temperature:"{name}: innstilt temperatur",temperature_sensor_label:"Temperatur",template_label:"Mal for temperatur",temperature_sensor_helper:"En temperatursensor på samme enhet som entiteten, eller en termostats nåværende eller innstilte temperatur.",template_helper:"En temperatur i enheten til Home Assistant, også fra en annen enhet. Variabler: entity_id, entity.",no_value:"ingen verdi",invalid:"Malen gir {value}, som ikke er et tall, så ingenting vises."},fault:{entity:"Entitet",template:"Mal",entity_label:"Boolsk entitet",template_label:"Mal",entity_helper:"På betyr feil. Utilgjengelig er ingen feil.",state:"Tilstand",state_label:"Entitet med tilstand",state_helper:"For eksempel en statussensor på elbilladeren.",states_label:"Tilstander",states_helper:"Velg eller skriv inn tilstandene. Alle andre tilstander regnes som det motsatte, unntatt utilgjengelig, som er ingen feil.",template_helper:"Sann betyr feil, alt annet ingen feil. Variabler: entity_id, entity.",true:"feil",false:"ingen feil",invalid:"Malen gir {value}, som ikke er sann eller usann, og regnes derfor som ingen feil."},charging:{name:"Navn",name_sub:"Vises i prioritetslisten og på statussiden.",one_at_a_time:"Én elbillader om gangen",one_at_a_time_sub:"Bare én bil i gruppen lader om gangen. Mens ingen lader, kan hver bil vente på minste ladestrøm, og den første som trekker effekt, får tur.",dynamic_order:"Dynamisk ladeprioritet",dynamic_order_sub:"Av: ladeprioriteten under gjelder alltid, så en bil høyere opp som trekker effekt, tar over fra en som lader under.\nPå: elbilladere som lader, går først, og de andre venter på tur.",chargers:"Ladeprioritet",chargers_sub:"Høyest øverst. Dra en elbillader til en annen gruppe for å flytte den.",add:"Legg til elbillader",empty:"Ingen elbilladere ennå.",no_groups:"Ingen grupper av elbilladere ennå. Legg til en gruppe, og så elbilladerne i den.",add_group:"Legg til gruppe",new_group_name:"Elbilladere",unnamed_group:"Gruppe uten navn",delete_group:"Slett gruppe",delete_group_not_empty:"Flytt eller slett elbilladerne for å slette gruppen.",switches_info:"Hver elbillader får tre brytere du kan bruke når reguleringen kjører: «‹lader› utenfor regulering», «‹lader› overstyr ladetidsrom» og «‹lader› fullfør lading etter ladetidsrom».",currents:"{min}–{max} A",min_current_power:"{power} W ved minste ladestrøm",window:"ladetidsrom {start}–{end}",finishes_after_window:"fullfører pågående lading etter tidsrommet",always_allowed:"alltid lov til å lade",car_from:"bil tilkoblet fra {source}",car_template:"bil tilkoblet fra mal",charging_from:"lader aktivt fra {source}",charging_template:"lader aktivt fra mal",power_from:"ladeeffekt fra {source}",power_template:"ladeeffekt fra mal",deactivated_on_fault:"deaktiveres ved feil",switched_by_current:"slås på og av med strømmen"},charger:{add_title:"Legg til elbillader",edit_title:"Rediger elbillader",view_title:"Elbillader",charging_current:"Ladestrøm",profile_applied:"Fylt ut fra laderprofilen {profile}. Sjekk alle feltene før du lagrer.",override_ends:{manual:"Når jeg slår den av",charging_stopped:"Når bilen ikke lader lenger",car_disconnected:"Når bilen kobles fra"},delete:"Slett elbillader",fields:{device_id:{label:"Enhet",helper:"Elbilladeren i Home Assistant. Entitetene velges under, og fylles ut når Kraftvakt kjenner laderen."},entity_id:{label:"Laderentitet",helper:"Vanligvis bryteren som tillater lading."},activate:{label:"Handling for å aktivere",helper:"Standard passer for de fleste entiteter."},deactivate:{label:"Handling for å deaktivere",helper:"Standard passer for de fleste entiteter."},min_current_a:{label:"Minste ladestrøm"},max_current_a:{label:"Største ladestrøm"},set_current:{label:"Sett ladestrøm"},min_current_power_w:{label:"Effekt ved minste ladestrøm",helper:"Det bilen trekker på minste ladestrøm, omtrent 1400 W på én fase. Bilen begynner å lade bare når så mye effekt er ledig. {min}–{max} W, standard {default} W, 6 A på tre faser."},car_connected:{label:"Bil tilkoblet",helper:"En elbillader uten bil aktiveres ikke. Utilgjengelig regnes som ikke tilkoblet."},actively_charging:{label:"Lader aktivt",helper:"Ladeeffekten er påkrevd, og forteller hvor mye bilen trekker. Lading av/på er valgfri, og kan fortelle tidligere at bilen lader."},charging_power:{label:"Ladeeffekt"},cloud_controlled:{label:"Skystyrt elbillader",helper:"For en elbillader som styres over internett. Den får færre gjentatte kommandoer, og effekten holdes ledig mens bilen begynner å lade."},start_delay_s:{label:"Startforsinkelse",helper:"Hvor lang tid bilen kan bruke på å begynne å lade etter at elbilladeren er aktivert. Effekten ved minste ladestrøm holdes ledig så lenge. {min}–{max} s, standard {default} s."},deactivate_on_fault:{label:"Deaktiver ved feil",helper:"Så lenge et feilflagg viser feil, stoppes elbilladeren, og de andre i gruppen kan lade. Utilgjengelig er ingen feil."},fault_flag:{label:"Feilflagg"},charging_window:{label:"Ladetidsrom",helper:"Elbilladeren lader bare innenfor dette tidsrommet hver dag, for eksempel om natten. Av: den kan alltid lade."},start:{label:"Start"},end:{label:"Slutt"},finish_after_window:{label:"Fullfør lading etter ladetidsrommet",helper:"En bil som lader når ladetidsrommet slutter, kan fortsette til den stopper. Deretter venter den på neste ladetidsrom."},override_ends:{label:"Avslutt overstyringen",helper:"Når bryteren «‹lader› overstyr ladetidsrom» slår seg av selv. Den kan slås på før bilen kommer."},switched_by_current:{label:"Lading slås på og av med",helper:"Velg strømmen for en elbillader som ikke kan slå lading på og av: 0 A stopper den."}},charging_current_info:"Strømmen økes og senkes én ampere om gangen etter ledig effekt. Minste ladestrøm er den laveste strømmen bilen lader med, vanligvis 6 A, og største det elbilladeren og sikringen tåler.",state_choices:{car_connected:{true:"Tilstander for tilkoblet",false:"Tilstander for frakoblet"},actively_charging:{true:"Tilstander for lading",false:"Tilstander for ikke lading"},fault_flag:{true:"Tilstander for feil",false:"Tilstander for ingen feil"}},switched_by:{actions:"Handlinger for å aktivere og deaktivere",current:"Ladestrømmen"}}}};function at(e){const t=rt[e]??rt[e.split("-")[0]]??rt.en;return(e,i={})=>(nt(t,e)??nt(rt.en,e)??e).replace(/\{(\w+)\}/g,(e,t)=>t in i?String(i[t]):e)}function nt(e,t){let i=e;for(const e of t.split("."))i=i?.[e];return"string"==typeof i?i:void 0}const st=["status","general","appliances","charging","advanced"],ot="/kraftvakt";function lt(e,t={}){const i=`${ot}/${e}`;t.replace?history.replaceState(null,"",i):history.pushState(null,"",i),window.dispatchEvent(new CustomEvent("location-changed",{detail:{replace:t.replace??!1}}))}function dt(e,t){const i=e.currentTarget;"click"===e.type&&e.detail>0&&i.blur(),i.dispatchEvent(new CustomEvent("hass-more-info",{detail:{entityId:t},bubbles:!0,composed:!0}))}const ct=g`
  .section-header {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px 12px;
    min-height: 40px;
  }
  .section-title {
    flex: 1;
    min-width: 0;
    font-size: var(--ha-font-size-l, 16px);
    font-weight: var(--ha-font-weight-medium, 500);
  }
  .description {
    margin: 0;
    color: var(--secondary-text-color);
  }
  .note {
    flex: 1;
    min-width: 0;
    font-size: var(--ha-font-size-s, 12px);
    color: var(--secondary-text-color);
  }
`;function ht(e,t=te){return X`
    <div class="section-header">
      <span class="section-title">${e}</span>
      ${t}
    </div>
  `}function pt(e){return e?X`<p class="description">${e}</p>`:te}function ut(e,t,i){return new Intl.NumberFormat(e,{minimumFractionDigits:i,maximumFractionDigits:i}).format(t)}function gt(e,t){return null===t?"–":ut(e,t/1e3,2)}function ft(e){if(null===e)return"–";const t=Math.round(e);return`${Math.floor(t/60)}:${String(t%60).padStart(2,"0")}`}function mt(e,t){return new Intl.NumberFormat(e,{style:"percent",maximumFractionDigits:0}).format(t)}function vt(e,t){return new Date(t).toLocaleTimeString(e)}function _t(e){return Math.min(1,Math.max(0,(e-.5)/.5))}function yt(e,t){const i=Math.min(_t(t/100),.8**(1/e)*.999)**e,r=i*(1-.8)/(.8-i);return t=>{const i=_t(t)**e;return 0===i?0:i*(1+r)/(i+r)}}function wt(e,t){return Math.max(0,Math.ceil(e/t-1e-9))*t}class bt{constructor(e,t){this.host=e,this.maxWidth=t,this.matches=!1,this.observer=new ResizeObserver(([e])=>{const t=e.contentRect.width<=this.maxWidth;t!==this.matches&&(this.matches=t,this.host.requestUpdate())}),e.addController(this)}hostConnected(){this.observer.observe(this.host)}hostDisconnected(){this.observer.disconnect()}}const $t=(e,t,i)=>{const r=new Map;for(let a=t;a<=i;a++)r.set(e[a],a);return r},kt=ze(class extends Se{constructor(e){if(super(e),e.type!==Ae)throw Error("repeat() can only be used in text expressions")}dt(e,t,i){let r;void 0===i?i=t:void 0!==t&&(r=t);const a=[],n=[];let s=0;for(const t of e)a[s]=r?r(t,s):s,n[s]=i(t,s),s++;return{values:n,keys:a}}render(e,t,i){return this.dt(e,t,i).values}update(e,[t,i,r]){const a=(e=>e._$AH)(e),{values:n,keys:s}=this.dt(t,i,r);if(!Array.isArray(a))return this.ut=s,n;const o=this.ut??=[],l=[];let d,c,h=0,p=a.length-1,u=0,g=n.length-1;for(;h<=p&&u<=g;)if(null===a[h])h++;else if(null===a[p])p--;else if(o[h]===s[u])l[u]=Le(a[h],n[u]),h++,u++;else if(o[p]===s[g])l[g]=Le(a[p],n[g]),p--,g--;else if(o[h]===s[g])l[g]=Le(a[h],n[g]),Te(e,l[g+1],a[h]),h++,g--;else if(o[p]===s[u])l[u]=Le(a[p],n[u]),Te(e,a[h],a[p]),p--,u++;else if(void 0===d&&(d=$t(s,u,g),c=$t(o,h,p)),d.has(o[h]))if(d.has(o[p])){const t=c.get(s[u]),i=void 0!==t?a[t]:null;if(null===i){const t=Te(e,a[h]);Le(t,n[u]),l[u]=t}else l[u]=Le(i,n[u]),Te(e,a[h],i),a[t]=null;u++}else Ie(a[p]),p--;else Ie(a[h]),h++;for(;u<=g;){const t=Te(e,l[g+1]);Le(t,n[u]),l[u++]=t}for(;h<=p;){const e=a[h++];null!==e&&Ie(e)}return this.ut=s,De(e,l),ee}});let xt=class extends ve{constructor(){super(...arguments),this.rows=[],this.locked=!1,this.emptyText=""}render(){return X`
      <ha-sortable
        handle-selector=".handle"
        group=${(e=>e??te)(this.group)}
        .disabled=${this.locked}
        @item-moved=${this.itemMoved}
        @item-added=${this.itemAdded}
        @item-removed=${this.itemRemoved}
      >
        <div class="list" data-empty=${this.emptyText}>${kt(this.rows,e=>e.key,(e,t)=>this.renderRow(e,t))}</div>
      </ha-sortable>
    `}renderRow(e,t){return X`
      <div class="row ${e.highlighted?"highlighted":""}" data-key=${e.key}>
        ${this.locked?te:X`<ha-svg-icon class="handle" .path=${i} title=${this.localize("list.drag")}></ha-svg-icon>`}
        <span class="rank">${t+1}</span>
        ${e.iconPath?X`<ha-svg-icon class="icon" .path=${e.iconPath}></ha-svg-icon>`:te}
        <div class="main">
          <div class="title">${e.title}${e.tag?X`<span class="tag">${e.tag}</span>`:te}</div>
          ${e.details.length>0?X`<div class="details">${r=e.details,r.map((e,t)=>X`${t>0?" · ":""}${e}`)}</div>`:te}
          ${e.errors.map(e=>X`<div class="error">${e}</div>`)}
        </div>
        ${e.openable?X`
              <ha-icon-button
                .path=${this.locked?a:s}
                .label=${this.localize(this.locked?"list.view":"list.edit")}
                @click=${()=>this.dispatchEvent(new CustomEvent("open-row",{detail:e.key}))}
              ></ha-icon-button>
            `:te}
      </div>
    `;var r}itemMoved(e){e.stopPropagation(),this.dispatchEvent(new CustomEvent("item-moved",{detail:e.detail}))}itemAdded(e){e.stopPropagation();const t=e.detail.item.dataset.key;void 0!==t&&this.dispatchEvent(new CustomEvent("item-added",{detail:{key:t,index:e.detail.index}}))}itemRemoved(e){e.stopPropagation()}static{this.styles=g`
    :host {
      display: block;
    }
    .list:empty {
      min-height: 48px;
    }
    .list:empty::before {
      content: attr(data-empty);
      display: block;
      padding: 0 16px 16px;
      color: var(--secondary-text-color);
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
    .row.highlighted {
      background: linear-gradient(var(--kraftvakt-essential-background), var(--kraftvakt-essential-background)),
        var(--card-background-color);
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
  `}};e([$e({attribute:!1})],xt.prototype,"localize",void 0),e([$e({attribute:!1})],xt.prototype,"rows",void 0),e([$e({type:Boolean})],xt.prototype,"locked",void 0),e([$e()],xt.prototype,"group",void 0),e([$e()],xt.prototype,"emptyText",void 0),xt=e([ye("kraftvakt-sortable-list")],xt);const At={missing_power_sensor:"missing.missing_power_sensor",missing_device:"missing.missing_device",missing_entity:"missing.missing_entity",missing_action:"missing.missing_action",missing_condition:"missing.missing_condition",missing_car_connected:"missing.missing_car_connected",missing_fault_flag:"missing.missing_fault_flag",missing_charging_power:"missing.missing_charging_power"},Ct={turn_on:"missing.actions.turn_on",turn_off:"missing.actions.turn_off",activate:"missing.actions.activate",deactivate:"missing.actions.deactivate",set_current:"missing.actions.set_current"},Et={general:"general",appliances:"appliances",priority:"appliances",charger_groups:"charging",chargers:"charging"},zt=new Set(["wait_curve_steepness","wait_curve_pivot","appliance_repeat_increment_factor","appliance_repeat_increments","charger_repeat_increment_factor","charger_repeat_increments","command_repeat_interval_min","action_timeout_s","power_sensor_timeout_s"]);function St(e,t){const i=e?.split(".").at(-1)??"";return Ct[i]?t(Ct[i]):e??""}function Vt(e,t,i){const r="chargers"===e.section?t&&it(t.config):t?.config.appliances,a=r?.find(t=>t.id===e.target),n=a?.entity_id,s=n?t?.entity_names[n]??n:i("chargers"===e.section?"missing.charger_without_entity":"missing.appliance_without_entity"),o=e.field?.startsWith("variants.")?e.field.split(".")[1]:void 0,l=a&&"variants"in a?a.variants.find(e=>e.id===o):void 0;return l?`${s} «${l.label}»`:s}const Mt={required:"errors.required",missing_power_sensor:"errors.required",missing_device:"errors.required",missing_entity:"errors.required",missing_action:"errors.required",missing_condition:"errors.required",missing_car_connected:"errors.required",missing_fault_flag:"errors.fault_flag_required",missing_charging_power:"errors.required",not_integer:"errors.not_integer",invalid_entity_id:"errors.invalid_entity_id",empty_label:"errors.empty_label",empty_name:"errors.empty_name",duplicate_name:"errors.duplicate_name",duplicate_label:"errors.duplicate_label",min_current_above_max:"errors.min_current_above_max",invalid_time:"errors.invalid_time",window_start_equals_end:"errors.window_start_equals_end",duplicate_entity:"errors.duplicate_entity",unknown_device:"errors.unknown_device",entity_not_on_device:"errors.entity_not_on_device",invalid_action:"errors.invalid_action",invalid_template:"errors.invalid_template",default_action_unavailable:"errors.default_action_unavailable",unsupported_entity_domain:"errors.unsupported_entity_domain",domain_action_unavailable:"errors.domain_action_unavailable",unsupported_option:"errors.unsupported_option",outside_entity_range:"errors.outside_entity_range",current_off_unsupported:"errors.current_off_unsupported",essential_with_variants:"errors.essential_with_variants",essential_with_power_reserve:"errors.essential_with_power_reserve",essential_not_at_top:"errors.essential_not_at_top",not_a_thermostat:"errors.not_a_thermostat"},Ht={general:"general",appliances:"appliances",chargers:"chargers"};function Tt(e,t,i,r){const a=Ht[e.section],n=a&&e.field?i?.limits[a][e.field]:void 0,s=e=>null===e?"":new Intl.NumberFormat(r).format(e);return"out_of_range"===e.code&&n?null===n.max?t("errors.at_least",{min:s(n.min)}):t("errors.out_of_range",{min:s(n.min),max:s(n.max)}):"invalid_resolution"===e.code&&n?t("errors.invalid_resolution",{resolution:s(n.resolution)}):t(Mt[e.code]??"errors.unknown",{code:e.code})}function Lt(e,t,i){const r={};for(const a of e)a.field?.startsWith(t)&&(r[a.field.slice(t.length)]??=i(a));return r}function Pt(e,t){return t?Object.values(e.entities??{}).filter(e=>e.device_id===t).map(e=>e.entity_id):[]}function Dt(e,t){return t&&e.entities?.[t]?.device_id||null}function It(e){return[["display_power",Nt(e.display_power)],["display_temperature",Nt(e.display_temperature)]].filter(e=>!!e[1])}function Ft(e,t,i){const r=Dt(i,t),a=r?new Set(Pt(i,r)):void 0;return{display_power:Ot(e.display_power,a),display_temperature:Ot(e.display_temperature,a)}}function Nt(e){return e&&"template"!==e.type?e.value:null}function Ot(e,t){const i=Nt(e);return i&&t&&!t.has(i)?null:e}function Wt(e,t,i,r){const a=e.domain_actions[t][i],n=r?.split(".")[0];return Object.fromEntries(Object.entries(a).filter(([,e])=>e.domain===n))}function jt(e,t,i,r,a){return a?.domain_action?Wt(e,t,i,r)[a.domain_action]:void 0}function Rt(e,t,i={}){return Object.fromEntries(e.parameters.map(e=>[e.name,i[e.name]??qt(e,t)]))}function Ut(e,t){return{min:Zt(t,e.min_attribute),max:Zt(t,e.max_attribute),step:Zt(t,e.step_attribute)}}function Bt(e,t,i){if(null===t)return;if("option"===e.type){const r=Gt(i,e.options_attribute);return Array.isArray(r)&&!r.includes(t)?"unsupported_option":void 0}const{min:r,max:a}=Ut(e,i);return"number"==typeof t&&(void 0!==r&&t<r||void 0!==a&&t>a)?"outside_entity_range":void 0}function qt(e,t){if("option"===e.type){const i=Gt(t,e.options_attribute),r=Array.isArray(i)?i:e.preferred_options;return e.preferred_options.find(e=>r.includes(e))??null}return e.default}function Gt(e,t){return t?e?.attributes[t]:void 0}function Zt(e,t){const i=Gt(e,t);return"number"==typeof i?i:void 0}const Kt=["turn_on","turn_off"];function Jt(e){return[...Kt.map(t=>({name:t,field:t,action:e[t]})),...e.variants.flatMap(e=>Kt.filter(t=>Qt(e.actions,t)).map(t=>({name:t,field:`variants.${e.id}.${t}`,action:e.actions[t]??null})))]}function Qt(e,t){return void 0!==e?.[t]}function Xt(e){return(e.switched_by_current?["set_current"]:["activate","deactivate","set_current"]).map(t=>({name:t,field:t,action:e[t]}))}function Yt(e){const t=e.map(e=>e.name.trim());return e.flatMap((e,i)=>{const r=t[i],a=r?t.filter(e=>e===r).length>1?"duplicate_name":void 0:"empty_name";return a?[{code:a,section:"charger_groups",target:e.id,field:"name"}]:[]})}function ei(e){const t=[];return e.general.power_sensor||t.push({code:"missing_power_sensor",section:"general",field:"power_sensor"}),t.push(...e.appliances.flatMap(ti),...it(e).flatMap(ii)),t}function ti(e){return[...ui("appliances",e,Jt(e)),...e.variants.filter(e=>!ci(e.condition)).map(t=>di(e,"missing_condition",`variants.${t.id}.condition`))]}function ii(e){const t=e.device_id?[]:[{code:"missing_device",section:"chargers",target:e.id,field:"device_id"}];return t.push(...ui("chargers",e,Xt(e))),ci(e.car_connected)||t.push({code:"missing_car_connected",section:"chargers",target:e.id,field:"car_connected"}),ci(e.charging_power)||t.push({code:"missing_charging_power",section:"chargers",target:e.id,field:"charging_power"}),e.deactivate_on_fault&&!ci(e.fault_flag)&&t.push({code:"missing_fault_flag",section:"chargers",target:e.id,field:"fault_flag"}),t}function ri(e,t,i){return e.default_actions[t][i]}function ai(e,t,i,r,a){switch(a?.mode){case"default":return ni(e,t,i,r);case"domain":return void 0!==jt(e,t,i,r,a);default:return!0}}function ni(e,t,i,r){return null!==r&&ri(e,t,i).domains.includes(r.split(".")[0])}function si(e,t,i){return e.filter(e=>e.section===t&&e.target===i)}function oi(e,t,i){const r=e.variants.map(e=>e.label.trim()),a=Dt(i,e.entity_id);return[...hi("appliances",e.id,e,t.limits.appliances,!1),...pi("appliances",e,Jt(e),t,i.states),...a?It(e).filter(([,e])=>Dt(i,e)!==a).map(([t])=>di(e,"entity_not_on_device",t)):[],...e.variants.flatMap((t,i)=>{const a=`variants.${t.id}.label`;return""===r[i]?[di(e,"empty_label",a)]:r.filter(e=>e===r[i]).length>1?[di(e,"duplicate_label",a)]:[]})]}function li(e,t,i){const r=(t,i)=>({code:t,section:"chargers",target:e.id,field:i}),a=[...hi("chargers",e.id,e,t.limits.chargers,!0),...pi("chargers",e,Xt(e),t,i.states),...gi(e,i).map(([e,t])=>r(e,t))];(function(e,t){const i=e.set_current;if(!e.switched_by_current||!i)return!0;const r="entity"===i.mode?i.entity_id:"default"===i.mode?e.entity_id:null,a=r?t[r]?.attributes.min:void 0;return"number"!=typeof a||a<=0})(e,i.states)||a.push(r("current_off_unsupported","set_current")),e.min_current_a>e.max_current_a&&a.push(r("min_current_above_max","min_current_a"));const n=e.charging_window;return!n||n.start&&n.end?n&&n.start===n.end&&a.push(r("window_start_equals_end","charging_window")):a.push(r("invalid_time","charging_window")),a}function di(e,t,i){return{code:t,section:"appliances",target:e.id,field:i}}function ci(e){return null!==e&&""!==e.value.trim()&&("state"!==e.type||(e.states??[]).length>0)}function hi(e,t,i,r,a){const n=i;return Object.entries(r).flatMap(([i,r])=>{const s=n[i],o="number"!=typeof s||Number.isNaN(s)?a?"required":void 0:function(e,t){if(null!==t.min&&e<t.min||null!==t.max&&e>t.max)return"out_of_range";const i=e/t.resolution;return Math.abs(i-Math.round(i))<1e-6?void 0:"invalid_resolution"}(s,r);return o?[{code:o,section:e,target:t,field:i}]:[]})}function pi(e,t,i,r,a){const n=t.entity_id;return null===n?[]:i.flatMap(({name:i,field:s,action:o})=>{const l=(i,r)=>({code:i,section:e,target:t.id,field:r?`${s}.${r}`:s});if(!ai(r,e,i,n,o))return[l("default"===o?.mode?"default_action_unavailable":"domain_action_unavailable")];const d=jt(r,e,i,n,o);return d?Object.entries(function(e,t,i){const r={};for(const a of e.parameters){const e=a.name in t?Bt(a,t[a.name],i):"required";e&&(r[a.name]=e)}return r}(d,o?.data??{},a[n])).map(([e,t])=>l(t,e)):[]})}function ui(e,t,i){return[...t.entity_id?[]:[{code:"missing_entity",section:e,target:t.id,field:"entity_id"}],...i.filter(({action:e})=>function(e){return null===e||"custom"===e.mode&&0===(e.action??[]).length||"entity"===e.mode&&!e.entity_id||"domain"===e.mode&&Object.values(e.data??{}).includes(null)}(e)).map(({field:i})=>({code:"missing_action",section:e,target:t.id,field:i}))]}function gi(e,t){return e.device_id?t.devices?.[e.device_id]?function(e){return[["entity_id",e.entity_id],["set_current","entity"===e.set_current?.mode?e.set_current.entity_id:null],["car_connected",Nt(e.car_connected)],["actively_charging",Nt(e.actively_charging)],["charging_power",Nt(e.charging_power)],["fault_flag",Nt(e.fault_flag)]].filter(e=>!!e[1])}(e).filter(([,i])=>t.entities?.[i]?.device_id!==e.device_id).map(([e])=>["entity_not_on_device",e]):[["unknown_device","device_id"]]:[]}class fi extends ve{constructor(){super(...arguments),this.narrow=!1,this.entityNames={},this.issues=[],this.saveErrors=[],this.locked=!1,this.describeIssue=e=>Tt(e,this.localize,this.capabilities,this.hass.language)}changeConfig(e){!function(e,t){e.dispatchEvent(new CustomEvent(Qe,{detail:t,bubbles:!0,composed:!0}))}(this,e)}formErrors(e,t,i=""){return Lt(si(this.issues,e,t),i,this.describeIssue)}entitiesUsedBesides(e){return[...this.config.appliances,...it(this.config)].filter(t=>t.id!==e&&t.entity_id).map(e=>e.entity_id)}renderCard(e){const t=e.description||void 0!==e.content&&e.content!==te;return X`
      <ha-card>
        <div class="card-header">
          <h2 class="card-title">${e.title}</h2>
          ${e.control??te}
        </div>
        ${t?X`<div class="card-content">${pt(e.description)} ${e.content??te}</div>`:te}
        ${e.list??te} ${e.footer??te}
      </ha-card>
    `}renderCardFooter(e,t){return X`<div class="card-footer"><span class="note">${e}</span>${t}</div>`}renderPageFooter(e,t){return X`<div class="page-footer"><span class="note">${e}</span>${t}</div>`}renderAddButton(e){return X`
      <ha-button .disabled=${e.locked} @click=${e.onAdd}>
        <ha-svg-icon slot="start" .path=${o}></ha-svg-icon>
        ${e.add}
      </ha-button>
    `}renderItemList(e){return 0!==e.rows.length||e.group?X`
          <kraftvakt-sortable-list
            class=${e.locked?"locked":""}
            .localize=${this.localize}
            .rows=${e.rows}
            .locked=${e.locked}
            .group=${e.group}
            .emptyText=${e.empty}
            @item-moved=${e.onMoved}
            @item-added=${e.onAdded}
            @open-row=${e.onOpen}
          ></kraftvakt-sortable-list>
        `:X`<div class="empty">${e.empty}</div>`}static{this.styles=[ct,g`
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
      .card-header {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px 12px;
        padding: 12px 16px 16px;
      }
      .card-title {
        flex: 1;
        min-width: 0;
        margin: 0;
        font-size: var(--ha-card-header-font-size, var(--ha-font-size-2xl, 24px));
        font-weight: var(--ha-font-weight-normal, 400);
        line-height: var(--ha-line-height-expanded, 1.5);
        letter-spacing: -0.012em;
        overflow-wrap: anywhere;
      }
      .card-content {
        display: grid;
        gap: 16px;
        padding: 0 16px 16px;
      }
      .card-footer {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
        padding: 8px 8px 8px 16px;
        border-top: 1px solid var(--divider-color);
      }
      .page-footer {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
        padding-inline-start: 16px;
      }
      .empty {
        padding: 0 16px 16px;
        color: var(--secondary-text-color);
      }
      kraftvakt-sortable-list.locked {
        opacity: 0.6;
      }
    `]}}e([$e({attribute:!1})],fi.prototype,"hass",void 0),e([$e({attribute:!1})],fi.prototype,"localize",void 0),e([$e({type:Boolean,reflect:!0})],fi.prototype,"narrow",void 0),e([$e({attribute:!1})],fi.prototype,"config",void 0),e([$e({attribute:!1})],fi.prototype,"entityNames",void 0),e([$e({attribute:!1})],fi.prototype,"capabilities",void 0),e([$e({attribute:!1})],fi.prototype,"issues",void 0),e([$e({attribute:!1})],fi.prototype,"saveErrors",void 0),e([$e({type:Boolean,reflect:!0})],fi.prototype,"locked",void 0);const mi={power_limit_w:"W",turn_on_margin_w:"W",regulation_window_s:"s",wait_at_limit_s:"s",penalty_threshold_w:"W",command_repeat_interval_min:"min",action_timeout_s:"s",power_sensor_timeout_s:"s"},vi=new Set(["regulation_interval","appliance_repeat_increment_factor","appliance_repeat_increments","charger_repeat_increment_factor","charger_repeat_increments"]);class _i extends fi{constructor(){super(...arguments),this.computeLabel=e=>this.localize(`general.fields.${e.name}.label`),this.computeHelper=e=>{const t=this.range(e.name),i=this.capabilities.defaults.general,r=e=>null==e?"":new Intl.NumberFormat(this.hass.language).format(e),a=this.config.general.regulation_window_s;return this.localize(`general.fields.${e.name}.helper`,{min:r(t?.min),max:r(t?.max),default:r(i[e.name]),seconds:r(a*this.config.general.regulation_interval)})}}renderForm(e){return X`
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
    `}renderRestoreDefaults(e){const t=this.config.general,i=this.capabilities.defaults.general,r=e.every(e=>t[e]===i[e]);return this.renderPageFooter("",X`
        <ha-button appearance="plain" .disabled=${this.locked||r} @click=${()=>{const r=Object.fromEntries(e.map(e=>[e,i[e]]));this.changeConfig({...this.config,general:{...t,...r}})}}>
          <ha-svg-icon slot="start" .path=${"M13,3A9,9 0 0,0 4,12H1L4.89,15.89L4.96,16.03L9,12H6A7,7 0 0,1 13,5A7,7 0 0,1 20,12A7,7 0 0,1 13,19C11.07,19 9.32,18.21 8.06,16.94L6.64,18.36C8.27,20 10.5,21 13,21A9,9 0 0,0 22,12A9,9 0 0,0 13,3Z"}></ha-svg-icon>
          ${this.localize("config.restore_defaults")}
        </ha-button>
      `)}numberField(e){const t=this.range(e);return{name:e,required:!0,selector:{number:{min:t.min??void 0,max:t.max??void 0,step:t.resolution,mode:"box",unit_of_measurement:mi[e]}}}}selectField(e,t){const i=this.range(e),r=[];for(let e=i.min??i.resolution;e<=(i.max??e);e+=i.resolution)r.push({value:String(e),label:t(e)});return{name:e,required:!0,selector:{select:{mode:"dropdown",options:r}}}}range(e){return this.capabilities.limits.general[e]}get formData(){const e=this.config.general;return Object.fromEntries(Object.entries(e).map(([e,t])=>[e,vi.has(e)&&null!==t?String(t):t]))}valueChanged(e){const t=e.detail.value,i={...this.config.general};for(const e of Object.keys(i)){const r=t[e];i[e]=vi.has(e)&&void 0!==r?Number(r):r??null}this.changeConfig({...this.config,general:i})}static{this.styles=fi.styles}}const yi=["wait_curve_steepness","wait_curve_pivot","appliance_repeat_increment_factor","appliance_repeat_increments","charger_repeat_increment_factor","charger_repeat_increments","command_repeat_interval_min","action_timeout_s","power_sensor_timeout_s"],wi=60,bi=[.1,.2,.5,1,2,5,10];const $i={wait_curve_steepness:!1,wait_curve_pivot:!0};let ki=class extends _i{constructor(){super(...arguments),this.narrowQuery=new bt(this,760)}get narrowPage(){return this.narrowQuery.matches}render(){return X`
      ${this.renderWaitCurveCard()} ${this.renderRepeatedTurnOnCard()} ${this.renderCommandRepeatCard()}
      ${this.renderTimeoutsCard()} ${this.renderRestoreDefaults(yi)}
    `}renderWaitCurveCard(){return this.renderCard({title:this.localize("advanced.wait_curve"),description:this.localize("advanced.wait_curve_info"),content:X`
        <div class="sliders">${["wait_curve_steepness","wait_curve_pivot"].map(e=>this.renderSlider(e))}</div>
        ${this.renderWaitCurve()}
      `})}renderRepeatedTurnOnCard(){return this.renderCard({title:this.localize("advanced.repeated_turn_on"),description:this.localize("advanced.repeated_turn_on_info"),content:X`
        ${this.renderRepeatedTurnOnSection("advanced.appliances","appliance_repeat_increment_factor","appliance_repeat_increments")}
        ${this.renderRepeatedTurnOnSection("advanced.chargers","charger_repeat_increment_factor","charger_repeat_increments")}
      `})}renderCommandRepeatCard(){return this.renderCard({title:this.localize("advanced.command_repeat"),description:this.localize("advanced.command_repeat_info"),content:this.renderForm([this.numberField("command_repeat_interval_min")])})}renderTimeoutsCard(){return this.renderCard({title:this.localize("advanced.timeouts"),description:this.localize("advanced.timeouts_info"),content:this.renderForm([this.numberField("action_timeout_s"),this.numberField("power_sensor_timeout_s")])})}renderRepeatedTurnOnSection(e,t,i){const r=this.hass.language;return X`
      ${ht(this.localize(e))}
      ${this.renderForm([this.selectField(t,e=>`× ${new Intl.NumberFormat(r).format(e)}`),this.selectField(i,e=>String(e))])}
      ${this.narrowPage?te:this.renderRepeatedTurnOnTable(this.config.general[t],this.config.general[i])}
    `}renderRepeatedTurnOnTable(e,t){const i=this.config.general,r=i.wait_at_limit_s,a=this.decisionInterval,n=yt(i.wait_curve_steepness,i.wait_curve_pivot)(i.wait_curve_pivot/100),s=Array.from({length:t+2+1},(e,t)=>t+1),o=(i,s)=>{if(null===r||s&&null===a)return"–";const o=i<=2?r*n:function(e,t,i,r){return t+t*i*Math.min(r,e-2-1)}(i,r,e,t);return ft(s?wt(o,a):o)};return X`
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
    `}get decisionInterval(){const e=this.config.general.regulation_window_s;return null===e?null:e*this.config.general.regulation_interval}renderSlider(e){const t=this.range(e),i=this.config.general[e],r=$i[e]?100-i:i,a=this.localize(`general.fields.${e}.label`),n=$i[e]?" %":"";return X`
      <span class="slider-label">${a}</span>
      <ha-slider
        aria-label=${a}
        .min=${t.min}
        .max=${t.max}
        .step=${t.resolution}
        .value=${i}
        .withTooltip=${!1}
        ?disabled=${this.locked}
        @input=${t=>this.changeCurve(e,Number(t.target.value))}
      ></ha-slider>
      <span class="slider-value">${new Intl.NumberFormat(this.hass.language).format(r)}${n}</span>
    `}changeCurve(e,t){t!==this.config.general[e]&&this.changeConfig({...this.config,general:{...this.config.general,[e]:t}})}renderWaitCurve(){const e=this.config.general,t=yt(e.wait_curve_steepness,e.wait_curve_pivot),i=e=>t(1-e/100),r=this.hass.language,a=e.power_limit_w,n=e.wait_at_limit_s,s=this.decisionInterval,o=e=>null===n?null:n*i(e),l=(e,t)=>X`
      <tr>
        <th>${this.localize(e)}</th>
        ${[50,40,30,25,20,15,10,7,4,1].map(e=>X`<td>${t(e)}</td>`)}
      </tr>
    `;return X`
      ${this.narrowPage?te:X`<table class="curve-table">
            ${l("advanced.free_power_kw",e=>gt(r,null===a?null:a*e/100))}
            ${l("advanced.waiting_minutes",e=>ft(o(e)))}
            ${l("advanced.actual_waiting_minutes",e=>ft((e=>{const t=o(e);return null===t||null===s?null:wt(t,s)})(e)))}
          </table>`}
      ${this.renderCurveGraph(i,a)}
    `}renderCurveGraph(e,t){const i=this.hass.language,[r,a]=this.narrowPage?[320,200]:[900,260],[n,s,o,l]=[44,24,8,38],d=e=>n+(r-n-s)*(wi-e)/wi,c=e=>o+(a-o-l)*(100-e)/100,h=`M${Array.from({length:201},(t,i)=>{const r=wi-i*wi/200;return`${d(r)},${c(100*e(r))}`}).join("L")}`,p=null===t?0:t/1e3,u=p*wi/100,g=(f=u,m=this.narrowPage?4:10,bi.find(e=>f/e<=m)??bi[bi.length-1]);var f,m;const v=u>0?Array.from({length:Math.floor(u/g+1e-9)+1},(e,t)=>t*g):[],_=g<1?1:0;return X`
      <svg class="curve" viewBox="0 0 ${r} ${a}" role="img" aria-label=${this.localize("advanced.wait_curve")}>
        ${[0,20,40,60,80,100].map(e=>Y`
            <line class="grid" x1=${n} x2=${r-s} y1=${c(e)} y2=${c(e)}></line>
            <text x=${n-6} y=${c(e)+4} text-anchor="end">${ut(i,e,0)} %</text>
          `)}
        ${v.map(e=>Y`<text x=${d(100*e/p)} y=${a-l+18} text-anchor="middle">${ut(i,e,_)}</text>`)}
        <text x=${d(30)} y=${a-4} text-anchor="middle">${this.localize("advanced.free_power_kw")}</text>
        <path class="area" d="${h}L${d(0)},${c(0)}L${d(wi)},${c(0)}Z"></path>
        <path class="line" d=${h}></path>
      </svg>
    `}static{this.styles=[_i.styles,g`
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
    `]}};ki=e([ye("kraftvakt-advanced-page")],ki);const xi=["binary_sensor","input_boolean","switch","schedule"];function Ai(e,t,i){return t[i]??e.states[i]?.attributes.friendly_name??i}function Ci(e,t,i){const r=i.device_id?e.devices?.[i.device_id]:void 0,a=r?.name_by_user??r?.name;return a||(i.entity_id?Ai(e,t,i.entity_id):null)}function Ei(e,t){return t&&e.states[t]?t:null}function zi(e){return Object.values(e.entities??{}).filter(e=>"kraftvakt"===e.platform).map(e=>e.entity_id)}function Si(e,t){return Object.values(e.entities??{}).find(e=>"kraftvakt"===e.platform&&e.translation_key===t)?.entity_id??null}function Vi(e,t){const i=e.states[t],r=Number(i?.state);if(!i||""===i.state.trim()||!Number.isFinite(r))return null;const a=i.attributes.unit_of_measurement,n="kW"===a?1e3:a&&"W"!==a?null:1;return null===n?null:Math.max(0,r)*n}const Mi=new Set(["unknown","unavailable",""]);const Hi={condition:["entity","template"],actively_charging:["entity","template"],charging_power:["power_sensor","template"],fault:["entity","template"],display_power:["power_sensor","template"],display_temperature:["temperature_sensor","template"]},Ti=["current_temperature","target_temperature"];let Li=class extends ve{constructor(){super(...arguments),this.value=null,this.entityId=null,this.kind="condition",this.disabled=!1,this.optional=!1,this.history={entityId:"",states:[]},this.computeLabel=e=>{switch(e.name){case"value":return this.text(`${this.shownType()}_label`);case"states":return this.text("states_label");default:return this.optionalText("type_label")}},this.computeHelper=e=>{switch(e.name){case"value":return this.text(`${this.shownType()}_helper`);case"states":return this.text("states_helper");default:return""}}}disconnectedCallback(){super.disconnectedCallback(),this.stopPreview()}updated(e){(e.has("value")||e.has("entityId"))&&this.schedulePreview(),e.has("value")&&this.loadHistory()}render(){const e=this.shownType();return X`
      <ha-form
        .hass=${this.hass}
        .data=${{type:e,value:this.listsTemperatures(e)&&this.value?.value?Pi(this.value):this.value?.value??"",states_are_true:String(this.value?.states_are_true??!0),states:this.value?.states??[]}}
        .schema=${this.schema(e)}
        .disabled=${this.disabled}
        .computeLabel=${this.computeLabel}
        .computeHelper=${this.computeHelper}
        @value-changed=${this.valueChanged}
      ></ha-form>
      ${this.renderPreview()} ${this.error?X`<div class="error">${this.error}</div>`:te}
    `}shownType(){const e=this.value?.type??this.types()[0];return Ti.includes(e)?"temperature_sensor":e}listsTemperatures(e){return"temperature_sensor"===e&&void 0!==this.includeEntities}types(){const e=Hi[this.kind];return this.stateChoices?e.flatMap(e=>"entity"===e?[e,"state"]:[e]):e}schema(e){return[{name:"type",selector:{select:{mode:"list",options:this.types().map(e=>({value:e,label:this.text(e)}))}}},...this.valueField(e)]}valueField(e){switch(e){case"entity":return[{name:"value",required:!this.optional,selector:{entity:{filter:{domain:xi},include_entities:this.includeEntities}}}];case"power_sensor":return[{name:"value",required:!this.optional,selector:{entity:{filter:{domain:"sensor",device_class:"power"},include_entities:this.includeEntities,exclude_entities:zi(this.hass)}}}];case"temperature_sensor":case"current_temperature":case"target_temperature":return this.listsTemperatures(e)?[{name:"value",required:!this.optional,selector:{select:{mode:"dropdown",options:this.temperatureOptions()}}}]:[{name:"value",required:!this.optional,selector:{entity:{filter:{domain:"sensor",device_class:"temperature"},include_entities:this.includeEntities}}}];case"state":return[{name:"value",required:!this.optional,selector:{entity:{include_entities:this.includeEntities}}},...this.value?.value&&this.stateChoices?[{name:"states_are_true",selector:{select:{mode:"list",options:[{value:"true",label:this.stateChoices.true},{value:"false",label:this.stateChoices.false}]}}},{name:"states",required:!this.optional,selector:{select:{multiple:!0,custom_value:!0,options:this.stateOptions()}}}]:[]];case"template":return[{name:"value",required:!this.optional,selector:{template:{}}}]}}temperatureOptions(){const e=(t=this.hass,(this.includeEntities??[]).flatMap(e=>e.startsWith("climate.")?[{type:"current_temperature",entityId:e},{type:"target_temperature",entityId:e}]:e.startsWith("sensor.")&&"temperature"===t.states[e]?.attributes.device_class?[{type:"temperature_sensor",entityId:e}]:[]));var t;const i=this.value?.value?{type:this.value.type,entityId:this.value.value}:void 0;return i&&!e.some(e=>Pi(e)===Pi(i))&&e.push(i),e.map(e=>({value:Pi(e),label:this.temperatureLabel(e)}))}temperatureLabel(e){const t=this.hass.states[e.entityId]?.attributes.friendly_name??e.entityId;return"temperature_sensor"===e.type?t:this.text(e.type,{name:t})}stateOptions(){const e=this.value?.value??"",t=this.hass.states[e],i=this.history.entityId===e?this.history.states:[];return function(e,t,i){const r=e?.attributes.options,a=[...Array.isArray(r)?r.map(String):[],e?.state??"",...t,...i];return[...new Set(a.filter(e=>!Mi.has(e)))]}(t,i,this.value?.states??[]).map(e=>{const i=t?this.hass.formatEntityState(t,e):e;return{value:e,label:i===e?e:`${i} (${e})`}})}loadHistory(){const e="state"===this.value?.type?this.value.value:"";e&&this.history.entityId!==e&&(this.history={entityId:e,states:[]},async function(e,t){const i=new Date(Date.now()-6048e5),r=await e.callWS({type:"history/history_during_period",start_time:i.toISOString(),entity_ids:[t],minimal_response:!0,no_attributes:!0,significant_changes_only:!1});return[...new Set((r[t]??[]).map(e=>e.s))]}(this.hass,e).then(t=>{this.history.entityId===e&&(this.history={entityId:e,states:t})}).catch(()=>{}))}renderPreview(){if(!this.value?.value)return te;if("template"===this.value.type&&void 0!==this.preview?.error)return X`<div class="preview error">${this.localize("condition.error",{message:this.preview.error})}</div>`;if("template"===this.value.type&&!this.preview)return te;if("display_power"===this.kind||"display_temperature"===this.kind)return this.renderDisplayValue(this.value);const e=this.evidence(this.value);return X`
      ${this.renderNow(this.value,e)}
      ${"template"===this.value.type&&null===e?X`<div class="warning">${this.text("invalid",{value:JSON.stringify(this.preview?.result)})}</div>`:te}
    `}evidence(e){switch(e.type){case"template":if("charging_power"===this.kind){const e=Di(this.preview?.result);return null===e?null:e>100}return"boolean"==typeof this.preview?.result?this.preview.result:null;case"power_sensor":{const t=Vi(this.hass,e.value);return null===t?null:t>100}case"state":return t=this.hass.states[e.value]?.state,i=e.states??[],r=e.states_are_true??!0,void 0===t||Mi.has(t)?null:i.includes(t)===r;default:{const t=this.hass.states[e.value]?.state;return"on"===t||"off"!==t&&null}}var t,i,r}renderNow(e,t){const i=this.text(!0===t?"true":"false"),r="template"===e.type?void 0:this.hass.states[e.value],a="entity"===e.type&&("on"===r?.state||"off"===r?.state),n="template"===e.type&&"charging_power"===this.kind?Di(this.preview?.result):null;return X`
      <div class="preview">
        ${this.localize("condition.now",{value:""})}${r?X`<b>${this.hass.formatEntityState(r)}</b>${a?te:X` · ${i}`}`:null!==n?X`<b>${new Intl.NumberFormat(this.hass.language).format(n)} W</b> · ${i}`:X`<b>${i}</b>`}
      </div>
    `}renderDisplayValue(e){const t=Ti.includes(e.type),i="template"===e.type||t?void 0:this.hass.states[e.value],r="template"===e.type?Ii(this.preview?.result):t?function(e,t){const i="current_temperature"===t.type?"current_temperature":"temperature",r=e.states[t.entityId]?.attributes[i];return"number"==typeof r&&Number.isFinite(r)?r:null}(this.hass,{type:e.type,entityId:e.value}):null;if("template"===e.type&&null===r)return X`<div class="warning">${this.text("invalid",{value:JSON.stringify(this.preview?.result)})}</div>`;const a="display_power"===this.kind?"W":this.hass.config.unit_system.temperature,n=null!==r?`${new Intl.NumberFormat(this.hass.language).format("display_power"===this.kind?Math.max(r,0):r)} ${a}`:i?this.hass.formatEntityState(i):this.text("no_value");return X`<div class="preview">${this.localize("condition.now",{value:""})}<b>${n}</b></div>`}text(e,t){return this.localize(`${this.kind}.${e}`,t)}optionalText(e){const t=this.text(e);return t===`${this.kind}.${e}`?"":t}valueChanged(e){e.stopPropagation();const{type:t,value:i,states:r,states_are_true:a}=e.detail.value,n=t===this.shownType(),s=n&&this.listsTemperatures(t)&&i?function(e){const[t,i]=e.split("|");return{type:t,entityId:i}}(i):void 0,o=s?{type:s.type,value:s.entityId}:{type:t,value:n?i??"":""};if("state"===t){const e=n&&o.value===this.value?.value;o.states=e?r??[]:[],o.states_are_true=!e||"false"!==a}this.dispatchEvent(new CustomEvent("value-changed",{detail:{value:o}}))}schedulePreview(){if(this.stopPreview(),"template"!==this.value?.type||!this.value.value.trim())return void(this.preview=void 0);const e=this.value.value;this.previewTimer=window.setTimeout(()=>this.startPreview(e),500)}startPreview(e){const t=this.entityId?this.hass.states[this.entityId]??null:null;this.unsubscribePreview=this.hass.connection.subscribeMessage(e=>this.preview=e,{type:"render_template",template:e,variables:{entity_id:this.entityId,entity:t},report_errors:!0}),this.unsubscribePreview.catch(e=>{this.preview={error:String(e instanceof Object&&"message"in e?e.message:e)}})}stopPreview(){window.clearTimeout(this.previewTimer),this.unsubscribePreview?.then(e=>e()).catch(()=>{}),this.unsubscribePreview=void 0}static{this.styles=g`
    :host {
      display: block;
    }
    /* Indented as Home Assistant indents the helper text of a field. */
    .preview,
    .error,
    .warning {
      padding-inline-start: 16px;
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
  `}};function Pi(e){return"entityId"in e?`${e.type}|${e.entityId}`:`${e.type}|${e.value}`}function Di(e){const t=Ii(e);return null===t?null:Math.max(t,0)}function Ii(e){const t="string"==typeof e&&""!==e.trim()?Number(e):e;return"number"==typeof t&&Number.isFinite(t)?t:null}e([$e({attribute:!1})],Li.prototype,"hass",void 0),e([$e({attribute:!1})],Li.prototype,"localize",void 0),e([$e({attribute:!1})],Li.prototype,"value",void 0),e([$e({attribute:!1})],Li.prototype,"entityId",void 0),e([$e({attribute:!1})],Li.prototype,"includeEntities",void 0),e([$e()],Li.prototype,"kind",void 0),e([$e()],Li.prototype,"error",void 0),e([$e({type:Boolean})],Li.prototype,"disabled",void 0),e([$e({type:Boolean})],Li.prototype,"optional",void 0),e([$e({attribute:!1})],Li.prototype,"stateChoices",void 0),e([ke()],Li.prototype,"history",void 0),e([ke()],Li.prototype,"preview",void 0),Li=e([ye("kraftvakt-condition-field")],Li);let Fi=class extends ve{constructor(){super(...arguments),this.label="",this.value=null,this.entityId=null,this.defaultAvailable=!1,this.entityDomains=[],this.domainActions={},this.parameterErrors={},this.variables=[],this.disabled=!1}render(){const e=this.value?.mode,t=this.domainAction;return X`
      <div class="field ${this.error?"invalid":""}">
        ${this.label?X`<div class="label">${this.label}</div>`:te}
        <ha-form
          .hass=${this.hass}
          .data=${{mode:"domain"===e?this.value?.domain_action:e,action:this.value?.action??[],entity_id:this.value?.entity_id??void 0}}
          .schema=${this.schema(e)}
          .disabled=${this.disabled}
          .computeLabel=${()=>""}
          @value-changed=${this.valueChanged}
        ></ha-form>
        ${t?this.renderParameters(t):te}
        <div class="helper">${this.helperText(e)}</div>
        ${this.error?X`<div class="error">${this.error}</div>`:te}
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
    `}parameterField(e){const t=this.stateObj;if("option"===e.type){const i=function(e,t){const i=Gt(t,e.options_attribute);return Array.isArray(i)?i.map(String):e.preferred_options}(e,t).map(e=>({value:e,label:t?this.hass.formatEntityState(t,e):e}));return{name:e.name,required:!0,selector:{select:{mode:"dropdown",options:i}}}}const{min:i,max:r,step:a}=Ut(e,t),n=this.hass.config.unit_system.temperature;return{name:e.name,required:!0,selector:{number:{min:i,max:r,step:a??"any",mode:"box",unit_of_measurement:n}}}}parameterHelper(e,t){const i=e.parameters.find(e=>e.name===t),{min:r,max:a}=i?Ut(i,this.stateObj):{};if(void 0===r||void 0===a)return"";const n=e=>new Intl.NumberFormat(this.hass.language).format(e);return this.localize("action.parameter_range",{min:n(r),max:n(a),unit:this.hass.config.unit_system.temperature})}schema(e){return[{name:"mode",selector:{select:{mode:"list",options:[...this.defaultAvailable?[{value:"default",label:this.localize("action.default")}]:[],...Object.keys(this.domainActions).map(e=>({value:e,label:this.localize(`action.domain_actions.${e}`)})),...this.entityDomains.length?[{value:"entity",label:this.localize("action.entity")}]:[],{value:"custom",label:this.localize("action.custom")}]}}},..."entity"===e?[{name:"entity_id",selector:{entity:{filter:{domain:this.entityDomains},include_entities:this.includeEntities}}}]:[],..."custom"===e?[{name:"action",selector:{action:{}}}]:[]]}helperText(e){if("custom"===e)return this.localize("action.variables",{variables:this.variables.join(", ")});if("domain"===e){const e=this.domainAction;return e?this.localize("action.default_runs",{service:`${e.domain}.${e.service}`}):""}if("entity"===e){const e=this.value?.entity_id;return e?this.localize("action.entity_runs",{service:this.defaultService(e)}):this.localize("action.choose_action_entity")}return this.defaultAvailable&&this.entityId?this.localize("action.default_runs",{service:this.defaultService(this.entityId)}):this.localize(this.entityId?"action.no_default":"action.choose_entity")}valueChanged(e){e.stopPropagation();const{mode:t,action:i,entity_id:r}=e.detail.value,a=t?this.domainActions[t]:void 0,n=a?{mode:"domain",domain_action:t,data:Rt(a,this.stateObj,this.value?.data)}:"default"===t?{mode:t}:"entity"===t?{mode:t,entity_id:r||null}:"custom"===t?{mode:t,action:"custom"===this.value?.mode?Ni(i):this.defaultSteps()}:null;this.fireChanged(n)}parametersChanged(e){e.stopPropagation();const t=Object.fromEntries((this.domainAction?.parameters??[]).map(({name:t})=>[t,e.detail.value[t]??null]));this.fireChanged({...this.value,data:t})}fireChanged(e){this.dispatchEvent(new CustomEvent("value-changed",{detail:{value:e}}))}get domainAction(){return"domain"===this.value?.mode&&this.value.domain_action?this.domainActions[this.value.domain_action]:void 0}get stateObj(){return this.entityId?this.hass.states[this.entityId]:void 0}defaultSteps(){if(!this.defaultAvailable||!this.entityId)return[];const e=this.defaultAction?.data??{};return[{action:this.defaultService(this.entityId),target:{entity_id:this.entityId},...Object.keys(e).length?{data:e}:{}}]}defaultService(e){return`${e.split(".")[0]}.${this.defaultAction?.service}`}static{this.styles=g`
    .label {
      font-weight: var(--ha-font-weight-medium, 500);
    }
    .invalid .label {
      color: var(--error-color);
    }
    /* Indented as Home Assistant indents the helper text of a field. */
    .helper,
    .error {
      padding-inline-start: 16px;
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
  `}};function Ni(e){return Array.isArray(e)?e:e&&"object"==typeof e?[e]:[]}e([$e({attribute:!1})],Fi.prototype,"hass",void 0),e([$e({attribute:!1})],Fi.prototype,"localize",void 0),e([$e()],Fi.prototype,"label",void 0),e([$e({attribute:!1})],Fi.prototype,"value",void 0),e([$e({attribute:!1})],Fi.prototype,"entityId",void 0),e([$e({attribute:!1})],Fi.prototype,"defaultAction",void 0),e([$e({type:Boolean})],Fi.prototype,"defaultAvailable",void 0),e([$e({attribute:!1})],Fi.prototype,"entityDomains",void 0),e([$e({attribute:!1})],Fi.prototype,"includeEntities",void 0),e([$e({attribute:!1})],Fi.prototype,"domainActions",void 0),e([$e({attribute:!1})],Fi.prototype,"parameterErrors",void 0),e([$e({attribute:!1})],Fi.prototype,"variables",void 0),e([$e()],Fi.prototype,"error",void 0),e([$e({type:Boolean})],Fi.prototype,"disabled",void 0),Fi=e([ye("kraftvakt-action-field")],Fi);class Oi extends ve{constructor(){super(...arguments),this.isNew=!1,this.usedEntities=[],this.saveErrors=[],this.locked=!1,this.open=!0,this.describe=e=>Tt(e,this.localize,this.capabilities,this.hass.language)}willUpdate(e){e.has("item")&&(this.draft=structuredClone(this.item))}render(){const e=this.errors(),t=[...e,...this.isNew?[]:this.missing(),...this.saveErrors];return X`
      <ha-dialog .open=${this.open} .headerTitle=${this.heading} prevent-scrim-close @closed=${this.closed}>
        <div class="content">${this.renderFields(t)}</div>
        <div slot="footer">${this.renderButtons(e.length>0)}</div>
      </ha-dialog>
    `}get entityScope(){}renderEntity(e){const t=[{name:"entity_id",required:!0,selector:{entity:{include_entities:this.entityScope,exclude_entities:this.usedEntities}}}];return this.renderForm(t,e,e=>this.entityChanged(e.entity_id||null))}renderAction(e,t,i,r=!1,a){return this.renderActionField({name:e,field:e,value:this.draft[e],label:a},t,i,t=>this.changeDraft({[e]:t}),r)}renderActionGroup(e,t,i){return this.renderGroup({title:this.label(e),description:this.helper(e),content:this.renderAction(e,t,i,!1,"")})}renderActionField(e,t,i,r,a=!1){const{name:n,field:s}=e,o=t.find(e=>e.field===s),l=Lt(t,`${s}.`,this.describe),d=ri(this.capabilities,this.section,n);return X`
      <kraftvakt-action-field
        .hass=${this.hass}
        .localize=${this.localize}
        .label=${e.label??this.label(n)}
        .value=${e.value}
        .entityId=${this.draft.entity_id}
        .defaultAction=${d}
        .defaultAvailable=${ni(this.capabilities,this.section,n,this.draft.entity_id)}
        .entityDomains=${a?d.domains:[]}
        .includeEntities=${this.entityScope}
        .domainActions=${Wt(this.capabilities,this.section,n,this.draft.entity_id)}
        .variables=${i}
        .error=${o?this.describe(o):void 0}
        .parameterErrors=${l}
        .disabled=${this.locked}
        @value-changed=${e=>r(e.detail.value)}
      ></kraftvakt-action-field>
    `}actionForEntity(e,t,i){return function(e,t,i,r,a,n){if(null===r){const r=Object.entries(Wt(e,t,i,a)).find(([,e])=>e.suggested);if(r){const[e,t]=r;return{mode:"domain",domain_action:e,data:Rt(t,n)}}if(ni(e,t,i,a))return{mode:"default"}}return null===a||ai(e,t,i,a,r)?r:{mode:"custom",action:[]}}(this.capabilities,this.section,e,t,i,i?this.hass.states[i]:void 0)}renderForm(e,t,i,r=this.draft){const a=e.flatMap(e=>e.schema?.map(e=>e.name)??[e.name]);return X`
      <ha-form
        .hass=${this.hass}
        .data=${r}
        .schema=${e}
        .error=${Lt(t.filter(e=>void 0!==e.field&&a.includes(e.field)),"",this.describe)}
        .disabled=${this.locked}
        .computeLabel=${e=>this.label(e.name)}
        .computeHelper=${e=>this.helper(e.name)}
        @value-changed=${e=>{e.stopPropagation(),i(e.detail.value)}}
      ></ha-form>
    `}numberField(e,t,i){const r=this.capabilities.limits[this.section][e];return{name:e,required:i,selector:{number:{min:r.min??void 0,max:r.max??void 0,step:r.resolution,mode:"box",unit_of_measurement:t}}}}label(e){return this.localize(`${this.texts}.fields.${e}.label`)}helper(e){const t=`${this.texts}.fields.${e}.helper`;if(this.localize(t)===t)return"";const i=this.capabilities.limits[this.section][e],r=this.capabilities.defaults[this.section],a=e=>"number"==typeof e?new Intl.NumberFormat(this.hass.language).format(e):"";return this.localize(t,{min:a(i?.min),max:a(i?.max),default:a(r[e])})}renderGroup(e){const t=e.toggle,i=t?X`
          <ha-switch
            .checked=${t.checked}
            .disabled=${this.locked||!0===t.disabled}
            aria-label=${e.title}
            @change=${e=>t.changed(e.target.checked)}
          ></ha-switch>
        `:e.control??te;return X`
      <section class="group ${e.error?"invalid":""}">
        ${ht(e.title,i)} ${pt(e.description)} ${e.content??te}
        ${e.error?X`<div class="error">${e.error}</div>`:te}
      </section>
    `}changeDraft(e){this.draft={...this.draft,...e}}entityChanged(e){this.changeDraft({entity_id:e,...this.actionsForEntity(e)})}renderButtons(e){return this.locked?X`<ha-button @click=${this.close}>${this.localize("dialog.close")}</ha-button>`:X`
      ${this.isNew?te:X`<ha-button variant="danger" appearance="plain" @click=${this.delete}>${this.deleteText}</ha-button>`}
      <span class="spacer"></span>
      <ha-button appearance="plain" @click=${this.close}>${this.localize("dialog.cancel")}</ha-button>
      <ha-button .disabled=${e} @click=${this.confirm}>${this.localize("dialog.ok")}</ha-button>
    `}get deleteText(){return this.localize(`${this.texts}.delete`)}get heading(){return this.locked?this.localize(`${this.texts}.view_title`):this.localize(this.isNew?`${this.texts}.add_title`:`${this.texts}.edit_title`)}confirm(){this.dispatchEvent(new CustomEvent("item-changed",{detail:this.draft})),this.close()}delete(){this.dispatchEvent(new CustomEvent("item-deleted",{detail:this.draft.id})),this.close()}close(){this.open=!1}closed(e){e.stopPropagation(),this.dispatchEvent(new CustomEvent("closed"))}static{this.styles=[ct,g`
      .content {
        display: grid;
        gap: 16px;
      }
      .group {
        display: grid;
        gap: 12px;
        padding: 16px;
        border: 1px solid var(--divider-color);
        border-radius: var(--ha-card-border-radius, 12px);
      }
      .group.invalid {
        border-color: var(--error-color);
      }
      .error {
        font-size: var(--ha-font-size-s, 12px);
        color: var(--error-color);
      }
      .spacer {
        flex: 1;
      }
      div[slot="footer"] {
        display: flex;
        align-items: center;
      }
    `]}}e([$e({attribute:!1})],Oi.prototype,"hass",void 0),e([$e({attribute:!1})],Oi.prototype,"localize",void 0),e([$e({attribute:!1})],Oi.prototype,"capabilities",void 0),e([$e({attribute:!1})],Oi.prototype,"item",void 0),e([$e({type:Boolean})],Oi.prototype,"isNew",void 0),e([$e({attribute:!1})],Oi.prototype,"usedEntities",void 0),e([$e({attribute:!1})],Oi.prototype,"saveErrors",void 0),e([$e({type:Boolean})],Oi.prototype,"locked",void 0),e([ke()],Oi.prototype,"open",void 0),e([ke()],Oi.prototype,"draft",void 0);const Wi=["entity_id","entity"];let ji=class extends Oi{constructor(){super(...arguments),this.section="appliances",this.texts="appliance",this.fixedLoad=!1,this.essentialChanged=e=>{e&&this.fixedLoadChanged(!1),this.changeDraft({essential:e})},this.fixedLoadChanged=e=>{this.fixedLoad=e,e||this.changeDraft({power_reserve_w:null})}}willUpdate(e){super.willUpdate(e),e.has("item")&&(this.fixedLoad=null!==this.item.power_reserve_w)}actionsForEntity(e){return{...Ft(this.draft,e,this.hass),turn_on:this.actionForEntity("turn_on",this.draft.turn_on,e),turn_off:this.actionForEntity("turn_off",this.draft.turn_off,e),variants:this.draft.variants.map(t=>({...t,actions:Object.fromEntries(Object.entries(t.actions).map(([t,i])=>[t,this.actionForEntity(t,i??null,e)]))}))}}errors(){return oi(this.draft,this.capabilities,this.hass)}missing(){return ti(this.draft)}renderFields(e){const t=this.draft.essential;return X`
      ${this.renderEntity(e)} ${this.renderActions(e)} ${this.renderEssential(e)}
      ${t?te:this.renderFixedLoad(e)} ${t?te:this.renderVariants()}
      ${this.renderDisplayValues(e)}
    `}renderEssential(e){const t=e.find(e=>"essential"===e.field);return this.renderGroup({title:this.label("essential"),description:this.helper("essential"),toggle:{checked:this.draft.essential,disabled:!this.draft.essential&&this.draft.variants.length>0,changed:this.essentialChanged},error:t?this.describe(t):void 0})}renderFixedLoad(e){const t=this.fixedLoad||e.some(e=>"power_reserve_w"===e.field);return this.renderGroup({title:this.label("fixed_load"),description:this.helper("fixed_load"),toggle:{checked:this.fixedLoad,changed:this.fixedLoadChanged},content:t?this.renderForm([this.numberField("power_reserve_w","W",!1)],e,e=>this.changeDraft({power_reserve_w:e.power_reserve_w??null})):te})}renderDisplayValues(e){return this.renderGroup({title:this.localize("appliance.display_values"),description:this.localize("appliance.display_values_info"),content:X`
        ${this.renderDisplayValue("display_power",e)} ${this.renderDisplayValue("display_temperature",e)}
      `})}renderDisplayValue(e,t){const i=t.find(t=>t.field===e);return X`
      <kraftvakt-condition-field
        .hass=${this.hass}
        .localize=${this.localize}
        .value=${this.draft[e]}
        .entityId=${this.draft.entity_id}
        .includeEntities=${function(e,t){const i=Dt(e,t.entity_id);return i?Pt(e,i):void 0}(this.hass,this.draft)}
        .kind=${e}
        optional
        .error=${i?this.describe(i):void 0}
        .disabled=${this.locked}
        @value-changed=${t=>this.changeDraft({[e]:t.detail.value})}
      ></kraftvakt-condition-field>
    `}renderActions(e){return Kt.map(t=>this.renderActionGroup(t,e,Wi))}renderVariants(){if(this.locked&&0===this.draft.variants.length)return te;const e=[...this.errors(),...this.saveErrors],t=this.locked||0===this.errors().length;return this.renderGroup({title:this.localize("appliance.variants"),description:this.localize("appliance.variants_info"),control:this.locked?te:X`
            <ha-button @click=${this.addVariant}>
              <ha-svg-icon slot="start" .path=${o}></ha-svg-icon>
              ${this.localize("appliance.add_variant")}
            </ha-button>
          `,content:0===this.draft.variants.length?te:X`
              <ha-sortable handle-selector=".handle" .disabled=${this.locked} @item-moved=${this.variantMoved}>
                <div class="variants">
                  ${kt(this.draft.variants,e=>e.id,i=>this.renderVariant(i,e,t))}
                </div>
              </ha-sortable>
            `})}renderVariant(e,t,r){const n=`variants.${e.id}.`,o=t.filter(e=>e.field?.startsWith(n)).map(e=>({...e,field:e.field?.slice(n.length)})),l=o.filter(e=>"label"!==e.field);return X`
      <div class="variant">
        <div class="variant-row">
          ${this.locked?te:X`<ha-svg-icon class="handle" .path=${i}></ha-svg-icon>`}
          <div class="label">
            ${this.renderForm(Ri,o,t=>this.changeVariant(e.id,{label:t.label??""}),e)}
          </div>
          <ha-icon-button
            .path=${this.locked?a:s}
            .label=${this.localize(this.locked?"list.view":"list.edit")}
            .disabled=${!r}
            @click=${()=>this.openVariant(e.id)}
          ></ha-icon-button>
        </div>
        ${l.map(e=>X`<div class="error">${this.label(e.field??"")}: ${this.describe(e)}</div>`)}
      </div>
    `}openVariant(e){this.locked||this.dispatchEvent(new CustomEvent("item-changed",{detail:this.draft})),this.dispatchEvent(new CustomEvent("variant-opened",{detail:e})),this.close()}addVariant(){const e={id:Xe(),label:"",condition:{type:"template",value:""},actions:{}};this.changeDraft({variants:[...this.draft.variants,e]})}changeVariant(e,t){this.changeDraft({variants:this.draft.variants.map(i=>i.id===e?{...i,...t}:i)})}variantMoved(e){e.stopPropagation(),this.changeDraft({variants:Ye(this.draft.variants,e.detail.oldIndex,e.detail.newIndex)})}static{this.styles=[Oi.styles,g`
      .variants {
        display: grid;
        gap: 8px;
      }
      .variant-row {
        display: flex;
        align-items: center;
        gap: 4px;
      }
      .label {
        flex: 1;
        min-width: 0;
      }
      .handle {
        cursor: grab;
        color: var(--secondary-text-color);
      }
      .variant .error {
        margin-top: 4px;
      }
    `]}};e([ke()],ji.prototype,"fixedLoad",void 0),ji=e([ye("kraftvakt-appliance-dialog")],ji);const Ri=[{name:"label",required:!0,selector:{text:{}}}];let Ui=class extends ve{constructor(){super(...arguments),this.kind="appliances",this.narrow=!1}render(){return X`
      <ha-alert alert-type="warning" .title=${this.localize(`warning.${this.kind}_title`)} .narrow=${this.narrow}>
        ${this.localize("warning.text")}
      </ha-alert>
    `}static{this.styles=g`
    :host {
      display: block;
    }
  `}};e([$e({attribute:!1})],Ui.prototype,"localize",void 0),e([$e()],Ui.prototype,"kind",void 0),e([$e({type:Boolean})],Ui.prototype,"narrow",void 0),Ui=e([ye("kraftvakt-manual-control-warning")],Ui);let Bi=class extends Oi{constructor(){super(...arguments),this.variantId="",this.applianceName="",this.section="appliances",this.texts="appliance",this.setAsideActions=new Map}actionsForEntity(){return{}}errors(){return this.ofVariant(oi(this.draft,this.capabilities,this.hass))}missing(){return this.ofVariant(ti(this.draft))}get deleteText(){return this.localize("variant.delete")}delete(){const e=this.draft.variants.filter(e=>e.id!==this.variantId);this.dispatchEvent(new CustomEvent("item-changed",{detail:{...this.draft,variants:e}})),this.close()}get heading(){const e=`${this.applianceName} «${this.variant?.label??""}»`;return this.localize(this.locked?"variant.view_title":"variant.edit_title",{name:e})}renderFields(e){const t=this.variant;if(!t)return X``;const i=e.find(e=>e.field===`${this.fieldPrefix}condition`);return X`
      ${this.renderGroup({title:this.localize("variant.condition"),description:this.localize("variant.condition_info"),content:X`
          <kraftvakt-condition-field
            .hass=${this.hass}
            .localize=${this.localize}
            .value=${t.condition}
            .entityId=${this.draft.entity_id}
            .error=${i?this.describe(i):void 0}
            .disabled=${this.locked}
            @value-changed=${e=>this.changeCondition(e.detail.value)}
          ></kraftvakt-condition-field>
        `})}
      ${Kt.map(t=>this.renderOverride(t,e))}
    `}renderOverride(e,t){const i=this.variant?.actions??{},r=Qt(i,e);return this.renderGroup({title:this.label(`override_${e}`),description:this.helper(`override_${e}`),toggle:{checked:r,changed:t=>this.override(e,t)},content:r?this.renderActionField({name:e,field:`${this.fieldPrefix}${e}`,value:i?.[e]??null,label:""},t,Wi,t=>this.changeVariant({actions:{...i,[e]:t}})):te})}get variant(){return this.draft.variants.find(e=>e.id===this.variantId)}get fieldPrefix(){return`variants.${this.variantId}.`}ofVariant(e){return e.filter(e=>e.field?.startsWith(this.fieldPrefix))}changeCondition(e){this.changeVariant({condition:e})}override(e,t){const{[e]:i,...r}=this.variant?.actions??{};if(t){const t=this.setAsideActions.has(e)?this.setAsideActions.get(e):structuredClone(this.draft[e]);this.changeVariant({actions:{...r,[e]:t??null}})}else this.setAsideActions.set(e,i??null),this.changeVariant({actions:r})}changeVariant(e){this.changeDraft({variants:this.draft.variants.map(t=>t.id===this.variantId?{...t,...e}:t)})}};e([$e()],Bi.prototype,"variantId",void 0),e([$e()],Bi.prototype,"applianceName",void 0),Bi=e([ye("kraftvakt-variant-dialog")],Bi);const qi=["entity_id","essential","turn_on","turn_off","power_reserve_w","label","condition","display_power","display_temperature"];let Gi=class extends fi{render(){return X`
      ${this.renderPriorityCard()}
      ${0===this.config.appliances.length?X`
            <kraftvakt-manual-control-warning
              .localize=${this.localize}
              .narrow=${this.narrow}
              kind="appliances"
            ></kraftvakt-manual-control-warning>
          `:te}
      ${this.editing?this.renderDialog(this.editing.appliance,this.editing.isNew):""}
      ${this.editingVariant?this.renderVariantDialog(this.editingVariant.appliance,this.editingVariant.variantId):""}
    `}renderPriorityCard(){const e={add:this.localize("appliances.add"),empty:this.localize("appliances.empty"),rows:this.config.priority.map(e=>this.row(e)),locked:this.locked,onAdd:this.addAppliance,onMoved:this.entryMoved,onOpen:this.openRow};return this.renderCard({title:this.localize("appliances.priority_title"),control:this.renderAddButton(e),description:this.localize("appliances.priority_sub"),list:this.renderItemList(e)})}renderVariantDialog(e,t){return X`
      <kraftvakt-variant-dialog
        .hass=${this.hass}
        .localize=${this.localize}
        .capabilities=${this.capabilities}
        .item=${e}
        .variantId=${t}
        .applianceName=${this.applianceName(e)}
        .saveErrors=${this.applianceSaveErrors(e)}
        .locked=${this.locked}
        @item-changed=${this.applianceChanged}
        @closed=${()=>this.editingVariant=void 0}
      ></kraftvakt-variant-dialog>
    `}renderDialog(e,t){return X`
      <kraftvakt-appliance-dialog
        .hass=${this.hass}
        .localize=${this.localize}
        .capabilities=${this.capabilities}
        .item=${e}
        .isNew=${t}
        .usedEntities=${this.entitiesUsedBesides(e.id)}
        .saveErrors=${this.applianceSaveErrors(e)}
        .locked=${this.locked}
        @item-changed=${this.applianceChanged}
        @item-deleted=${this.applianceDeleted}
        @variant-opened=${e=>this.variantToOpen=e.detail}
        @closed=${this.applianceDialogClosed}
      ></kraftvakt-appliance-dialog>
    `}applianceSaveErrors(e){return si(this.saveErrors,"appliances",e.id)}applianceDialogClosed(){const e=this.config.appliances.find(e=>e.id===this.editing?.appliance.id),t=this.variantToOpen;this.editing=void 0,this.variantToOpen=void 0,e&&t&&(this.editingVariant={appliance:e,variantId:t})}row(e){if("charger_group"===e.type){const t=this.config.charger_groups.find(t=>t.id===e.group_id);return{key:et(e),title:t?.name??"",iconPath:r,details:[X`${this.localize("appliances.charger_group_sub",{count:t?.chargers.length??0})}
            <a href="${ot}/charging" @click=${this.openChargingPage}>${this.localize("tabs.charging")}</a>`],errors:[],openable:!1}}const t=this.config.appliances.find(t=>t.id===e.appliance_id),i=t?.variants.find(t=>t.id===e.variant_id),a=si(this.issues,"appliances",e.appliance_id).filter(e=>i?e.field?.startsWith(`variants.${i.id}.`):!e.field?.startsWith("variants."));return{key:et(e),title:t?this.applianceName(t):"",tag:i?.label,details:t?i?this.variantDetails(i):this.applianceDetails(t):[],errors:a.map(e=>`${this.fieldLabel(e)}: ${this.describeIssue(e)}`),openable:!0,highlighted:t?.essential}}applianceName(e){return e.entity_id?Ai(this.hass,this.entityNames,e.entity_id):this.localize("missing.appliance_without_entity")}applianceDetails(e){const t=e.entity_id?[e.entity_id]:[];return e.essential&&t.push(this.localize("appliances.essential")),null!==e.power_reserve_w&&t.push(this.localize("appliances.power_reserve",{power:ut(this.hass.language,e.power_reserve_w,0)})),e.variants.length>0&&t.push(this.localize("appliances.variant_count",{count:e.variants.length})),t}variantDetails(e){const t="entity"===e.condition.type?this.localize("appliances.variant_entity",{entity:e.condition.value}):this.localize("appliances.variant_template"),i=Kt.filter(t=>Qt(e.actions,t));return i.length===Kt.length?[t,this.localize("appliances.variant_own_actions")]:[t,...i.map(e=>this.localize(`appliances.variant_own_${e}`))]}fieldLabel(e){const t=e.field?.split(".").at(-1)??"";return qi.includes(t)?this.localize(`appliance.fields.${t}.label`):t}entryMoved(e){const{oldIndex:t,newIndex:i}=e.detail;this.changeConfig({...this.config,priority:Ye(this.config.priority,t,i)})}addAppliance(){const e={id:Xe(),entity_id:null,turn_on:null,turn_off:null,essential:!1,power_reserve_w:this.capabilities.defaults.appliances.power_reserve_w,variants:[],display_power:null,display_temperature:null};this.editing={appliance:e,isNew:!0}}openRow(e){const t=this.config.priority.find(t=>et(t)===e.detail);if("appliance"!==t?.type)return;const i=this.config.appliances.find(e=>e.id===t.appliance_id);i&&t.variant_id?this.editingVariant={appliance:i,variantId:t.variant_id}:i&&(this.editing={appliance:i,isNew:!1})}applianceChanged(e){const t=e.detail,i=this.config.appliances.some(e=>e.id===t.id)?this.config.appliances.map(e=>e.id===t.id?t:e):[...this.config.appliances,t];this.changeConfig({...this.config,appliances:i})}applianceDeleted(e){this.changeConfig({...this.config,appliances:this.config.appliances.filter(t=>t.id!==e.detail)})}openChargingPage(e){e.preventDefault(),lt("charging")}static{this.styles=fi.styles}};e([ke()],Gi.prototype,"editing",void 0),e([ke()],Gi.prototype,"editingVariant",void 0),Gi=e([ye("kraftvakt-appliances-page")],Gi);const Zi=["entity_id","entity"];let Ki=class extends Oi{constructor(){super(...arguments),this.section="chargers",this.texts="charger",this.profile=null}actionsForEntity(e){return{activate:this.actionForEntity("activate",this.draft.activate,e),deactivate:this.actionForEntity("deactivate",this.draft.deactivate,e),set_current:this.actionForEntity("set_current",this.draft.set_current,e)}}errors(){return li(this.draft,this.capabilities,this.hass)}get entityScope(){return Pt(this.hass,this.draft.device_id)}missing(){return ii(this.draft)}renderFields(e){return X`
      ${this.renderDevice(e)} ${this.renderEntity(e)}
      ${this.renderForm([this.numberField("min_current_power_w","W",!0)],e,e=>this.changeDraft({min_current_power_w:e.min_current_power_w}))}
      ${this.renderSwitchedBy(e)}
      ${this.draft.switched_by_current?te:X`${this.renderActionGroup("activate",e,Zi)} ${this.renderActionGroup("deactivate",e,Zi)}`}
      ${this.renderChargingCurrent(e)}
      ${this.renderCarConnected(e)} ${this.renderActivelyCharging(e)}
      ${this.renderCloudControl(e)} ${this.renderChargingWindow(e)} ${this.renderDeactivateOnFault(e)}
    `}renderSwitchedBy(e){const t=["actions","current"].map(e=>({value:e,label:this.localize(`charger.switched_by.${e}`)}));return this.renderForm([{name:"switched_by_current",required:!0,selector:{select:{mode:"list",options:t}}}],e,e=>this.changeDraft({switched_by_current:"current"===e.switched_by_current}),{switched_by_current:this.draft.switched_by_current?"current":"actions"})}renderChargingCurrent(e){const t=[{type:"grid",name:"",schema:[this.numberField("min_current_a","A",!0),this.numberField("max_current_a","A",!0)]}];return this.renderGroup({title:this.localize("charger.charging_current"),description:this.localize("charger.charging_current_info"),content:X`
        ${this.renderForm(t,e,e=>this.changeDraft({min_current_a:e.min_current_a,max_current_a:e.max_current_a}))}
        ${this.renderAction("set_current",e,["current","min_current","max_current",...Zi],!0)}
      `})}renderDevice(e){return X`
      ${this.renderForm([{name:"device_id",required:!0,selector:{device:{}}}],e,e=>this.deviceChanged(e.device_id||null))}
      ${this.profile?X`<ha-alert alert-type="info">${this.localize("charger.profile_applied",{profile:this.profile})}</ha-alert>`:te}
    `}async deviceChanged(e){if(e===this.draft.device_id)return;const t=function(e,t,i){const r=new Set(Pt(i,t)),a=e=>e&&r.has(e)?e:null,n=e.set_current;return{device_id:t,entity_id:a(e.entity_id),set_current:"entity"!==n?.mode||a(n.entity_id)?n:{mode:"entity",entity_id:null},car_connected:Ot(e.car_connected,r),actively_charging:Ot(e.actively_charging,r),charging_power:Ot(e.charging_power,r),fault_flag:Ot(e.fault_flag,r)}}(this.draft,e,this.hass);if(this.changeDraft(t),this.entityChanged(t.entity_id??null),this.profile=null,!e)return;const{profile:i,fields:r}=await((e,t)=>e.callWS({type:"kraftvakt/charger_profile/get",device_id:t}))(this.hass,e).catch(()=>({profile:null,fields:{}}));i&&this.draft.device_id===e&&(this.changeDraft(r),this.profile=i)}renderCarConnected(e){return this.renderGroup({title:this.label("car_connected"),description:this.helper("car_connected"),content:this.renderCondition("car_connected","condition",e)})}renderActivelyCharging(e){return this.renderGroup({title:this.label("actively_charging"),description:this.helper("actively_charging"),content:X`
        ${this.renderCondition("charging_power","charging_power",e)}
        ${this.renderCondition("actively_charging","actively_charging",e,!0)}
      `})}stateChoices(e){return{true:this.localize(`charger.state_choices.${e}.true`),false:this.localize(`charger.state_choices.${e}.false`)}}renderCondition(e,t,i,r=!1){const a=i.find(t=>t.field===e);return X`
      <kraftvakt-condition-field
        .hass=${this.hass}
        .localize=${this.localize}
        .value=${this.draft[e]}
        .entityId=${this.draft.entity_id}
        .includeEntities=${this.entityScope}
        .kind=${t}
        .optional=${r}
        .stateChoices=${"charging_power"===e?void 0:this.stateChoices(e)}
        .error=${a?this.describe(a):void 0}
        .disabled=${this.locked}
        @value-changed=${t=>this.changeDraft({[e]:t.detail.value})}
      ></kraftvakt-condition-field>
    `}renderCloudControl(e){const t=this.draft.cloud_controlled||e.some(e=>"start_delay_s"===e.field);return this.renderGroup({title:this.label("cloud_controlled"),description:this.helper("cloud_controlled"),toggle:{checked:this.draft.cloud_controlled,changed:e=>this.changeDraft({cloud_controlled:e})},content:t?this.renderForm([this.numberField("start_delay_s","s",!0)],e,e=>this.changeDraft({start_delay_s:e.start_delay_s})):te})}renderDeactivateOnFault(e){const t=this.draft.deactivate_on_fault||e.some(e=>"fault_flag"===e.field);return this.renderGroup({title:this.label("deactivate_on_fault"),description:this.helper("deactivate_on_fault"),toggle:{checked:this.draft.deactivate_on_fault,changed:e=>this.changeDraft({deactivate_on_fault:e})},content:t?this.renderCondition("fault_flag","fault",e):te})}renderChargingWindow(e){const t=this.draft.charging_window,i=e.find(e=>"charging_window"===e.field);return this.renderGroup({title:this.label("charging_window"),description:this.helper("charging_window"),toggle:{checked:null!==t,changed:e=>this.changeDraft({charging_window:e?{start:"",end:""}:null})},content:t?this.renderWindowFields(e):te,error:i?this.describe(i):void 0})}renderWindowFields(e){const t=this.draft.charging_window,i=[{type:"grid",name:"",schema:[{name:"start",required:!0,selector:{time:{no_second:!0}}},{name:"end",required:!0,selector:{time:{no_second:!0}}}]},{name:"finish_after_window",selector:{boolean:{}}},{name:"override_ends",required:!0,selector:{select:{mode:"dropdown",options:Ue.map(e=>({value:e,label:this.localize(`charger.override_ends.${e}`)}))}}}],r={start:t?.start??"",end:t?.end??"",finish_after_window:this.draft.finish_after_window,override_ends:this.draft.override_ends};return this.renderForm(i,e,e=>this.changeDraft({charging_window:{start:Ji(e.start),end:Ji(e.end)},finish_after_window:!!e.finish_after_window,override_ends:e.override_ends??this.draft.override_ends}),r)}static{this.styles=Oi.styles}};function Ji(e){return"string"==typeof e?e.slice(0,5):""}e([ke()],Ki.prototype,"profile",void 0),Ki=e([ye("kraftvakt-charger-dialog")],Ki);const Qi=["device_id","entity_id","activate","deactivate","switched_by_current","set_current","min_current_a","max_current_a","min_current_power_w","car_connected","actively_charging","charging_power","cloud_controlled","start_delay_s","charging_window","finish_after_window","override_ends","deactivate_on_fault","fault_flag"],Xi=[{name:"name",required:!0,selector:{text:{}}},{name:"one_at_a_time",selector:{boolean:{}}},{name:"dynamic_order",selector:{boolean:{}}}];let Yi=class extends fi{render(){const e=this.config.charger_groups;return X`
      ${0===e.length?X`<div class="empty">${this.localize("charging.no_groups")}</div>`:e.map(e=>this.renderGroup(e))}
      ${this.renderPageFooter(e.length>0?this.localize("charging.switches_info"):"",X`
          <ha-button .disabled=${this.locked} @click=${this.addGroup}>
            <ha-svg-icon slot="start" .path=${o}></ha-svg-icon>
            ${this.localize("charging.add_group")}
          </ha-button>
        `)}
      ${0===it(this.config).length?X`
            <kraftvakt-manual-control-warning
              .localize=${this.localize}
              .narrow=${this.narrow}
              kind="chargers"
            ></kraftvakt-manual-control-warning>
          `:te}
      ${this.editing?this.renderDialog(this.editing.charger,this.editing.groupId,this.editing.isNew):te}
    `}renderGroup(e){const t=0===e.chargers.length,i={add:this.localize("charging.add"),empty:this.localize("charging.empty"),rows:e.chargers.map(e=>this.row(e)),locked:this.locked,group:"kraftvakt-chargers",onAdd:()=>this.addCharger(e),onMoved:t=>this.chargerMoved(e,t),onAdded:t=>this.chargerAdded(e,t),onOpen:t=>this.openRow(e,t)};return this.renderCard({title:e.name.trim()||this.localize("charging.unnamed_group"),content:X`
        <ha-form
          .hass=${this.hass}
          .data=${e}
          .schema=${Xi}
          .error=${this.formErrors("charger_groups",e.id)}
          .disabled=${this.locked}
          .computeLabel=${e=>this.localize(`charging.${e.name}`)}
          .computeHelper=${e=>this.localize(`charging.${e.name}_sub`).split("\n").map((e,t)=>0===t?e:X`<br />${e}`)}
          .computeError=${e=>e}
          @value-changed=${t=>this.groupChanged(e,t)}
        ></ha-form>
        ${ht(this.localize("charging.chargers"),this.renderAddButton(i))}
        ${pt(this.localize("charging.chargers_sub"))}
      `,list:this.renderItemList(i),footer:this.renderCardFooter(t?"":this.localize("charging.delete_group_not_empty"),X`
          <ha-button variant="danger" appearance="plain" .disabled=${this.locked||!t} @click=${()=>this.deleteGroup(e)}>
            <ha-svg-icon slot="start" .path=${"M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"}></ha-svg-icon>
            ${this.localize("charging.delete_group")}
          </ha-button>
        `)})}renderDialog(e,t,i){return X`
      <kraftvakt-charger-dialog
        .hass=${this.hass}
        .localize=${this.localize}
        .capabilities=${this.capabilities}
        .item=${e}
        .isNew=${i}
        .usedEntities=${this.entitiesUsedBesides(e.id)}
        .saveErrors=${si(this.saveErrors,"chargers",e.id)}
        .locked=${this.locked}
        @item-changed=${e=>this.chargerChanged(t,e.detail)}
        @item-deleted=${this.chargerDeleted}
        @closed=${()=>this.editing=void 0}
      ></kraftvakt-charger-dialog>
    `}row(e){const t=this.hass.language,i=[this.localize("charging.currents",{min:e.min_current_a,max:e.max_current_a}),this.localize("charging.min_current_power",{power:ut(t,e.min_current_power_w,0)}),e.charging_window?this.localize("charging.window",{...e.charging_window}):this.localize("charging.always_allowed")];e.charging_window&&e.finish_after_window&&i.push(this.localize("charging.finishes_after_window")),e.car_connected&&i.push("entity"===e.car_connected.type?this.localize("charging.car_from",{source:e.car_connected.value}):this.localize("charging.car_template")),e.actively_charging?.value&&i.push("template"===e.actively_charging.type?this.localize("charging.charging_template"):this.localize("charging.charging_from",{source:e.actively_charging.value})),e.charging_power?.value&&i.push("template"===e.charging_power.type?this.localize("charging.power_template"):this.localize("charging.power_from",{source:e.charging_power.value})),e.switched_by_current&&i.push(this.localize("charging.switched_by_current")),e.deactivate_on_fault&&i.push(this.localize("charging.deactivated_on_fault"));const a=si(this.issues,"chargers",e.id);return{key:e.id,title:Ci(this.hass,this.entityNames,e)??this.localize("missing.charger_without_entity"),iconPath:r,details:i,errors:a.map(e=>`${this.fieldLabel(e)}: ${this.describeIssue(e)}`),openable:!0}}fieldLabel(e){const t=e.field??"";return Qi.includes(t)?this.localize(`charger.fields.${t}.label`):t}groupChanged(e,t){const{name:i,one_at_a_time:r,dynamic_order:a}=t.detail.value;this.changeGroup({...e,name:i??"",one_at_a_time:r??e.one_at_a_time,dynamic_order:a??e.dynamic_order})}addGroup(){const e=this.config.charger_groups,t=this.localize("charging.new_group_name"),i=new Set(e.map(e=>e.name.trim()));let r=t;for(let e=2;i.has(r);e++)r=`${t} ${e}`;const a=this.capabilities.defaults.charger_groups,n={id:Xe(),name:r,...a,chargers:[]};this.changeConfig({...this.config,charger_groups:[...e,n]})}deleteGroup(e){this.changeConfig({...this.config,charger_groups:this.config.charger_groups.filter(t=>t.id!==e.id)})}chargerMoved(e,t){const{oldIndex:i,newIndex:r}=t.detail;this.changeGroup({...e,chargers:Ye(e.chargers,i,r)})}chargerAdded(e,t){const{key:i,index:r}=t.detail,a=it(this.config).find(e=>e.id===i);if(!a)return;const n=this.config.charger_groups.map(t=>{const n=t.chargers.filter(e=>e.id!==i);return t.id===e.id&&n.splice(r,0,a),{...t,chargers:n}});this.changeConfig({...this.config,charger_groups:n})}addCharger(e){const t=this.capabilities.defaults.chargers,i={id:Xe(),device_id:null,entity_id:null,activate:null,deactivate:null,switched_by_current:!1,set_current:null,min_current_a:t.min_current_a,max_current_a:t.max_current_a,min_current_power_w:t.min_current_power_w,car_connected:null,actively_charging:null,charging_power:null,charging_window:null,finish_after_window:!1,override_ends:t.override_ends,cloud_controlled:!1,start_delay_s:t.start_delay_s,deactivate_on_fault:!1,fault_flag:null};this.editing={charger:i,groupId:e.id,isNew:!0}}openRow(e,t){const i=e.chargers.find(e=>e.id===t.detail);i&&(this.editing={charger:i,groupId:e.id,isNew:!1})}chargerChanged(e,t){const i=this.config.charger_groups.find(t=>t.id===e);if(!i)return;const r=i.chargers.some(e=>e.id===t.id);this.changeGroup({...i,chargers:r?i.chargers.map(e=>e.id===t.id?t:e):[...i.chargers,t]})}chargerDeleted(e){const t=this.config.charger_groups.map(t=>({...t,chargers:t.chargers.filter(t=>t.id!==e.detail)}));this.changeConfig({...this.config,charger_groups:t})}changeGroup(e){const t=this.config.charger_groups.map(t=>t.id===e.id?e:t);this.changeConfig({...this.config,charger_groups:t})}static{this.styles=fi.styles}};e([ke()],Yi.prototype,"editing",void 0),Yi=e([ye("kraftvakt-charging-page")],Yi);const er=["regulation_window_s","turn_on_margin_w","regulation_interval","wait_at_limit_s","penalty_threshold_w"];let tr=class extends _i{render(){return X`
      ${this.renderSettingsCard("general.measurement",[this.entityField("power_sensor"),this.numberField("regulation_window_s")])}
      ${this.renderSettingsCard("general.regulation",[this.numberField("power_limit_w"),this.numberField("turn_on_margin_w"),this.intervalField(),this.numberField("wait_at_limit_s")])}
      ${this.renderSettingsCard("general.penalty",[this.numberField("penalty_threshold_w")],"general.penalty_info")}
      ${this.renderRestoreDefaults(er)}
    `}renderSettingsCard(e,t,i){return this.renderCard({title:this.localize(e),description:i&&this.localize(i),content:this.renderForm(t)})}entityField(e){return{name:e,required:!0,selector:{entity:{filter:{domain:"sensor",device_class:"power"},exclude_entities:zi(this.hass)}}}}intervalField(){return this.selectField("regulation_interval",e=>this.localize("general.interval_option",{count:e}))}};tr=e([ye("kraftvakt-general-page")],tr);const ir=2*Math.PI*7;class rr extends ve{constructor(){super(...arguments),this.start=0,this.end=0}connectedCallback(){super.connectedCallback(),this.hasUpdated&&this.startCountdown()}disconnectedCallback(){this.countdown?.cancel(),super.disconnectedCallback()}updated(e){(e.has("start")||e.has("end"))&&this.startCountdown()}startCountdown(){this.countdown?.cancel();const e=this.renderRoot.querySelector(".fill");if(!e)return;const t=Math.max(0,this.end-Date.now()),i=Math.min(1,t/Math.max(1,this.end-this.start));this.countdown=e.animate(this.keyframes(i),{duration:t,easing:"linear",fill:"forwards"})}}e([$e({type:Number})],rr.prototype,"start",void 0),e([$e({type:Number})],rr.prototype,"end",void 0);let ar=class extends rr{render(){return X`
      <svg viewBox="0 0 18 18" aria-hidden="true">
        ${Y`
          <circle class="track" cx="9" cy="9" r=${7}></circle>
          <circle class="fill" cx="9" cy="9" r=${7} stroke-dasharray=${ir} transform="rotate(-90 9 9)"></circle>
        `}
      </svg>
    `}keyframes(e){return[{strokeDashoffset:""+ir*(1-e)},{strokeDashoffset:`${ir}`}]}static{this.styles=g`
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
  `}};ar=e([ye("kraftvakt-countdown-ring")],ar);let nr=class extends rr{render(){return X`<div class="fill"></div>`}keyframes(e){return[{transform:`scaleX(${e})`},{transform:"scaleX(0)"}]}static{this.styles=g`
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
  `}};nr=e([ye("kraftvakt-countdown-bar")],nr);const sr=[1,2,5,10,20,50];let or=class extends ve{constructor(){super(...arguments),this.narrow=!1,this.powerNowW=null,this.powerSensor=null}render(){const e=this.status,t=this.hass.language;return X`
      <div class="stats">
        ${this.renderStat({swatch:"power-now",label:"status.power_now",value:gt(t,this.powerNowW),period:this.localize("status.momentary"),entityId:this.powerSensor})}
        ${this.renderStat({swatch:"regulation-average",label:"status.regulation_average",value:gt(t,e.regulation_average_w),period:this.localize("status.average_over_seconds",{seconds:e.regulation_window_s}),entityId:Si(this.hass,"power_regulation_average")})}
        ${this.renderStat({swatch:"tariff-average",label:"status.tariff_average",value:gt(t,e.tariff_average_w),period:this.localize("status.average_over_hour"),entityId:Si(this.hass,"power_tariff_average"),alarm:(i=e.tariff_average_w,null!==i&&i>e.power_limit_w)})}
        ${this.renderStat({swatch:"power-limit",label:"status.power_limit",value:gt(t,e.power_limit_w),entityId:Si(this.hass,"power_limit")})}
      </div>
      ${this.renderMeter()}
    `;var i}renderStat(e){const t=X`
      <div class="stat-label"><span class="swatch ${e.swatch}"></span>${this.localize(e.label)}</div>
      <div class="stat-value ${e.alarm?"alarm":""}">${e.value} <small>kW</small></div>
      ${e.period?X`<div class="stat-period">${e.period}</div>`:te}
    `,i=e.entityId;return i?X`<button class="stat" @click=${e=>dt(e,i)}>${t}</button>`:X`<div class="stat">${t}</div>`}renderMeter(){const e=this.status,t=e=>null===e?null:e/1e3,i=e.power_limit_w/1e3,r=t(this.powerNowW),a=t(e.tariff_average_w),n=t(e.regulation_average_w),s=[r,a,n],{step:o,end:l}=function(e){const t=sr.find(t=>e/t<=15)??sr[sr.length-1];return{step:t,end:Math.ceil(e/t)*t}}(Math.max(1.2*i,...s.map(e=>e??0))),d=e=>100*Math.min(e,l)/l+"%",c=this.hass.language,h=Array.from({length:l/o+1},(e,t)=>t*o),p=this.narrow?3:2,u=h.filter((e,t)=>t%p===0),g=(e,t,i)=>null===i?te:X`<span
            class="marker ${e}"
            style="left: ${d(i)}"
            title="${this.localize(t)} ${ut(c,i,2)} kW"
          ></span>`;return X`
      <div class="meter">
        <div class="markers">
          ${g("power-limit","status.power_limit",i)}
          ${g("tariff-average","status.tariff_average",a)}
          ${g("regulation-average","status.regulation_average",n)}
        </div>
        <div class="bar">
          ${null===r?te:X`<div class="fill power-now" style="width: ${d(r)}"></div>`}
        </div>
        <div class="ticks">${h.map(e=>X`<span style="left: ${d(e)}"></span>`)}</div>
        <div class="scale">
          ${u.map((e,t)=>X`<span class=${0===e?"start":e===l?"end":""} style="left: ${d(e)}"
                >${ut(c,e,0)}${t===u.length-1?" kW":""}</span
              >`)}
        </div>
      </div>
    `}static{this.styles=g`
    :host {
      display: grid;
      gap: 16px;
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
    button.stat {
      border: none;
      margin: 0;
      font: inherit;
      color: inherit;
      text-align: start;
      cursor: pointer;
    }
    button.stat:hover {
      background: color-mix(in srgb, var(--secondary-background-color), var(--primary-text-color) 6%);
    }
    button.stat:focus-visible {
      outline: 2px solid var(--primary-color);
      outline-offset: 2px;
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
    .tariff-average {
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
  `}};e([$e({attribute:!1})],or.prototype,"hass",void 0),e([$e({attribute:!1})],or.prototype,"localize",void 0),e([$e({type:Boolean,reflect:!0})],or.prototype,"narrow",void 0),e([$e({attribute:!1})],or.prototype,"status",void 0),e([$e({attribute:!1})],or.prototype,"powerNowW",void 0),e([$e({attribute:!1})],or.prototype,"powerSensor",void 0),or=e([ye("kraftvakt-power-overview")],or);const lr=g`
  .card-header {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    min-height: 40px;
    padding: 12px 16px;
    font-size: var(--ha-font-size-xl, 20px);
  }
`,dr=g`
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
  .chip ha-svg-icon {
    --mdc-icon-size: 16px;
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
`,cr={kind:"on"},hr={kind:"off"},pr={kind:"outline",icon:"M12 2C17.5 2 22 6.5 22 12S17.5 22 12 22 2 17.5 2 12 6.5 2 12 2M12 4C10.1 4 8.4 4.6 7.1 5.7L18.3 16.9C19.3 15.5 20 13.8 20 12C20 7.6 16.4 4 12 4M16.9 18.3L5.7 7.1C4.6 8.4 4 10.1 4 12C4 16.4 7.6 20 12 20C13.9 20 15.6 19.4 16.9 18.3Z"},ur={first_decision:[{kind:"off",icon:l},"status.chip_first_decision","status.first_decision"],fault:[{kind:"alarm",icon:"M11,15H13V17H11V15M11,7H13V13H11V7M12,2C6.47,2 2,6.5 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20Z"},"status.chip_fault","status.fault"],excluded:[pr,"status.chip_excluded","status.excluded"],outside_window:[{kind:"outline",icon:"M12,20A8,8 0 0,0 20,12A8,8 0 0,0 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22C6.47,22 2,17.5 2,12A10,10 0 0,1 12,2M12.5,7V12.25L17,14.92L16.25,16.15L11,13V7H12.5Z"},"status.chip_window","status.outside_window"],no_car:[{kind:"warning",icon:"M20.5,19.85L6.41,5.76L2.41,1.76L1.11,3L4.57,6.46L3,11V19A1,1 0 0,0 4,20H5A1,1 0 0,0 6,19V18H16.11L20.84,22.73L22.11,21.46L20.5,19.85M6.5,15A1.5,1.5 0 0,1 5,13.5A1.5,1.5 0 0,1 6.5,12A1.5,1.5 0 0,1 8,13.5A1.5,1.5 0 0,1 6.5,15M5,10L5.78,7.67L8.11,10H5M17.5,5.5L19,10H13.2L16.12,12.92C16.5,12.17 17.37,11.86 18.12,12.21C18.87,12.57 19.18,13.47 18.83,14.21C18.68,14.5 18.43,14.77 18.12,14.92L21,17.8V11L18.92,5C18.71,4.4 18.14,4 17.5,4H7.2L8.7,5.5H17.5Z"},"status.chip_no_car","status.bypassed_no_car"],queued:[{kind:"off",icon:l},"status.chip_queued","status.waiting_charger"],starting:[{kind:"info",icon:"M23 15.5C23 14.79 22.84 14.14 22.55 13.54C21.89 11.79 20.56 10.38 18.86 9.62C18.61 8.26 18 7.06 16.96 6.04C15.6 4.68 13.95 4 12 4C10.42 4 9 4.47 7.75 5.43S5.67 7.62 5.25 9.15C4 9.43 2.96 10.08 2.17 11.1S1 13.28 1 14.58C1 16.09 1.54 17.38 2.61 18.43C3.69 19.5 5 20 6.5 20H10.26C11.53 21.81 13.62 23 16 23C19.87 23 23 19.87 23 16C23 15.89 23 15.79 23 15.68C23 15.62 23 15.56 23 15.5M6.5 18C5.53 18 4.71 17.66 4.03 17C3.34 16.29 3 15.47 3 14.5S3.34 12.71 4.03 12.03C4.71 11.34 5.53 11 6.5 11H7C7 9.62 7.5 8.44 8.46 7.46C9.44 6.5 10.62 6 12 6S14.56 6.5 15.54 7.46C16 7.93 16.35 8.46 16.59 9.03C16.4 9 16.2 9 16 9C12.13 9 9 12.13 9 16C9 16.7 9.11 17.37 9.29 18H6.5M16 21C13.24 21 11 18.76 11 16S13.24 11 16 11 21 13.24 21 16 18.76 21 16 21M16.5 16.25L19.36 17.94L18.61 19.16L15 17V12H16.5V16.25Z"},"status.chip_starting","status.starting_until"],override:[{kind:"info",icon:"M15,4A8,8 0 0,1 23,12A8,8 0 0,1 15,20A8,8 0 0,1 7,12A8,8 0 0,1 15,4M15,6A6,6 0 0,0 9,12A6,6 0 0,0 15,18A6,6 0 0,0 21,12A6,6 0 0,0 15,6M14,8H15.5V11.78L17.83,14.11L16.77,15.17L14,12.4V8M2,18A1,1 0 0,1 1,17A1,1 0 0,1 2,16H5.83C6.14,16.71 6.54,17.38 7,18H2M3,13A1,1 0 0,1 2,12A1,1 0 0,1 3,11H5.05L5,12L5.05,13H3M4,8A1,1 0 0,1 3,7A1,1 0 0,1 4,6H7C6.54,6.62 6.14,7.29 5.83,8H4Z"},"status.chip_override","status.window_overridden"],finishing:[{kind:"info",icon:"M12,1C8.14,1 5,4.14 5,8A7,7 0 0,0 12,15C15.86,15 19,11.87 19,8C19,4.14 15.86,1 12,1M12,3.15C14.67,3.15 16.85,5.32 16.85,8C16.85,10.68 14.67,12.85 12,12.85A4.85,4.85 0 0,1 7.15,8A4.85,4.85 0 0,1 12,3.15M11,5V8.69L14.19,10.53L14.94,9.23L12.5,7.82V5M15,16V19H3V21H15V24L19,20M19,20V24H21V16H19"},"status.chip_finishing","status.finishing_at"],charging:[{kind:"on",icon:n},"status.chip_charging","status.charging_at"],activated:[cr,"status.activated","status.activated_not_charging"],deactivated:[hr,"status.deactivated","status.deactivated"]};function gr(e){return e.endsWith(":00")?e.slice(0,-3):e}let fr=class extends ve{constructor(){super(...arguments),this.narrow=!1,this.phoneQuery=new bt(this,600),this.hasPower=!1}get phone(){return this.phoneQuery.matches}render(){const e=function(e){return e.priority.map(e=>"appliance"===e.type?{kind:"appliance",appliance:e,on:e.on}:{kind:"charger_group",group:e,on:e.chargers.some(e=>e.activated&&!e.bypassed)})}(this.status),t=function(e){const t=e.map(e=>e.on).lastIndexOf(!0),i=e.slice(t+1).some(e=>"charger_group"===e.kind||!e.appliance.excluded);return t>=0&&i?t:-1}(e);return this.hasPower=function(e){return e.priority.flatMap(e=>"appliance"===e.type?[e]:e.chargers).some(e=>null!==e.power_w)}(this.status),X`
      <ha-card>
        <div class="card-header">
          <span>${this.localize("status.appliances_and_chargers")}</span>
        </div>
        ${0===e.length?X`<div class="empty">${this.localize("status.no_appliances")}</div>`:X`<div class="list ${this.phone?"phone":""}" style=${this.phone?"":this.columns()}>
              ${e.map((e,i)=>X`
                  ${"appliance"===e.kind?this.renderApplianceRow(e.appliance,i+1):this.renderChargerGroup(e.group,i+1)}
                  ${i===t?this.renderCutOff():te}
                `)}
            </div>`}
      </ha-card>
    `}columns(){return`grid-template-columns: ${["minmax(24px, max-content)","minmax(0, 1fr)","max-content",...this.hasPower?["max-content"]:[],"var(--waiting-width)","max-content"].join(" ")}`}renderRow(e,t,i){if(!t)return X`<div class="row ${e}">${i}</div>`;const r=e=>{e.preventDefault(),dt(e,t)};return X`
      <div
        class="row ${e} clickable"
        role="button"
        tabindex="0"
        @click=${r}
        @keydown=${e=>"Enter"===e.key||" "===e.key?r(e):void 0}
      >
        ${i}
      </div>
    `}renderApplianceRow(e,t){const i=null!==e.temperature&&!this.phone;return this.renderRow(`appliance ${e.on?"":"off"} ${e.excluded?"excluded":""} ${e.essential?"essential":""} ${i?"with-temperature":""}`,Ei(this.hass,this.applianceEntity(e)),X`
        ${this.renderRank(t)}
        <div class="row-title">
          ${this.renderApplianceIcon(e)}${this.renderName(e.name)}
          ${e.variant&&!this.phone?X`<span class="variant" title=${e.variant}>${e.variant}</span>`:te}
        </div>
        ${this.renderTemperature(e)} ${this.renderPower(e.power_w)}
        ${this.renderWaiting(e,"M12,20A7,7 0 0,1 5,13A7,7 0 0,1 12,6A7,7 0 0,1 19,13A7,7 0 0,1 12,20M19.03,7.39L20.45,5.97C20,5.46 19.55,5 19.04,4.56L17.62,6C16.07,4.74 14.12,4 12,4A9,9 0 0,0 3,13A9,9 0 0,0 12,22C17,22 21,17.97 21,13C21,10.88 20.26,8.93 19.03,7.39M11,14H13V8H11M15,1H9V3H15V1Z","status.delayed_turn_on","status.waiting_ends_at")}
        ${this.renderApplianceChip(e)}
      `)}renderRank(e){return this.renderWideOnly(X`<span class="rank">${e??te}</span>`)}renderWideOnly(e){return this.phone?te:e}renderName(e){return X`<span class="name" title=${e}>${e}</span>`}renderApplianceChip(e){return e.excluded?this.renderChip(pr,"status.chip_excluded","status.excluded"):e.on?this.renderChip(cr,"status.on","status.on"):this.renderChip(hr,"status.off","status.off")}renderApplianceIcon(e){const t=this.applianceEntity(e),i=t?this.hass.states[t]:void 0;return X`
      <span class="device-icon ${e.on?"on":""}">
        ${i?X`<ha-state-icon .hass=${this.hass} .stateObj=${i}></ha-state-icon>`:te}
        <ha-svg-icon .path=${"M7,2V13H10V22L17,10H13L17,2H7Z"}></ha-svg-icon>
      </span>
    `}renderChargerGroup(e,i){const r=e.chargers,a=r.filter(e=>e.charging).length;return X`
      <div class="row group">
        ${this.renderRank(i)}
        <div class="row-title">
          <ha-svg-icon class="ev-icon" .path=${t}></ha-svg-icon>
          ${this.renderName(e.name)}
          ${0!==r.length||this.phone?te:X`<span class="row-sub">${this.localize("status.no_chargers")}</span>`}
        </div>
        ${this.renderWideOnly(0===r.length?X`<span></span>`:X`<span
                class="charging-count"
                title=${this.localize("status.chargers_charging",{charging:a,total:r.length})}
              >
                <ha-svg-icon .path=${n}></ha-svg-icon>${a} / ${r.length}
              </span>`)}
      </div>
      ${r.map(e=>this.renderChargerRow(e))}
    `}renderChargerRow(e){return this.renderRow("charger "+(e.activated?"":"off"),Ei(this.hass,this.chargerConfig(e)?.entity_id),X`
        ${this.renderRank(null)}
        <div class="row-title">
          <ha-svg-icon class="device-icon ev ${e.activated?"on":""}" .path=${r}></ha-svg-icon>
          ${this.renderName(e.name)}
        </div>
        ${this.phone?this.renderPhoneCurrent(e):this.renderAmperes(e)}
        ${this.renderPower(e.power_w)}
        ${this.renderWaiting(e,o,"status.delayed_turn_on","status.next_ampere_at")}
        ${this.renderChargerChip(e)}
      `)}renderWaiting(e,t,i,r){if(!e.waiting_since||!e.waiting_ends_at)return this.phone?te:X`<span></span>`;const a=vt(this.hass.language,e.waiting_ends_at);return X`
      <span class="waiting" title="${this.localize(i)}: ${this.localize(r,{time:a})}">
        <ha-svg-icon .path=${t}></ha-svg-icon>
        ${this.renderWideOnly(X`<kraftvakt-countdown-bar
            .start=${Date.parse(e.waiting_since)}
            .end=${Date.parse(e.waiting_ends_at)}
          ></kraftvakt-countdown-bar>`)}
      </span>
    `}renderPower(e){return this.hasPower?this.renderWideOnly(X`<span class="measured" title=${this.localize("status.power")}
        >${null===e?te:`${gt(this.hass.language,e)} kW`}</span
      >`):te}renderTemperature(e){const t=e.temperature;return null===t||this.phone?te:X`<span class="measured" title=${this.localize("status.temperature")}
      >${ut(this.hass.language,t.value,1)} ${t.unit}</span
    >`}renderAmperes(e){const t=this.chargerConfig(e);if(!t)return X`<span></span>`;const i=t.max_current_a-t.min_current_a+1,r=null===e.current_a?0:e.current_a-t.min_current_a+1,a=e.bypassed?"on bypassed":"on";return X`
      <span class="amperes">
        <span class="current ${null===e.current_a?"none":""}"
          >${null===e.current_a?"–":this.localize("status.amperes",{current:e.current_a})}</span
        >
        <span class="ampere-steps ${i>16?"small":""}">
          ${Array.from({length:i},(e,t)=>X`<span class="ampere ${t<r?a:""}"></span>`)}
        </span>
      </span>
    `}renderPhoneCurrent(e){return null===e.current_a?te:X`<span class="current">${this.localize("status.amperes",{current:e.current_a})}</span>`}renderChargerChip(e){const[t,i,r]=ur[e.state],a=this.chargerConfig(e)?.charging_window;if("outside_window"===e.state&&a){const e={start:gr(a.start),end:gr(a.end)};return this.renderChip(t,i,r,e,{...a})}return e.starting_until?this.renderChip(t,i,r,{},{time:vt(this.hass.language,e.starting_until)}):"queued"===e.state&&this.sharesByChargingPower(e)?this.renderChip(t,i,"status.queued_for_room"):this.renderChip(t,i,r,{},{current:e.current_a??0})}renderChip(e,t,i,r={},a=r){return X`
      <span class="state chip ${e.kind}" title=${this.localize(i,a)}>
        ${e.icon?X`<ha-svg-icon .path=${e.icon}></ha-svg-icon>`:X`<span class="dot"></span>`}
        ${this.localize(t,r)}
      </span>
    `}renderCutOff(){const e=this.status,t=this.hass.language,i=e.regulation_average_w,r=null===i?0:e.power_limit_w-i;return X`
      <div class="cut-off" title=${this.localize("status.power_runs_out")}>
        <ha-svg-icon .path=${"M11,4H13V16L18.5,10.5L19.92,11.92L12,19.84L4.08,11.92L5.5,10.5L11,16V4Z"}></ha-svg-icon>
        ${r>0?this.localize("status.free_power",{power:gt(t,r),share:mt(t,r/e.power_limit_w)}):te}
      </div>
    `}applianceEntity(e){return this.config?.config.appliances.find(t=>t.id===e.id)?.entity_id}chargerConfig(e){return this.config&&it(this.config.config).find(t=>t.id===e.id)}sharesByChargingPower(e){const t=this.config?.config.charger_groups.find(t=>t.chargers.some(t=>t.id===e.id));return!!t&&t.dynamic_order&&!t.one_at_a_time}static{this.styles=[lr,dr,g`
      :host {
        display: block;
        container-type: inline-size;
      }
      /*
       * The spacing grows with the list's width, from tight just above the phone layout (600 px)
       * to the widest list the panel gets (1040 px), where the columns after the name take its right half.
       */
      ha-card {
        --column-gap: clamp(12px, 5.455cqi - 20.7px, 36px);
        --waiting-width: clamp(72px, 14.545cqi - 15.3px, 136px);
        --row-padding-end: clamp(16px, 3.636cqi - 5.8px, 32px);
      }
      .empty {
        padding: 0 16px 16px;
        color: var(--secondary-text-color);
      }
      .list {
        display: grid;
        column-gap: var(--column-gap);
      }
      .row {
        grid-column: 1 / -1;
        display: grid;
        grid-template-columns: subgrid;
        align-items: center;
        min-height: 48px;
        padding: 4px var(--row-padding-end) 4px 16px;
        border-top: 1px solid var(--divider-color);
        box-sizing: border-box;
      }
      :host([narrow]) .row {
        padding-inline-start: 12px;
      }
      .row.group,
      .row.charger {
        background: color-mix(in srgb, var(--kraftvakt-ev-color) 7%, transparent);
      }
      .row.essential {
        background: var(--kraftvakt-essential-background);
      }
      .row.clickable {
        cursor: pointer;
      }
      .row.clickable:hover {
        background-image: linear-gradient(color-mix(in srgb, var(--primary-text-color) 6%, transparent) 0 0);
      }
      .row.clickable:focus-visible {
        outline: 2px solid var(--primary-color);
        outline-offset: -2px;
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
      .row.appliance:not(.with-temperature) .row-title {
        grid-column: span 2;
      }
      .row.charger .row-title {
        padding-inline-start: 24px;
      }
      :host([narrow]) .row.charger .row-title {
        padding-inline-start: 16px;
      }
      /* The rank stays close to the name, whatever the gap between the columns. */
      .rank {
        margin-inline-end: calc(12px - var(--column-gap));
        text-align: end;
        font-variant-numeric: tabular-nums;
        color: var(--secondary-text-color);
      }
      .row > .chip {
        justify-self: start;
      }
      .measured {
        text-align: end;
        font-variant-numeric: tabular-nums;
        white-space: nowrap;
        overflow: hidden;
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
      .current {
        min-width: 40px;
        text-align: end;
        font-weight: 500;
        white-space: nowrap;
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
      .row-title {
        display: flex;
        align-items: center;
        gap: 10px;
        min-width: 0;
      }
      .name {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .row-title ha-svg-icon,
      .row-title ha-state-icon {
        flex: none;
        --mdc-icon-size: 20px;
      }
      .row-title ha-svg-icon,
      .row-title .device-icon {
        color: var(--state-inactive-color, var(--secondary-text-color));
      }
      .row-title .device-icon > * {
        color: inherit;
      }
      span.device-icon {
        display: flex;
        flex: none;
        width: 20px;
        height: 20px;
        overflow: hidden;
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
        flex: none;
        color: var(--secondary-text-color);
        font-size: var(--ha-font-size-s, 12px);
      }
      .variant {
        flex: 0 1000 auto;
        min-width: 3em;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        padding: 0 8px;
        border-radius: 999px;
        font-size: var(--ha-font-size-s, 12px);
        background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.16);
        color: var(--primary-color);
      }
      .list.phone {
        display: block;
      }
      .list.phone .row {
        display: flex;
        gap: 8px;
      }
      .list.phone .row-title {
        flex: 1;
      }
    `]}};e([$e({attribute:!1})],fr.prototype,"hass",void 0),e([$e({attribute:!1})],fr.prototype,"localize",void 0),e([$e({type:Boolean,reflect:!0})],fr.prototype,"narrow",void 0),e([$e({attribute:!1})],fr.prototype,"status",void 0),e([$e({attribute:!1})],fr.prototype,"config",void 0),fr=e([ye("kraftvakt-priority-list")],fr);let mr=class extends ve{constructor(){super(...arguments),this.narrow=!1}render(){if(!this.status)return te;const e=this.status;return X`
      <div class="cards">
        ${this.renderRegulationCard(e)}
        ${e.running?X`<kraftvakt-priority-list
              .hass=${this.hass}
              .localize=${this.localize}
              .narrow=${this.narrow}
              .status=${e}
              .config=${this.config}
            ></kraftvakt-priority-list>`:te}
      </div>
    `}renderRegulationCard(e){return X`
      <ha-card class="regulation">
        <div class="card-header">
          <span>${this.localize("status.regulation")}</span>
          <span class="chip ${e.running?"running":"off"}">
            <span class="dot"></span>
            ${this.localize(e.running?"status.running":"status.stopped")}
          </span>
          ${e.running&&e.safe_state?X`<span class="chip alarm">${this.localize("status.safe_state_chip")}</span>`:te}
          ${e.running&&e.penalty.active?X`<span class="chip alarm">${this.localize("status.penalty_chip")}</span>`:te}
          <span class="spacer"></span>
          ${e.running&&e.next_decision_at?this.renderNextDecision(e,e.next_decision_at):te}
        </div>
        <div class="card-content">
          ${this.runningError?X`<ha-alert alert-type="error">${this.runningError}</ha-alert>`:te}
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
    `}renderRunning(e){const t=this.config?.config.general.power_sensor??null,i=Vi(this.hass,t??"");return X`
      ${e.safe_state?this.renderSafeState(null!==i):te} ${e.penalty.active?this.renderPenalty(e):te}
      <kraftvakt-power-overview
        .hass=${this.hass}
        .localize=${this.localize}
        .narrow=${this.narrow}
        .status=${e}
        .powerNowW=${i}
        .powerSensor=${t}
      ></kraftvakt-power-overview>
    `}renderNextDecision(e,t){const i=Date.parse(t),r=e.regulation_window_s*e.regulation_interval*1e3,a=vt(this.hass.language,t);return X`
      <span class="next-decision" title=${this.localize("status.next_decision_at",{time:a})}>
        ${this.narrow?te:this.localize("status.next_decision")}
        <kraftvakt-countdown-ring .start=${i-r} .end=${i}></kraftvakt-countdown-ring>
      </span>
    `}renderSafeState(e){const t=this.config?.config.general.power_sensor??"",i=this.hass.states[t]?.attributes.friendly_name??t;return X`
      <ha-alert alert-type=${e?"info":"error"} .title=${this.localize("status.safe_state_title")}>
        ${this.localize(e?"status.safe_state_back_text":"status.safe_state_text",{sensor:i})}
      </ha-alert>
    `}renderPenalty(e){const t=(i=this.hass.language,r=Math.max(0,e.penalty.overconsumption_wh),ut(i,r/1e3,2));var i,r;const a=e.penalty.recovery_started?"status.recovery_started":"status.recovery_not_started";return X`
      <ha-alert alert-type="warning" .title=${this.localize("status.penalty_title")}>
        ${this.localize("status.penalty_text")}
        <div class="penalty-details">${this.localize("status.overconsumption_left",{energy:t})} · ${this.localize(a)}</div>
      </ha-alert>
    `}renderStopped(e){return 0===e.missing.length?X`<ha-alert alert-type="info">${this.localize("status.stopped_info")}</ha-alert>`:X`
      <ha-alert alert-type="warning" .title=${this.localize("status.incomplete_title")}>
        <ul class="missing">
          ${e.missing.map(e=>{const t=function(e){return"general"===e.section&&e.field&&zt.has(e.field)?"advanced":Et[e.section]}(e);return X`
              <li>
                ${function(e,t,i){const r={item:Vt(e,t,i),action:St(e.field,i),code:e.code};return i(At[e.code]??"missing.unknown",r)}(e,this.config,this.localize)}
                <a href="${ot}/${t}" @click=${e=>this.openPage(e,t)}>
                  ${this.localize(`tabs.${t}`)}
                </a>
              </li>
            `})}
        </ul>
      </ha-alert>
    `}openPage(e,t){e.preventDefault(),lt(t)}static{this.styles=[lr,dr,g`
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
      .next-decision {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-size: var(--ha-font-size-m, 14px);
        color: var(--secondary-text-color);
      }
      .penalty-details {
        margin-top: 8px;
      }
      ul.missing {
        margin: 6px 0 0;
        padding-inline-start: 18px;
      }
      ul.missing a {
        color: var(--primary-color);
      }
    `]}};e([$e({attribute:!1})],mr.prototype,"hass",void 0),e([$e({attribute:!1})],mr.prototype,"localize",void 0),e([$e({type:Boolean,reflect:!0})],mr.prototype,"narrow",void 0),e([$e({attribute:!1})],mr.prototype,"status",void 0),e([$e({attribute:!1})],mr.prototype,"config",void 0),e([ke()],mr.prototype,"runningError",void 0),mr=e([ye("kraftvakt-status-page")],mr);const vr={status:"M3,13H5.79L10.1,4.79L11.28,13.75L14.5,9.66L17.83,13H21V15H17L14.67,12.67L9.92,18.73L8.94,11.31L7,15H3V13Z",general:"M12,15.5A3.5,3.5 0 0,1 8.5,12A3.5,3.5 0 0,1 12,8.5A3.5,3.5 0 0,1 15.5,12A3.5,3.5 0 0,1 12,15.5M19.43,12.97C19.47,12.65 19.5,12.33 19.5,12C19.5,11.67 19.47,11.34 19.43,11L21.54,9.37C21.73,9.22 21.78,8.95 21.66,8.73L19.66,5.27C19.54,5.05 19.27,4.96 19.05,5.05L16.56,6.05C16.04,5.66 15.5,5.32 14.87,5.07L14.5,2.42C14.46,2.18 14.25,2 14,2H10C9.75,2 9.54,2.18 9.5,2.42L9.13,5.07C8.5,5.32 7.96,5.66 7.44,6.05L4.95,5.05C4.73,4.96 4.46,5.05 4.34,5.27L2.34,8.73C2.21,8.95 2.27,9.22 2.46,9.37L4.57,11C4.53,11.34 4.5,11.67 4.5,12C4.5,12.33 4.53,12.65 4.57,12.97L2.46,14.63C2.27,14.78 2.21,15.05 2.34,15.27L4.34,18.73C4.46,18.95 4.73,19.03 4.95,18.95L7.44,17.94C7.96,18.34 8.5,18.68 9.13,18.93L9.5,21.58C9.54,21.82 9.75,22 10,22H14C14.25,22 14.46,21.82 14.5,21.58L14.87,18.93C15.5,18.67 16.04,18.34 16.56,17.94L19.05,18.95C19.27,19.03 19.54,18.95 19.66,18.73L21.66,15.27C21.78,15.05 21.73,14.78 21.54,14.63L19.43,12.97Z",appliances:"M7,13V11H21V13H7M7,19V17H21V19H7M7,7V5H21V7H7M3,8V5H2V4H4V8H3M2,17V16H5V20H2V19H4V18.5H3V17.5H4V17H2M4.25,10A0.75,0.75 0 0,1 5,10.75C5,10.95 4.92,11.14 4.79,11.27L3.12,13H5V14H2V13.08L4,11H2V10H4.25Z",charging:t,advanced:"M3,17V19H9V17H3M3,5V7H13V5H3M13,21V19H21V17H13V15H11V21H13M7,9V11H3V13H7V15H9V9H7M21,13V11H11V13H21M15,9H17V7H21V5H17V3H15V9Z"},_r={general:We`kraftvakt-general-page`,appliances:We`kraftvakt-appliances-page`,charging:We`kraftvakt-charging-page`,advanced:We`kraftvakt-advanced-page`};let yr=class extends ve{constructor(){super(...arguments),this.narrow=!1,this.haElementsReady=!1,this.saveErrors=[],this.saving=!1,this.localize=at("en"),this.warnBeforeUnload=e=>{this.dirty&&e.preventDefault()}}connectedCallback(){super.connectedCallback(),window.addEventListener("beforeunload",this.warnBeforeUnload),customElements.whenDefined("ha-form").then(()=>{this.haElementsReady=!0}),this.hass&&this.subscribe()}disconnectedCallback(){super.disconnectedCallback(),window.removeEventListener("beforeunload",this.warnBeforeUnload),this.unsubscribe()}willUpdate(e){e.has("hass")&&this.hass?.language!==e.get("hass")?.language&&(this.localize=at(this.hass?.language??"en"),this.hass?.loadFragmentTranslation("config")),e.has("hass")&&this.hass&&!this.unsubscribeStatus&&this.subscribe()}updated(e){e.has("route")&&this.openAppliancesFromConfigureButton()}render(){if(!this.hass||!this.haElementsReady)return X``;const e=this.currentPage;return X`
      <div class="toolbar">
        <ha-menu-button .hass=${this.hass} .narrow=${this.narrow}></ha-menu-button>
        <div class="title">${this.localize("panel.title")}</div>
        <ha-tab-group @wa-tab-show=${this.tabShown}>
          ${Object.entries(vr).map(([t,i])=>X`
              <ha-tab-group-tab
                slot="nav"
                panel=${t}
                .active=${Fe(t===e)}
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
    `}renderLoadError(){if(void 0===this.loadError)return"";const e=Be(this.loadError)&&"not_loaded"===this.loadError.code?this.localize("panel.not_loaded"):this.localize("panel.error",{message:qe(this.loadError)});return X`<ha-alert alert-type="error">${e}</ha-alert>`}renderPage(e){switch(e){case"status":return X`
          <kraftvakt-status-page
            .hass=${this.hass}
            .localize=${this.localize}
            .narrow=${this.narrow}
            .status=${this.status}
            .config=${this.config}
          ></kraftvakt-status-page>
        `;case"general":case"appliances":case"charging":case"advanced":return this.renderConfigPage(e)}}renderConfigPage(e){if(!(this.hass&&this.status&&this.config&&this.draft&&this.capabilities))return"";const t=this.status.running,i=t?[]:function(e,t,i){return[...hi("general",void 0,e.general,t.limits.general,!0),...e.appliances.flatMap(e=>oi(e,t,i)),...Yt(e.charger_groups),...it(e).flatMap(e=>li(e,t,i))]}(this.draft,this.capabilities,this.hass),r=!t&&(this.dirty||this.saveErrors.length>0),a=t?[]:this.pageIssues(i);return X`
      ${t?X`<kraftvakt-locked-banner
            .hass=${this.hass}
            .localize=${this.localize}
            .narrow=${this.narrow}
          ></kraftvakt-locked-banner>`:""}
      ${this.renderConfigPageContent(e,t?this.config.config:this.draft,a,t)}
      ${r?X`
            <kraftvakt-save-bar
              .localize=${this.localize}
              .errorCount=${i.length}
              .saving=${this.saving}
              .message=${this.saveMessage}
              @save=${this.save}
              @discard=${this.discard}
            ></kraftvakt-save-bar>
          `:""}
    `}renderConfigPageContent(e,t,i,r){const a=_r[e];return Re`
      <${a}
        .hass=${this.hass}
        .localize=${this.localize}
        .narrow=${this.narrow}
        .config=${t}
        .entityNames=${this.config?.entity_names??{}}
        .capabilities=${this.capabilities}
        .issues=${i}
        .saveErrors=${this.saveErrors}
        .locked=${r}
      ></${a}>
    `}pageIssues(e){return this.draft?[...e,...this.saveErrors,...ei(this.draft)]:[]}get dirty(){return void 0!==this.draft&&(e=this.draft,t=this.savedConfig,!(JSON.stringify(e)===JSON.stringify(t)));var e,t}get savedConfig(){return this.config&&tt(this.config.config)}draftChanged(e){e.type!==Qe||this.status?.running||(this.draft=tt(e.detail))}async save(){if(this.hass&&this.draft){this.saving=!0,this.saveMessage=void 0;try{const e=await((e,t)=>e.callWS({type:"kraftvakt/config/save",config:t}))(this.hass,this.draft);e.saved?(this.saveErrors=[],await this.loadConfig({resetDraft:!0})):(this.saveErrors=e.errors,this.saveMessage=this.localize("config.not_saved"))}catch(e){this.saveMessage=Be(e)&&"regulation_running"===e.code?this.localize("config.save_refused_running"):this.localize("panel.error",{message:qe(e)})}finally{this.saving=!1}}}discard(){this.resetDraft()}resetDraft(){this.draft=this.savedConfig,this.saveErrors=[],this.saveMessage=void 0}leaveConfirmed(){const e=this.leavingTo;this.leavingTo=void 0,this.resetDraft(),e&&lt(e)}leaveCancelled(){this.leavingTo=void 0}get currentPage(){return function(e){const t=e.split("/")[1]??"";return st.includes(t)?t:"status"}(this.route?.path??"")}tabLabel(e){return this.localize(`tabs.${e}`)}tabShown(e){const t=e.detail.name;t!==this.currentPage&&("status"===t&&this.dirty?this.leavingTo=t:lt(t))}subscribe(){var e,t;this.hass&&(this.unsubscribeStatus=(e=this.hass,t=e=>this.statusReceived(e),e.connection.subscribeMessage(t,{type:"kraftvakt/status/subscribe"})),this.unsubscribeStatus.catch(e=>{this.loadError=e,this.unsubscribeStatus=void 0}),(e=>e.callWS({type:"kraftvakt/capabilities"}))(this.hass).then(e=>this.capabilities=e).catch(e=>this.loadError=e))}unsubscribe(){this.unsubscribeStatus?.then(e=>e()).catch(()=>{}),this.unsubscribeStatus=void 0}statusReceived(e){const t=this.status;this.status=e,this.loadError=void 0,void 0!==t&&t.running===e.running&&t.config_version===e.config_version&&JSON.stringify(t.missing)===JSON.stringify(e.missing)||this.loadConfig()}async loadConfig(e={}){var t;if(this.hass)try{const i=this.dirty&&!e.resetDraft&&!this.status?.running;this.config=await(t=this.hass,t.callWS({type:"kraftvakt/config/get"})),i||this.resetDraft()}catch(e){this.loadError=e}}openAppliancesFromConfigureButton(){new URLSearchParams(window.location.search).has("config_entry")&&lt("appliances",{replace:!0})}static{this.styles=g`
    :host {
      display: block;
      min-height: 100vh;
      background: var(--primary-background-color);
      color: var(--primary-text-color);
      --kraftvakt-essential-background: color-mix(in srgb, var(--amber-color, #ffc107) 12%, transparent);
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
  `}};e([$e({attribute:!1})],yr.prototype,"hass",void 0),e([$e({type:Boolean,reflect:!0})],yr.prototype,"narrow",void 0),e([$e({attribute:!1})],yr.prototype,"route",void 0),e([ke()],yr.prototype,"haElementsReady",void 0),e([ke()],yr.prototype,"status",void 0),e([ke()],yr.prototype,"config",void 0),e([ke()],yr.prototype,"loadError",void 0),e([ke()],yr.prototype,"capabilities",void 0),e([ke()],yr.prototype,"draft",void 0),e([ke()],yr.prototype,"saveErrors",void 0),e([ke()],yr.prototype,"saveMessage",void 0),e([ke()],yr.prototype,"saving",void 0),e([ke()],yr.prototype,"leavingTo",void 0),yr=e([ye("kraftvakt-panel")],yr);export{yr as KraftvaktPanel};
