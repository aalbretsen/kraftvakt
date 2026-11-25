function e(e,t,i,r){var a,n=arguments.length,s=n<3?t:null===r?r=Object.getOwnPropertyDescriptor(t,i):r;if("object"==typeof Reflect&&"function"==typeof Reflect.decorate)s=Reflect.decorate(e,t,i,r);else for(var o=e.length-1;o>=0;o--)(a=e[o])&&(s=(n<3?a(s):n>3?a(t,i,s):a(t,i))||s);return n>3&&s&&Object.defineProperty(t,i,s),s}"function"==typeof SuppressedError&&SuppressedError;var t="M18.92 2C18.72 1.42 18.16 1 17.5 1H6.5C5.84 1 5.29 1.42 5.08 2L3 8V16C3 16.55 3.45 17 4 17H5C5.55 17 6 16.55 6 16V15H18V16C18 16.55 18.45 17 19 17H20C20.55 17 21 16.55 21 16V8L18.92 2M6.5 12C5.67 12 5 11.33 5 10.5S5.67 9 6.5 9 8 9.67 8 10.5 7.33 12 6.5 12M17.5 12C16.67 12 16 11.33 16 10.5S16.67 9 17.5 9 19 9.67 19 10.5 18.33 12 17.5 12M5 7L6.5 2.5H17.5L19 7H5M7 20H11V18L17 21H13V23L7 20Z",i="M21 11H3V9H21V11M21 13H3V15H21V13Z",r="M19.77,7.23L19.78,7.22L16.06,3.5L15,4.56L17.11,6.67C16.17,7.03 15.5,7.93 15.5,9A2.5,2.5 0 0,0 18,11.5C18.36,11.5 18.69,11.42 19,11.29V18.5A1,1 0 0,1 18,19.5A1,1 0 0,1 17,18.5V14A2,2 0 0,0 15,12H14V5A2,2 0 0,0 12,3H6A2,2 0 0,0 4,5V21H14V13.5H15.5V18.5A2.5,2.5 0 0,0 18,21A2.5,2.5 0 0,0 20.5,18.5V9C20.5,8.31 20.22,7.68 19.77,7.23M18,10A1,1 0 0,1 17,9A1,1 0 0,1 18,8A1,1 0 0,1 19,9A1,1 0 0,1 18,10M8,18V13.5H6L10,6V11H12L8,18Z",a="M12,9A3,3 0 0,0 9,12A3,3 0 0,0 12,15A3,3 0 0,0 15,12A3,3 0 0,0 12,9M12,17A5,5 0 0,1 7,12A5,5 0 0,1 12,7A5,5 0 0,1 17,12A5,5 0 0,1 12,17M12,4.5C7,4.5 2.73,7.61 1,12C2.73,16.39 7,19.5 12,19.5C17,19.5 21.27,16.39 23,12C21.27,7.61 17,4.5 12,4.5Z",n="M11 15H6L13 1V9H18L11 23V15Z",s="M20.71,7.04C21.1,6.65 21.1,6 20.71,5.63L18.37,3.29C18,2.9 17.35,2.9 16.96,3.29L15.12,5.12L18.87,8.87M3,17.25V21H6.75L17.81,9.93L14.06,6.18L3,17.25Z",o="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z",l="M6,2H18V8H18V8L14,12L18,16V16H18V22H6V16H6V16L10,12L6,8V8H6V2M16,16.5L12,12.5L8,16.5V20H16V16.5M12,11.5L16,7.5V4H8V7.5L12,11.5M10,6H14V6.75L12,8.75L10,6.75V6Z";const d=globalThis,c=d.ShadowRoot&&(void 0===d.ShadyCSS||d.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,h=Symbol(),p=new WeakMap;let u=class{constructor(e,t,i){if(this._$cssResult$=!0,i!==h)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=e,this.t=t}get styleSheet(){let e=this.o;const t=this.t;if(c&&void 0===e){const i=void 0!==t&&1===t.length;i&&(e=p.get(t)),void 0===e&&((this.o=e=new CSSStyleSheet).replaceSync(this.cssText),i&&p.set(t,e))}return e}toString(){return this.cssText}};const g=(e,...t)=>{const i=1===e.length?e[0]:t.reduce((t,i,r)=>t+(e=>{if(!0===e._$cssResult$)return e.cssText;if("number"==typeof e)return e;throw Error("Value passed to 'css' function must be a 'css' function result: "+e+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(i)+e[r+1],e[0]);return new u(i,e,h)},m=c?e=>e:e=>e instanceof CSSStyleSheet?(e=>{let t="";for(const i of e.cssRules)t+=i.cssText;return(e=>new u("string"==typeof e?e:e+"",void 0,h))(t)})(e):e,{is:_,defineProperty:f,getOwnPropertyDescriptor:v,getOwnPropertyNames:w,getOwnPropertySymbols:y,getPrototypeOf:b}=Object,$=globalThis,k=$.trustedTypes,x=k?k.emptyScript:"",A=$.reactiveElementPolyfillSupport,C=(e,t)=>e,z={toAttribute(e,t){switch(t){case Boolean:e=e?x:null;break;case Object:case Array:e=null==e?e:JSON.stringify(e)}return e},fromAttribute(e,t){let i=e;switch(t){case Boolean:i=null!==e;break;case Number:i=null===e?null:Number(e);break;case Object:case Array:try{i=JSON.parse(e)}catch(e){i=null}}return i}},E=(e,t)=>!_(e,t),S={attribute:!0,type:String,converter:z,reflect:!1,useDefault:!1,hasChanged:E};Symbol.metadata??=Symbol("metadata"),$.litPropertyMetadata??=new WeakMap;let V=class extends HTMLElement{static addInitializer(e){this._$Ei(),(this.l??=[]).push(e)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(e,t=S){if(t.state&&(t.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(e)&&((t=Object.create(t)).wrapped=!0),this.elementProperties.set(e,t),!t.noAccessor){const i=Symbol(),r=this.getPropertyDescriptor(e,i,t);void 0!==r&&f(this.prototype,e,r)}}static getPropertyDescriptor(e,t,i){const{get:r,set:a}=v(this.prototype,e)??{get(){return this[t]},set(e){this[t]=e}};return{get:r,set(t){const n=r?.call(this);a?.call(this,t),this.requestUpdate(e,n,i)},configurable:!0,enumerable:!0}}static getPropertyOptions(e){return this.elementProperties.get(e)??S}static _$Ei(){if(this.hasOwnProperty(C("elementProperties")))return;const e=b(this);e.finalize(),void 0!==e.l&&(this.l=[...e.l]),this.elementProperties=new Map(e.elementProperties)}static finalize(){if(this.hasOwnProperty(C("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(C("properties"))){const e=this.properties,t=[...w(e),...y(e)];for(const i of t)this.createProperty(i,e[i])}const e=this[Symbol.metadata];if(null!==e){const t=litPropertyMetadata.get(e);if(void 0!==t)for(const[e,i]of t)this.elementProperties.set(e,i)}this._$Eh=new Map;for(const[e,t]of this.elementProperties){const i=this._$Eu(e,t);void 0!==i&&this._$Eh.set(i,e)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(e){const t=[];if(Array.isArray(e)){const i=new Set(e.flat(1/0).reverse());for(const e of i)t.unshift(m(e))}else void 0!==e&&t.push(m(e));return t}static _$Eu(e,t){const i=t.attribute;return!1===i?void 0:"string"==typeof i?i:"string"==typeof e?e.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(e=>this.enableUpdating=e),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(e=>e(this))}addController(e){(this._$EO??=new Set).add(e),void 0!==this.renderRoot&&this.isConnected&&e.hostConnected?.()}removeController(e){this._$EO?.delete(e)}_$E_(){const e=new Map,t=this.constructor.elementProperties;for(const i of t.keys())this.hasOwnProperty(i)&&(e.set(i,this[i]),delete this[i]);e.size>0&&(this._$Ep=e)}createRenderRoot(){const e=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return((e,t)=>{if(c)e.adoptedStyleSheets=t.map(e=>e instanceof CSSStyleSheet?e:e.styleSheet);else for(const i of t){const t=document.createElement("style"),r=d.litNonce;void 0!==r&&t.setAttribute("nonce",r),t.textContent=i.cssText,e.appendChild(t)}})(e,this.constructor.elementStyles),e}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(e=>e.hostConnected?.())}enableUpdating(e){}disconnectedCallback(){this._$EO?.forEach(e=>e.hostDisconnected?.())}attributeChangedCallback(e,t,i){this._$AK(e,i)}_$ET(e,t){const i=this.constructor.elementProperties.get(e),r=this.constructor._$Eu(e,i);if(void 0!==r&&!0===i.reflect){const a=(void 0!==i.converter?.toAttribute?i.converter:z).toAttribute(t,i.type);this._$Em=e,null==a?this.removeAttribute(r):this.setAttribute(r,a),this._$Em=null}}_$AK(e,t){const i=this.constructor,r=i._$Eh.get(e);if(void 0!==r&&this._$Em!==r){const e=i.getPropertyOptions(r),a="function"==typeof e.converter?{fromAttribute:e.converter}:void 0!==e.converter?.fromAttribute?e.converter:z;this._$Em=r;const n=a.fromAttribute(t,e.type);this[r]=n??this._$Ej?.get(r)??n,this._$Em=null}}requestUpdate(e,t,i,r=!1,a){if(void 0!==e){const n=this.constructor;if(!1===r&&(a=this[e]),i??=n.getPropertyOptions(e),!((i.hasChanged??E)(a,t)||i.useDefault&&i.reflect&&a===this._$Ej?.get(e)&&!this.hasAttribute(n._$Eu(e,i))))return;this.C(e,t,i)}!1===this.isUpdatePending&&(this._$ES=this._$EP())}C(e,t,{useDefault:i,reflect:r,wrapped:a},n){i&&!(this._$Ej??=new Map).has(e)&&(this._$Ej.set(e,n??t??this[e]),!0!==a||void 0!==n)||(this._$AL.has(e)||(this.hasUpdated||i||(t=void 0),this._$AL.set(e,t)),!0===r&&this._$Em!==e&&(this._$Eq??=new Set).add(e))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(e){Promise.reject(e)}const e=this.scheduleUpdate();return null!=e&&await e,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(const[e,t]of this._$Ep)this[e]=t;this._$Ep=void 0}const e=this.constructor.elementProperties;if(e.size>0)for(const[t,i]of e){const{wrapped:e}=i,r=this[t];!0!==e||this._$AL.has(t)||void 0===r||this.C(t,void 0,i,r)}}let e=!1;const t=this._$AL;try{e=this.shouldUpdate(t),e?(this.willUpdate(t),this._$EO?.forEach(e=>e.hostUpdate?.()),this.update(t)):this._$EM()}catch(t){throw e=!1,this._$EM(),t}e&&this._$AE(t)}willUpdate(e){}_$AE(e){this._$EO?.forEach(e=>e.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(e)),this.updated(e)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(e){return!0}update(e){this._$Eq&&=this._$Eq.forEach(e=>this._$ET(e,this[e])),this._$EM()}updated(e){}firstUpdated(e){}};V.elementStyles=[],V.shadowRootOptions={mode:"open"},V[C("elementProperties")]=new Map,V[C("finalized")]=new Map,A?.({ReactiveElement:V}),($.reactiveElementVersions??=[]).push("2.1.2");const M=globalThis,H=e=>e,T=M.trustedTypes,L=T?T.createPolicy("lit-html",{createHTML:e=>e}):void 0,D="$lit$",N=`lit$${Math.random().toFixed(9).slice(2)}$`,P="?"+N,O=`<${P}>`,F=document,W=()=>F.createComment(""),j=e=>null===e||"object"!=typeof e&&"function"!=typeof e,I=Array.isArray,R="[ \t\n\f\r]",B=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,U=/-->/g,q=/>/g,G=RegExp(`>|${R}(?:([^\\s"'>=/]+)(${R}*=${R}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`,"g"),K=/'/g,Z=/"/g,J=/^(?:script|style|textarea|title)$/i,Q=e=>(t,...i)=>({_$litType$:e,strings:t,values:i}),X=Q(1),Y=Q(2),ee=Symbol.for("lit-noChange"),te=Symbol.for("lit-nothing"),ie=new WeakMap,re=F.createTreeWalker(F,129);function ae(e,t){if(!I(e)||!e.hasOwnProperty("raw"))throw Error("invalid template strings array");return void 0!==L?L.createHTML(t):t}class ne{constructor({strings:e,_$litType$:t},i){let r;this.parts=[];let a=0,n=0;const s=e.length-1,o=this.parts,[l,d]=((e,t)=>{const i=e.length-1,r=[];let a,n=2===t?"<svg>":3===t?"<math>":"",s=B;for(let t=0;t<i;t++){const i=e[t];let o,l,d=-1,c=0;for(;c<i.length&&(s.lastIndex=c,l=s.exec(i),null!==l);)c=s.lastIndex,s===B?"!--"===l[1]?s=U:void 0!==l[1]?s=q:void 0!==l[2]?(J.test(l[2])&&(a=RegExp("</"+l[2],"g")),s=G):void 0!==l[3]&&(s=G):s===G?">"===l[0]?(s=a??B,d=-1):void 0===l[1]?d=-2:(d=s.lastIndex-l[2].length,o=l[1],s=void 0===l[3]?G:'"'===l[3]?Z:K):s===Z||s===K?s=G:s===U||s===q?s=B:(s=G,a=void 0);const h=s===G&&e[t+1].startsWith("/>")?" ":"";n+=s===B?i+O:d>=0?(r.push(o),i.slice(0,d)+D+i.slice(d)+N+h):i+N+(-2===d?t:h)}return[ae(e,n+(e[i]||"<?>")+(2===t?"</svg>":3===t?"</math>":"")),r]})(e,t);if(this.el=ne.createElement(l,i),re.currentNode=this.el.content,2===t||3===t){const e=this.el.content.firstChild;e.replaceWith(...e.childNodes)}for(;null!==(r=re.nextNode())&&o.length<s;){if(1===r.nodeType){if(r.hasAttributes())for(const e of r.getAttributeNames())if(e.endsWith(D)){const t=d[n++],i=r.getAttribute(e).split(N),s=/([.?@])?(.*)/.exec(t);o.push({type:1,index:a,name:s[2],strings:i,ctor:"."===s[1]?ce:"?"===s[1]?he:"@"===s[1]?pe:de}),r.removeAttribute(e)}else e.startsWith(N)&&(o.push({type:6,index:a}),r.removeAttribute(e));if(J.test(r.tagName)){const e=r.textContent.split(N),t=e.length-1;if(t>0){r.textContent=T?T.emptyScript:"";for(let i=0;i<t;i++)r.append(e[i],W()),re.nextNode(),o.push({type:2,index:++a});r.append(e[t],W())}}}else if(8===r.nodeType)if(r.data===P)o.push({type:2,index:a});else{let e=-1;for(;-1!==(e=r.data.indexOf(N,e+1));)o.push({type:7,index:a}),e+=N.length-1}a++}}static createElement(e,t){const i=F.createElement("template");return i.innerHTML=e,i}}function se(e,t,i=e,r){if(t===ee)return t;let a=void 0!==r?i._$Co?.[r]:i._$Cl;const n=j(t)?void 0:t._$litDirective$;return a?.constructor!==n&&(a?._$AO?.(!1),void 0===n?a=void 0:(a=new n(e),a._$AT(e,i,r)),void 0!==r?(i._$Co??=[])[r]=a:i._$Cl=a),void 0!==a&&(t=se(e,a._$AS(e,t.values),a,r)),t}class oe{constructor(e,t){this._$AV=[],this._$AN=void 0,this._$AD=e,this._$AM=t}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(e){const{el:{content:t},parts:i}=this._$AD,r=(e?.creationScope??F).importNode(t,!0);re.currentNode=r;let a=re.nextNode(),n=0,s=0,o=i[0];for(;void 0!==o;){if(n===o.index){let t;2===o.type?t=new le(a,a.nextSibling,this,e):1===o.type?t=new o.ctor(a,o.name,o.strings,this,e):6===o.type&&(t=new ue(a,this,e)),this._$AV.push(t),o=i[++s]}n!==o?.index&&(a=re.nextNode(),n++)}return re.currentNode=F,r}p(e){let t=0;for(const i of this._$AV)void 0!==i&&(void 0!==i.strings?(i._$AI(e,i,t),t+=i.strings.length-2):i._$AI(e[t])),t++}}class le{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(e,t,i,r){this.type=2,this._$AH=te,this._$AN=void 0,this._$AA=e,this._$AB=t,this._$AM=i,this.options=r,this._$Cv=r?.isConnected??!0}get parentNode(){let e=this._$AA.parentNode;const t=this._$AM;return void 0!==t&&11===e?.nodeType&&(e=t.parentNode),e}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(e,t=this){e=se(this,e,t),j(e)?e===te||null==e||""===e?(this._$AH!==te&&this._$AR(),this._$AH=te):e!==this._$AH&&e!==ee&&this._(e):void 0!==e._$litType$?this.$(e):void 0!==e.nodeType?this.T(e):(e=>I(e)||"function"==typeof e?.[Symbol.iterator])(e)?this.k(e):this._(e)}O(e){return this._$AA.parentNode.insertBefore(e,this._$AB)}T(e){this._$AH!==e&&(this._$AR(),this._$AH=this.O(e))}_(e){this._$AH!==te&&j(this._$AH)?this._$AA.nextSibling.data=e:this.T(F.createTextNode(e)),this._$AH=e}$(e){const{values:t,_$litType$:i}=e,r="number"==typeof i?this._$AC(e):(void 0===i.el&&(i.el=ne.createElement(ae(i.h,i.h[0]),this.options)),i);if(this._$AH?._$AD===r)this._$AH.p(t);else{const e=new oe(r,this),i=e.u(this.options);e.p(t),this.T(i),this._$AH=e}}_$AC(e){let t=ie.get(e.strings);return void 0===t&&ie.set(e.strings,t=new ne(e)),t}k(e){I(this._$AH)||(this._$AH=[],this._$AR());const t=this._$AH;let i,r=0;for(const a of e)r===t.length?t.push(i=new le(this.O(W()),this.O(W()),this,this.options)):i=t[r],i._$AI(a),r++;r<t.length&&(this._$AR(i&&i._$AB.nextSibling,r),t.length=r)}_$AR(e=this._$AA.nextSibling,t){for(this._$AP?.(!1,!0,t);e!==this._$AB;){const t=H(e).nextSibling;H(e).remove(),e=t}}setConnected(e){void 0===this._$AM&&(this._$Cv=e,this._$AP?.(e))}}class de{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(e,t,i,r,a){this.type=1,this._$AH=te,this._$AN=void 0,this.element=e,this.name=t,this._$AM=r,this.options=a,i.length>2||""!==i[0]||""!==i[1]?(this._$AH=Array(i.length-1).fill(new String),this.strings=i):this._$AH=te}_$AI(e,t=this,i,r){const a=this.strings;let n=!1;if(void 0===a)e=se(this,e,t,0),n=!j(e)||e!==this._$AH&&e!==ee,n&&(this._$AH=e);else{const r=e;let s,o;for(e=a[0],s=0;s<a.length-1;s++)o=se(this,r[i+s],t,s),o===ee&&(o=this._$AH[s]),n||=!j(o)||o!==this._$AH[s],o===te?e=te:e!==te&&(e+=(o??"")+a[s+1]),this._$AH[s]=o}n&&!r&&this.j(e)}j(e){e===te?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,e??"")}}class ce extends de{constructor(){super(...arguments),this.type=3}j(e){this.element[this.name]=e===te?void 0:e}}class he extends de{constructor(){super(...arguments),this.type=4}j(e){this.element.toggleAttribute(this.name,!!e&&e!==te)}}class pe extends de{constructor(e,t,i,r,a){super(e,t,i,r,a),this.type=5}_$AI(e,t=this){if((e=se(this,e,t,0)??te)===ee)return;const i=this._$AH,r=e===te&&i!==te||e.capture!==i.capture||e.once!==i.once||e.passive!==i.passive,a=e!==te&&(i===te||r);r&&this.element.removeEventListener(this.name,this,i),a&&this.element.addEventListener(this.name,this,e),this._$AH=e}handleEvent(e){"function"==typeof this._$AH?this._$AH.call(this.options?.host??this.element,e):this._$AH.handleEvent(e)}}class ue{constructor(e,t,i){this.element=e,this.type=6,this._$AN=void 0,this._$AM=t,this.options=i}get _$AU(){return this._$AM._$AU}_$AI(e){se(this,e)}}const ge={I:le},me=M.litHtmlPolyfillSupport;me?.(ne,le),(M.litHtmlVersions??=[]).push("3.3.3");const _e=globalThis;let fe=class extends V{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){const e=super.createRenderRoot();return this.renderOptions.renderBefore??=e.firstChild,e}update(e){const t=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(e),this._$Do=((e,t,i)=>{const r=i?.renderBefore??t;let a=r._$litPart$;if(void 0===a){const e=i?.renderBefore??null;r._$litPart$=a=new le(t.insertBefore(W(),e),e,void 0,i??{})}return a._$AI(e),a})(t,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return ee}};fe._$litElement$=!0,fe.finalized=!0,_e.litElementHydrateSupport?.({LitElement:fe});const ve=_e.litElementPolyfillSupport;ve?.({LitElement:fe}),(_e.litElementVersions??=[]).push("4.2.2");const we=e=>(t,i)=>{void 0!==i?i.addInitializer(()=>{customElements.define(e,t)}):customElements.define(e,t)},ye={attribute:!0,type:String,converter:z,reflect:!1,hasChanged:E},be=(e=ye,t,i)=>{const{kind:r,metadata:a}=i;let n=globalThis.litPropertyMetadata.get(a);if(void 0===n&&globalThis.litPropertyMetadata.set(a,n=new Map),"setter"===r&&((e=Object.create(e)).wrapped=!0),n.set(i.name,e),"accessor"===r){const{name:r}=i;return{set(i){const a=t.get.call(this);t.set.call(this,i),this.requestUpdate(r,a,e,!0,i)},init(t){return void 0!==t&&this.C(r,void 0,e,t),t}}}if("setter"===r){const{name:r}=i;return function(i){const a=this[r];t.call(this,i),this.requestUpdate(r,a,e,!0,i)}}throw Error("Unsupported decorator location: "+r)};function $e(e){return(t,i)=>"object"==typeof i?be(e,t,i):((e,t,i)=>{const r=t.hasOwnProperty(i);return t.constructor.createProperty(i,e),r?Object.getOwnPropertyDescriptor(t,i):void 0})(e,t,i)}function ke(e){return $e({...e,state:!0,attribute:!1})}const xe=1,Ae=2,Ce=3,ze=4,Ee=e=>(...t)=>({_$litDirective$:e,values:t});let Se=class{constructor(e){}get _$AU(){return this._$AM._$AU}_$AT(e,t,i){this._$Ct=e,this._$AM=t,this._$Ci=i}_$AS(e,t){return this.update(e,t)}update(e,t){return this.render(...t)}};const{I:Ve}=ge,Me=e=>e,He=()=>document.createComment(""),Te=(e,t,i)=>{const r=e._$AA.parentNode,a=void 0===t?e._$AB:t._$AA;if(void 0===i){const t=r.insertBefore(He(),a),n=r.insertBefore(He(),a);i=new Ve(t,n,e,e.options)}else{const t=i._$AB.nextSibling,n=i._$AM,s=n!==e;if(s){let t;i._$AQ?.(e),i._$AM=e,void 0!==i._$AP&&(t=e._$AU)!==n._$AU&&i._$AP(t)}if(t!==a||s){let e=i._$AA;for(;e!==t;){const t=Me(e).nextSibling;Me(r).insertBefore(e,a),e=t}}}return i},Le=(e,t,i=e)=>(e._$AI(t,i),e),De={},Ne=(e,t=De)=>e._$AH=t,Pe=e=>{e._$AR(),e._$AA.remove()},Oe=Ee(class extends Se{constructor(e){if(super(e),e.type!==Ce&&e.type!==xe&&e.type!==ze)throw Error("The `live` directive is not allowed on child or event bindings");if(!(e=>void 0===e.strings)(e))throw Error("`live` bindings can only contain a single expression")}render(e){return e}update(e,[t]){if(t===ee||t===te)return t;const i=e.element,r=e.name;if(e.type===Ce){if(t===i[r])return ee}else if(e.type===ze){if(!!t===i.hasAttribute(r))return ee}else if(e.type===xe&&i.getAttribute(r)===t+"")return ee;return Ne(e),t}}),Fe=Symbol.for(""),We=e=>{if(e?.r===Fe)return e?._$litStatic$},je=(e,...t)=>({_$litStatic$:t.reduce((t,i,r)=>t+(e=>{if(void 0!==e._$litStatic$)return e._$litStatic$;throw Error(`Value passed to 'literal' function must be a 'literal' result: ${e}. Use 'unsafeStatic' to pass non-literal values, but\n            take care to ensure page security.`)})(i)+e[r+1],e[0]),r:Fe}),Ie=new Map,Re=(e=>(t,...i)=>{const r=i.length;let a,n;const s=[],o=[];let l,d=0,c=!1;for(;d<r;){for(l=t[d];d<r&&void 0!==(n=i[d],a=We(n));)l+=a+t[++d],c=!0;d!==r&&o.push(n),s.push(l),d++}if(d===r&&s.push(t[r]),c){const e=s.join("$$lit$$");void 0===(t=Ie.get(e))&&(s.raw=s,Ie.set(e,t=s)),i=o}return e(t,...i)})(X),Be=["on_off_entity","current","actions"],Ue=["manual","charging_stopped","car_disconnected"];function qe(e){return"object"==typeof e&&null!==e&&"code"in e&&"message"in e}function Ge(e){return qe(e)?e.message:String(e)}let Ke=class extends fe{constructor(){super(...arguments),this.open=!1,this.heading="",this.text="",this.confirmText="",this.cancelText="",this.confirmed=!1}render(){return X`
      <ha-dialog .open=${this.open} .headerTitle=${this.heading} @closed=${this.closed}>
        <p>${this.text}</p>
        <div slot="footer">
          <ha-button appearance="plain" @click=${this.cancel}>${this.cancelText}</ha-button>
          <ha-button variant="danger" @click=${this.confirm}>${this.confirmText}</ha-button>
        </div>
      </ha-dialog>
    `}confirm(){this.confirmed=!0,this.open=!1}cancel(){this.open=!1}closed(e){e.stopPropagation();const t=this.confirmed?"confirm":"cancel";this.confirmed=!1,this.open=!1,this.dispatchEvent(new CustomEvent(t))}};e([$e({type:Boolean})],Ke.prototype,"open",void 0),e([$e()],Ke.prototype,"heading",void 0),e([$e()],Ke.prototype,"text",void 0),e([$e()],Ke.prototype,"confirmText",void 0),e([$e()],Ke.prototype,"cancelText",void 0),Ke=e([we("kraftvakt-confirm-dialog")],Ke);let Ze=class extends fe{constructor(){super(...arguments),this.running=!1,this.appearance="plain",this.disabled=!1,this.changing=!1}render(){return this.running?X`
          <ha-button variant="danger" appearance=${this.appearance} .disabled=${this.disabled||this.changing} @click=${this.toggle}>
            <ha-svg-icon slot="start" .path=${"M18,18H6V6H18V18Z"}></ha-svg-icon>
            ${this.localize("status.stop")}
          </ha-button>
        `:X`
          <ha-button .disabled=${this.disabled||this.changing} @click=${this.toggle}>
            <ha-svg-icon slot="start" .path=${"M8,5.14V19.14L19,12.14L8,5.14Z"}></ha-svg-icon>
            ${this.localize("status.start")}
          </ha-button>
        `}async toggle(){this.changing=!0,this.fireError(void 0);try{await(e=this.hass,t=!this.running,e.callWS({type:"kraftvakt/regulation/set_running",running:t}))}catch(e){this.fireError(qe(e)&&"config_incomplete"===e.code?this.localize("status.start_refused"):this.localize("panel.error",{message:Ge(e)}))}finally{this.changing=!1}var e,t}fireError(e){this.dispatchEvent(new CustomEvent("running-error",{detail:e}))}static{this.styles=g`
    ha-button::part(base) {
      white-space: nowrap;
    }
  `}};e([$e({attribute:!1})],Ze.prototype,"hass",void 0),e([$e({attribute:!1})],Ze.prototype,"localize",void 0),e([$e({type:Boolean})],Ze.prototype,"running",void 0),e([$e()],Ze.prototype,"appearance",void 0),e([$e({type:Boolean})],Ze.prototype,"disabled",void 0),e([ke()],Ze.prototype,"changing",void 0),Ze=e([we("kraftvakt-running-button")],Ze);let Je=class extends fe{constructor(){super(...arguments),this.narrow=!1}render(){return X`
      <ha-alert alert-type="warning" .title=${this.localize("locked.title")} .narrow=${this.narrow}>
        <ha-svg-icon slot="icon" .path=${"M12,17A2,2 0 0,0 14,15C14,13.89 13.1,13 12,13A2,2 0 0,0 10,15A2,2 0 0,0 12,17M18,8A2,2 0 0,1 20,10V20A2,2 0 0,1 18,22H6A2,2 0 0,1 4,20V10C4,8.89 4.9,8 6,8H7V6A5,5 0 0,1 12,1A5,5 0 0,1 17,6V8H18M12,3A3,3 0 0,0 9,6V8H15V6A3,3 0 0,0 12,3Z"}></ha-svg-icon>
        ${this.localize("locked.text")} ${this.error?X`<div class="error">${this.error}</div>`:te}
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
  `}};e([$e({attribute:!1})],Je.prototype,"hass",void 0),e([$e({attribute:!1})],Je.prototype,"localize",void 0),e([$e({type:Boolean})],Je.prototype,"narrow",void 0),e([ke()],Je.prototype,"error",void 0),Je=e([we("kraftvakt-locked-banner")],Je);let Qe=class extends fe{constructor(){super(...arguments),this.errorCount=0,this.saving=!1}render(){const e=this.errorCount>0?this.localize("config.fix_before_saving"):this.message;return X`
      <div class="bar" role="region" aria-label=${this.localize("config.unsaved")}>
        <div class="text">
          <div class="title">${this.localize("config.unsaved")}</div>
          ${e?X`<div class="error">${e}</div>`:te}
        </div>
        <ha-button appearance="plain" .disabled=${this.saving} @click=${()=>this.fire("discard")}> ${this.localize("config.discard")} </ha-button>
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
  `}};e([$e({attribute:!1})],Qe.prototype,"localize",void 0),e([$e({type:Number})],Qe.prototype,"errorCount",void 0),e([$e({type:Boolean})],Qe.prototype,"saving",void 0),e([$e()],Qe.prototype,"message",void 0),Qe=e([we("kraftvakt-save-bar")],Qe);const Xe="draft-changed";function Ye(){const e=crypto.getRandomValues(new Uint8Array(6));return Array.from(e,e=>e.toString(16).padStart(2,"0")).join("")}function et(e,t,i){const r=[...e],[a]=r.splice(t,1);return r.splice(i,0,a),r}function tt(e){return"charger_group"===e.type?`group/${e.group_id}`:`${e.appliance_id}/${e.variant_id??""}`}function it(e){const t=function(e){const t=e.appliances.flatMap(e=>[{type:"appliance",appliance_id:e.id,variant_id:null},...e.variants.map(t=>({type:"appliance",appliance_id:e.id,variant_id:t.id}))]);return t.push(...e.charger_groups.map(e=>({type:"charger_group",group_id:e.id}))),t}(e),i=new Set(t.map(tt)),r=new Set,a=e.priority.filter(e=>{const t=tt(e);return!(!i.has(t)||r.has(t))&&(r.add(t),!0)}),n=t.filter(e=>!r.has(tt(e))),s=new Set(e.appliances.filter(e=>e.essential).map(e=>e.id)),o=e=>"appliance"===e.type&&s.has(e.appliance_id),l=[...a,...n];return{...e,priority:[...l.filter(o),...l.filter(e=>!o(e))]}}function rt(e){return e.charger_groups.flatMap(e=>e.chargers)}const at={en:{panel:{title:"Kraftvakt",not_loaded:"Kraftvakt is not loaded. Check the integration under Settings → Devices & services.",error:"Something went wrong: {message}"},tabs:{status:"Status",general:"General",appliances:"Appliances",charging:"EV charging",advanced:"Advanced",diagnostics:"Diagnostics"},status:{regulation:"Regulation",running:"Running",stopped:"Stopped",start:"Start regulation",stop:"Stop regulation",stopped_info:"The regulation is stopped, and all regulated appliances and EV chargers are turned off. The configuration can be changed. When the regulation starts, the appliances are turned on again one by one.",incomplete_title:"The configuration is not complete",start_refused:"The regulation cannot start before the configuration is complete.",safe_state_title:"Safe state",safe_state_text:"The power sensor {sensor} gives no valid measurement. All regulated appliances and EV chargers are turned off. The regulation starts again by itself when the sensor gives a valid value again.",penalty_title:"Penalty period",penalty_text:"The tariff average has been above the power limit. All regulated appliances and EV chargers are kept off until the overconsumption is recovered.",overconsumption_left:"Overconsumption left: {energy} kWh",recovery_started:"recovery has started",recovery_not_started:"recovery has not started",regulation_average:"Regulation average",tariff_average:"Tariff average",average_over_seconds:"over {seconds} s",average_over_hour:"over 1 hour",power_now:"Consumption now",momentary:"momentary value",power_limit:"Power limit",safe_state_chip:"Safe state",safe_state_back_text:"The power sensor {sensor} gives a valid value again. The regulation starts again with everything off at the next decision.",penalty_chip:"Penalty period",next_decision:"Next decision",next_decision_at:"Next decision at {time}",appliances_and_chargers:"Appliances and EV chargers",power:"Power",temperature:"Temperature",no_chargers:"No EV chargers in the group.",no_appliances:"No appliances are configured.",on:"On",off:"Off",activated:"Activated",deactivated:"Deactivated",waiting_ends_at:"Turns on at the decision at {time}",power_to_free_turn_on:"{power} kW must be freed before it is turned on",power_to_free_activate:"{power} kW must be freed before the EV charger is activated",power_to_free_ampere:"{power} kW must be freed before the EV charger gets one more ampere",delayed_turn_on:"Delayed turn-on",damping:"Damping of current changes",damping_ampere_at:"One more ampere at the decision at {time}",start_delay:"Start delay",start_delay_ends_at:"Nothing below it is turned on before the decision at {time}",delayed_activation:"Delayed activation",activated_at:"Activated at the decision at {time}",charging_at:"Charging at {current} A",first_decision:"Waiting for the first decision",bypassed_no_car:"Bypassed: no car connected",waiting_charger:"Queued: another EV charger in the group has its turn",starting_until:"Waiting until {time} for the car to start charging. Nothing below it is turned on until then.",excluded:"Excluded from the regulation",outside_window:"Outside the charging window ({start}–{end})",amperes:"{current} A",chargers_charging:"{charging} of {total} EV chargers are charging",activated_not_charging:"Activated: the car does not use power, so it waits at the minimum current",window_overridden:"The charging window is overridden",chip_charging:"Charging",chip_no_car:"Car disconnected",chip_queued:"Queued",chip_starting:"Starting",chip_excluded:"Excluded",chip_window:"{start}–{end}",chip_override:"Override",chip_stopped:"Stopped",regulation_stopped:"The regulation is stopped, so the EV charger is deactivated",chip_first_decision:"First decision",chip_fault:"Fault",fault:"A fault flag shows a fault, so the EV charger is deactivated until the fault clears",free_power:"{power} kW ({share}) free",power_runs_out:"The power runs out here. What is below waits for free power.",queued_for_room:"Queued: waiting for room beside the EV chargers that charge",queued_waiting_time:"Queued: next in turn, after its waiting time"},diagnostics:{power_sensor:"Power sensor",valid:"Valid",not_valid:"No valid value",update_interval:"Update interval",stored_interval:"Stored update interval",reports_every:"Reports every {seconds} s",seconds:"{seconds} s",regulation_window:"Regulation window",window_updates:"{seconds} s ({updates} × {interval} s)",last_missed_windows:"Last missed windows",none:"None",actions:"Actions",failed_count:"{count} failed",last_failed:"Last failed",commands_waiting:"Commands waiting",action_timeout:"Action timeout",running_for:"Running for {duration}",started:"Started",yes:"Yes",no:"No",overconsumption:"Overconsumption",watt_hours:"{energy} Wh",command_repeat:"Command repeat",next_at:"Next at {time}",timeline:"Timeline",minutes:"{minutes} min",consumption:"Consumption",waiting:"Waiting",waiting_time:"Waiting time",damping:"Damping",start_delay:"Start delay",not_known:"Not known",oldest_decision:"Oldest decision kept",chart_label:"Consumption, regulation average, tariff average and power limit over the last hour",lanes_label:"What each appliance and EV charger was set to, in priority order",now:"now",decision_at:"Decision at {time}",no_decision_kept:"No decision kept",event_log:"Event log",filter_all:"All",filter_commands:"Commands",filter_failed:"Failed actions",no_events:"No commands or failed actions are kept.",log_kept:"The commands of the decisions kept, and the last failed actions. Kept until Home Assistant restarts or the integration is reloaded.",download:"Download diagnostics on the integration's page",kind_on:"On",kind_off:"Off",kind_current:"Current",kind_failed:"Failed",error:"Error",power_sensor_valid:"Power sensor valid",commands:"Commands",turn_on:"Turn on {name}",turn_off:"Turn off {name}",activate:"Activate {name}",deactivate:"Deactivate {name}",set_current:"{name} at {current} A"},missing:{missing_power_sensor:"The power sensor is not chosen.",missing_regulation_window:"The regulation window is not set.",missing_device:"{item}: the device is not chosen.",missing_entity:"{item}: the switch or thermostat is not chosen.",missing_on_off_entity:"{item}: the switch that turns charging on and off is not chosen.",missing_action:"{item}: the action to {action} is missing.",missing_condition:"{item}: the expression is missing.",missing_car_connected:"{item}: «car connected» is missing.",missing_fault_flag:"{item}: «fault flag» is missing.",unknown:"{item}: {code}",appliance_without_entity:"An appliance without a switch or thermostat",charger_without_device:"An EV charger without a device",actions:{turn_on:"turn it on",turn_off:"turn it off",activate:"activate it",deactivate:"deactivate it",set_current:"set the charging current"},missing_charging_power:"{item}: «charging power» is missing."},config:{save:"Save",restore_defaults:"Restore defaults",discard:"Discard",unsaved:"Unsaved changes",fix_before_saving:"Fix the marked settings before saving.",not_saved:"The configuration was not saved. Fix the marked settings.",save_refused_running:"The configuration cannot be saved while the regulation runs.",leave_title:"Discard unsaved changes?",leave_text:"The changes on the configuration pages are not saved. They are lost if you leave.",stay:"Keep editing",leave:"Discard changes"},locked:{title:"The configuration is locked",text:"The regulation runs. Stop the regulation to change the configuration. When the regulation stops, all regulated appliances and EV chargers are turned off."},warning:{appliances_title:"Do not turn regulated appliances on or off outside Kraftvakt",chargers_title:"Do not turn EV chargers on or off outside Kraftvakt",text:"It disturbs the regulation, and Kraftvakt sets them back. Turn on the switch «excluded from regulation» for one you want to control yourself."},errors:{required:"Required.",fault_flag_required:"Choose a fault flag, or turn the setting off.",out_of_range:"Must be between {min} and {max}.",at_least:"Must be at least {min}.",invalid_resolution:"Must be a multiple of {resolution}.",not_integer:"Must be a whole number.",invalid_entity_id:"Not a valid entity ID.",empty_label:"The label cannot be empty.",duplicate_label:"The label must be unique for the appliance.",empty_name:"The name cannot be empty.",duplicate_name:"The name is already used by another group.",min_current_above_max:"The minimum current cannot be above the maximum current.",invalid_time:"Give both start and end.",window_start_equals_end:"Start and end cannot be the same.",duplicate_entity:"The entity is already used by another appliance or EV charger.",unknown_device:"The device no longer exists in Home Assistant.",entity_not_on_device:"The entity does not belong to the device of the EV charger, or to the device of the appliance's switch.",invalid_action:"Home Assistant cannot read the action.",invalid_template:"The template has a syntax error.",default_action_unavailable:"The entity has no standard action. Choose custom actions.",unsupported_entity_domain:"This type of entity cannot be used here. Choose one from the list.",domain_action_unavailable:"The action is not available for the entity. Choose another action.",unsupported_option:"The entity does not support this value.",outside_entity_range:"Outside the range of the entity.",unknown:"Invalid value ({code}).",current_off_unsupported:"The entity cannot be set to 0 A, which stops an EV charger turned on and off by the current.",essential_with_variants:"An essential appliance cannot have variants. Delete them, or turn the setting off.",essential_with_power_reserve:"An essential appliance has no power reserve. Turn the setting off, or turn off Fixed load first.",essential_not_at_top:"An essential appliance must be above every other entry in the priority list.",not_a_thermostat:"Choose a thermostat, a climate entity."},dialog:{ok:"OK",cancel:"Cancel",close:"Close"},general:{measurement:"Measurement",regulation:"Regulation",penalty:"Penalty",window_option_one:"1 update ({seconds} s)",window_option:"{count} updates ({seconds} s)",window_no_power_sensor:"Choose the power sensor first.",window_measuring:"Measuring how often the power sensor reports. It can take up to 30 seconds.",window_not_measured:"Could not find how often the power sensor reports. Choose it again when it reports regularly.",window_too_seldom:"The power sensor reports every {interval} s, too seldom for a regulation window of at most {max} s.",fields:{power_sensor:{label:"Power sensor",helper:"The power the whole house uses, usually from the HAN port of the electricity meter."},regulation_window_updates:{label:"Regulation window",helper:"A longer window evens out short peaks, a shorter one reacts faster. {min}–{max} s."},power_sensor_interval_s:{label:"Update interval of the power sensor"},power_limit_w:{label:"Power limit",helper:"The step in the capacity tariff you want to stay below. {min}–{max} W, default {default} W."},turn_on_margin_w:{label:"Turn-on margin",helper:"How far below the power limit consumption must be before anything is turned on. A larger margin means less switching. {min}–{max} W, default {default} W."},wait_at_limit_s:{label:"Waiting time at the power limit",helper:"How long an appliance waits before it is turned on when consumption is close to the power limit. {min}–{max} s, default {default} s."},penalty_threshold_w:{label:"Penalty threshold",helper:"How far the consumption over the last hour may go above the power limit before everything is turned off until the overconsumption is paid back. {min}–{max} W, default {default} W."},wait_curve_steepness:{label:"Steepness"},wait_curve_pivot:{label:"Pivot point"},appliance_repeat_increment_factor:{label:"Increase each time",helper:"Share of the waiting time at the power limit. Default × {default}."},appliance_repeat_increments:{label:"Most increases",helper:"{min}–{max}, default {default}."},ampere_damping_s:{label:"Damping time",helper:"How long an EV charger waits before it gets back an ampere it lost. Longer gives steadier consumption, shorter more charging. {min}–{max} s, default {default} s."},charger_waiting_factor:{label:"Waiting time for EV chargers",helper:"How many times longer than an appliance an EV charger waits before it is activated again. {min}×–{max}×, default {default}×."},command_repeat_interval_min:{label:"Repeat the command after",helper:"{min}–{max} min, default {default} min."},action_timeout_s:{label:"Action timeout",helper:"An action that takes longer is stopped. {min}–{max} s, default {default} s."},power_sensor_timeout_s:{label:"Power sensor timeout",helper:"When the power sensor has not reported for this long, everything is turned off until it is back. {min}–{max} s, default {default} s."}},penalty_info:"A safety valve for when consumption gets far above the power limit, for example when something outside Kraftvakt is turned on."},advanced:{wait_curve:"Waiting time curve",wait_curve_info:"How long an appliance waits, by how much power is free. The actual waiting time is rounded up to the next decision.",free_power_kw:"Free power kW",waiting_minutes:"Waiting time min:s",actual_waiting_minutes:"Actual waiting time min:s",repeated_turn_on:"Waiting time on repeated turn-on",repeated_turn_on_info:"The waiting time grows when the same appliance is turned on again and again. The first two times follow the curve, shown at the pivot point.",turn_on_in_a_row:"Turn-on in a row",chargers:"EV chargers",chargers_info:"Keeps an EV charger from going up and down, or on and off, when consumption changes for a short moment.",command_repeat:"Command repeat",command_repeat_info:"Sets appliances and EV chargers back if they have changed by themselves, for example after a power cut.",timeouts:"Timeouts",timeouts_info:"Guards against actions that never finish and a power sensor that stops reporting."},list:{drag:"Drag to change the order",edit:"Edit",view:"Show"},appliances:{priority_title:"Priority list",priority_sub:"Highest priority at the top. Drag to change the order.",add:"Add appliance",empty:"No appliances yet. Add the ones Kraftvakt shall turn on and off.",charger_group_sub:"EV chargers: {count} · configured under",power_reserve:"power reserve {power} W",essential:"Essential",variant_count:"variants: {count}",variant_entity:"Variant · {entity}",variant_template:"Variant · custom template",variant_own_actions:"own actions",variant_own_turn_on:"own action to turn on",variant_own_turn_off:"own action to turn off"},appliance:{add_title:"Add appliance",edit_title:"Edit appliance",view_title:"Appliance",variants:"Variants",variants_info:"Gives the appliance another place in the priority list while the expression is true, for example higher up for the water heater in the morning. The top variant that applies is used.",add_variant:"Add variant",display_values:"Display values",display_values_info:"Optional. Shown only on the status page.",delete:"Delete appliance",fields:{entity_id:{label:"Switch or thermostat",helper:"What Kraftvakt turns on and off, for example the switch of the water heater."},essential:{label:"Essential appliance",helper:"For an appliance that must always run, such as a freezer. Cannot have variants."},turn_on:{label:"Action to turn on",helper:"Standard works for most."},turn_off:{label:"Action to turn off",helper:"Standard works for most."},fixed_load:{label:"Fixed load",helper:"For an appliance that always uses the same power while it is on, such as a ceiling fan. It is turned on without waiting when enough power is free. Not for one with a thermostat or other control of its own."},power_reserve_w:{label:"Power reserve",helper:"What the appliance uses while it is on. Applies to every variant."},label:{label:"Label"},condition:{label:"Expression"},override_turn_on:{label:"Own action to turn on",helper:"For example another HVAC mode."},override_turn_off:{label:"Own action to turn off",helper:"For example frost protection."},display_power:{label:"Power"},display_temperature:{label:"Temperature"}}},variant:{edit_title:"Edit variant {name}",view_title:"Variant {name}",condition:"Expression",delete:"Delete variant",condition_info:"The variant applies while the expression is true, for example between 05 and 08."},action:{default:"Standard",custom:"Custom actions",entity:"Number entity",domain_actions:{climate_hvac_mode:"HVAC mode",climate_temperature:"Temperature",climate_hvac_mode_and_temperature:"HVAC mode and temperature"},default_runs:"Runs {service} for the entity.",entity_runs:"Runs {service} for the chosen entity with the current as value.",no_default:"This type of entity has no standard action. Use custom actions.",choose_entity:"Choose the entity to use the standard action.",choose_action_entity:"Choose the number entity that gets the charging current.",variables:"Variables: {variables}.",parameters:{hvac_mode:"HVAC mode",temperature:"Target temperature",temperature_from:"Target temperature from",temperature_entity:"Sensor, number or thermostat",temperature_reading:"Temperature of the thermostat"},readings:{target_temperature:"Set temperature",current_temperature:"Current temperature"},value_from:{number:"Fixed value",source:"Sensor, number or thermostat",template:"Custom template"},parameter_range:"{min}–{max} {unit} for the entity.",source_now:"Now: {value}.",source_no_value:"No temperature now: the action fails while it has none.",source_read:"Read when the action runs.",source_range:"Read when the action runs, and kept within {min}–{max} {unit}."},condition:{entity:"Binary sensor or switch",template:"Custom template",entity_label:"Binary sensor or switch",template_label:"Custom template",entity_helper:"True while it is on.",state:"Status sensor",state_label:"Status sensor",state_helper:"For example a sensor that shows the status of the EV charger.",states_label:"States",states_helper:"Choose or type the states.",template_helper:"Should give true or false. Variables: {variables}.",now:"Now: {value}",true:"true",false:"false",error:"Error: {message}",invalid:"The template gives {value}, not true or false, so it counts as false."},one_at_a_time:{entity:"Binary sensor or switch",template:"Custom template",entity_label:"Binary sensor or switch",template_label:"Custom template",entity_helper:"One EV charger at a time while it is on.",template_helper:"True gives one EV charger at a time, for example {{ power_limit < 15000 }}. Variables: {variables}.",true:"one at a time",false:"several at once",invalid:"The template gives {value}, not true or false, so the EV chargers charge several at once."},actively_charging:{type_label:"Car charging from",entity:"Binary sensor or switch",template:"Custom template",entity_label:"Binary sensor or switch",template_label:"Custom template",entity_helper:"On while the car charges.",state:"Status sensor",state_label:"Status sensor",state_helper:"For example a sensor that shows the status of the EV charger.",states_label:"States",states_helper:"Choose or type the states.",template_helper:"True while the car charges. Variables: {variables}.",true:"charging",false:"not charging",invalid:"The template gives {value}, not true or false, so it counts as not charging."},charging_power:{type_label:"Charging power from",power_sensor:"Power sensor",template:"Custom template",power_sensor_label:"Power sensor",template_label:"Custom template for charging power",power_sensor_helper:"What the car charges with now.",template_helper:"The power in W. Variables: {variables}.",true:"charging",false:"not charging",invalid:"The template gives {value}, not a number, so it counts as not charging."},display_power:{type_label:"Power from",power_sensor:"Power sensor",template:"Custom template",power_sensor_label:"Power sensor",template_label:"Custom template for power",power_sensor_helper:"A sensor of the same device as the switch or thermostat.",template_helper:"The power in W, also from another device. Variables: {variables}.",no_value:"no value",invalid:"The template gives {value}, not a number, so nothing is shown."},display_temperature:{type_label:"Temperature from",temperature_sensor:"Sensor or thermostat",template:"Custom template",current_temperature:"{name}: current temperature",target_temperature:"{name}: set temperature",temperature_sensor_label:"Temperature sensor or thermostat",template_label:"Custom template for temperature",temperature_sensor_helper:"From the same device as the switch or thermostat.",template_helper:"The temperature in the unit of Home Assistant, also from another device. Variables: {variables}.",no_value:"no value",invalid:"The template gives {value}, not a number, so nothing is shown."},fault:{entity:"Binary sensor or switch",template:"Custom template",entity_label:"Binary sensor or switch",template_label:"Custom template",entity_helper:"On means a fault.",state:"Status sensor",state_label:"Status sensor",state_helper:"For example a sensor that shows the status of the EV charger.",states_label:"States",states_helper:"Choose or type the states.",template_helper:"True means a fault. Variables: {variables}.",true:"fault",false:"no fault",invalid:"The template gives {value}, not true or false, so it counts as no fault."},charging:{name:"Name",name_sub:"Shown in the priority list and on the status page.",one_at_a_time:"Restrict to one EV charger at a time",one_at_a_time_sub:"Only one car in the group charges at a time, so it is full sooner.",one_at_a_time_always:"Always",one_at_a_time_never:"Never",one_at_a_time_condition:"While an expression is true",one_at_a_time_applies:"Applies",dynamic_order:"Dynamic charging order",dynamic_order_sub:"Cars that charge keep charging, and the others wait their turn.",needs_two_chargers:"Applies only with two or more EV chargers in the group.",chargers:"Charging priority",chargers_sub:"Highest priority at the top. Drag an EV charger to another group to move it.",add:"Add EV charger",empty:"No EV chargers yet.",no_groups:"No groups of EV chargers yet. Add a group, and then its EV chargers.",add_group:"Add group",new_group_name:"EV chargers",unnamed_group:"Group without a name",delete_group:"Delete group",delete_group_not_empty:"Move or delete its EV chargers to delete the group.",switches_info:"While the regulation runs, you can control each EV charger with the switches «‹charger› excluded from regulation», «‹charger› override charging window» and «‹charger› charge until car disconnected».",currents:"{min}–{max} A ({power} W at {min} A)",window:"charging window {start}–{end}",charges_until_disconnected:"charges until the car is disconnected",deactivated_on_fault:"deactivated on fault"},charger:{add_title:"Add EV charger",edit_title:"Edit EV charger",view_title:"EV charger",charging_current:"Charging current",start:"Charging start",start_info:"How long the car may take to start charging after the EV charger is activated.",on_off:"Turn charging on and off",on_off_info:"How Kraftvakt activates and deactivates the EV charger.",switched_by_current_info:"Choose the entity or action that sets the current under Charging current. It must take 0 A.",profile_applied:"Filled in from the charger profile {profile}. Check every field before you save.",override_ends:{manual:"When I turn it off",charging_stopped:"When the car no longer charges",car_disconnected:"When the car is disconnected"},delete:"Delete EV charger",fields:{device_id:{label:"Device",helper:"The EV charger in Home Assistant. When Kraftvakt knows the charger, the fields below are filled in."},switched_by:{label:""},on_off_entity:{label:"Switch that allows charging",helper:"Turned on to activate the EV charger and off to deactivate it."},activate:{label:"Action to activate"},deactivate:{label:"Action to deactivate"},min_current_a:{label:"Minimum charging current"},max_current_a:{label:"Maximum charging current"},set_current:{label:"Set charging current"},min_current_power_w:{label:"Power at minimum current",helper:"What the car uses at the minimum current, about 1,400 W on one phase. {min}–{max} W, default {default} W, 6 A on three phases."},car_connected:{label:"Car connected",helper:"Tells whether a car is connected to the EV charger."},actively_charging:{label:"Actively charging",helper:"The charging power tells how much the car uses. «Car charging» is optional, and may tell sooner that the car has started charging."},charging_power:{label:"Charging power"},cloud_controlled:{label:"Cloud-controlled EV charger",helper:"For an EV charger controlled through a cloud service. Kraftvakt then sends it fewer commands."},start_delay_s:{label:"Start delay",helper:"{min}–{max} s."},deactivate_on_fault:{label:"Deactivate on fault",helper:"Stops the EV charger while it has a fault, so the others in the group may charge."},fault_flag:{label:"Fault flag"},charging_window:{label:"Charging window",helper:"The EV charger charges only within this time each day, for example at night."},start:{label:"Start"},end:{label:"End"},charge_until_disconnected:{label:"Charge until the car is disconnected",helper:"A car that has started charging within the charging window may go on charging after it ends."},override_ends:{label:"End the override",helper:"When the switch «‹charger› override charging window» turns itself off."}},charging_current_info:"The minimum is the lowest current the car charges with, usually 6 A, and the maximum what the EV charger and its fuse allow.",state_choices:{car_connected:{true:"States for connected",false:"States for disconnected"},actively_charging:{true:"States for charging",false:"States for not charging"},fault_flag:{true:"States for a fault",false:"States for no fault"}},switched_by:{on_off_entity:"Switch for on and off",current:"The charging current, where 0 A stops charging",actions:"Custom actions"}}},nb:{panel:{title:"Kraftvakt",not_loaded:"Kraftvakt er ikke lastet. Sjekk integrasjonen under Innstillinger → Enheter og tjenester.",error:"Noe gikk galt: {message}"},tabs:{status:"Status",general:"Generelt",appliances:"Apparater",charging:"Billading",advanced:"Avansert",diagnostics:"Diagnostikk"},status:{regulation:"Regulering",running:"Kjører",stopped:"Stoppet",start:"Start regulering",stop:"Stopp regulering",stopped_info:"Reguleringen er stoppet, og alle regulerte apparater og elbilladere er slått av. Nå kan du endre konfigurasjonen. Når reguleringen starter igjen, slås apparatene på ett og ett.",incomplete_title:"Konfigurasjonen er ikke ferdig",start_refused:"Reguleringen kan ikke starte før konfigurasjonen er ferdig.",safe_state_title:"Sikker tilstand",safe_state_text:"Effektsensoren {sensor} gir ingen gyldig måling, så alle regulerte apparater og elbilladere er slått av. Reguleringen starter av seg selv når sensoren gir gyldige verdier igjen.",penalty_title:"Straffeperiode",penalty_text:"Tariffsnittet har vært over effektgrensen. Alle regulerte apparater og elbilladere holdes av til overforbruket er tatt igjen.",overconsumption_left:"Overforbruk igjen: {energy} kWh",recovery_started:"innhentingen er i gang",recovery_not_started:"innhentingen har ikke begynt",regulation_average:"Reguleringssnitt",tariff_average:"Tariffsnitt",average_over_seconds:"siste {seconds} s",average_over_hour:"siste time",power_now:"Forbruk nå",momentary:"øyeblikksverdi",power_limit:"Effektgrense",safe_state_chip:"Sikker tilstand",safe_state_back_text:"Effektsensoren {sensor} gir gyldige verdier igjen. Reguleringen starter på nytt, med alt avslått, ved neste avgjørelse.",penalty_chip:"Straffeperiode",next_decision:"Neste avgjørelse",next_decision_at:"Neste avgjørelse kl. {time}",appliances_and_chargers:"Apparater og elbilladere",power:"Effekt",temperature:"Temperatur",no_chargers:"Ingen elbilladere i gruppen.",no_appliances:"Ingen apparater er lagt til.",on:"På",off:"Av",activated:"Aktivert",deactivated:"Deaktivert",waiting_ends_at:"Slås på ved avgjørelsen kl. {time}",power_to_free_turn_on:"{power} kW må bli ledig før det kan slås på",power_to_free_activate:"{power} kW må bli ledig før elbilladeren kan aktiveres",power_to_free_ampere:"{power} kW må bli ledig før elbilladeren kan få én ampere til",delayed_turn_on:"Venter med å slå på",damping:"Demping av strømendringer",damping_ampere_at:"Én ampere til ved avgjørelsen kl. {time}",start_delay:"Startforsinkelse",start_delay_ends_at:"Ingenting under den slås på før avgjørelsen kl. {time}",delayed_activation:"Venter med å aktivere",activated_at:"Aktiveres ved avgjørelsen kl. {time}",charging_at:"Lader med {current} A",first_decision:"Venter på første avgjørelse",bypassed_no_car:"Hoppes over: ingen bil tilkoblet",waiting_charger:"I kø: en annen elbillader i gruppen har tur",starting_until:"Venter til kl. {time} på at bilen begynner å lade. Ingenting under den slås på før det.",excluded:"Utenfor regulering",outside_window:"Utenfor ladetidsrommet ({start}–{end})",amperes:"{current} A",chargers_charging:"{charging} av {total} elbilladere lader",activated_not_charging:"Aktivert: bilen bruker ikke strøm, og venter på minste ladestrøm",window_overridden:"Ladetidsrommet er overstyrt",chip_charging:"Lader",chip_no_car:"Bil frakoblet",chip_queued:"I kø",chip_starting:"Starter",chip_excluded:"Utenfor regulering",chip_window:"{start}–{end}",chip_override:"Overstyrt",chip_stopped:"Stoppet",regulation_stopped:"Reguleringen er stoppet, så elbilladeren er deaktivert",chip_first_decision:"Første avgjørelse",chip_fault:"Feil",fault:"Feilflagget viser feil, så elbilladeren er deaktivert til feilen er borte",free_power:"{power} kW ({share}) ledig",power_runs_out:"Her er effekten brukt opp. Det som står under, venter på ledig effekt.",queued_for_room:"I kø: venter på plass ved siden av elbilladerne som lader",queued_waiting_time:"I kø: neste i tur, etter ventetiden"},diagnostics:{power_sensor:"Effektsensor",valid:"Gyldig",not_valid:"Ingen gyldig verdi",update_interval:"Oppdateringsintervall",stored_interval:"Lagret oppdateringsintervall",reports_every:"Rapporterer hvert {seconds} s",seconds:"{seconds} s",regulation_window:"Reguleringsvindu",window_updates:"{seconds} s ({updates} × {interval} s)",last_missed_windows:"Sist hoppet over",none:"Ingen",actions:"Handlinger",failed_count:"{count} mislykket",last_failed:"Sist mislykket",commands_waiting:"Kommandoer som venter",action_timeout:"Tidsgrense for handlinger",running_for:"Har kjørt i {duration}",started:"Startet",yes:"Ja",no:"Nei",overconsumption:"Overforbruk",watt_hours:"{energy} Wh",command_repeat:"Gjentatte kommandoer",next_at:"Neste kl. {time}",timeline:"Tidslinje",minutes:"{minutes} min",consumption:"Forbruk",waiting:"Venter",waiting_time:"Ventetid",damping:"Demping",start_delay:"Startforsinkelse",not_known:"Ukjent",oldest_decision:"Eldste avgjørelse tatt vare på",chart_label:"Forbruk, reguleringssnitt, tariffsnitt og effektgrense den siste timen",lanes_label:"Hva hvert apparat og hver elbillader var satt til, i prioritert rekkefølge",now:"nå",decision_at:"Avgjørelse kl. {time}",no_decision_kept:"Ingen avgjørelse tatt vare på",event_log:"Hendelseslogg",filter_all:"Alle",filter_commands:"Kommandoer",filter_failed:"Mislykkede handlinger",no_events:"Ingen kommandoer eller mislykkede handlinger er tatt vare på.",log_kept:"Kommandoene i avgjørelsene som er tatt vare på, og de siste mislykkede handlingene. Tas vare på til Home Assistant startes på nytt eller integrasjonen lastes inn igjen.",download:"Last ned diagnostikk på siden til integrasjonen",kind_on:"På",kind_off:"Av",kind_current:"Strøm",kind_failed:"Mislykket",error:"Feil",power_sensor_valid:"Effektsensor gyldig",commands:"Kommandoer",turn_on:"Slå på {name}",turn_off:"Slå av {name}",activate:"Aktiver {name}",deactivate:"Deaktiver {name}",set_current:"{name} på {current} A"},missing:{missing_power_sensor:"Effektsensoren er ikke valgt.",missing_regulation_window:"Reguleringsvinduet er ikke valgt.",missing_device:"{item}: enheten er ikke valgt.",missing_entity:"{item}: bryteren eller termostaten er ikke valgt.",missing_on_off_entity:"{item}: bryteren som slår lading av og på, er ikke valgt.",missing_action:"{item}: handlingen for å {action} mangler.",missing_condition:"{item}: uttrykket mangler.",missing_car_connected:"{item}: «Bil tilkoblet» mangler.",missing_fault_flag:"{item}: feilflagget mangler.",unknown:"{item}: {code}",appliance_without_entity:"Et apparat uten bryter eller termostat",charger_without_device:"En elbillader uten enhet",actions:{turn_on:"slå på",turn_off:"slå av",activate:"aktivere",deactivate:"deaktivere",set_current:"sette ladestrømmen"},missing_charging_power:"{item}: ladeeffekten mangler."},config:{save:"Lagre",restore_defaults:"Gjenopprett standardinnstillinger",discard:"Forkast",unsaved:"Ulagrede endringer",fix_before_saving:"Rett opp de merkede innstillingene før du lagrer.",not_saved:"Konfigurasjonen ble ikke lagret. Rett opp de merkede innstillingene.",save_refused_running:"Konfigurasjonen kan ikke lagres mens reguleringen kjører.",leave_title:"Forkaste endringene?",leave_text:"Endringene på konfigurasjonssidene er ikke lagret, og går tapt hvis du går videre.",stay:"Fortsett å redigere",leave:"Forkast endringene"},locked:{title:"Konfigurasjonen er låst",text:"Reguleringen kjører. Stopp den for å endre konfigurasjonen. Da slås alle regulerte apparater og elbilladere av."},warning:{appliances_title:"Ikke slå regulerte apparater av eller på selv",chargers_title:"Ikke slå elbilladere av eller på selv",text:"Det forstyrrer reguleringen, og Kraftvakt setter dem tilbake. Slå på bryteren «utenfor regulering» for det du vil styre selv."},errors:{required:"Må fylles ut.",fault_flag_required:"Velg et feilflagg, eller slå av innstillingen.",out_of_range:"Må være mellom {min} og {max}.",at_least:"Må være minst {min}.",invalid_resolution:"Må gå opp i {resolution}.",not_integer:"Må være et helt tall.",invalid_entity_id:"Ikke en gyldig entitets-ID.",empty_label:"Navnet kan ikke være tomt.",duplicate_label:"Apparatet har allerede en variant med dette navnet.",empty_name:"Navnet kan ikke være tomt.",duplicate_name:"En annen gruppe har allerede dette navnet.",min_current_above_max:"Minste ladestrøm kan ikke være høyere enn største.",invalid_time:"Fyll ut både start og slutt.",window_start_equals_end:"Start og slutt kan ikke være like.",duplicate_entity:"Et annet apparat eller en annen elbillader bruker allerede denne entiteten.",unknown_device:"Enheten finnes ikke lenger i Home Assistant.",entity_not_on_device:"Entiteten hører ikke til enheten til elbilladeren, eller til enheten til apparatets bryter.",invalid_action:"Home Assistant forstår ikke handlingen.",invalid_template:"Malen har en syntaksfeil.",default_action_unavailable:"Denne entitetstypen har ingen standardhandling. Velg egendefinerte handlinger.",unsupported_entity_domain:"Denne entitetstypen kan ikke brukes her. Velg en fra listen.",domain_action_unavailable:"Handlingen passer ikke til entiteten. Velg en annen handling.",unsupported_option:"Entiteten støtter ikke denne verdien.",outside_entity_range:"Utenfor det entiteten tillater.",unknown:"Ugyldig verdi ({code}).",current_off_unsupported:"Entiteten kan ikke settes til 0 A, og det er slik en elbillader som slås av og på med strømmen, stoppes.",essential_with_variants:"Et nødvendig apparat kan ikke ha varianter. Slett dem, eller slå av innstillingen.",essential_with_power_reserve:"Et nødvendig apparat har ingen effektreserve. Slå av Fast last først, eller slå av denne innstillingen.",essential_not_at_top:"Et nødvendig apparat må stå over alle andre i prioritetslisten.",not_a_thermostat:"Velg en termostat (climate-entitet)."},dialog:{ok:"OK",cancel:"Avbryt",close:"Lukk"},general:{measurement:"Måling",regulation:"Regulering",penalty:"Straff",window_option_one:"1 oppdatering ({seconds} s)",window_option:"{count} oppdateringer ({seconds} s)",window_no_power_sensor:"Velg effektsensoren først.",window_measuring:"Måler hvor ofte effektsensoren rapporterer. Det kan ta opptil 30 sekunder.",window_not_measured:"Fant ikke ut hvor ofte effektsensoren rapporterer. Velg den på nytt når den rapporterer jevnt.",window_too_seldom:"Effektsensoren rapporterer hvert {interval} s. Det er for sjelden for et reguleringsvindu på høyst {max} s.",fields:{power_sensor:{label:"Effektsensor",helper:"Hele husets forbruk, vanligvis fra HAN-porten på strømmåleren."},regulation_window_updates:{label:"Reguleringsvindu",helper:"Et lengre vindu jevner ut korte topper, et kortere reagerer raskere. {min}–{max} s."},power_sensor_interval_s:{label:"Hvor ofte effektsensoren rapporterer"},power_limit_w:{label:"Effektgrense",helper:"Trinnet i kapasitetsleddet du vil holde deg under. {min}–{max} W, standard {default} W."},turn_on_margin_w:{label:"Innkoblingsmargin",helper:"Hvor langt under effektgrensen forbruket må være før noe slås på. En større margin gir færre av- og påslag. {min}–{max} W, standard {default} W."},wait_at_limit_s:{label:"Ventetid ved effektgrensen",helper:"Hvor lenge et apparat venter før det slås på når forbruket er nær effektgrensen. {min}–{max} s, standard {default} s."},penalty_threshold_w:{label:"Straffeterskel",helper:"Hvor langt forbruket den siste timen kan gå over effektgrensen før alt slås av til overforbruket er tatt igjen. {min}–{max} W, standard {default} W."},wait_curve_steepness:{label:"Bratthet"},wait_curve_pivot:{label:"Vendepunkt"},appliance_repeat_increment_factor:{label:"Økning hver gang",helper:"Andel av ventetiden ved effektgrensen. Standard × {default}."},appliance_repeat_increments:{label:"Antall økninger",helper:"{min}–{max}, standard {default}."},ampere_damping_s:{label:"Dempingstid",helper:"Hvor lenge en elbillader venter før den får tilbake en ampere den har mistet. Lengre gir jevnere forbruk, kortere gir mer lading. {min}–{max} s, standard {default} s."},charger_waiting_factor:{label:"Ventetid for elbilladere",helper:"Hvor mange ganger lenger enn et apparat en elbillader venter før den aktiveres igjen. {min}×–{max}×, standard {default}×."},command_repeat_interval_min:{label:"Send kommandoen på nytt etter",helper:"{min}–{max} min, standard {default} min."},action_timeout_s:{label:"Tidsgrense for handlinger",helper:"En handling som tar lengre tid, avbrytes. {min}–{max} s, standard {default} s."},power_sensor_timeout_s:{label:"Tidsgrense for effektsensoren",helper:"Har effektsensoren ikke rapportert på så lenge, slås alt av til den er tilbake. {min}–{max} s, standard {default} s."}},penalty_info:"En sikkerhetsventil som slår til hvis forbruket blir mye høyere enn effektgrensen, for eksempel når noe utenfor Kraftvakt slås på."},advanced:{wait_curve:"Ventetidskurve",wait_curve_info:"Hvor lenge et apparat venter, etter hvor mye effekt som er ledig. Den faktiske ventetiden rundes opp til neste avgjørelse.",free_power_kw:"Ledig effekt kW",waiting_minutes:"Ventetid min:s",actual_waiting_minutes:"Faktisk ventetid min:s",repeated_turn_on:"Ventetid når det samme slås på igjen og igjen",repeated_turn_on_info:"Ventetiden øker når det samme apparatet slås på igjen og igjen. De to første gangene følger kurven, og vises ved vendepunktet.",turn_on_in_a_row:"Innkobling på rad",chargers:"Elbilladere",chargers_info:"Hindrer at en elbillader går opp og ned, eller av og på, når forbruket svinger et kort øyeblikk.",command_repeat:"Gjentatte kommandoer",command_repeat_info:"Setter apparater og elbilladere tilbake hvis de har endret seg av seg selv, for eksempel etter et strømbrudd.",timeouts:"Tidsgrenser",timeouts_info:"Beskytter mot handlinger som aldri blir ferdige, og mot en effektsensor som slutter å rapportere."},list:{drag:"Dra for å endre rekkefølgen",edit:"Rediger",view:"Vis"},appliances:{priority_title:"Prioritetsliste",priority_sub:"Øverst har høyest prioritet. Dra for å endre rekkefølgen.",add:"Legg til apparat",empty:"Ingen apparater ennå. Legg til dem Kraftvakt skal slå av og på.",charger_group_sub:"elbilladere: {count} · settes opp under",power_reserve:"effektreserve {power} W",essential:"Nødvendig",variant_count:"varianter: {count}",variant_entity:"Variant · {entity}",variant_template:"Variant · egendefinert mal",variant_own_actions:"egne handlinger",variant_own_turn_on:"egen handling for å slå på",variant_own_turn_off:"egen handling for å slå av"},appliance:{add_title:"Legg til apparat",edit_title:"Rediger apparat",view_title:"Apparat",variants:"Varianter",variants_info:"Gir apparatet en annen plass i prioritetslisten når uttrykket er sant, for eksempel høyere opp for varmtvannsberederen om morgenen. Den øverste varianten som gjelder, brukes.",add_variant:"Legg til variant",display_values:"Visning",display_values_info:"Valgfritt. Vises bare på statussiden.",delete:"Slett apparat",fields:{entity_id:{label:"Bryter eller termostat",helper:"Det Kraftvakt slår av og på, for eksempel bryteren til varmtvannsberederen."},essential:{label:"Nødvendig apparat",helper:"For apparater som alltid skal være på, som en fryser. Kan ikke ha varianter."},turn_on:{label:"Handling for å slå på",helper:"Standard passer for de fleste."},turn_off:{label:"Handling for å slå av",helper:"Standard passer for de fleste."},fixed_load:{label:"Fast last",helper:"For apparater som alltid bruker like mye når de er på, som en takvifte. De slås på uten å vente når nok effekt er ledig. Ikke for apparater med termostat eller annen egen styring."},power_reserve_w:{label:"Effektreserve",helper:"Det apparatet bruker når det er på. Gjelder alle variantene."},label:{label:"Navn"},condition:{label:"Uttrykk"},override_turn_on:{label:"Egen handling for å slå på",helper:"For eksempel en annen HVAC-modus."},override_turn_off:{label:"Egen handling for å slå av",helper:"For eksempel frostsikring."},display_power:{label:"Effekt"},display_temperature:{label:"Temperatur"}}},variant:{edit_title:"Rediger variant {name}",view_title:"Variant {name}",condition:"Uttrykk",delete:"Slett variant",condition_info:"Varianten gjelder når uttrykket er sant, for eksempel mellom kl. 05 og 08."},action:{default:"Standard",custom:"Egendefinerte handlinger",entity:"Tallentitet",domain_actions:{climate_hvac_mode:"HVAC-modus",climate_temperature:"Temperatur",climate_hvac_mode_and_temperature:"HVAC-modus og temperatur"},default_runs:"Kjører {service} for entiteten.",entity_runs:"Kjører {service} for den valgte entiteten, med ladestrømmen som verdi.",no_default:"Denne entitetstypen har ingen standardhandling. Bruk egendefinerte handlinger.",choose_entity:"Velg en entitet for å bruke standardhandlingen.",choose_action_entity:"Velg tallentiteten som skal få ladestrømmen.",variables:"Variabler: {variables}.",parameters:{hvac_mode:"HVAC-modus",temperature:"Måltemperatur",temperature_from:"Måltemperatur fra",temperature_entity:"Sensor, tall eller termostat",temperature_reading:"Termostatens temperatur"},readings:{target_temperature:"Innstilt temperatur",current_temperature:"Nåværende temperatur"},value_from:{number:"Fast verdi",source:"Sensor, tall eller termostat",template:"Egendefinert mal"},parameter_range:"{min}–{max} {unit} for entiteten.",source_now:"Nå: {value}.",source_no_value:"Ingen temperatur nå: handlingen feiler så lenge den mangler.",source_read:"Leses når handlingen kjøres.",source_range:"Leses når handlingen kjøres, og holdes innenfor {min}–{max} {unit}."},condition:{entity:"Binærsensor eller bryter",template:"Egendefinert mal",entity_label:"Binærsensor eller bryter",template_label:"Egendefinert mal",entity_helper:"Sann når den er på.",state:"Statussensor",state_label:"Statussensor",state_helper:"For eksempel en sensor som viser status for elbilladeren.",states_label:"Tilstander",states_helper:"Velg eller skriv inn tilstandene.",template_helper:"Skal gi sann eller usann. Variabler: {variables}.",now:"Nå: {value}",true:"sann",false:"usann",error:"Feil: {message}",invalid:"Malen gir {value}, ikke sann eller usann, og regnes som usann."},one_at_a_time:{entity:"Binærsensor eller bryter",template:"Egendefinert mal",entity_label:"Binærsensor eller bryter",template_label:"Egendefinert mal",entity_helper:"Én elbillader om gangen når den er på.",template_helper:"Sann gir én elbillader om gangen, for eksempel {{ power_limit < 15000 }}. Variabler: {variables}.",true:"én om gangen",false:"flere samtidig",invalid:"Malen gir {value}, ikke sann eller usann, så elbilladerne lader flere samtidig."},actively_charging:{type_label:"Bilen lader, ifølge",entity:"Binærsensor eller bryter",template:"Egendefinert mal",entity_label:"Binærsensor eller bryter",template_label:"Egendefinert mal",entity_helper:"På når bilen lader.",state:"Statussensor",state_label:"Statussensor",state_helper:"For eksempel en sensor som viser status for elbilladeren.",states_label:"Tilstander",states_helper:"Velg eller skriv inn tilstandene.",template_helper:"Sann når bilen lader. Variabler: {variables}.",true:"lader",false:"lader ikke",invalid:"Malen gir {value}, ikke sann eller usann, og regnes som at bilen ikke lader."},charging_power:{type_label:"Ladeeffekt fra",power_sensor:"Effektsensor",template:"Egendefinert mal",power_sensor_label:"Effektsensor",template_label:"Egendefinert mal for ladeeffekt",power_sensor_helper:"Det bilen lader med nå.",template_helper:"Effekten i W. Variabler: {variables}.",true:"lader",false:"lader ikke",invalid:"Malen gir {value}, ikke et tall, og regnes som at bilen ikke lader."},display_power:{type_label:"Effekt fra",power_sensor:"Effektsensor",template:"Egendefinert mal",power_sensor_label:"Effektsensor",template_label:"Egendefinert mal for effekt",power_sensor_helper:"En sensor på samme enhet som bryteren eller termostaten.",template_helper:"Effekten i W, også fra en annen enhet. Variabler: {variables}.",no_value:"ingen verdi",invalid:"Malen gir {value}, ikke et tall, så ingenting vises."},display_temperature:{type_label:"Temperatur fra",temperature_sensor:"Sensor eller termostat",template:"Egendefinert mal",current_temperature:"{name}: nåværende temperatur",target_temperature:"{name}: innstilt temperatur",temperature_sensor_label:"Temperatursensor eller termostat",template_label:"Egendefinert mal for temperatur",temperature_sensor_helper:"Fra samme enhet som bryteren eller termostaten.",template_helper:"Temperaturen i Home Assistants enhet, også fra en annen enhet. Variabler: {variables}.",no_value:"ingen verdi",invalid:"Malen gir {value}, ikke et tall, så ingenting vises."},fault:{entity:"Binærsensor eller bryter",template:"Egendefinert mal",entity_label:"Binærsensor eller bryter",template_label:"Egendefinert mal",entity_helper:"På betyr feil.",state:"Statussensor",state_label:"Statussensor",state_helper:"For eksempel en sensor som viser status for elbilladeren.",states_label:"Tilstander",states_helper:"Velg eller skriv inn tilstandene.",template_helper:"Sann betyr feil. Variabler: {variables}.",true:"feil",false:"ingen feil",invalid:"Malen gir {value}, ikke sann eller usann, og regnes som ingen feil."},charging:{name:"Navn",name_sub:"Vises i prioritetslisten og på statussiden.",one_at_a_time:"Begrens til én elbillader om gangen",one_at_a_time_sub:"Bare én bil i gruppen lader om gangen, så den blir fortere full.",one_at_a_time_always:"Alltid",one_at_a_time_never:"Aldri",one_at_a_time_condition:"Når et uttrykk er sant",one_at_a_time_applies:"Gjelder",dynamic_order:"Dynamisk ladeprioritet",dynamic_order_sub:"Biler som lader, får fortsette, og de andre venter på tur.",needs_two_chargers:"Gjelder bare med minst to elbilladere i gruppen.",chargers:"Ladeprioritet",chargers_sub:"Øverst har høyest prioritet. Dra en elbillader til en annen gruppe for å flytte den.",add:"Legg til elbillader",empty:"Ingen elbilladere ennå.",no_groups:"Ingen grupper med elbilladere ennå. Legg til en gruppe, og deretter elbilladerne i den.",add_group:"Legg til gruppe",new_group_name:"Elbilladere",unnamed_group:"Gruppe uten navn",delete_group:"Slett gruppe",delete_group_not_empty:"Flytt eller slett elbilladerne før du sletter gruppen.",switches_info:"Mens reguleringen kjører, kan du styre hver elbillader med bryterne «‹lader› utenfor regulering», «‹lader› overstyr ladetidsrom» og «‹lader› lad til bilen kobles fra».",currents:"{min}–{max} A ({power} W ved {min} A)",window:"ladetidsrom {start}–{end}",charges_until_disconnected:"lader til bilen kobles fra",deactivated_on_fault:"deaktiveres ved feil"},charger:{add_title:"Legg til elbillader",edit_title:"Rediger elbillader",view_title:"Elbillader",charging_current:"Ladestrøm",start:"Oppstart",start_info:"Hvor lang tid bilen kan bruke på å begynne å lade etter at elbilladeren er aktivert.",on_off:"Slå lading av og på",on_off_info:"Hvordan Kraftvakt aktiverer og deaktiverer elbilladeren.",switched_by_current_info:"Velg entiteten eller handlingen som setter strømmen, under Ladestrøm. Den må kunne settes til 0 A.",profile_applied:"Fylt ut fra laderprofilen {profile}. Se over alle feltene før du lagrer.",override_ends:{manual:"Når jeg slår den av",charging_stopped:"Når bilen slutter å lade",car_disconnected:"Når bilen kobles fra"},delete:"Slett elbillader",fields:{device_id:{label:"Enhet",helper:"Elbilladeren i Home Assistant. Kjenner Kraftvakt laderen, fylles feltene under ut."},switched_by:{label:""},on_off_entity:{label:"Bryter som tillater lading",helper:"Slås på for å aktivere elbilladeren og av for å deaktivere den."},activate:{label:"Handling for å aktivere"},deactivate:{label:"Handling for å deaktivere"},min_current_a:{label:"Minste ladestrøm"},max_current_a:{label:"Største ladestrøm"},set_current:{label:"Sett ladestrøm"},min_current_power_w:{label:"Effekt ved minste ladestrøm",helper:"Det bilen bruker ved minste ladestrøm, omtrent 1 400 W på én fase. {min}–{max} W, standard {default} W (6 A på tre faser)."},car_connected:{label:"Bil tilkoblet",helper:"Viser om en bil er koblet til elbilladeren."},actively_charging:{label:"Lader aktivt",helper:"Ladeeffekten viser hvor mye bilen bruker. «Bilen lader» er valgfritt, og kan vise raskere at bilen har begynt å lade."},charging_power:{label:"Ladeeffekt"},cloud_controlled:{label:"Skystyrt elbillader",helper:"For elbilladere som styres via en skytjeneste. Kraftvakt sender den da færre kommandoer."},start_delay_s:{label:"Startforsinkelse",helper:"{min}–{max} s."},deactivate_on_fault:{label:"Deaktiver ved feil",helper:"Stopper elbilladeren så lenge den har feil, så de andre i gruppen kan lade."},fault_flag:{label:"Feilflagg"},charging_window:{label:"Ladetidsrom",helper:"Elbilladeren lader bare i dette tidsrommet hver dag, for eksempel om natten."},start:{label:"Start"},end:{label:"Slutt"},charge_until_disconnected:{label:"Lad til bilen kobles fra",helper:"En bil som har begynt å lade i ladetidsrommet, kan lade videre etter at det er slutt."},override_ends:{label:"Avslutt overstyringen",helper:"Når bryteren «‹lader› overstyr ladetidsrom» slår seg av igjen."}},charging_current_info:"Minste ladestrøm er det laveste bilen lader med, vanligvis 6 A. Største ladestrøm er det elbilladeren og sikringen tåler.",state_choices:{car_connected:{true:"Tilstander for tilkoblet",false:"Tilstander for frakoblet"},actively_charging:{true:"Tilstander når bilen lader",false:"Tilstander når bilen ikke lader"},fault_flag:{true:"Tilstander for feil",false:"Tilstander for ingen feil"}},switched_by:{on_off_entity:"Bryter for av og på",current:"Ladestrømmen, der 0 A stopper ladingen",actions:"Egendefinerte handlinger"}}}};function nt(e){const t=at[e]??at[e.split("-")[0]]??at.en;return(e,i={})=>(st(t,e)??st(at.en,e)??e).replace(/\{(\w+)\}/g,(e,t)=>t in i?String(i[t]):e)}function st(e,t){let i=e;for(const e of t.split("."))i=i?.[e];return"string"==typeof i?i:void 0}const ot=["status","general","appliances","charging","advanced","diagnostics"],lt="/kraftvakt";function dt(e,t={}){const i=`${lt}/${e}`;t.replace?history.replaceState(null,"",i):history.pushState(null,"",i),window.dispatchEvent(new CustomEvent("location-changed",{detail:{replace:t.replace??!1}}))}function ct(e,t){const i=e.currentTarget;"click"===e.type&&e.detail>0&&i.blur(),i.dispatchEvent(new CustomEvent("hass-more-info",{detail:{entityId:t},bubbles:!0,composed:!0}))}function ht(e,t,i){return new Intl.NumberFormat(e,{minimumFractionDigits:i,maximumFractionDigits:i}).format(t)}function pt(e,t){return null===t?"–":ht(e,t/1e3,2)}function ut(e){if(null===e)return"–";const t=Math.round(e);return`${Math.floor(t/60)}:${String(t%60).padStart(2,"0")}`}function gt(e,t){return new Intl.NumberFormat(e,{style:"percent",maximumFractionDigits:0}).format(t)}function mt(e){const{language:t,time_zone:i,time_format:r}=e.locale,a="system"===r?new Intl.DateTimeFormat(void 0,{hour:"numeric"}).resolvedOptions().hour12:"12"===r;return{language:t,timeZone:"server"===i?e.config.time_zone:void 0,hourCycle:"language"===r?void 0:a?"h12":"h23"}}function _t(e){return{timeZone:e.timeZone,hourCycle:e.hourCycle}}function ft(e,t,i=!0){const r=i?{}:{hour:"2-digit",minute:"2-digit"};return new Date(t).toLocaleTimeString(e.language,{..._t(e),...r})}function vt(e,t,i=new Date){const r=new Date(t),a=t=>t.toLocaleDateString("en-CA",{timeZone:e.timeZone});return a(r)===a(i)?ft(e,t):r.toLocaleString(e.language,_t(e))}function wt(e,t){const i=Math.floor(t/6e4),r=Math.floor(i/60),a=Math.floor(r/24),[n,s]=a>0?[a,"day"]:r>0?[r,"hour"]:[i,"minute"];return new Intl.NumberFormat(e,{style:"unit",unit:s,unitDisplay:"long"}).format(n)}function yt(e,t){const i=t.seconds.min??0,r=t.seconds.max??i,a=Math.max(1,Math.ceil(i/e-1e-9));return Array.from({length:t.choices},(e,t)=>a*(t+1)).filter(t=>t*e<=r+1e-9)}function bt(e){const{regulation_window_updates:t,power_sensor_interval_s:i}=e;return null===t||null===i?null:t*i}function $t(e){return Math.min(1,Math.max(0,(e-.5)/.5))}function kt(e,t){const i=Math.min($t(t/100),.8**(1/e)*.999)**e,r=i*(1-.8)/(.8-i);return t=>{const i=$t(t)**e;return 0===i?0:i*(1+r)/(i+r)}}function xt(e,t){return Math.max(0,Math.ceil(Math.round(e)/t-1e-9))*t}class At{constructor(e,t){this.host=e,this.maxWidth=t,this.matches=!1,this.observer=new ResizeObserver(([e])=>{const t=e.contentRect.width<=this.maxWidth;t!==this.matches&&(this.matches=t,this.host.requestUpdate())}),e.addController(this)}hostConnected(){this.observer.observe(this.host)}hostDisconnected(){this.observer.disconnect()}}const Ct=(e,t,i)=>{const r=new Map;for(let a=t;a<=i;a++)r.set(e[a],a);return r},zt=Ee(class extends Se{constructor(e){if(super(e),e.type!==Ae)throw Error("repeat() can only be used in text expressions")}dt(e,t,i){let r;void 0===i?i=t:void 0!==t&&(r=t);const a=[],n=[];let s=0;for(const t of e)a[s]=r?r(t,s):s,n[s]=i(t,s),s++;return{values:n,keys:a}}render(e,t,i){return this.dt(e,t,i).values}update(e,[t,i,r]){const a=(e=>e._$AH)(e),{values:n,keys:s}=this.dt(t,i,r);if(!Array.isArray(a))return this.ut=s,n;const o=this.ut??=[],l=[];let d,c,h=0,p=a.length-1,u=0,g=n.length-1;for(;h<=p&&u<=g;)if(null===a[h])h++;else if(null===a[p])p--;else if(o[h]===s[u])l[u]=Le(a[h],n[u]),h++,u++;else if(o[p]===s[g])l[g]=Le(a[p],n[g]),p--,g--;else if(o[h]===s[g])l[g]=Le(a[h],n[g]),Te(e,l[g+1],a[h]),h++,g--;else if(o[p]===s[u])l[u]=Le(a[p],n[u]),Te(e,a[h],a[p]),p--,u++;else if(void 0===d&&(d=Ct(s,u,g),c=Ct(o,h,p)),d.has(o[h]))if(d.has(o[p])){const t=c.get(s[u]),i=void 0!==t?a[t]:null;if(null===i){const t=Te(e,a[h]);Le(t,n[u]),l[u]=t}else l[u]=Le(i,n[u]),Te(e,a[h],i),a[t]=null;u++}else Pe(a[p]),p--;else Pe(a[h]),h++;for(;u<=g;){const t=Te(e,l[g+1]);Le(t,n[u]),l[u++]=t}for(;h<=p;){const e=a[h++];null!==e&&Pe(e)}return this.ut=s,Ne(e,l),ee}});let Et=class extends fe{constructor(){super(...arguments),this.rows=[],this.locked=!1,this.emptyText=""}render(){return X`
      <ha-sortable
        handle-selector=".handle"
        group=${(e=>e??te)(this.group)}
        .disabled=${this.locked}
        @item-moved=${this.itemMoved}
        @item-added=${this.itemAdded}
        @item-removed=${this.itemRemoved}
      >
        <div class="list" data-empty=${this.emptyText}>
          ${zt(this.rows,e=>e.key,(e,t)=>this.renderRow(e,t))}
        </div>
      </ha-sortable>
    `}renderRow(e,t){return X`
      <div class="row ${e.highlighted?"highlighted":""}" data-key=${e.key}>
        ${this.locked?te:X`<ha-svg-icon class="handle" .path=${i} title=${this.localize("list.drag")}></ha-svg-icon>`}
        <span class="rank">${t+1}</span>
        ${e.iconPath?X`<ha-svg-icon class="icon" .path=${e.iconPath}></ha-svg-icon>`:te}
        <div class="main">
          <div class="title">${e.title}${e.tag?X`<span class="tag">${e.tag}</span>`:te}</div>
          ${e.details.length>0?X`<div class="details">${r=e.details,r.map((e,t)=>X`${t>0?" · ":""}${e}`)}</div>`:te} ${e.errors.map(e=>X`<div class="error">${e}</div>`)}
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
      background: linear-gradient(var(--kraftvakt-essential-background), var(--kraftvakt-essential-background)), var(--card-background-color);
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
  `}};function St(e,t,i){const r=e.domain_actions.appliances[t],a=i?.split(".")[0];return Object.fromEntries(Object.entries(r).filter(([,e])=>e.domain===a))}function Vt(e,t,i,r){return r?.domain_action?St(e,t,i)[r.domain_action]:void 0}function Mt(e,t,i={}){return Object.fromEntries(e.parameters.map(e=>[e.name,i[e.name]??Nt(e,t)]))}function Ht(e,t){return{min:Ot(t,e.min_attribute),max:Ot(t,e.max_attribute),step:Ot(t,e.step_attribute)}}function Tt(e,t,i){if(null===t||"temperature"===e.type&&"string"==typeof t)return;if("option"===e.type){if("string"!=typeof t)return"invalid_type";const r=Pt(i,e.options_attribute);return Array.isArray(r)&&!r.includes(t)?"unsupported_option":void 0}if("object"==typeof t)return function(e){const t=Lt[e.type];if(!t)return"invalid_type";if(!e.value||t.includes(e.value.split(".")[0]))return;return"temperature_sensor"===e.type?"unsupported_entity_domain":"not_a_thermostat"}(t);const{min:r,max:a}=Ht(e,i);return"number"==typeof t&&(void 0!==r&&t<r||void 0!==a&&t>a)?"outside_entity_range":void 0}e([$e({attribute:!1})],Et.prototype,"localize",void 0),e([$e({attribute:!1})],Et.prototype,"rows",void 0),e([$e({type:Boolean})],Et.prototype,"locked",void 0),e([$e()],Et.prototype,"group",void 0),e([$e()],Et.prototype,"emptyText",void 0),Et=e([we("kraftvakt-sortable-list")],Et);const Lt={temperature_sensor:["sensor","input_number","number"],current_temperature:["climate"],target_temperature:["climate"]};function Dt(e,t){const i="temperature_sensor"===e.type?t?.state:t?.attributes["current_temperature"===e.type?"current_temperature":"temperature"],r="number"==typeof i?i:"string"==typeof i&&""!==i.trim()?Number(i):NaN;return Number.isFinite(r)?r:null}function Nt(e,t){if("option"===e.type){const i=Pt(t,e.options_attribute),r=Array.isArray(i)?i:e.preferred_options;return e.preferred_options.find(e=>r.includes(e))??null}return e.default}function Pt(e,t){return t?e?.attributes[t]:void 0}function Ot(e,t){const i=Pt(e,t);return"number"==typeof i?i:void 0}const Ft=["binary_sensor","input_boolean","switch","schedule"];function Wt(e,t,i){return t[i]??e.states[i]?.attributes.friendly_name??i}function jt(e){return"switched_by"in e?"on_off_entity"===e.switched_by?e.on_off_entity:null:e.entity_id}function It(e,t,i){const r=i.device_id?e.devices?.[i.device_id]:void 0,a=r?.name_by_user??r?.name;if(a)return a;const n=jt(i);return n?Wt(e,t,n):null}function Rt(e,t){return t&&e.states[t]?t:null}function Bt(e){return Object.values(e.entities??{}).filter(e=>"kraftvakt"===e.platform).map(e=>e.entity_id)}function Ut(e,t){return Object.values(e.entities??{}).find(e=>"kraftvakt"===e.platform&&e.translation_key===t)?.entity_id??null}function qt(e,t){const i=e.states[t],r=Number(i?.state);if(!i||""===i.state.trim()||!Number.isFinite(r))return null;const a=i.attributes.unit_of_measurement,n="kW"===a?1e3:a&&"W"!==a?null:1;return null===n?null:Math.max(0,r)*n}const Gt={missing_power_sensor:"missing.missing_power_sensor",missing_regulation_window:"missing.missing_regulation_window",missing_device:"missing.missing_device",missing_entity:"missing.missing_entity",missing_on_off_entity:"missing.missing_on_off_entity",missing_action:"missing.missing_action",missing_condition:"missing.missing_condition",missing_car_connected:"missing.missing_car_connected",missing_fault_flag:"missing.missing_fault_flag",missing_charging_power:"missing.missing_charging_power"},Kt={turn_on:"missing.actions.turn_on",turn_off:"missing.actions.turn_off",activate:"missing.actions.activate",deactivate:"missing.actions.deactivate",set_current:"missing.actions.set_current"},Zt={general:"general",appliances:"appliances",priority:"appliances",charger_groups:"charging",chargers:"charging"},Jt=new Set(["wait_curve_steepness","wait_curve_pivot","appliance_repeat_increment_factor","appliance_repeat_increments","ampere_damping_s","charger_waiting_factor","command_repeat_interval_min","action_timeout_s","power_sensor_timeout_s"]);function Qt(e,t){const i=e?.split(".").at(-1)??"";return Kt[i]?t(Kt[i]):e??""}function Xt(e,t,i,r){const a=t?.entity_names??{};if("charger_groups"===e.section){const r=t?.config.charger_groups.find(t=>t.id===e.target);return r?.name.trim()||i("charging.unnamed_group")}if("chargers"===e.section){const n=t&&rt(t.config).find(t=>t.id===e.target);return(n&&It(r,a,n))??i("missing.charger_without_device")}const n=t?.config.appliances.find(t=>t.id===e.target),s=n?.entity_id?Wt(r,a,n.entity_id):i("missing.appliance_without_entity"),o=e.field?.startsWith("variants.")?e.field.split(".")[1]:void 0,l=n?.variants.find(e=>e.id===o);return l?`${s} «${l.label}»`:s}const Yt={required:"errors.required",missing_power_sensor:"errors.required",missing_regulation_window:"errors.required",missing_device:"errors.required",missing_entity:"errors.required",missing_on_off_entity:"errors.required",missing_action:"errors.required",missing_condition:"errors.required",missing_car_connected:"errors.required",missing_fault_flag:"errors.fault_flag_required",missing_charging_power:"errors.required",not_integer:"errors.not_integer",invalid_entity_id:"errors.invalid_entity_id",empty_label:"errors.empty_label",empty_name:"errors.empty_name",duplicate_name:"errors.duplicate_name",duplicate_label:"errors.duplicate_label",min_current_above_max:"errors.min_current_above_max",invalid_time:"errors.invalid_time",window_start_equals_end:"errors.window_start_equals_end",duplicate_entity:"errors.duplicate_entity",unknown_device:"errors.unknown_device",entity_not_on_device:"errors.entity_not_on_device",invalid_action:"errors.invalid_action",invalid_template:"errors.invalid_template",default_action_unavailable:"errors.default_action_unavailable",unsupported_entity_domain:"errors.unsupported_entity_domain",domain_action_unavailable:"errors.domain_action_unavailable",unsupported_option:"errors.unsupported_option",outside_entity_range:"errors.outside_entity_range",current_off_unsupported:"errors.current_off_unsupported",essential_with_variants:"errors.essential_with_variants",essential_with_power_reserve:"errors.essential_with_power_reserve",essential_not_at_top:"errors.essential_not_at_top",not_a_thermostat:"errors.not_a_thermostat"},ei={general:"general",appliances:"appliances",chargers:"chargers"};function ti(e,t,i,r){const a=ei[e.section],n=a&&e.field?i?.limits[a][e.field]:void 0,s=e=>null===e?"":new Intl.NumberFormat(r).format(e);return"out_of_range"===e.code&&n?null===n.max?t("errors.at_least",{min:s(n.min)}):t("errors.out_of_range",{min:s(n.min),max:s(n.max)}):"invalid_resolution"===e.code&&n?t("errors.invalid_resolution",{resolution:s(n.resolution)}):t(Yt[e.code]??"errors.unknown",{code:e.code})}function ii(e,t,i){const r={};for(const a of e)a.field?.startsWith(t)&&(r[a.field.slice(t.length)]??=i(a));return r}const ri=g`
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
`;function ai(e,t=te){return X`
    <div class="section-header">
      <span class="section-title">${e}</span>
      ${t}
    </div>
  `}function ni(e){return e?X`<p class="description">${e}</p>`:te}function si(e,t){return t?Object.values(e.entities??{}).filter(e=>e.device_id===t).map(e=>e.entity_id):[]}function oi(e,t){return t&&e.entities?.[t]?.device_id||null}function li(e){return[["display_power",ci(e.display_power)],["display_temperature",ci(e.display_temperature)]].filter(e=>!!e[1])}function di(e,t,i){const r=oi(i,t),a=r?new Set(si(i,r)):void 0;return{display_power:hi(e.display_power,a),display_temperature:hi(e.display_temperature,a)}}function ci(e){return e&&"template"!==e.type?e.value:null}function hi(e,t){const i=ci(e);return i&&t&&!t.has(i)?null:e}const pi=["turn_on","turn_off"];function ui(e){return[...pi.map(t=>({name:t,field:t,action:e[t]})),...e.variants.flatMap(e=>pi.filter(t=>gi(e.actions,t)).map(t=>({name:t,field:`variants.${e.id}.${t}`,action:e.actions[t]??null})))]}function gi(e,t){return void 0!==e?.[t]}function mi(e,t,i){return[...Mi("general",void 0,e.general,t.limits.general,!0).filter(e=>!(e=>"required"===e.code&&null===t.defaults.general[e.field])(e)),...e.appliances.flatMap(e=>zi(e,t,i)),..._i(e.charger_groups),...rt(e).flatMap(e=>Ei(e,t,i))]}function _i(e){const t=e.map(e=>e.name.trim());return e.flatMap((e,i)=>{const r=t[i],a=r?t.filter(e=>e===r).length>1?"duplicate_name":void 0:"empty_name";return a?[{code:a,section:"charger_groups",target:e.id,field:"name"}]:[]})}function fi(e){const t=[];return e.general.power_sensor||t.push({code:"missing_power_sensor",section:"general",field:"power_sensor"}),null!==e.general.regulation_window_updates&&null!==e.general.power_sensor_interval_s||t.push({code:"missing_regulation_window",section:"general",field:"regulation_window_updates"}),t.push(...e.appliances.flatMap(yi),...e.charger_groups.flatMap(wi),...rt(e).flatMap(bi)),t}function vi(e){return e.chargers.length>1}function wi(e){return vi(e)&&"object"==typeof e.one_at_a_time&&!Vi(e.one_at_a_time)?[{code:"missing_condition",section:"charger_groups",target:e.id,field:"one_at_a_time"}]:[]}function yi(e){return[...e.entity_id?[]:[Si(e,"missing_entity","entity_id")],...Ti("appliances",e,ui(e)),...e.variants.filter(e=>!Vi(e.condition)).map(t=>Si(e,"missing_condition",`variants.${t.id}.condition`))]}function bi(e){const t=e.device_id?[]:[{code:"missing_device",section:"chargers",target:e.id,field:"device_id"}];return"on_off_entity"!==e.switched_by||e.on_off_entity||t.push({code:"missing_on_off_entity",section:"chargers",target:e.id,field:"on_off_entity"}),t.push(...Ti("chargers",e,function(e){return("actions"===e.switched_by?["activate","deactivate","set_current"]:["set_current"]).map(t=>({name:t,field:t,action:e[t]}))}(e))),Vi(e.car_connected)||t.push({code:"missing_car_connected",section:"chargers",target:e.id,field:"car_connected"}),Vi(e.charging_power)||t.push({code:"missing_charging_power",section:"chargers",target:e.id,field:"charging_power"}),e.deactivate_on_fault&&!Vi(e.fault_flag)&&t.push({code:"missing_fault_flag",section:"chargers",target:e.id,field:"fault_flag"}),t}function $i(e,t,i){return e.default_actions[t][i]}function ki(e,t,i,r){switch(r?.mode){case"default":return xi(e,"appliances",t,i);case"domain":return void 0!==Vt(e,t,i,r);default:return!0}}function xi(e,t,i,r){return null!==r&&$i(e,t,i).domains.includes(r.split(".")[0])}function Ai(e,t,i){return e.filter(e=>e.section===t&&e.target===i)}function Ci(e){return"object"==typeof e&&null!==e?!e.value:null===e||""===e}function zi(e,t,i){const r=e.variants.map(e=>e.label.trim()),a=oi(i,e.entity_id);return[...Mi("appliances",e.id,e,t.limits.appliances,!1),...Hi(e,t,i.states),...a?li(e).filter(([,e])=>oi(i,e)!==a).map(([t])=>Si(e,"entity_not_on_device",t)):[],...e.variants.flatMap((t,i)=>{const a=`variants.${t.id}.label`;return""===r[i]?[Si(e,"empty_label",a)]:r.filter(e=>e===r[i]).length>1?[Si(e,"duplicate_label",a)]:[]})]}function Ei(e,t,i){const r=(t,i)=>({code:t,section:"chargers",target:e.id,field:i}),a=[...Mi("chargers",e.id,e,t.limits.chargers,!0),...Li(e,i).map(([e,t])=>r(e,t))],n=jt(e);n&&!xi(t,"chargers","activate",n)&&a.push(r("unsupported_entity_domain","on_off_entity")),function(e,t){const i=e.set_current;if("current"!==e.switched_by||!i)return!0;const r="entity"===i.mode?i.entity_id:null,a=r?t[r]?.attributes.min:void 0;return"number"!=typeof a||a<=0}(e,i.states)||a.push(r("current_off_unsupported","set_current")),e.min_current_a>e.max_current_a&&a.push(r("min_current_above_max","min_current_a"));const s=e.charging_window;return!s||s.start&&s.end?s&&s.start===s.end&&a.push(r("window_start_equals_end","charging_window")):a.push(r("invalid_time","charging_window")),a}function Si(e,t,i){return{code:t,section:"appliances",target:e.id,field:i}}function Vi(e){return null!==e&&""!==e.value.trim()&&("state"!==e.type||(e.states??[]).length>0)}function Mi(e,t,i,r,a){const n=i;return Object.entries(r).flatMap(([i,r])=>{const s=n[i],o="number"!=typeof s||Number.isNaN(s)?a?"required":void 0:function(e,t){if(null!==t.min&&e<t.min||null!==t.max&&e>t.max)return"out_of_range";const i=e/t.resolution;return Math.abs(i-Math.round(i))<1e-6?void 0:"invalid_resolution"}(s,r);return o?[{code:o,section:e,target:t,field:i}]:[]})}function Hi(e,t,i){const r=e.entity_id;return null===r?[]:ui(e).flatMap(({name:a,field:n,action:s})=>{const o=(t,i)=>Si(e,t,i?`${n}.${i}`:n);if(!ki(t,a,r,s))return[o("default"===s?.mode?"default_action_unavailable":"domain_action_unavailable")];const l=Vt(t,a,r,s);return l?Object.entries(function(e,t,i){const r={};for(const a of e.parameters){const e=a.name in t?Tt(a,t[a.name],i):"required";e&&(r[a.name]=e)}return r}(l,s?.data??{},i[r])).map(([e,t])=>o(t,e)):[]})}function Ti(e,t,i){return i.filter(({action:e})=>function(e){return null===e||"custom"===e.mode&&0===(e.action??[]).length||"entity"===e.mode&&!e.entity_id||"domain"===e.mode&&Object.values(e.data??{}).some(Ci)}(e)).map(({field:i})=>({code:"missing_action",section:e,target:t.id,field:i}))}function Li(e,t){return e.device_id?t.devices?.[e.device_id]?function(e){return[["on_off_entity","on_off_entity"===e.switched_by?e.on_off_entity:null],["set_current","entity"===e.set_current?.mode?e.set_current.entity_id:null],["car_connected",ci(e.car_connected)],["actively_charging",ci(e.actively_charging)],["charging_power",ci(e.charging_power)],["fault_flag",ci(e.fault_flag)]].filter(e=>!!e[1])}(e).filter(([,i])=>t.entities?.[i]?.device_id!==e.device_id).map(([e])=>["entity_not_on_device",e]):[["unknown_device","device_id"]]:[]}class Di extends fe{constructor(){super(...arguments),this.narrow=!1,this.entityNames={},this.issues=[],this.saveErrors=[],this.locked=!1,this.describeIssue=e=>ti(e,this.localize,this.capabilities,this.hass.language)}changeConfig(e){!function(e,t){e.dispatchEvent(new CustomEvent(Xe,{detail:t,bubbles:!0,composed:!0}))}(this,e)}formErrors(e,t,i=""){return ii(Ai(this.issues,e,t),i,this.describeIssue)}entitiesUsedBesides(e){return[...this.config.appliances,...rt(this.config)].flatMap(t=>{const i=t.id===e?null:jt(t);return i?[i]:[]})}renderCard(e){const t=e.sections?.map(e=>X`<div class="section">${e}</div>`)??te,i=e.description||e.sections?.length||void 0!==e.content&&e.content!==te;return X`
      <ha-card>
        <div class="card-header">
          <h2 class="card-title">${e.title}</h2>
          ${e.control??te}
        </div>
        ${i?X`<div class="card-content">${ni(e.description)} ${e.content??te} ${t}</div>`:te} ${e.list??te}
        ${e.footer??te}
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
        `:X`<div class="empty">${e.empty}</div>`}static{this.styles=[ri,g`
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
      .section {
        display: grid;
        gap: 16px;
      }
      .section + .section {
        margin-inline: -16px;
        padding: 16px 16px 0;
        border-top: 1px solid var(--divider-color);
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
    `]}}e([$e({attribute:!1})],Di.prototype,"hass",void 0),e([$e({attribute:!1})],Di.prototype,"localize",void 0),e([$e({type:Boolean,reflect:!0})],Di.prototype,"narrow",void 0),e([$e({attribute:!1})],Di.prototype,"config",void 0),e([$e({attribute:!1})],Di.prototype,"entityNames",void 0),e([$e({attribute:!1})],Di.prototype,"capabilities",void 0),e([$e({attribute:!1})],Di.prototype,"issues",void 0),e([$e({attribute:!1})],Di.prototype,"saveErrors",void 0),e([$e({type:Boolean,reflect:!0})],Di.prototype,"locked",void 0);const Ni={power_limit_w:"W",turn_on_margin_w:"W",wait_at_limit_s:"s",ampere_damping_s:"s",penalty_threshold_w:"W",command_repeat_interval_min:"min",action_timeout_s:"s",power_sensor_timeout_s:"s"},Pi=new Set(["regulation_window_updates","appliance_repeat_increment_factor","appliance_repeat_increments","charger_waiting_factor"]);class Oi extends Di{constructor(){super(...arguments),this.computeLabel=e=>this.localize(`general.fields.${e.name}.label`),this.computeHelper=e=>this.helperText(e)}renderForm(e){return X`
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
      `)}numberField(e){const t=this.range(e);return{name:e,required:!0,selector:{number:{min:t.min??void 0,max:t.max??void 0,step:t.resolution,mode:"box",unit_of_measurement:Ni[e]}}}}selectField(e,t){const i=this.range(e),r=[];for(let e=i.min??i.resolution;e<=(i.max??e);e+=i.resolution)r.push({value:String(e),label:t(e)});return{name:e,required:!0,selector:{select:{mode:"dropdown",options:r}}}}range(e){return this.capabilities.limits.general[e]}get formData(){const e=this.config.general;return Object.fromEntries(Object.entries(e).map(([e,t])=>[e,Pi.has(e)&&null!==t?String(t):t]))}valueChanged(e){const t=e.detail.value,i={...this.config.general};for(const e of Object.keys(i)){const r=t[e];i[e]=Pi.has(e)&&void 0!==r?Number(r):r??null}this.changeConfig({...this.config,general:i})}helperText(e){const t=this.range(e.name),i=this.capabilities.defaults.general;return this.localize(`general.fields.${e.name}.helper`,{min:this.formatNumber(t?.min),max:this.formatNumber(t?.max),default:this.formatNumber(i[e.name])})}formatNumber(e){return null==e?"":new Intl.NumberFormat(this.hass.language).format(e)}static{this.styles=Di.styles}}const Fi=["wait_curve_steepness","wait_curve_pivot","appliance_repeat_increment_factor","appliance_repeat_increments","ampere_damping_s","charger_waiting_factor","command_repeat_interval_min","action_timeout_s","power_sensor_timeout_s"],Wi=60,ji=[.1,.2,.5,1,2,5,10];const Ii={wait_curve_steepness:!1,wait_curve_pivot:!0};let Ri=class extends Oi{constructor(){super(...arguments),this.narrowQuery=new At(this,760)}get narrowPage(){return this.narrowQuery.matches}render(){return X`
      ${this.renderWaitCurveCard()} ${this.renderRepeatedTurnOnCard()} ${this.renderChargersCard()} ${this.renderCommandRepeatCard()} ${this.renderTimeoutsCard()}
      ${this.renderRestoreDefaults(Fi)}
    `}renderWaitCurveCard(){return this.renderCard({title:this.localize("advanced.wait_curve"),description:this.localize("advanced.wait_curve_info"),content:X`
        <div class="sliders">${["wait_curve_steepness","wait_curve_pivot"].map(e=>this.renderSlider(e))}</div>
        ${this.renderWaitCurve()}
      `})}renderRepeatedTurnOnCard(){return this.renderCard({title:this.localize("advanced.repeated_turn_on"),description:this.localize("advanced.repeated_turn_on_info"),content:this.renderRepeatedTurnOn()})}renderChargersCard(){return this.renderCard({title:this.localize("advanced.chargers"),description:this.localize("advanced.chargers_info"),content:this.renderForm([this.numberField("ampere_damping_s"),this.selectField("charger_waiting_factor",e=>`${e}×`)])})}renderCommandRepeatCard(){return this.renderCard({title:this.localize("advanced.command_repeat"),description:this.localize("advanced.command_repeat_info"),content:this.renderForm([this.numberField("command_repeat_interval_min")])})}renderTimeoutsCard(){return this.renderCard({title:this.localize("advanced.timeouts"),description:this.localize("advanced.timeouts_info"),content:this.renderForm([this.numberField("action_timeout_s"),this.numberField("power_sensor_timeout_s")])})}renderRepeatedTurnOn(){const e=this.hass.language,t=this.config.general,i=[this.selectField("appliance_repeat_increment_factor",t=>`× ${new Intl.NumberFormat(e).format(t)}`),this.selectField("appliance_repeat_increments",e=>String(e))];return X`
      ${this.renderForm(i)} ${this.narrowPage?te:this.renderRepeatedTurnOnTable(t.appliance_repeat_increment_factor,t.appliance_repeat_increments)}
    `}renderRepeatedTurnOnTable(e,t){const i=this.config.general,r=i.wait_at_limit_s,a=this.decisionInterval,n=kt(i.wait_curve_steepness,i.wait_curve_pivot)(i.wait_curve_pivot/100),s=Array.from({length:t+2+1},(e,t)=>t+1),o=(i,s)=>{if(null===r||s&&null===a)return"–";const o=i<=2?r*n:function(e,t,i,r){return t+t*i*Math.min(r,e-2-1)}(i,r,e,t);return ut(s?xt(o,a):o)};return X`
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
    `}get decisionInterval(){return bt(this.config.general)}renderSlider(e){const t=this.range(e),i=this.config.general[e],r=Ii[e]?100-i:i,a=this.localize(`general.fields.${e}.label`),n=Ii[e]?" %":"";return X`
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
    `}changeCurve(e,t){t!==this.config.general[e]&&this.changeConfig({...this.config,general:{...this.config.general,[e]:t}})}renderWaitCurve(){const e=this.config.general,t=kt(e.wait_curve_steepness,e.wait_curve_pivot),i=e=>t(1-e/100),r=this.hass.language,a=e.power_limit_w,n=e.wait_at_limit_s,s=this.decisionInterval,o=e=>null===n?null:n*i(e),l=(e,t)=>X`
      <tr>
        <th>${this.localize(e)}</th>
        ${[50,40,30,25,20,15,10,7,4,1].map(e=>X`<td>${t(e)}</td>`)}
      </tr>
    `;return X`
      ${this.narrowPage?te:X`<table class="curve-table">
              ${l("advanced.free_power_kw",e=>pt(r,null===a?null:a*e/100))}
              ${l("advanced.waiting_minutes",e=>ut(o(e)))} ${l("advanced.actual_waiting_minutes",e=>ut((e=>{const t=o(e);return null===t||null===s?null:xt(t,s)})(e)))}
            </table>`}
      ${this.renderCurveGraph(i,a)}
    `}renderCurveGraph(e,t){const i=this.hass.language,[r,a]=this.narrowPage?[320,200]:[900,260],[n,s,o,l]=[44,24,8,38],d=e=>n+(r-n-s)*(Wi-e)/Wi,c=e=>o+(a-o-l)*(100-e)/100,h=`M${Array.from({length:201},(t,i)=>{const r=Wi-i*Wi/200;return`${d(r)},${c(100*e(r))}`}).join("L")}`,p=null===t?0:t/1e3,u=p*Wi/100,g=(m=u,_=this.narrowPage?4:10,ji.find(e=>m/e<=_)??ji[ji.length-1]);var m,_;const f=u>0?Array.from({length:Math.floor(u/g+1e-9)+1},(e,t)=>t*g):[],v=g<1?1:0;return X`
      <svg class="curve" viewBox="0 0 ${r} ${a}" role="img" aria-label=${this.localize("advanced.wait_curve")}>
        ${[0,20,40,60,80,100].map(e=>Y`
            <line class="grid" x1=${n} x2=${r-s} y1=${c(e)} y2=${c(e)}></line>
            <text x=${n-6} y=${c(e)+4} text-anchor="end">${ht(i,e,0)} %</text>
          `)}
        ${f.map(e=>Y`<text x=${d(100*e/p)} y=${a-l+18} text-anchor="middle">${ht(i,e,v)}</text>`)}
        <text x=${d(30)} y=${a-4} text-anchor="middle">${this.localize("advanced.free_power_kw")}</text>
        <path class="area" d="${h}L${d(0)},${c(0)}L${d(Wi)},${c(0)}Z"></path>
        <path class="line" d=${h}></path>
      </svg>
    `}static{this.styles=[Oi.styles,g`
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
    `]}};Ri=e([we("kraftvakt-advanced-page")],Ri);const Bi=new Set(["unknown","unavailable",""]);const Ui={condition:["entity","template"],one_at_a_time:["entity","template"],actively_charging:["entity","template"],charging_power:["power_sensor","template"],fault:["entity","template"],display_power:["power_sensor","template"],display_temperature:["temperature_sensor","template"]},qi=["current_temperature","target_temperature"];let Gi=class extends fe{constructor(){super(...arguments),this.value=null,this.variables={},this.kind="condition",this.disabled=!1,this.optional=!1,this.history={entityId:"",states:[]},this.previewedVariables="",this.computeLabel=e=>{switch(e.name){case"value":return this.text(`${this.shownType()}_label`);case"states":return this.text("states_label");default:return this.optionalText("type_label")}},this.computeHelper=e=>{switch(e.name){case"value":return this.text(`${this.shownType()}_helper`,{variables:Object.keys(this.variables).join(", ")});case"states":return this.text("states_helper");default:return""}}}disconnectedCallback(){super.disconnectedCallback(),this.stopPreview()}updated(e){const t=JSON.stringify(this.variables);(e.has("value")||t!==this.previewedVariables)&&(this.previewedVariables=t,this.schedulePreview()),e.has("value")&&this.loadHistory()}render(){const e=this.shownType(),t=this.types().map(e=>({value:e,label:this.text(e)}));return X`
      ${this.renderForm([{name:"type",selector:{select:{mode:"list",options:t}}}])}
      <div class="shown" part="shown">${this.renderForm(this.valueField(e))} ${this.renderPreview()} ${this.error?X`<div class="error">${this.error}</div>`:te}</div>
    `}renderForm(e){return X`
      <ha-form
        .hass=${this.hass}
        .data=${this.formData()}
        .schema=${e}
        .disabled=${this.disabled}
        .computeLabel=${this.computeLabel}
        .computeHelper=${this.computeHelper}
        @value-changed=${this.valueChanged}
      ></ha-form>
    `}formData(){const e=this.shownType();return{type:e,value:this.listsTemperatures(e)&&this.value?.value?Ki(this.value):this.value?.value??"",states_are_true:String(this.value?.states_are_true??!0),states:this.value?.states??[]}}shownType(){const e=this.value?.type??this.types()[0];return qi.includes(e)?"temperature_sensor":e}listsTemperatures(e){return"temperature_sensor"===e&&void 0!==this.includeEntities}types(){const e=Ui[this.kind];return this.stateChoices?e.flatMap(e=>"entity"===e?[e,"state"]:[e]):e}valueField(e){switch(e){case"entity":return[{name:"value",required:!this.optional,selector:{entity:{filter:{domain:Ft},include_entities:this.includeEntities}}}];case"power_sensor":return[{name:"value",required:!this.optional,selector:{entity:{filter:{domain:"sensor",device_class:"power"},include_entities:this.includeEntities,exclude_entities:Bt(this.hass)}}}];case"temperature_sensor":case"current_temperature":case"target_temperature":return this.listsTemperatures(e)?[{name:"value",required:!this.optional,selector:{select:{mode:"dropdown",options:this.temperatureOptions()}}}]:[{name:"value",required:!this.optional,selector:{entity:{filter:{domain:"sensor",device_class:"temperature"},include_entities:this.includeEntities}}}];case"state":return[{name:"value",required:!this.optional,selector:{entity:{include_entities:this.includeEntities}}},...this.value?.value&&this.stateChoices?[{name:"states_are_true",selector:{select:{mode:"list",options:[{value:"true",label:this.stateChoices.true},{value:"false",label:this.stateChoices.false}]}}},{name:"states",required:!this.optional,selector:{select:{multiple:!0,custom_value:!0,options:this.stateOptions()}}}]:[]];case"template":return[{name:"value",required:!this.optional,selector:{template:{}}}]}}temperatureOptions(){const e=(t=this.hass,(this.includeEntities??[]).flatMap(e=>e.startsWith("climate.")?[{type:"current_temperature",entityId:e},{type:"target_temperature",entityId:e}]:e.startsWith("sensor.")&&"temperature"===t.states[e]?.attributes.device_class?[{type:"temperature_sensor",entityId:e}]:[]));var t;const i=this.value?.value?{type:this.value.type,entityId:this.value.value}:void 0;return i&&!e.some(e=>Ki(e)===Ki(i))&&e.push(i),e.map(e=>({value:Ki(e),label:this.temperatureLabel(e)}))}temperatureLabel(e){const t=this.hass.states[e.entityId]?.attributes.friendly_name??e.entityId;return"temperature_sensor"===e.type?t:this.text(e.type,{name:t})}stateOptions(){const e=this.value?.value??"",t=this.hass.states[e],i=this.history.entityId===e?this.history.states:[];return function(e,t,i){const r=e?.attributes.options,a=[...Array.isArray(r)?r.map(String):[],e?.state??"",...t,...i];return[...new Set(a.filter(e=>!Bi.has(e)))]}(t,i,this.value?.states??[]).map(e=>{const i=t?this.hass.formatEntityState(t,e):e;return{value:e,label:i===e?e:`${i} (${e})`}})}loadHistory(){const e="state"===this.value?.type?this.value.value:"";e&&this.history.entityId!==e&&(this.history={entityId:e,states:[]},async function(e,t){const i=new Date(Date.now()-6048e5),r=await e.callWS({type:"history/history_during_period",start_time:i.toISOString(),entity_ids:[t],minimal_response:!0,no_attributes:!0,significant_changes_only:!1});return[...new Set((r[t]??[]).map(e=>e.s))]}(this.hass,e).then(t=>{this.history.entityId===e&&(this.history={entityId:e,states:t})}).catch(()=>{}))}renderPreview(){if(!this.value?.value)return te;if("template"===this.value.type&&void 0!==this.preview?.error)return X`<div class="preview error">${this.localize("condition.error",{message:this.preview.error})}</div>`;if("template"===this.value.type&&!this.preview)return te;if("display_power"===this.kind||"display_temperature"===this.kind)return this.renderDisplayValue(this.value);const e=this.evidence(this.value);return X`
      ${this.renderNow(this.value,e)}
      ${"template"===this.value.type&&null===e?X`<div class="warning">${this.text("invalid",{value:JSON.stringify(this.preview?.result)})}</div>`:te}
    `}evidence(e){switch(e.type){case"template":if("charging_power"===this.kind){const e=Zi(this.preview?.result);return null===e?null:e>100}return"boolean"==typeof this.preview?.result?this.preview.result:null;case"power_sensor":{const t=qt(this.hass,e.value);return null===t?null:t>100}case"state":return t=this.hass.states[e.value]?.state,i=e.states??[],r=e.states_are_true??!0,void 0===t||Bi.has(t)?null:i.includes(t)===r;default:{const t=this.hass.states[e.value]?.state;return"on"===t||"off"!==t&&null}}var t,i,r}renderNow(e,t){const i=this.text(!0===t?"true":"false"),r="template"===e.type?void 0:this.hass.states[e.value],a="entity"===e.type&&("on"===r?.state||"off"===r?.state),n="template"===e.type&&"charging_power"===this.kind?Zi(this.preview?.result):null;return X`
      <div class="preview">
        ${this.localize("condition.now",{value:""})}${r?X`<b>${this.hass.formatEntityState(r)}</b>${a?te:X` · ${i}`}`:null!==n?X`<b>${new Intl.NumberFormat(this.hass.language).format(n)} W</b> · ${i}`:X`<b>${i}</b>`}
      </div>
    `}renderDisplayValue(e){const t=qi.includes(e.type),i="template"===e.type||t?void 0:this.hass.states[e.value],r="template"===e.type?Ji(this.preview?.result):t?(a=this.hass,Dt({type:(n={type:e.type,entityId:e.value}).type},a.states[n.entityId])):null;var a,n;if("template"===e.type&&null===r)return X`<div class="warning">${this.text("invalid",{value:JSON.stringify(this.preview?.result)})}</div>`;const s="display_power"===this.kind?"W":this.hass.config.unit_system.temperature,o=null!==r?`${new Intl.NumberFormat(this.hass.language).format("display_power"===this.kind?Math.max(r,0):r)} ${s}`:i?this.hass.formatEntityState(i):this.text("no_value");return X`<div class="preview">${this.localize("condition.now",{value:""})}<b>${o}</b></div>`}text(e,t){return this.localize(`${this.kind}.${e}`,t)}optionalText(e){const t=this.text(e);return t===`${this.kind}.${e}`?"":t}valueChanged(e){e.stopPropagation();const{type:t,value:i,states:r,states_are_true:a}={...this.formData(),...e.detail.value},n=t===this.shownType(),s=n&&this.listsTemperatures(t)&&i?function(e){const[t,i]=e.split("|");return{type:t,entityId:i}}(i):void 0,o=s?{type:s.type,value:s.entityId}:{type:t,value:n?i??"":""};if("state"===t){const e=n&&o.value===this.value?.value;o.states=e?r??[]:[],o.states_are_true=!e||"false"!==a}this.dispatchEvent(new CustomEvent("value-changed",{detail:{value:o}}))}schedulePreview(){if(this.stopPreview(),"template"!==this.value?.type||!this.value.value.trim())return void(this.preview=void 0);const e=this.value.value;this.previewTimer=window.setTimeout(()=>this.startPreview(e),500)}startPreview(e){this.unsubscribePreview=this.hass.connection.subscribeMessage(e=>this.preview=e,{type:"render_template",template:e,variables:this.variables,report_errors:!0}),this.unsubscribePreview.catch(e=>{this.preview={error:String(e instanceof Object&&"message"in e?e.message:e)}})}stopPreview(){window.clearTimeout(this.previewTimer),this.unsubscribePreview?.then(e=>e()).catch(()=>{}),this.unsubscribePreview=void 0}static{this.styles=g`
    :host {
      display: block;
    }
    /* From edge to edge of the group, across its padding. */
    .shown {
      margin: 16px -16px 0;
      padding: 16px 16px 0;
      border-top: 1px solid var(--divider-color);
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
  `}};function Ki(e){return"entityId"in e?`${e.type}|${e.entityId}`:`${e.type}|${e.value}`}function Zi(e){const t=Ji(e);return null===t?null:Math.max(t,0)}function Ji(e){const t="string"==typeof e&&""!==e.trim()?Number(e):e;return"number"==typeof t&&Number.isFinite(t)?t:null}e([$e({attribute:!1})],Gi.prototype,"hass",void 0),e([$e({attribute:!1})],Gi.prototype,"localize",void 0),e([$e({attribute:!1})],Gi.prototype,"value",void 0),e([$e({attribute:!1})],Gi.prototype,"variables",void 0),e([$e({attribute:!1})],Gi.prototype,"includeEntities",void 0),e([$e()],Gi.prototype,"kind",void 0),e([$e()],Gi.prototype,"error",void 0),e([$e({type:Boolean})],Gi.prototype,"disabled",void 0),e([$e({type:Boolean})],Gi.prototype,"optional",void 0),e([$e({attribute:!1})],Gi.prototype,"stateChoices",void 0),e([ke()],Gi.prototype,"history",void 0),e([ke()],Gi.prototype,"preview",void 0),Gi=e([we("kraftvakt-condition-field")],Gi);let Qi=class extends fe{constructor(){super(...arguments),this.label="",this.value=null,this.entityId=null,this.defaultAvailable=!1,this.entityDomains=[],this.domainActions={},this.parameterErrors={},this.variables=[],this.disabled=!1}render(){const e=this.onlyMode??this.value?.mode,t=this.domainAction,i=this.shownSchema(e);return X`
      <div class="field ${this.error?"invalid":""}">
        ${this.label?X`<div class="label">${this.label}</div>`:te}
        ${this.onlyMode?te:this.renderForm([{name:"mode",selector:{select:{mode:"list",options:this.modeOptions}}}])}
        ${i.length||t?X`
                <div class=${this.onlyMode?"":"shown"}>${i.length?this.renderForm(i):te} ${t?this.renderParameters(t):te}</div>
              `:te}
        <div class="helper">${this.helperText(e)}</div>
        ${this.error?X`<div class="error">${this.error}</div>`:te}
      </div>
    `}renderParameters(e){const t=this.value?.data??{};return X`
      <ha-form
        .hass=${this.hass}
        .data=${this.parameterFormData(e,t)}
        .schema=${e.parameters.flatMap(e=>this.parameterFields(e,t[e.name]??null))}
        .error=${this.parameterFormErrors(t)}
        .disabled=${this.disabled}
        .computeLabel=${e=>this.localize(`action.parameters.${e.name}`)}
        .computeHelper=${i=>this.parameterHelper(e,i.name,t[i.name]??null)}
        @value-changed=${this.parametersChanged}
      ></ha-form>
    `}parameterFormData(e,t){return Object.fromEntries(e.parameters.flatMap(({name:e,type:i})=>{const r=t[e]??null;return"temperature"!==i?[[e,r??void 0]]:tr(r)?[[`${e}_from`,"source"],[`${e}_entity`,r.value??void 0],[`${e}_reading`,r.type]]:[[`${e}_from`,ir(r)],[e,r??void 0]]}))}parameterFormErrors(e){return Object.fromEntries(Object.entries(this.parameterErrors).map(([t,i])=>[tr(e[t]??null)?`${t}_entity`:t,i]))}parameterFields(e,t){const i=this.stateObj;if("option"===e.type){const t=function(e,t){const i=Pt(t,e.options_attribute);return Array.isArray(i)?i.map(String):e.preferred_options}(e,i).map(e=>({value:e,label:i?this.hass.formatEntityState(i,e):e}));return[{name:e.name,required:!0,selector:{select:{mode:"dropdown",options:t}}}]}const r={name:`${e.name}_from`,selector:{select:{mode:"list",options:Xi.map(e=>({value:e,label:this.localize(`action.value_from.${e}`)}))}}};if(tr(t)){const i=t.value?.startsWith("climate.")??!1;return[r,{name:`${e.name}_entity`,required:!0,selector:{entity:{filter:{domain:er},exclude_entities:this.entityId?[this.entityId]:[]}}},...i?[{name:`${e.name}_reading`,required:!0,selector:{select:{mode:"dropdown",options:Yi.map(e=>({value:e,label:this.localize(`action.readings.${e}`)}))}}}]:[]]}if("string"==typeof t)return[r,{name:e.name,required:!0,selector:{template:{}}}];const{min:a,max:n,step:s}=Ht(e,i),o=this.hass.config.unit_system.temperature;return[r,{name:e.name,required:!0,selector:{number:{min:a,max:n,step:s??"any",mode:"box",unit_of_measurement:o}}}]}parameterHelper(e,t,i){const r=e.parameters.find(e=>e.name===t||`${e.name}_entity`===t);if(!r)return"";if(t===`${r.name}_entity`){const e=this.value?.data?.[r.name]??null;return tr(e)?this.sourceHelper(r,e):""}return"string"==typeof i&&function(e){return"temperature"===e.type}(r)?this.localize("action.variables",{variables:this.variables.join(", ")}):this.rangeText(r,"action.parameter_range")}sourceHelper(e,t){const i=this.rangeText(e,"action.source_range")||this.localize("action.source_read");if(!t.value)return i;const r=this.hass.states[t.value],a=Dt(t,r);if(null===a)return[this.localize("action.source_no_value"),i].join(" ");const n="temperature_sensor"===t.type&&r?this.hass.formatEntityState(r):`${new Intl.NumberFormat(this.hass.language).format(a)} ${this.hass.config.unit_system.temperature}`;return[this.localize("action.source_now",{value:n}),i].join(" ")}rangeText(e,t){const{min:i,max:r}=Ht(e,this.stateObj);if(void 0===i||void 0===r)return"";const a=e=>new Intl.NumberFormat(this.hass.language).format(e);return this.localize(t,{min:a(i),max:a(r),unit:this.hass.config.unit_system.temperature})}get modeOptions(){return[...this.defaultAvailable?[{value:"default",label:this.localize("action.default")}]:[],...Object.keys(this.domainActions).map(e=>({value:e,label:this.localize(`action.domain_actions.${e}`)})),...this.entityDomains.length?[{value:"entity",label:this.localize("action.entity")}]:[],{value:"custom",label:this.localize("action.custom")}]}get onlyMode(){return 1===this.modeOptions.length?"custom":void 0}renderForm(e){const t=this.onlyMode??this.value?.mode;return X`
      <ha-form .hass=${this.hass} .data=${this.formData(t)} .schema=${e} .disabled=${this.disabled} .computeLabel=${()=>""} @value-changed=${this.valueChanged}></ha-form>
    `}formData(e){return{mode:"domain"===e?this.value?.domain_action:e,action:this.value?.action??[],entity_id:this.value?.entity_id??void 0}}shownSchema(e){return[..."entity"===e?[{name:"entity_id",selector:{entity:{filter:{domain:this.entityDomains},include_entities:this.includeEntities}}}]:[],..."custom"===e?[{name:"action",selector:{action:{}}}]:[]]}helperText(e){if("custom"===e)return this.localize("action.variables",{variables:this.variables.join(", ")});if("domain"===e){const e=this.domainAction;return e?this.localize("action.default_runs",{service:`${e.domain}.${e.service}`}):""}if("entity"===e){const e=this.value?.entity_id;return e?this.localize("action.entity_runs",{service:this.defaultService(e)}):this.localize("action.choose_action_entity")}return this.defaultAvailable&&this.entityId?this.localize("action.default_runs",{service:this.defaultService(this.entityId)}):this.localize(this.entityId?"action.no_default":"action.choose_entity")}valueChanged(e){e.stopPropagation();const{action:t,entity_id:i,mode:r}={...this.formData(this.onlyMode??this.value?.mode),...e.detail.value},a=this.onlyMode??r,n=a?this.domainActions[a]:void 0,s=n?{mode:"domain",domain_action:a,data:Mt(n,this.stateObj,this.value?.data)}:"default"===a?{mode:a}:"entity"===a?{mode:a,entity_id:i||null}:"custom"===a?{mode:a,action:"custom"===this.value?.mode||this.onlyMode?rr(t):this.defaultSteps()}:null;this.fireChanged(s)}parametersChanged(e){e.stopPropagation();const t=e.detail.value,i=this.value?.data??{},r=Object.fromEntries((this.domainAction?.parameters??[]).map(({name:e,type:r})=>{if("temperature"!==r)return[e,t[e]??null];const a=t[`${e}_from`];if(a!==ir(i[e]??null))return[e,"number"===a?null:"template"===a?"":{type:"temperature_sensor",value:null}];if("source"===a){const i=t[`${e}_entity`]||null,r=t[`${e}_reading`];return[e,{type:i?.startsWith("climate.")??!1?Yi.includes(r)?r:"target_temperature":"temperature_sensor",value:i}]}return[e,t[e]??("template"===a?"":null)]}));this.fireChanged({...this.value,data:r})}fireChanged(e){this.dispatchEvent(new CustomEvent("value-changed",{detail:{value:e}}))}get domainAction(){return"domain"===this.value?.mode&&this.value.domain_action?this.domainActions[this.value.domain_action]:void 0}get stateObj(){return this.entityId?this.hass.states[this.entityId]:void 0}defaultSteps(){if(!this.defaultAvailable||!this.entityId)return[];const e=this.defaultAction?.data??{};return[{action:this.defaultService(this.entityId),target:{entity_id:this.entityId},...Object.keys(e).length?{data:e}:{}}]}defaultService(e){return`${e.split(".")[0]}.${this.defaultAction?.service}`}static{this.styles=g`
    .label {
      margin-bottom: 8px;
      font-weight: var(--ha-font-weight-medium, 500);
    }
    .invalid .label {
      color: var(--error-color);
    }
    /* What the chosen way shows is divided from the choice by a line from edge to edge of the group, across its padding. */
    .shown {
      display: grid;
      gap: 16px;
      margin: 16px -16px 0;
      padding: 16px 16px 0;
      border-top: 1px solid var(--divider-color);
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
  `}};e([$e({attribute:!1})],Qi.prototype,"hass",void 0),e([$e({attribute:!1})],Qi.prototype,"localize",void 0),e([$e()],Qi.prototype,"label",void 0),e([$e({attribute:!1})],Qi.prototype,"value",void 0),e([$e({attribute:!1})],Qi.prototype,"entityId",void 0),e([$e({attribute:!1})],Qi.prototype,"defaultAction",void 0),e([$e({type:Boolean})],Qi.prototype,"defaultAvailable",void 0),e([$e({attribute:!1})],Qi.prototype,"entityDomains",void 0),e([$e({attribute:!1})],Qi.prototype,"includeEntities",void 0),e([$e({attribute:!1})],Qi.prototype,"domainActions",void 0),e([$e({attribute:!1})],Qi.prototype,"parameterErrors",void 0),e([$e({attribute:!1})],Qi.prototype,"variables",void 0),e([$e()],Qi.prototype,"error",void 0),e([$e({type:Boolean})],Qi.prototype,"disabled",void 0),Qi=e([we("kraftvakt-action-field")],Qi);const Xi=["number","source","template"],Yi=["target_temperature","current_temperature"],er=[...new Set(Object.values(Lt).flat())];function tr(e){return"object"==typeof e&&null!==e}function ir(e){return tr(e)?"source":"string"==typeof e?"template":"number"}function rr(e){return Array.isArray(e)?e:e&&"object"==typeof e?[e]:[]}class ar extends fe{constructor(){super(...arguments),this.isNew=!1,this.usedEntities=[],this.saveErrors=[],this.locked=!1,this.open=!0,this.describe=e=>ti(e,this.localize,this.capabilities,this.hass.language)}willUpdate(e){e.has("item")&&(this.draft=structuredClone(this.item))}render(){const e=this.errors(),t=[...e,...this.isNew?[]:this.missing(),...this.saveErrors];return X`
      <ha-dialog .open=${this.open} .headerTitle=${this.heading} prevent-scrim-close @closed=${this.closed}>
        <div class="content">${this.renderFields(t)}</div>
        <div slot="footer">${this.renderButtons(e.length>0)}</div>
      </ha-dialog>
    `}get entityScope(){}get actionEntity(){return"entity_id"in this.draft?this.draft.entity_id:null}get variables(){return e=this.hass,"switched_by"in(t=this.draft)?{device_id:t.device_id}:{entity_id:t.entity_id,entity:t.entity_id?e.states[t.entity_id]??null:null};var e,t}renderEntityField(e,t,i,r){const a=[{name:e,required:!0,selector:{entity:{filter:r?{domain:r}:void 0,include_entities:this.entityScope,exclude_entities:this.usedEntities}}}];return this.renderForm(a,t,t=>i(t[e]||null))}renderAction(e,t,i={}){return this.renderActionField({name:e,field:e,value:this.draft[e],label:i.label},t,t=>this.changeDraft({[e]:t}),i)}renderActionGroup(e,t){return this.renderGroup({title:this.label(e),description:this.helper(e),content:this.renderAction(e,t,{label:""})})}renderActionField(e,t,i,{entityAllowed:r=!1,extraVariables:a=[]}={}){const{name:n,field:s}=e,o=t.find(e=>e.field===s),l=ii(t,`${s}.`,this.describe),d=$i(this.capabilities,this.section,n),c=this.actionEntity;return X`
      <kraftvakt-action-field
        .hass=${this.hass}
        .localize=${this.localize}
        .label=${e.label??this.label(n)}
        .value=${e.value}
        .entityId=${c}
        .defaultAction=${d}
        .defaultAvailable=${xi(this.capabilities,this.section,n,c)}
        .entityDomains=${r?d.domains:[]}
        .includeEntities=${this.entityScope}
        .domainActions=${"appliances"===this.section?St(this.capabilities,n,c):{}}
        .variables=${[...a,...Object.keys(this.variables)]}
        .error=${o?this.describe(o):void 0}
        .parameterErrors=${l}
        .disabled=${this.locked}
        @value-changed=${e=>i(e.detail.value)}
      ></kraftvakt-action-field>
    `}renderForm(e,t,i,r=this.draft){const a=e.flatMap(e=>e.schema?.map(e=>e.name)??[e.name]);return X`
      <ha-form
        .hass=${this.hass}
        .data=${r}
        .schema=${e}
        .error=${ii(t.filter(e=>void 0!==e.field&&a.includes(e.field)),"",this.describe)}
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
        ${ai(e.title,i)} ${ni(e.description)} ${r=e.content,Array.isArray(r)?X`<div class="parts">${r.filter(e=>e!==te).map(e=>X`<div class="part">${e}</div>`)}</div>`:r??te}
        ${e.error?X`<div class="error">${e.error}</div>`:te}
      </section>
    `;var r}changeDraft(e){this.draft={...this.draft,...e}}renderButtons(e){return this.locked?X`<ha-button @click=${this.close}>${this.localize("dialog.close")}</ha-button>`:X`
      ${this.isNew?te:X`<ha-button variant="danger" appearance="plain" @click=${this.delete}>${this.deleteText}</ha-button>`}
      <span class="spacer"></span>
      <ha-button appearance="plain" @click=${this.close}>${this.localize("dialog.cancel")}</ha-button>
      <ha-button .disabled=${e} @click=${this.confirm}>${this.localize("dialog.ok")}</ha-button>
    `}get deleteText(){return this.localize(`${this.texts}.delete`)}get heading(){return this.locked?this.localize(`${this.texts}.view_title`):this.localize(this.isNew?`${this.texts}.add_title`:`${this.texts}.edit_title`)}confirm(){this.dispatchEvent(new CustomEvent("item-changed",{detail:this.draft})),this.close()}delete(){this.dispatchEvent(new CustomEvent("item-deleted",{detail:this.draft.id})),this.close()}close(){this.open=!1}closed(e){e.stopPropagation(),this.dispatchEvent(new CustomEvent("closed"))}static{this.styles=[ri,g`
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
      .parts {
        display: grid;
        gap: 16px;
      }
      /* The line goes from edge to edge of the group, across its padding. */
      .part + .part {
        margin-inline: -16px;
        padding: 16px 16px 0;
        border-top: 1px solid var(--divider-color);
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
    `]}}e([$e({attribute:!1})],ar.prototype,"hass",void 0),e([$e({attribute:!1})],ar.prototype,"localize",void 0),e([$e({attribute:!1})],ar.prototype,"capabilities",void 0),e([$e({attribute:!1})],ar.prototype,"item",void 0),e([$e({type:Boolean})],ar.prototype,"isNew",void 0),e([$e({attribute:!1})],ar.prototype,"usedEntities",void 0),e([$e({attribute:!1})],ar.prototype,"saveErrors",void 0),e([$e({type:Boolean})],ar.prototype,"locked",void 0),e([ke()],ar.prototype,"open",void 0),e([ke()],ar.prototype,"draft",void 0);let nr=class extends ar{constructor(){super(...arguments),this.section="appliances",this.texts="appliance",this.fixedLoad=!1,this.entityChanged=e=>{const t=(t,i)=>function(e,t,i,r,a){if(null===i){const i=Object.entries(St(e,t,r)).find(([,e])=>e.suggested);if(i){const[e,t]=i;return{mode:"domain",domain_action:e,data:Mt(t,a)}}if(xi(e,"appliances",t,r))return{mode:"default"}}return null===r||ki(e,t,r,i)?i:{mode:"custom",action:[]}}(this.capabilities,t,i,e,e?this.hass.states[e]:void 0);this.changeDraft({entity_id:e,...di(this.draft,e,this.hass),turn_on:t("turn_on",this.draft.turn_on),turn_off:t("turn_off",this.draft.turn_off),variants:this.draft.variants.map(e=>({...e,actions:Object.fromEntries(Object.entries(e.actions).map(([e,i])=>[e,t(e,i??null)]))}))})},this.essentialChanged=e=>{e&&this.fixedLoadChanged(!1),this.changeDraft({essential:e})},this.fixedLoadChanged=e=>{this.fixedLoad=e,e||this.changeDraft({power_reserve_w:null})}}willUpdate(e){super.willUpdate(e),e.has("item")&&(this.fixedLoad=null!==this.item.power_reserve_w)}errors(){return zi(this.draft,this.capabilities,this.hass)}missing(){return yi(this.draft)}renderFields(e){const t=this.draft.essential;return X`
      ${this.renderEntityField("entity_id",e,this.entityChanged)} ${this.renderActions(e)} ${this.renderEssential(e)}
      ${t?te:this.renderFixedLoad(e)} ${t?te:this.renderVariants()} ${this.renderDisplayValues(e)}
    `}renderEssential(e){const t=e.find(e=>"essential"===e.field);return this.renderGroup({title:this.label("essential"),description:this.helper("essential"),toggle:{checked:this.draft.essential,disabled:!this.draft.essential&&this.draft.variants.length>0,changed:this.essentialChanged},error:t?this.describe(t):void 0})}renderFixedLoad(e){const t=this.fixedLoad||e.some(e=>"power_reserve_w"===e.field);return this.renderGroup({title:this.label("fixed_load"),description:this.helper("fixed_load"),toggle:{checked:this.fixedLoad,changed:this.fixedLoadChanged},content:t?this.renderForm([this.numberField("power_reserve_w","W",!1)],e,e=>this.changeDraft({power_reserve_w:e.power_reserve_w??null})):te})}renderDisplayValues(e){return this.renderGroup({title:this.localize("appliance.display_values"),description:this.localize("appliance.display_values_info"),content:[this.renderDisplayValue("display_power",e),this.renderDisplayValue("display_temperature",e)]})}renderDisplayValue(e,t){const i=t.find(t=>t.field===e);return X`
      <kraftvakt-condition-field
        .hass=${this.hass}
        .localize=${this.localize}
        .value=${this.draft[e]}
        .variables=${this.variables}
        .includeEntities=${function(e,t){const i=oi(e,t.entity_id);return i?si(e,i):void 0}(this.hass,this.draft)}
        .kind=${e}
        optional
        .error=${i?this.describe(i):void 0}
        .disabled=${this.locked}
        @value-changed=${t=>this.changeDraft({[e]:t.detail.value})}
      ></kraftvakt-condition-field>
    `}renderActions(e){return pi.map(t=>this.renderActionGroup(t,e))}renderVariants(){if(this.locked&&0===this.draft.variants.length)return te;const e=[...this.errors(),...this.saveErrors],t=this.locked||0===this.errors().length;return this.renderGroup({title:this.localize("appliance.variants"),description:this.localize("appliance.variants_info"),control:this.locked?te:X`
            <ha-button @click=${this.addVariant}>
              <ha-svg-icon slot="start" .path=${o}></ha-svg-icon>
              ${this.localize("appliance.add_variant")}
            </ha-button>
          `,content:0===this.draft.variants.length?te:X`
              <ha-sortable handle-selector=".handle" .disabled=${this.locked} @item-moved=${this.variantMoved}>
                <div class="variants">
                  ${zt(this.draft.variants,e=>e.id,i=>this.renderVariant(i,e,t))}
                </div>
              </ha-sortable>
            `})}renderVariant(e,t,r){const n=`variants.${e.id}.`,o=t.filter(e=>e.field?.startsWith(n)).map(e=>({...e,field:e.field?.slice(n.length)})),l=o.filter(e=>"label"!==e.field);return X`
      <div class="variant">
        <div class="variant-row">
          ${this.locked?te:X`<ha-svg-icon class="handle" .path=${i}></ha-svg-icon>`}
          <div class="label">
            ${this.renderForm(sr,o,t=>this.changeVariant(e.id,{label:t.label??""}),e)}
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
    `}openVariant(e){this.locked||this.dispatchEvent(new CustomEvent("item-changed",{detail:this.draft})),this.dispatchEvent(new CustomEvent("variant-opened",{detail:e})),this.close()}addVariant(){const e={id:Ye(),label:"",condition:{type:"template",value:""},actions:{}};this.changeDraft({variants:[...this.draft.variants,e]})}changeVariant(e,t){this.changeDraft({variants:this.draft.variants.map(i=>i.id===e?{...i,...t}:i)})}variantMoved(e){e.stopPropagation(),this.changeDraft({variants:et(this.draft.variants,e.detail.oldIndex,e.detail.newIndex)})}static{this.styles=[ar.styles,g`
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
    `]}};e([ke()],nr.prototype,"fixedLoad",void 0),nr=e([we("kraftvakt-appliance-dialog")],nr);const sr=[{name:"label",required:!0,selector:{text:{}}}];let or=class extends fe{constructor(){super(...arguments),this.kind="appliances",this.narrow=!1}render(){return X` <ha-alert alert-type="warning" .title=${this.localize(`warning.${this.kind}_title`)} .narrow=${this.narrow}> ${this.localize("warning.text")} </ha-alert> `}static{this.styles=g`
    :host {
      display: block;
    }
  `}};e([$e({attribute:!1})],or.prototype,"localize",void 0),e([$e()],or.prototype,"kind",void 0),e([$e({type:Boolean})],or.prototype,"narrow",void 0),or=e([we("kraftvakt-manual-control-warning")],or);let lr=class extends ar{constructor(){super(...arguments),this.variantId="",this.applianceName="",this.section="appliances",this.texts="appliance",this.setAsideActions=new Map}errors(){return this.ofVariant(zi(this.draft,this.capabilities,this.hass))}missing(){return this.ofVariant(yi(this.draft))}get deleteText(){return this.localize("variant.delete")}delete(){const e=this.draft.variants.filter(e=>e.id!==this.variantId);this.dispatchEvent(new CustomEvent("item-changed",{detail:{...this.draft,variants:e}})),this.close()}get heading(){const e=`${this.applianceName} «${this.variant?.label??""}»`;return this.localize(this.locked?"variant.view_title":"variant.edit_title",{name:e})}renderFields(e){const t=this.variant;if(!t)return X``;const i=e.find(e=>e.field===`${this.fieldPrefix}condition`);return X`
      ${this.renderGroup({title:this.localize("variant.condition"),description:this.localize("variant.condition_info"),content:X`
          <kraftvakt-condition-field
            .hass=${this.hass}
            .localize=${this.localize}
            .value=${t.condition}
            .variables=${this.variables}
            .error=${i?this.describe(i):void 0}
            .disabled=${this.locked}
            @value-changed=${e=>this.changeCondition(e.detail.value)}
          ></kraftvakt-condition-field>
        `})}
      ${pi.map(t=>this.renderOverride(t,e))}
    `}renderOverride(e,t){const i=this.variant?.actions??{},r=gi(i,e);return this.renderGroup({title:this.label(`override_${e}`),description:this.helper(`override_${e}`),toggle:{checked:r,changed:t=>this.override(e,t)},content:r?this.renderActionField({name:e,field:`${this.fieldPrefix}${e}`,value:i?.[e]??null,label:""},t,t=>this.changeVariant({actions:{...i,[e]:t}})):te})}get variant(){return this.draft.variants.find(e=>e.id===this.variantId)}get fieldPrefix(){return`variants.${this.variantId}.`}ofVariant(e){return e.filter(e=>e.field?.startsWith(this.fieldPrefix))}changeCondition(e){this.changeVariant({condition:e})}override(e,t){const{[e]:i,...r}=this.variant?.actions??{};if(t){const t=this.setAsideActions.has(e)?this.setAsideActions.get(e):structuredClone(this.draft[e]);this.changeVariant({actions:{...r,[e]:t??null}})}else this.setAsideActions.set(e,i??null),this.changeVariant({actions:r})}changeVariant(e){this.changeDraft({variants:this.draft.variants.map(t=>t.id===this.variantId?{...t,...e}:t)})}};e([$e()],lr.prototype,"variantId",void 0),e([$e()],lr.prototype,"applianceName",void 0),lr=e([we("kraftvakt-variant-dialog")],lr);const dr=["entity_id","essential","turn_on","turn_off","power_reserve_w","label","condition","display_power","display_temperature"];let cr=class extends Di{render(){return X`
      ${this.renderPriorityCard()}
      ${0===this.config.appliances.length?X` <kraftvakt-manual-control-warning .localize=${this.localize} .narrow=${this.narrow} kind="appliances"></kraftvakt-manual-control-warning> `:te}
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
    `}applianceSaveErrors(e){return Ai(this.saveErrors,"appliances",e.id)}applianceDialogClosed(){const e=this.config.appliances.find(e=>e.id===this.editing?.appliance.id),t=this.variantToOpen;this.editing=void 0,this.variantToOpen=void 0,e&&t&&(this.editingVariant={appliance:e,variantId:t})}row(e){if("charger_group"===e.type){const t=this.config.charger_groups.find(t=>t.id===e.group_id);return{key:tt(e),title:t?.name??"",iconPath:r,details:[X`${this.localize("appliances.charger_group_sub",{count:t?.chargers.length??0})}
            <a href="${lt}/charging" @click=${this.openChargingPage}>${this.localize("tabs.charging")}</a>`],errors:[],openable:!1}}const t=this.config.appliances.find(t=>t.id===e.appliance_id),i=t?.variants.find(t=>t.id===e.variant_id),a=Ai(this.issues,"appliances",e.appliance_id).filter(e=>i?e.field?.startsWith(`variants.${i.id}.`):!e.field?.startsWith("variants."));return{key:tt(e),title:t?this.applianceName(t):"",tag:i?.label,details:t?i?this.variantDetails(i):this.applianceDetails(t):[],errors:a.map(e=>`${this.fieldLabel(e)}: ${this.describeIssue(e)}`),openable:!0,highlighted:t?.essential}}applianceName(e){return e.entity_id?Wt(this.hass,this.entityNames,e.entity_id):this.localize("missing.appliance_without_entity")}applianceDetails(e){const t=e.entity_id?[e.entity_id]:[];return e.essential&&t.push(this.localize("appliances.essential")),null!==e.power_reserve_w&&t.push(this.localize("appliances.power_reserve",{power:ht(this.hass.language,e.power_reserve_w,0)})),e.variants.length>0&&t.push(this.localize("appliances.variant_count",{count:e.variants.length})),t}variantDetails(e){const t="entity"===e.condition.type?this.localize("appliances.variant_entity",{entity:e.condition.value}):this.localize("appliances.variant_template"),i=pi.filter(t=>gi(e.actions,t));return i.length===pi.length?[t,this.localize("appliances.variant_own_actions")]:[t,...i.map(e=>this.localize(`appliances.variant_own_${e}`))]}fieldLabel(e){const t=e.field?.split(".").at(-1)??"";return dr.includes(t)?this.localize(`appliance.fields.${t}.label`):t}entryMoved(e){const{oldIndex:t,newIndex:i}=e.detail;this.changeConfig({...this.config,priority:et(this.config.priority,t,i)})}addAppliance(){const e={id:Ye(),entity_id:null,turn_on:null,turn_off:null,essential:!1,power_reserve_w:this.capabilities.defaults.appliances.power_reserve_w,variants:[],display_power:null,display_temperature:null};this.editing={appliance:e,isNew:!0}}openRow(e){const t=this.config.priority.find(t=>tt(t)===e.detail);if("appliance"!==t?.type)return;const i=this.config.appliances.find(e=>e.id===t.appliance_id);i&&t.variant_id?this.editingVariant={appliance:i,variantId:t.variant_id}:i&&(this.editing={appliance:i,isNew:!1})}applianceChanged(e){const t=e.detail,i=this.config.appliances.some(e=>e.id===t.id)?this.config.appliances.map(e=>e.id===t.id?t:e):[...this.config.appliances,t];this.changeConfig({...this.config,appliances:i})}applianceDeleted(e){this.changeConfig({...this.config,appliances:this.config.appliances.filter(t=>t.id!==e.detail)})}openChargingPage(e){e.preventDefault(),dt("charging")}static{this.styles=Di.styles}};e([ke()],cr.prototype,"editing",void 0),e([ke()],cr.prototype,"editingVariant",void 0),cr=e([we("kraftvakt-appliances-page")],cr);let hr=class extends ar{constructor(){super(...arguments),this.section="chargers",this.texts="charger",this.profile=null}errors(){return Ei(this.draft,this.capabilities,this.hass)}get entityScope(){return si(this.hass,this.draft.device_id)}missing(){return bi(this.draft)}renderFields(e){return X`
      ${this.renderDevice(e)}
      ${this.renderForm([this.numberField("min_current_power_w","W",!0)],e,e=>this.changeDraft({min_current_power_w:e.min_current_power_w}))}
      ${this.renderOnOff(e)} ${this.renderStartDelay(e)} ${this.renderChargingCurrent(e)} ${this.renderCarConnected(e)} ${this.renderActivelyCharging(e)}
      ${this.renderCloudControl()} ${this.renderChargingWindow(e)} ${this.renderDeactivateOnFault(e)}
    `}renderOnOff(e){const t=Be.map(e=>({value:e,label:this.localize(`charger.switched_by.${e}`)})),i=this.renderForm([{name:"switched_by",required:!0,selector:{select:{mode:"list",options:t}}}],e,e=>this.switchedByChanged(e.switched_by));return this.renderGroup({title:this.localize("charger.on_off"),description:this.localize("charger.on_off_info"),content:[i,...this.renderOnOffChoice(e)]})}renderOnOffChoice(e){switch(this.draft.switched_by){case"on_off_entity":return[this.renderEntityField("on_off_entity",e,e=>this.changeDraft({on_off_entity:e}),$i(this.capabilities,"chargers","activate").domains)];case"actions":return[this.renderAction("activate",e),this.renderAction("deactivate",e)];case"current":return[X`<div class="helper">${this.localize("charger.switched_by_current_info")}</div>`]}}switchedByChanged(e){const t={mode:"custom",action:[]};this.changeDraft({switched_by:e??this.draft.switched_by,activate:this.draft.activate??t,deactivate:this.draft.deactivate??t})}renderStartDelay(e){return this.renderGroup({title:this.localize("charger.start"),description:this.localize("charger.start_info"),content:this.renderForm([this.numberField("start_delay_s","s",!0)],e,e=>this.changeDraft({start_delay_s:e.start_delay_s}))})}renderChargingCurrent(e){const t=[{type:"grid",name:"",schema:[this.numberField("min_current_a","A",!0),this.numberField("max_current_a","A",!0)]}];return this.renderGroup({title:this.localize("charger.charging_current"),description:this.localize("charger.charging_current_info"),content:[this.renderForm(t,e,e=>this.changeDraft({min_current_a:e.min_current_a,max_current_a:e.max_current_a})),this.renderAction("set_current",e,{entityAllowed:!0,extraVariables:["current","min_current","max_current"]})]})}renderDevice(e){return X`
      ${this.renderForm([{name:"device_id",required:!0,selector:{device:{}}}],e,e=>this.deviceChanged(e.device_id||null))}
      ${this.profile?X`<ha-alert alert-type="info">${this.localize("charger.profile_applied",{profile:this.profile})}</ha-alert>`:te}
    `}async deviceChanged(e){if(e===this.draft.device_id)return;if(this.changeDraft(function(e,t,i){const r=new Set(si(i,t)),a=e=>e&&r.has(e)?e:null,n=e.set_current;return{device_id:t,on_off_entity:a(e.on_off_entity),set_current:"entity"!==n?.mode||a(n.entity_id)?n:{mode:"entity",entity_id:null},car_connected:hi(e.car_connected,r),actively_charging:hi(e.actively_charging,r),charging_power:hi(e.charging_power,r),fault_flag:hi(e.fault_flag,r)}}(this.draft,e,this.hass)),this.profile=null,!e)return;const{profile:t,fields:i}=await function(e,t,i){return((e,t)=>e.callWS({type:"kraftvakt/charger_profile/get",device_id:t}))(e,t).catch(()=>({profile:null,fields:{cloud_controlled:i.defaults.chargers.cloud_controlled}}))}(this.hass,e,this.capabilities);this.draft.device_id===e&&(this.changeDraft(i),this.profile=t)}renderCarConnected(e){return this.renderGroup({title:this.label("car_connected"),description:this.helper("car_connected"),content:this.renderCondition("car_connected","condition",e)})}renderActivelyCharging(e){return this.renderGroup({title:this.label("actively_charging"),description:this.helper("actively_charging"),content:[this.renderCondition("charging_power","charging_power",e),this.renderCondition("actively_charging","actively_charging",e,!0)]})}stateChoices(e){return{true:this.localize(`charger.state_choices.${e}.true`),false:this.localize(`charger.state_choices.${e}.false`)}}renderCondition(e,t,i,r=!1){const a=i.find(t=>t.field===e);return X`
      <kraftvakt-condition-field
        .hass=${this.hass}
        .localize=${this.localize}
        .value=${this.draft[e]}
        .variables=${this.variables}
        .includeEntities=${this.entityScope}
        .kind=${t}
        .optional=${r}
        .stateChoices=${"charging_power"===e?void 0:this.stateChoices(e)}
        .error=${a?this.describe(a):void 0}
        .disabled=${this.locked}
        @value-changed=${t=>this.changeDraft({[e]:t.detail.value})}
      ></kraftvakt-condition-field>
    `}renderCloudControl(){return this.renderGroup({title:this.label("cloud_controlled"),description:this.helper("cloud_controlled"),toggle:{checked:this.draft.cloud_controlled,changed:e=>this.changeDraft({cloud_controlled:e})},content:te})}renderDeactivateOnFault(e){const t=this.draft.deactivate_on_fault||e.some(e=>"fault_flag"===e.field);return this.renderGroup({title:this.label("deactivate_on_fault"),description:this.helper("deactivate_on_fault"),toggle:{checked:this.draft.deactivate_on_fault,changed:e=>this.changeDraft({deactivate_on_fault:e})},content:t?this.renderCondition("fault_flag","fault",e):te})}renderChargingWindow(e){const t=this.draft.charging_window,i=e.find(e=>"charging_window"===e.field);return this.renderGroup({title:this.label("charging_window"),description:this.helper("charging_window"),toggle:{checked:null!==t,changed:e=>this.changeDraft({charging_window:e?{start:"",end:""}:null})},content:t?this.renderWindowFields(e):te,error:i?this.describe(i):void 0})}renderWindowFields(e){const t=this.draft.charging_window,i=[{type:"grid",name:"",schema:[{name:"start",required:!0,selector:{time:{no_second:!0}}},{name:"end",required:!0,selector:{time:{no_second:!0}}}]},{name:"charge_until_disconnected",selector:{boolean:{}}},{name:"override_ends",required:!0,selector:{select:{mode:"dropdown",options:Ue.map(e=>({value:e,label:this.localize(`charger.override_ends.${e}`)}))}}}],r={start:t?.start??"",end:t?.end??"",charge_until_disconnected:this.draft.charge_until_disconnected,override_ends:this.draft.override_ends};return this.renderForm(i,e,e=>this.changeDraft({charging_window:{start:pr(e.start),end:pr(e.end)},charge_until_disconnected:!!e.charge_until_disconnected,override_ends:e.override_ends??this.draft.override_ends}),r)}static{this.styles=[ar.styles,g`
      /* Indented as Home Assistant indents the helper text of a field. */
      .helper {
        padding-inline-start: 16px;
        font-size: var(--ha-font-size-s, 12px);
        color: var(--secondary-text-color);
      }
    `]}};function pr(e){return"string"==typeof e?e.slice(0,5):""}e([ke()],hr.prototype,"profile",void 0),hr=e([we("kraftvakt-charger-dialog")],hr);const ur=["device_id","switched_by","on_off_entity","activate","deactivate","set_current","min_current_a","max_current_a","min_current_power_w","car_connected","actively_charging","charging_power","cloud_controlled","start_delay_s","charging_window","charge_until_disconnected","override_ends","deactivate_on_fault","fault_flag"],gr=["never","always","condition"],mr=[{name:"name",required:!0,selector:{text:{}}}],_r=[{name:"dynamic_order",selector:{boolean:{}}}],fr={name:"charging.name",one_at_a_time:"charging.one_at_a_time_applies",dynamic_order:"charging.dynamic_order"},vr=new Set(["one_at_a_time","dynamic_order"]);let wr=class extends Di{render(){const e=this.config.charger_groups;return X`
      ${0===e.length?X`<div class="empty">${this.localize("charging.no_groups")}</div>`:e.map(e=>this.renderGroup(e))}
      ${this.renderPageFooter(e.length>0?this.localize("charging.switches_info"):"",X`
          <ha-button .disabled=${this.locked} @click=${this.addGroup}>
            <ha-svg-icon slot="start" .path=${o}></ha-svg-icon>
            ${this.localize("charging.add_group")}
          </ha-button>
        `)}
      ${0===rt(this.config).length?X` <kraftvakt-manual-control-warning .localize=${this.localize} .narrow=${this.narrow} kind="chargers"></kraftvakt-manual-control-warning> `:te}
      ${this.editing?this.renderDialog(this.editing.charger,this.editing.groupId,this.editing.isNew):te}
    `}renderGroup(e){const t=0===e.chargers.length,i={add:this.localize("charging.add"),empty:this.localize("charging.empty"),rows:e.chargers.map(e=>this.row(e)),locked:this.locked,group:"kraftvakt-chargers",onAdd:()=>this.addCharger(e),onMoved:t=>this.chargerMoved(e,t),onAdded:t=>this.chargerAdded(e,t),onOpen:t=>this.openRow(e,t)};return this.renderCard({title:e.name.trim()||this.localize("charging.unnamed_group"),sections:[this.renderGroupForm(e,mr),X`
          ${ai(this.localize("charging.one_at_a_time"))} ${ni(this.localize("charging.one_at_a_time_sub"))}
          ${this.renderGroupForm(e,this.sharingSchema())} ${"object"==typeof e.one_at_a_time?this.renderSharingCondition(e,e.one_at_a_time):te}
        `,X`
          ${ai(this.localize("charging.chargers"),this.renderAddButton(i))} ${ni(this.localize("charging.chargers_sub"))}
          ${this.renderGroupForm(e,_r)}
        `],list:this.renderItemList(i),footer:this.renderCardFooter(t?"":this.localize("charging.delete_group_not_empty"),X`
          <ha-button variant="danger" appearance="plain" .disabled=${this.locked||!t} @click=${()=>this.deleteGroup(e)}>
            <ha-svg-icon slot="start" .path=${"M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"}></ha-svg-icon>
            ${this.localize("charging.delete_group")}
          </ha-button>
        `)})}sharingSchema(){return[{name:"one_at_a_time",required:!0,selector:{select:{mode:"dropdown",options:gr.map(e=>({value:e,label:this.localize(`charging.one_at_a_time_${e}`)}))}}}]}renderGroupForm(e,t){const{one_at_a_time:i,...r}=this.formErrors("charger_groups",e.id);return X`
      <ha-form
        .hass=${this.hass}
        .data=${yr(e)}
        .schema=${t.map(t=>this.sharingDisabled(e,t.name)?{...t,disabled:!0}:t)}
        .error=${r}
        .disabled=${this.locked}
        .computeLabel=${e=>this.localize(fr[e.name])}
        .computeHelper=${t=>this.groupHelper(e,t.name).split("\n").map((e,t)=>0===t?e:X`<br />${e}`)}
        .computeError=${e=>e}
        @value-changed=${t=>this.groupChanged(e,t.detail.value)}
      ></ha-form>
    `}renderSharingCondition(e,t){return X`
      <kraftvakt-condition-field
        .hass=${this.hass}
        .localize=${this.localize}
        .value=${t}
        .variables=${{power_limit:this.config.general.power_limit_w}}
        kind="one_at_a_time"
        .error=${this.formErrors("charger_groups",e.id).one_at_a_time}
        .disabled=${this.locked||this.sharingDisabled(e,"one_at_a_time")}
        @value-changed=${t=>this.changeGroup({...e,one_at_a_time:t.detail.value})}
      ></kraftvakt-condition-field>
    `}sharingDisabled(e,t){return!vi(e)&&vr.has(t)}groupHelper(e,t){return["one_at_a_time"===t?"":this.localize(`charging.${t}_sub`),this.sharingDisabled(e,t)?this.localize("charging.needs_two_chargers"):""].filter(Boolean).join("\n")}renderDialog(e,t,i){return X`
      <kraftvakt-charger-dialog
        .hass=${this.hass}
        .localize=${this.localize}
        .capabilities=${this.capabilities}
        .item=${e}
        .isNew=${i}
        .usedEntities=${this.entitiesUsedBesides(e.id)}
        .saveErrors=${Ai(this.saveErrors,"chargers",e.id)}
        .locked=${this.locked}
        @item-changed=${e=>this.chargerChanged(t,e.detail)}
        @item-deleted=${this.chargerDeleted}
        @closed=${()=>this.editing=void 0}
      ></kraftvakt-charger-dialog>
    `}row(e){const t=[this.localize("charging.currents",{min:e.min_current_a,max:e.max_current_a,power:ht(this.hass.language,e.min_current_power_w,0)})];if(e.charging_window){const i=this.localize("charging.window",{...e.charging_window});t.push(e.charge_until_disconnected?`${i}, ${this.localize("charging.charges_until_disconnected")}`:i)}e.deactivate_on_fault&&t.push(this.localize("charging.deactivated_on_fault"));const i=Ai(this.issues,"chargers",e.id);return{key:e.id,title:It(this.hass,this.entityNames,e)??this.localize("missing.charger_without_device"),iconPath:r,details:t,errors:i.map(e=>`${this.fieldLabel(e)}: ${this.describeIssue(e)}`),openable:!0}}fieldLabel(e){const t=e.field??"";return ur.includes(t)?this.localize(`charger.fields.${t}.label`):t}groupChanged(e,t){const i=t.one_at_a_time??yr(e).one_at_a_time,r=i===yr(e).one_at_a_time;this.changeGroup({...e,name:t.name??e.name,one_at_a_time:r?e.one_at_a_time:"condition"===i?{type:"template",value:""}:"always"===i,dynamic_order:t.dynamic_order??e.dynamic_order})}addGroup(){const e=this.config.charger_groups,t=this.localize("charging.new_group_name"),i=new Set(e.map(e=>e.name.trim()));let r=t;for(let e=2;i.has(r);e++)r=`${t} ${e}`;const a=this.capabilities.defaults.charger_groups,n={id:Ye(),name:r,...a,chargers:[]};this.changeConfig({...this.config,charger_groups:[...e,n]})}deleteGroup(e){this.changeConfig({...this.config,charger_groups:this.config.charger_groups.filter(t=>t.id!==e.id)})}chargerMoved(e,t){const{oldIndex:i,newIndex:r}=t.detail;this.changeGroup({...e,chargers:et(e.chargers,i,r)})}chargerAdded(e,t){const{key:i,index:r}=t.detail,a=rt(this.config).find(e=>e.id===i);if(!a)return;const n=this.config.charger_groups.map(t=>{const n=t.chargers.filter(e=>e.id!==i);return t.id===e.id&&n.splice(r,0,a),{...t,chargers:n}});this.changeConfig({...this.config,charger_groups:n})}addCharger(e){const t=this.capabilities.defaults.chargers,i={id:Ye(),device_id:null,switched_by:t.switched_by,on_off_entity:null,activate:{mode:"custom",action:[]},deactivate:{mode:"custom",action:[]},set_current:{mode:"entity",entity_id:null},min_current_a:t.min_current_a,max_current_a:t.max_current_a,min_current_power_w:t.min_current_power_w,car_connected:null,actively_charging:null,charging_power:null,charging_window:null,charge_until_disconnected:!1,override_ends:t.override_ends,cloud_controlled:t.cloud_controlled,start_delay_s:t.start_delay_s,deactivate_on_fault:!1,fault_flag:null};this.editing={charger:i,groupId:e.id,isNew:!0}}openRow(e,t){const i=e.chargers.find(e=>e.id===t.detail);i&&(this.editing={charger:i,groupId:e.id,isNew:!1})}chargerChanged(e,t){const i=this.config.charger_groups.find(t=>t.id===e);if(!i)return;const r=i.chargers.some(e=>e.id===t.id);this.changeGroup({...i,chargers:r?i.chargers.map(e=>e.id===t.id?t:e):[...i.chargers,t]})}chargerDeleted(e){const t=this.config.charger_groups.map(t=>({...t,chargers:t.chargers.filter(t=>t.id!==e.detail)}));this.changeConfig({...this.config,charger_groups:t})}changeGroup(e){const t=this.config.charger_groups.map(t=>t.id===e.id?e:t);this.changeConfig({...this.config,charger_groups:t})}static{this.styles=[Di.styles,g`
      kraftvakt-condition-field::part(shown) {
        margin-inline: 0;
        padding: 0;
        border-top: none;
      }
    `]}};function yr(e){const t=e.one_at_a_time;return{name:e.name,one_at_a_time:"object"==typeof t?"condition":t?"always":"never",dynamic_order:e.dynamic_order}}function br(e,t,i){if(t.replace)return t.items;const r=null===t.kept_from?1/0:Date.parse(t.kept_from),a=t.items.length>0?Date.parse(i(t.items[0])):1/0;return[...e.filter(e=>{const t=Date.parse(i(e));return t>=r&&t<a}),...t.items]}function $r(e,t,i,r,a,n){const s=[];for(const t of e){let e;for(const i of t.commands){const t=n(i);e=void 0===t?e:t}void 0!==e&&s.push({time:Date.parse(t.time),value:e})}return 0===s.length?r&&i>t?[{start:t,end:i,value:a}]:[]:s.map((e,t)=>({start:e.time,end:s[t+1]?.time??i,value:e.value}))}function kr(e,t){if("appliance_id"in e&&e.appliance_id===t)return"TurnOnAppliance"===e.command}function xr(e,t){if("charger_id"in e&&e.charger_id===t)switch(e.command){case"SetChargingCurrent":return e.current_a>0?e.current_a:null;case"DeactivateCharger":return null;case"ActivateCharger":return}}function Ar(e,t,i,r){const a={};let n;for(const i of e){const e=Date.parse(i.time),r=i.waiting&&{id:Cr(i.waiting.key),startedAt:i.waiting.started_at,reason:i.waiting.reason};if(n&&r?.id===n.id&&r.startedAt===n.startedAt&&r.reason===n.reason)n.segment.end=e;else if(n&&(n.segment.end=e),n=void 0,r){const i={start:Math.max(Date.parse(r.startedAt),t),end:e,value:r.reason};(a[r.id]??=[]).push(i),n={...r,segment:i}}}return n&&r&&(n.segment.end=i),a}function Cr(e){return"appliance_id"in e?e.appliance_id:e.charger_id}function zr(e){return e.priority.filter(e=>"appliance"===e.type)}function Er(e){return e.priority.flatMap(e=>"charger_group"===e.type?e.chargers:[])}e([ke()],wr.prototype,"editing",void 0),wr=e([we("kraftvakt-charging-page")],wr);const Sr=g`
  .card-header {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    min-height: 40px;
    padding: 12px 16px;
    font-size: var(--ha-font-size-xl, 20px);
  }
`,Vr=g`
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
  .chip.outline {
    background: none;
    box-shadow: inset 0 0 0 1px var(--divider-color);
  }
  .chip.info {
    background: rgba(var(--rgb-info-color, 3, 155, 229), 0.16);
    color: var(--info-color, #039be5);
  }
  .chip.waiting {
    background: rgba(var(--rgb-amber-color, 255, 193, 7), 0.16);
    color: var(--amber-color, #ffc107);
  }
`,Mr=[15,30,60];let Hr=class extends fe{constructor(){super(...arguments),this.narrow=!1,this.measurements=[],this.decisions=[],this.rangeMin=60,this.filter="all",this.chartWidth=0,this.chartResize=new ResizeObserver(([e])=>this.chartWidth=e.contentRect.width)}connectedCallback(){super.connectedCallback(),this.subscribe()}disconnectedCallback(){super.disconnectedCallback(),this.unsubscribe?.then(e=>e()).catch(()=>{}),this.unsubscribe=void 0,this.chartResize.disconnect()}willUpdate(e){e.has("hass")&&this.subscribe()}updated(){const e=this.renderRoot.querySelector(".chart");e&&this.chartResize.observe(e)}subscribe(){var e,t;this.hass&&!this.unsubscribe&&(this.unsubscribe=(e=this.hass,t=e=>this.received(e),e.connection.subscribeMessage(t,{type:"kraftvakt/diagnostics/subscribe"})),this.unsubscribe.catch(e=>{this.error=e,this.unsubscribe=void 0}))}received(e){this.diagnostics=e,this.measurements=br(this.measurements,e.measurements,e=>e.start),this.decisions=br(this.decisions,e.decisions,e=>e.time),this.error=void 0}render(){if(void 0!==this.error)return X`<ha-alert alert-type="error">${this.localize("panel.error",{message:String(this.error)})}</ha-alert>`;if(!this.diagnostics||!this.status||!this.config)return te;const e=Date.now(),t=function(e,t,i,r,a){const n=null!==r,s=null===t?a:Date.parse(t.time),o=e.filter(e=>Date.parse(e.time)>s),l=o.length>0?Date.parse(o[o.length-1].time):s,d=n?a:l,c=null===t?o:[{time:t.time,commands:t.commands},...o],h={};for(const e of zr(i))h[e.id]=$r(c,s,d,n,e.on,t=>kr(t,e.id));const p={};for(const e of Er(i))p[e.id]=$r(c,s,d,n,e.activated?e.current_a:null,t=>xr(t,e.id));return{from:s,to:d,appliances:h,chargers:p,waiting:Ar(o,s,d,n)}}(this.decisions,this.diagnostics.commands_before_decisions,this.status,this.diagnostics.started_at,e);return X` <div class="cards">${this.renderHealth(this.diagnostics,this.status,this.config)} ${this.renderTimeline(t,e)} ${this.renderLog()}</div> `}renderHealth(e,t,i){const r=this.hass.language,a=i.config.general,n=e.power_sensor,s=e=>null===e?"–":this.localize("diagnostics.seconds",{seconds:ht(r,e,0)}),o=null===n.reported_interval_s?s(n.update_interval_s):this.localize("diagnostics.reports_every",{seconds:ht(r,n.reported_interval_s,1)}),l=n.last_missed_windows,d=e.failed_actions,c=function(e){return[...Object.entries(e.appliances).map(([e,t])=>({type:"appliance",id:e,dueAt:t})),...Object.entries(e.chargers).map(([e,t])=>({type:"charger",id:e,dueAt:t}))].sort((e,t)=>Date.parse(e.dueAt)-Date.parse(t.dueAt))}(e.repeats_due_at),h=null!==e.started_at;return X`
      <div class="tiles">
        ${this.renderTile("diagnostics.power_sensor",n.valid?null!==n.reported_interval_s?"warning":"ok":"alarm",this.localize(n.valid?"diagnostics.valid":"diagnostics.not_valid"),[["diagnostics.update_interval",o],["diagnostics.stored_interval",s(a.power_sensor_interval_s)],["diagnostics.regulation_window",null===a.regulation_window_updates||null===a.power_sensor_interval_s?"–":this.localize("diagnostics.window_updates",{seconds:ht(r,t.regulation_window_s,0),updates:a.regulation_window_updates,interval:ht(r,a.power_sensor_interval_s,0)})],["diagnostics.last_missed_windows",null===l?this.localize("diagnostics.none"):`${vt(this.timeLocale,l.start)}–${ft(this.timeLocale,l.end)}`]])}
        ${this.renderTile("diagnostics.actions",d.length>0?"warning":"ok",this.localize("diagnostics.failed_count",{count:d.length}),[["diagnostics.last_failed",d.length>0?vt(this.timeLocale,d[d.length-1].time):this.localize("diagnostics.none")],["diagnostics.commands_waiting",String(e.queued_commands)],["diagnostics.action_timeout",s(a.action_timeout_s)]])}
        ${this.renderTile("status.regulation",h?t.safe_state||t.penalty.active?"alarm":"ok":"off",null===e.started_at?this.localize("status.stopped"):this.localize("diagnostics.running_for",{duration:wt(r,Date.now()-Date.parse(e.started_at))}),[...null===e.started_at?[]:[["diagnostics.started",(p=this.timeLocale,u=e.started_at,new Date(u).toLocaleString(p.language,{..._t(p),dateStyle:"short",timeStyle:"short"}))]],["status.safe_state_title",this.localize(t.safe_state?"diagnostics.yes":"diagnostics.no")],["status.penalty_title",this.localize(t.penalty.active?"diagnostics.yes":"diagnostics.no")],["diagnostics.overconsumption",this.localize("diagnostics.watt_hours",{energy:ht(r,Math.max(0,t.penalty.overconsumption_wh),0)})]])}
        ${this.renderTile("diagnostics.command_repeat","off",c.length>0?this.localize("diagnostics.next_at",{time:ft(this.timeLocale,c[0].dueAt)}):this.localize("diagnostics.none"),c.slice(0,3).map(e=>[this.itemName(e.type,e.id),ft(this.timeLocale,e.dueAt)]))}
      </div>
    `;var p,u}renderTile(e,t,i,r){return X`
      <ha-card class="tile">
        <div class="tile-title"><span class="dot ${t}"></span>${this.localize(e)}</div>
        <div class="tile-value">${i}</div>
        <dl>
          ${r.map(([e,t])=>X`<dt>${e.startsWith("diagnostics.")||e.startsWith("status.")?this.localize(e):e}</dt>
                <dd>${t}</dd>`)}
        </dl>
      </ha-card>
    `}renderTimeline(e,t){return X`
      <ha-card>
        <div class="card-header">
          <span>${this.localize("diagnostics.timeline")}</span>
          <span class="spacer"></span>
          <span class="toggles">
            ${Mr.map(e=>X`
                <button class="toggle" aria-pressed=${e===this.rangeMin} @click=${()=>this.rangeMin=e}>
                  ${this.localize("diagnostics.minutes",{minutes:e})}
                </button>
              `)}
          </span>
        </div>
        <div class="legend">
          <div class="legend-group">
            <span><i class="swatch oldest"></i>${this.localize("diagnostics.oldest_decision")}</span>
            <span><i class="swatch consumption"></i>${this.localize("diagnostics.consumption")}</span>
            <span><i class="swatch line"></i>${this.localize("status.regulation_average")}</span>
            <span><i class="swatch line tariff"></i>${this.localize("status.tariff_average")}</span>
            <span><i class="swatch line limit"></i>${this.localize("status.power_limit")}</span>
          </div>
          <div class="legend-group">
            <span><i class="swatch on"></i>${this.localize("status.on")}</span>
            <span><i class="swatch current"></i>${this.localize("charger.charging_current")}</span>
            <span><i class="swatch waiting"></i>${this.localize("diagnostics.waiting_time")}</span>
            <span><i class="swatch waiting damping"></i>${this.localize("diagnostics.damping")}</span>
            <span><i class="swatch waiting start_delay"></i>${this.localize("diagnostics.start_delay")}</span>
            <span><i class="swatch unknown"></i>${this.localize("diagnostics.not_known")}</span>
          </div>
        </div>
        <div class="chart" @pointermove=${this.pointerMoved} @pointerleave=${()=>this.hoverMs=void 0}>
          ${this.chartWidth>0?this.renderChart(e,t):te} ${this.renderTooltip(t)}
        </div>
      </ha-card>
    `}get compactChart(){return this.chartWidth<560}get timeLocale(){return mt(this.hass)}scale(e){const t=this.chartWidth,i=this.compactChart?96:176,r=e-6e4*this.rangeMin;return{width:t,left:i,right:8,start:r,x:a=>i+(Math.min(Math.max(a,r),e)-r)/(e-r)*(t-i-8)}}renderChart(e,t){const{width:i,left:r,right:a,start:n,x:s}=this.scale(t),o=this.status,l=this.compactChart?160:200,d=this.measurements.filter((e,i)=>(Date.parse(this.measurements[i+1]?.start??"")||t)>n),c=Math.max(o.power_limit_w,...d.map(e=>e.power_w),...this.decisions.map(e=>e.regulation_average_w??0)),h=c>2e4?5:2,p=Math.ceil(1.1*c/1e3/h)*h,u=e=>8+(1-e/1e3/p)*(l-8-22),g=d.map((e,i)=>{const r=s(Date.parse(e.start)),a=s(Date.parse(d[i+1]?.start??"")||t);return`L${r},${u(e.power_w)}L${a},${u(e.power_w)}`}).join(""),m=d.length>0?s(Date.parse(d[0].start)):s(t),_=1e3*o.regulation_window_s,f=this.decisions.filter(e=>null!==e.regulation_average_w&&Date.parse(e.time)>n),v=f.map((e,t)=>{const i=Date.parse(e.time);return`${0===t?"M":"L"}${s(i-_)},${u(e.regulation_average_w)}L${s(i)},${u(e.regulation_average_w)}`}).join(""),w=f.filter(e=>null!==e.tariff_average_w).map((e,t)=>`${0===t?"M":"L"}${s(Date.parse(e.time))},${u(e.tariff_average_w)}`).join(""),y=(this.rangeMin<=30?5:10)*(this.compactChart?2:1)*6e4,b=[];for(let e=Math.ceil(n/y)*y;e<t-y/2;e+=y)b.push(e);const $=Array.from({length:p/h+1},(e,t)=>t*h),k=this.decisions[0]?Date.parse(this.decisions[0].time):void 0,x=this.openRow&&Date.parse(this.openRow.time);return X`
      <svg class="power" width=${i} height=${l} viewBox="0 0 ${i} ${l}" role="img" aria-label=${this.localize("diagnostics.chart_label")}>
        ${$.map(e=>Y`
            <line class="grid" x1=${r} x2=${i-a} y1=${u(1e3*e)} y2=${u(1e3*e)}></line>
            <text x=${r-6} y=${u(1e3*e)+4} text-anchor="end">${e===p?`${e} kW`:e}</text>
          `)}
        ${b.map(e=>Y`<text x=${s(e)} y=${l-6} text-anchor="middle">${ft(this.timeLocale,e,!1)}</text>`)}
        <text x=${i-a} y=${l-6} text-anchor="end">${this.localize("diagnostics.now")}</text>
        ${g?Y`<path class="consumption" d="M${m},${u(0)}${g}L${s(t)},${u(0)}Z"></path>`:te}
        <path class="tariff" d=${w}></path>
        <path class="regulation" d=${v}></path>
        <line class="limit" x1=${r} x2=${i-a} y1=${u(o.power_limit_w)} y2=${u(o.power_limit_w)}></line>
        ${void 0!==k&&k>n?Y`<line class="oldest" x1=${s(k)} x2=${s(k)} y1=${8} y2=${l-22}></line>`:te}
        ${this.renderCursor(x,8,l-22,s,n)} ${this.renderCursor(this.hoverMs,8,l-22,s,n,"hover")}
      </svg>
      ${this.renderLanes(e,t)}
    `}renderCursor(e,t,i,r,a,n="marked"){return void 0!==e&&e>a?Y`<line class=${n} x1=${r(e)} x2=${r(e)} y1=${t} y2=${i}></line>`:te}renderLanes(e,t){const{width:i,start:r,x:a}=this.scale(t),n=this.laneRows(),s=26,o=s*n.length+2,l=this.hoverMs,d=this.openRow&&Date.parse(this.openRow.time),c=(e,t,i=1,r="on")=>{const n=Math.max(2,16*i);return Y`<rect class=${r} x=${a(e.start)} y=${t+5+(16-n)} width=${Math.max(1.5,a(e.end)-a(e.start))} height=${n}></rect>`};return X`
      <svg class="lanes" width=${i} height=${o} viewBox="0 0 ${i} ${o}" role="img" aria-label=${this.localize("diagnostics.lanes_label")}>
        <defs>
          <pattern id="unknown" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)">
            <line x1="0" y1="0" x2="0" y2="6" class="unknown-line"></line>
          </pattern>
          ${["waiting_time","damping","start_delay"].map(e=>Y`
              <pattern id=${e} width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
                <line x1="0" y1="0" x2="0" y2="5" class="waiting-line ${e}"></line>
              </pattern>
            `)}
        </defs>
        ${n.map((n,o)=>{const l=o*s+1,d=n.charger?e.chargers[n.id]??[]:e.appliances[n.id]??[],h=n.charger;return Y`
            ${n.essential?Y`<rect class="essential" x="0" y=${l} width=${i} height=${s}></rect>`:te}
            <line class="row-line" x1="0" x2=${i} y1=${l} y2=${l}></line>
            <text class="lane-name" x="4" y=${l+13+4}>${this.shortName(n.name)}<title>${n.name}</title></text>
            <rect class="unknown" x=${a(r)} y=${l+3} width=${a(t)-a(r)} height=${20}></rect>
            ${d.map(e=>Y`<rect class="known" x=${a(e.start)} y=${l+3} width=${Math.max(0,a(e.end)-a(e.start))} height=${20}></rect>`)}
            ${h?(e.chargers[n.id]??[]).map(e=>null===e.value?te:c(e,l,(e.value-h.min_current_a+1)/(h.max_current_a-h.min_current_a+1),"current")):(e.appliances[n.id]??[]).map(e=>e.value?c(e,l):te)}
            ${(e.waiting[n.id]??[]).map(e=>c(e,l,1,`waiting ${e.value}`))}
          `})}
        ${this.renderCursor(d,0,o,a,r)} ${this.renderCursor(l,0,o,a,r,"hover")}
      </svg>
    `}shortName(e){const t=this.compactChart?11:22;return e.length>t?`${e.slice(0,t-1)}…`:e}laneRows(){const e=new Map((this.config?.config.charger_groups??[]).flatMap(e=>e.chargers).map(e=>[e.id,e]));return this.status.priority.flatMap(t=>"appliance"===t.type?[{id:t.id,name:t.name,essential:t.essential}]:t.chargers.map(t=>({id:t.id,name:t.name,essential:!1,charger:e.get(t.id)})))}pointerMoved(e){const t=e.currentTarget,{width:i,left:r,right:a,start:n}=this.scale(Date.now()),s=e.clientX-t.getBoundingClientRect().left;this.hoverMs=s<r||s>i-a?void 0:n+(s-r)/(i-r-a)*(Date.now()-n)}renderTooltip(e){const t=this.hoverMs;if(void 0===t)return te;const i=this.hass.language,r=[...this.measurements].reverse().find(e=>Date.parse(e.start)<=t),a=1e3*(this.status?.regulation_window_s??0),n=this.decisions.find(e=>Date.parse(e.time)>=t&&Date.parse(e.time)-a<t),{x:s,width:o}=this.scale(e),l=s(t);return X`
      <div class="tooltip" style=${l>o/2?`right: ${o-l+12}px`:`left: ${l+12}px`}>
        <b>${ft(this.timeLocale,t)}</b>
        <div>${this.localize("diagnostics.consumption")}: ${r?`${pt(i,r.power_w)} kW`:"–"}</div>
        ${n?X`
                <div class="tooltip-decision">
                  <b>${this.localize("diagnostics.decision_at",{time:ft(this.timeLocale,n.time)})}</b>
                  <div>${this.localize("status.regulation_average")}: ${pt(i,n.regulation_average_w)} kW</div>
                  <div>${this.localize("status.tariff_average")}: ${pt(i,n.tariff_average_w)} kW</div>
                  ${n.commands.map(e=>X`<div>${this.commandText(e)}</div>`)}
                </div>
              `:X`<div>${this.localize("diagnostics.no_decision_kept")}</div>`}
      </div>
    `}renderLog(){const e=function(e,t){const i=[...e.flatMap(e=>e.commands.map(t=>({time:e.time,command:t,decision:e}))),...t.map(e=>({time:e.time,failed:e}))];return i.map((e,t)=>({row:e,index:t})).sort((e,t)=>Date.parse(t.row.time)-Date.parse(e.row.time)||t.index-e.index).map(({row:e})=>e)}(this.decisions,this.diagnostics?.failed_actions??[]).filter(e=>"all"===this.filter||"failed"===this.filter=="failed"in e);return X`
      <ha-card>
        <div class="card-header">
          <span>${this.localize("diagnostics.event_log")}</span>
          <span class="spacer"></span>
          <span class="toggles">
            ${["all","commands","failed"].map(e=>X`
                <button class="toggle" aria-pressed=${e===this.filter} @click=${()=>this.filter=e}>${this.localize(`diagnostics.filter_${e}`)}</button>
              `)}
          </span>
        </div>
        ${0===e.length?X`<p class="description">${this.localize("diagnostics.no_events")}</p>`:X`
                <div class="table">
                  <table>
                    <tbody>
                      ${e.map(e=>this.renderLogRow(e))}
                    </tbody>
                  </table>
                </div>
              `}
        <div class="card-footer">
          <span>${this.localize("diagnostics.log_kept")}</span>
          <a href="/config/integrations/integration/kraftvakt">${this.localize("diagnostics.download")}</a>
        </div>
      </ha-card>
    `}renderLogRow(e){const t=`${e.time} ${"failed"in e?e.failed.action:JSON.stringify(e.command)}`,i=this.openRow?.key===t,r=()=>this.openRow=i?void 0:{key:t,time:e.time},a="failed"in e?"failed":this.commandKind(e.command);return X`
      <tr
        class="event ${i?"open":""}"
        tabindex="0"
        @click=${r}
        @keydown=${e=>{"Enter"!==e.key&&" "!==e.key||(e.preventDefault(),r())}}
      >
        <td class="time">${ft(this.timeLocale,e.time)}</td>
        <td class="kind"><span class="chip ${a}">${this.localize(`diagnostics.kind_${a}`)}</span></td>
        <td>${"failed"in e?e.failed.action:this.commandText(e.command)}</td>
      </tr>
      ${i?X`<tr class="details">
              <td></td>
              <td colspan="2">${"failed"in e?this.renderFailed(e.failed.error):this.renderDecision(e.decision)}</td>
            </tr>`:te}
    `}renderFailed(e){return X`<dl class="facts">
      <dt>${this.localize("diagnostics.error")}</dt>
      <dd>${e}</dd>
    </dl>`}renderDecision(e){const t=this.hass.language,i=e.waiting,r=e=>this.localize(e?"diagnostics.yes":"diagnostics.no"),a=i&&("appliance_id"in i.key?this.itemName("appliance",i.key.appliance_id):this.itemName("charger",i.key.charger_id));return X`
      <dl class="facts">
        <dt>${this.localize("status.regulation_average")}</dt>
        <dd>${pt(t,e.regulation_average_w)} kW</dd>
        <dt>${this.localize("status.tariff_average")}</dt>
        <dd>${pt(t,e.tariff_average_w)} kW</dd>
        <dt>${this.localize("diagnostics.power_sensor_valid")}</dt>
        <dd>${r(e.power_sensor_valid)}</dd>
        <dt>${this.localize("status.safe_state_title")}</dt>
        <dd>${r(e.safe_state)}</dd>
        <dt>${this.localize("status.penalty_title")}</dt>
        <dd>${r(e.penalty_active)}</dd>
        <dt>${this.localize("diagnostics.overconsumption")}</dt>
        <dd>${this.localize("diagnostics.watt_hours",{energy:ht(t,e.overconsumption_wh,0)})}</dd>
        <dt>${this.localize("diagnostics.waiting")}</dt>
        <dd>
          ${i?`${a}, ${this.localize(`diagnostics.${i.reason}`)}, ${ft(this.timeLocale,i.started_at)}–${ft(this.timeLocale,i.until)}`:this.localize("diagnostics.none")}
        </dd>
        <dt>${this.localize("diagnostics.commands")}</dt>
        <dd>${e.commands.map(e=>this.commandText(e)).join(", ")}</dd>
      </dl>
    `}commandKind(e){switch(e.command){case"TurnOnAppliance":case"ActivateCharger":return"on";case"TurnOffAppliance":case"DeactivateCharger":return"off";case"SetChargingCurrent":return"current"}}commandText(e){switch(e.command){case"TurnOnAppliance":case"TurnOffAppliance":{const t=this.itemName("appliance",e.appliance_id),i=this.config?.config.appliances.find(t=>t.id===e.appliance_id)?.variants.find(t=>t.id===e.variant_id),r="TurnOnAppliance"===e.command?"diagnostics.turn_on":"diagnostics.turn_off";return this.localize(r,{name:i?`${t} (${i.label})`:t})}case"ActivateCharger":return this.localize("diagnostics.activate",{name:this.itemName("charger",e.charger_id)});case"DeactivateCharger":return this.localize("diagnostics.deactivate",{name:this.itemName("charger",e.charger_id)});case"SetChargingCurrent":return this.localize("diagnostics.set_current",{name:this.itemName("charger",e.charger_id),current:e.current_a})}}itemName(e,t){const i=this.status,r=i?"appliance"===e?zr(i):Er(i):[];return r.find(e=>e.id===t)?.name??t}static{this.styles=[Sr,Vr,g`
      :host {
        display: block;
        --kraftvakt-grid-color: var(--energy-grid-consumption-color, #488fc2);
        --kraftvakt-ev-color: var(--teal-color, #009688);
        --kraftvakt-on-color: var(--state-active-color, var(--amber-color, #ffc107));
        --kraftvakt-waiting-color: var(--purple-color, #926bc7);
        --kraftvakt-damping-color: var(--orange-color, #ff9800);
        --kraftvakt-start-delay-color: var(--light-blue-color, #03a9f4);
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
      .tiles {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 16px;
      }
      :host([narrow]) .tiles {
        gap: 8px;
      }
      .tile {
        display: grid;
        gap: 6px;
        align-content: start;
        padding: 14px 16px;
      }
      .tile-title {
        display: flex;
        align-items: center;
        gap: 8px;
        color: var(--secondary-text-color);
        font-weight: 500;
      }
      .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--disabled-text-color);
      }
      .dot.ok {
        background: var(--success-color, #43a047);
      }
      .dot.warning {
        background: var(--warning-color, #ffa600);
      }
      .dot.alarm {
        background: var(--error-color, #db4437);
      }
      .tile-value {
        font-size: var(--ha-font-size-xl, 20px);
      }
      dl {
        display: grid;
        grid-template-columns: auto minmax(0, 1fr);
        gap: 2px 12px;
        margin: 0;
        font-size: var(--ha-font-size-s, 12px);
      }
      dt {
        color: var(--secondary-text-color);
      }
      dd {
        margin: 0;
        font-variant-numeric: tabular-nums;
        overflow-wrap: anywhere;
      }
      .tile dd {
        text-align: end;
      }
      .description {
        margin: 0;
        padding: 0 16px 8px;
        color: var(--secondary-text-color);
      }
      .toggles {
        display: inline-flex;
        gap: 6px;
        flex-wrap: wrap;
      }
      .toggle {
        font: inherit;
        font-size: var(--ha-font-size-s, 12px);
        font-weight: 500;
        padding: 4px 10px;
        border-radius: 999px;
        border: 1px solid var(--divider-color);
        background: none;
        color: var(--secondary-text-color);
        cursor: pointer;
      }
      .toggle[aria-pressed="true"] {
        background: var(--primary-color);
        border-color: var(--primary-color);
        color: var(--text-primary-color, #fff);
      }
      .legend {
        display: grid;
        gap: 6px;
        padding: 0 16px 4px;
        font-size: var(--ha-font-size-s, 12px);
        color: var(--secondary-text-color);
      }
      .legend-group {
        display: flex;
        flex-wrap: wrap;
        gap: 6px 14px;
      }
      .legend span {
        display: inline-flex;
        align-items: center;
        gap: 6px;
      }
      .swatch {
        display: inline-block;
        width: 16px;
        height: 10px;
      }
      .swatch.consumption {
        background: color-mix(in srgb, var(--secondary-text-color) 30%, transparent);
      }
      .swatch.line {
        height: 0;
        border-top: 2px solid var(--primary-text-color);
      }
      .swatch.line.tariff {
        border-top-color: var(--kraftvakt-grid-color);
      }
      .swatch.line.limit {
        border-top: 2px dashed var(--error-color, #db4437);
      }
      .swatch.on {
        background: var(--kraftvakt-on-color);
      }
      .swatch.current {
        border: 1px solid var(--kraftvakt-ev-color);
        background: color-mix(in srgb, var(--kraftvakt-ev-color) 45%, transparent);
        box-sizing: border-box;
      }
      .waiting {
        --kraftvakt-reason-color: var(--kraftvakt-waiting-color);
      }
      .damping {
        --kraftvakt-reason-color: var(--kraftvakt-damping-color);
      }
      .start_delay {
        --kraftvakt-reason-color: var(--kraftvakt-start-delay-color);
      }
      .swatch.waiting {
        border: 1px solid var(--kraftvakt-reason-color);
        background: repeating-linear-gradient(45deg, transparent 0 3px, var(--kraftvakt-reason-color) 3px 4px);
        box-sizing: border-box;
      }
      .swatch.unknown {
        border: 1px solid var(--divider-color);
        background: repeating-linear-gradient(-45deg, transparent 0 3px, var(--divider-color) 3px 5px);
        box-sizing: border-box;
      }
      .swatch.oldest {
        width: 0;
        height: 12px;
        border-left: 1px dashed var(--secondary-text-color);
      }
      .chart {
        position: relative;
        padding: 4px 0 12px;
        touch-action: pan-y;
      }
      svg {
        display: block;
        overflow: visible;
      }
      svg text {
        font-size: 11px;
        fill: var(--secondary-text-color);
      }
      svg .lane-name {
        font-size: var(--ha-font-size-s, 12px);
        fill: var(--primary-text-color);
      }
      .grid,
      .row-line {
        stroke: var(--divider-color);
      }
      .consumption {
        fill: color-mix(in srgb, var(--secondary-text-color) 30%, transparent);
      }
      .regulation {
        fill: none;
        stroke: var(--primary-text-color);
        stroke-width: 1.4;
      }
      .tariff {
        fill: none;
        stroke: var(--kraftvakt-grid-color);
        stroke-width: 2;
      }
      .limit {
        stroke: var(--error-color, #db4437);
        stroke-width: 1.5;
        stroke-dasharray: 6 4;
      }
      .oldest {
        stroke: var(--secondary-text-color);
        stroke-dasharray: 2 3;
      }
      .marked {
        stroke: var(--primary-color);
        stroke-width: 2;
      }
      .hover {
        stroke: var(--secondary-text-color);
      }
      .essential {
        fill: var(--kraftvakt-essential-background);
      }
      .unknown {
        fill: url(#unknown);
      }
      .unknown-line {
        stroke: var(--divider-color);
        stroke-width: 2;
      }
      .known {
        fill: var(--card-background-color, var(--ha-card-background, #fff));
      }
      rect.on {
        fill: var(--kraftvakt-on-color);
      }
      rect.current {
        fill: color-mix(in srgb, var(--kraftvakt-ev-color) 45%, transparent);
        stroke: var(--kraftvakt-ev-color);
      }
      rect.waiting {
        fill: url(#waiting_time);
        stroke: var(--kraftvakt-reason-color);
        stroke-width: 0.8;
      }
      rect.damping {
        fill: url(#damping);
      }
      rect.start_delay {
        fill: url(#start_delay);
      }
      .waiting-line {
        stroke: var(--kraftvakt-waiting-color);
        stroke-width: 1.6;
      }
      .waiting-line.damping {
        stroke: var(--kraftvakt-damping-color);
      }
      .waiting-line.start_delay {
        stroke: var(--kraftvakt-start-delay-color);
      }
      .tooltip {
        position: absolute;
        top: 8px;
        z-index: 1;
        pointer-events: none;
        min-width: 180px;
        max-width: 260px;
        padding: 8px 10px;
        border-radius: 8px;
        background: var(--card-background-color, #fff);
        box-shadow: var(--ha-card-box-shadow, 0 2px 8px rgba(0, 0, 0, 0.25));
        border: 1px solid var(--divider-color);
        font-size: var(--ha-font-size-s, 12px);
        font-variant-numeric: tabular-nums;
      }
      .tooltip b {
        font-weight: 500;
      }
      .tooltip-decision {
        margin-top: 4px;
        padding-top: 4px;
        border-top: 1px solid var(--divider-color);
      }
      .table {
        overflow-x: auto;
      }
      table {
        width: 100%;
        border-collapse: collapse;
      }
      td {
        padding: 8px 16px;
        border-top: 1px solid var(--divider-color);
        vertical-align: top;
      }
      td.time,
      td.kind {
        width: 1%;
        white-space: nowrap;
        font-variant-numeric: tabular-nums;
        color: var(--secondary-text-color);
      }
      tr.event {
        cursor: pointer;
      }
      tr.event:hover td,
      tr.event.open td {
        background: color-mix(in srgb, var(--primary-color) 8%, transparent);
      }
      tr.event:focus-visible {
        outline: 2px solid var(--primary-color);
        outline-offset: -2px;
      }
      tr.details td {
        border-top: none;
        background: var(--secondary-background-color);
      }
      .chip.current {
        background: color-mix(in srgb, var(--kraftvakt-ev-color) 16%, transparent);
        color: var(--kraftvakt-ev-color);
      }
      .chip.failed {
        background: rgba(var(--rgb-error-color, 219, 68, 55), 0.16);
        color: var(--error-color, #db4437);
      }
      .card-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px 16px;
        padding: 12px 16px;
        border-top: 1px solid var(--divider-color);
        color: var(--secondary-text-color);
        font-size: var(--ha-font-size-s, 12px);
      }
      .card-footer a {
        color: var(--primary-color);
      }
    `]}};e([$e({attribute:!1})],Hr.prototype,"hass",void 0),e([$e({attribute:!1})],Hr.prototype,"localize",void 0),e([$e({type:Boolean,reflect:!0})],Hr.prototype,"narrow",void 0),e([$e({attribute:!1})],Hr.prototype,"status",void 0),e([$e({attribute:!1})],Hr.prototype,"config",void 0),e([ke()],Hr.prototype,"diagnostics",void 0),e([ke()],Hr.prototype,"measurements",void 0),e([ke()],Hr.prototype,"decisions",void 0),e([ke()],Hr.prototype,"error",void 0),e([ke()],Hr.prototype,"rangeMin",void 0),e([ke()],Hr.prototype,"filter",void 0),e([ke()],Hr.prototype,"openRow",void 0),e([ke()],Hr.prototype,"hoverMs",void 0),e([ke()],Hr.prototype,"chartWidth",void 0),Hr=e([we("kraftvakt-diagnostics-page")],Hr);const Tr=["turn_on_margin_w","wait_at_limit_s","penalty_threshold_w"];let Lr=class extends Oi{render(){return X`
      ${this.renderSettingsCard("general.measurement",[this.entityField("power_sensor"),this.windowField()])}
      ${this.renderSettingsCard("general.regulation",[this.numberField("power_limit_w"),this.numberField("turn_on_margin_w"),this.numberField("wait_at_limit_s")])}
      ${this.renderSettingsCard("general.penalty",[this.numberField("penalty_threshold_w")],"general.penalty_info")} ${this.renderRestoreDefaults(Tr)}
    `}willUpdate(e){super.willUpdate(e);const{power_sensor:t,power_sensor_interval_s:i}=this.config.general;t&&null===i&&!this.locked&&this.measuring!==t&&this.notMeasured!==t&&this.measureInterval(t)}changeConfig(e){const t=e.general;t.power_sensor!==this.config.general.power_sensor&&(this.secondsBeforeNewSensor=bt(this.config.general)??this.secondsBeforeNewSensor,this.notMeasured=void 0,e={...e,general:{...t,power_sensor_interval_s:null,regulation_window_updates:null}}),super.changeConfig(e)}async measureInterval(e){this.measuring=e;let t=null;try{t=(await(i=this.hass,r=e,i.callWS({type:"kraftvakt/power_sensor/interval",entity_id:r}))).interval_s}catch{t=null}var i,r;this.measuring=void 0;const a=this.config.general;if(a.power_sensor!==e||this.locked)return;if(null===t)return void(this.notMeasured=e);const n=this.capabilities.regulation_window,s=function(e,t,i){return yt(t,i).reduce((i,r)=>null===i||Math.abs(r*t-e)<Math.abs(i*t-e)-1e-9?r:i,null)}(this.secondsBeforeNewSensor??n.seconds.min??0,t,n);super.changeConfig({...this.config,general:{...a,power_sensor_interval_s:t,regulation_window_updates:s}})}renderSettingsCard(e,t,i){return this.renderCard({title:this.localize(e),description:i&&this.localize(i),content:this.renderForm(t)})}entityField(e){return{name:e,required:!0,selector:{entity:{filter:{domain:"sensor",device_class:"power"},exclude_entities:Bt(this.hass)}}}}windowField(){const e=this.config.general.power_sensor_interval_s,t=this.windowOptions().map(t=>({value:String(t),label:this.localize(1===t?"general.window_option_one":"general.window_option",{count:t,seconds:this.formatNumber(t*(e??0))})}));return{name:"regulation_window_updates",required:!0,disabled:0===t.length,selector:{select:{mode:"dropdown",options:t}}}}windowOptions(){const e=this.config.general.power_sensor_interval_s;return null===e?[]:yt(e,this.capabilities.regulation_window)}formErrors(e,t,i=""){const r=super.formErrors(e,t,i);return"general"===e&&0===this.windowOptions().length&&delete r.regulation_window_updates,r}helperText(e){if("regulation_window_updates"!==e.name)return super.helperText(e);const{power_sensor:t,power_sensor_interval_s:i}=this.config.general,r=this.capabilities.regulation_window.seconds,a={interval:this.formatNumber(i),min:this.formatNumber(r.min),max:this.formatNumber(r.max)};return t?this.measuring===t?this.localize("general.window_measuring"):null===i?this.localize("general.window_not_measured"):0===this.windowOptions().length?this.localize("general.window_too_seldom",a):this.localize("general.fields.regulation_window_updates.helper",a):this.localize("general.window_no_power_sensor")}};e([ke()],Lr.prototype,"measuring",void 0),e([ke()],Lr.prototype,"notMeasured",void 0),Lr=e([we("kraftvakt-general-page")],Lr);const Dr=2*Math.PI*7;class Nr extends fe{constructor(){super(...arguments),this.start=0,this.end=0}connectedCallback(){super.connectedCallback(),this.hasUpdated&&this.startCountdown()}disconnectedCallback(){this.countdown?.cancel(),super.disconnectedCallback()}updated(e){(e.has("start")||e.has("end"))&&this.startCountdown()}startCountdown(){this.countdown?.cancel();const e=this.renderRoot.querySelector(".fill");if(!e)return;const t=Math.max(0,this.end-Date.now()),i=Math.min(1,t/Math.max(1,this.end-this.start));this.countdown=e.animate(this.keyframes(i),{duration:t,easing:"linear",fill:"forwards"})}}e([$e({type:Number})],Nr.prototype,"start",void 0),e([$e({type:Number})],Nr.prototype,"end",void 0);let Pr=class extends Nr{render(){return X`
      <svg viewBox="0 0 18 18" aria-hidden="true">
        ${Y`
          <circle class="track" cx="9" cy="9" r=${7}></circle>
          <circle class="fill" cx="9" cy="9" r=${7} stroke-dasharray=${Dr} transform="rotate(-90 9 9)"></circle>
        `}
      </svg>
    `}keyframes(e){return[{strokeDashoffset:""+Dr*(1-e)},{strokeDashoffset:`${Dr}`}]}static{this.styles=g`
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
  `}};Pr=e([we("kraftvakt-countdown-ring")],Pr);let Or=class extends Nr{render(){return X`<div class="fill"></div>`}keyframes(e){return[{transform:`scaleX(${e})`},{transform:"scaleX(0)"}]}static{this.styles=g`
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
  `}};Or=e([we("kraftvakt-countdown-bar")],Or);const Fr=[1,2,5,10,20,50];let Wr=class extends fe{constructor(){super(...arguments),this.narrow=!1,this.powerNowW=null,this.powerSensor=null}render(){const e=this.status,t=this.hass.language;return X`
      <div class="stats">
        ${this.renderStat({swatch:"power-now",label:"status.power_now",value:pt(t,this.powerNowW),period:this.localize("status.momentary"),entityId:this.powerSensor})}
        ${this.renderStat({swatch:"regulation-average",label:"status.regulation_average",value:pt(t,e.regulation_average_w),period:this.localize("status.average_over_seconds",{seconds:e.regulation_window_s}),entityId:Ut(this.hass,"power_regulation_average")})}
        ${this.renderStat({swatch:"tariff-average",label:"status.tariff_average",value:pt(t,e.tariff_average_w),period:this.localize("status.average_over_hour"),entityId:Ut(this.hass,"power_tariff_average"),alarm:(i=e.tariff_average_w,null!==i&&i>e.power_limit_w)})}
        ${this.renderStat({swatch:"power-limit",label:"status.power_limit",value:pt(t,e.power_limit_w),entityId:Ut(this.hass,"power_limit")})}
      </div>
      ${this.renderMeter()}
    `;var i}renderStat(e){const t=X`
      <div class="stat-label"><span class="swatch ${e.swatch}"></span>${this.localize(e.label)}</div>
      <div class="stat-value ${e.alarm?"alarm":""}">${e.value} <small>kW</small></div>
      ${e.period?X`<div class="stat-period">${e.period}</div>`:te}
    `,i=e.entityId;return i?X`<button class="stat" @click=${e=>ct(e,i)}>${t}</button>`:X`<div class="stat">${t}</div>`}renderMeter(){const e=this.status,t=e=>null===e?null:e/1e3,i=e.power_limit_w/1e3,r=t(this.powerNowW),a=t(e.tariff_average_w),n=t(e.regulation_average_w),s=[r,a,n],{step:o,end:l}=function(e){const t=Fr.find(t=>e/t<=15)??Fr[Fr.length-1];return{step:t,end:Math.ceil(e/t)*t}}(Math.max(1.2*i,...s.map(e=>e??0))),d=e=>100*Math.min(e,l)/l+"%",c=this.hass.language,h=Array.from({length:l/o+1},(e,t)=>t*o),p=this.narrow?3:2,u=h.filter((e,t)=>t%p===0),g=(e,t,i)=>null===i?te:X`<span class="marker ${e}" style="left: ${d(i)}" title="${this.localize(t)} ${ht(c,i,2)} kW"></span>`;return X`
      <div class="meter">
        <div class="markers">
          ${g("power-limit","status.power_limit",i)} ${g("tariff-average","status.tariff_average",a)}
          ${g("regulation-average","status.regulation_average",n)}
        </div>
        <div class="bar">${null===r?te:X`<div class="fill power-now" style="width: ${d(r)}"></div>`}</div>
        <div class="ticks">${h.map(e=>X`<span style="left: ${d(e)}"></span>`)}</div>
        <div class="scale">
          ${u.map((e,t)=>X`<span class=${0===e?"start":e===l?"end":""} style="left: ${d(e)}"
                >${ht(c,e,0)}${t===u.length-1?" kW":""}</span
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
  `}};e([$e({attribute:!1})],Wr.prototype,"hass",void 0),e([$e({attribute:!1})],Wr.prototype,"localize",void 0),e([$e({type:Boolean,reflect:!0})],Wr.prototype,"narrow",void 0),e([$e({attribute:!1})],Wr.prototype,"status",void 0),e([$e({attribute:!1})],Wr.prototype,"powerNowW",void 0),e([$e({attribute:!1})],Wr.prototype,"powerSensor",void 0),Wr=e([we("kraftvakt-power-overview")],Wr);const jr={kind:"outline",icon:"M12 2C17.5 2 22 6.5 22 12S17.5 22 12 22 2 17.5 2 12 6.5 2 12 2M12 4C10.1 4 8.4 4.6 7.1 5.7L18.3 16.9C19.3 15.5 20 13.8 20 12C20 7.6 16.4 4 12 4M16.9 18.3L5.7 7.1C4.6 8.4 4 10.1 4 12C4 16.4 7.6 20 12 20C13.9 20 15.6 19.4 16.9 18.3Z"},Ir={stopped:[{kind:"alarm",icon:"M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4M9,9V15H15V9"},"status.chip_stopped","status.regulation_stopped"],fault:[{kind:"alarm",icon:"M11,15H13V17H11V15M11,7H13V13H11V7M12,2C6.47,2 2,6.5 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20Z"},"status.chip_fault","status.fault"],first_decision:[{kind:"off",icon:l},"status.chip_first_decision","status.first_decision"],no_car:[{kind:"off",icon:"M20.5,19.85L6.41,5.76L2.41,1.76L1.11,3L4.57,6.46L3,11V19A1,1 0 0,0 4,20H5A1,1 0 0,0 6,19V18H16.11L20.84,22.73L22.11,21.46L20.5,19.85M6.5,15A1.5,1.5 0 0,1 5,13.5A1.5,1.5 0 0,1 6.5,12A1.5,1.5 0 0,1 8,13.5A1.5,1.5 0 0,1 6.5,15M5,10L5.78,7.67L8.11,10H5M17.5,5.5L19,10H13.2L16.12,12.92C16.5,12.17 17.37,11.86 18.12,12.21C18.87,12.57 19.18,13.47 18.83,14.21C18.68,14.5 18.43,14.77 18.12,14.92L21,17.8V11L18.92,5C18.71,4.4 18.14,4 17.5,4H7.2L8.7,5.5H17.5Z"},"status.chip_no_car","status.bypassed_no_car"],excluded:[jr,"status.chip_excluded","status.excluded"],outside_window:[{kind:"waiting",icon:"M12,20A8,8 0 0,0 20,12A8,8 0 0,0 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22C6.47,22 2,17.5 2,12A10,10 0 0,1 12,2M12.5,7V12.25L17,14.92L16.25,16.15L11,13V7H12.5Z"},"status.chip_window","status.outside_window"],queued:[{kind:"waiting",icon:l},"status.chip_queued","status.waiting_charger"],starting:[{kind:"info",icon:"M23 8C23 4.13 19.87 1 16 1C12.47 1 9.57 3.61 9.08 7H4.5C3.84 7 3.28 7.42 3.08 8L1 14V22C1 22.55 1.45 23 2 23H3C3.55 23 4 22.55 4 22V21H16V22C16 22.55 16.45 23 17 23H18C18.55 23 19 22.55 19 22V14.32C21.36 13.19 23 10.79 23 8M4.5 8.5H9.03C9.15 10.26 9.92 11.84 11.11 13H3L4.5 8.5M4.5 18C3.67 18 3 17.33 3 16.5S3.67 15 4.5 15 6 15.67 6 16.5 5.33 18 4.5 18M15.5 18C14.67 18 14 17.33 14 16.5S14.67 15 15.5 15 17 15.67 17 16.5 16.33 18 15.5 18M16 13C14.61 13 13.44 12.5 12.47 11.53C11.5 10.56 11 9.39 11 8C11 6.64 11.5 5.46 12.47 4.5C13.44 3.5 14.61 3 16 3C17.36 3 18.54 3.5 19.5 4.5C20.5 5.46 21 6.64 21 8C21 9.39 20.5 10.56 19.5 11.53C18.54 12.5 17.36 13 16 13M16.5 8.25L19.36 9.94L18.61 11.16L15 9V4H16.5V8.25Z"},"status.chip_starting","status.starting_until"],charging:[{kind:"on",icon:n},"status.chip_charging","status.charging_at"],activated:[{kind:"on",icon:"M16,7V3H14V7H10V3H8V7H8C7,7 6,8 6,9V14.5L9.5,18V21H14.5V18L18,14.5V9C18,8 17,7 16,7Z"},"status.activated","status.activated_not_charging"],override:[{kind:"info",icon:"M15,4A8,8 0 0,1 23,12A8,8 0 0,1 15,20A8,8 0 0,1 7,12A8,8 0 0,1 15,4M15,6A6,6 0 0,0 9,12A6,6 0 0,0 15,18A6,6 0 0,0 21,12A6,6 0 0,0 15,6M14,8H15.5V11.78L17.83,14.11L16.77,15.17L14,12.4V8M2,18A1,1 0 0,1 1,17A1,1 0 0,1 2,16H5.83C6.14,16.71 6.54,17.38 7,18H2M3,13A1,1 0 0,1 2,12A1,1 0 0,1 3,11H5.05L5,12L5.05,13H3M4,8A1,1 0 0,1 3,7A1,1 0 0,1 4,6H7C6.54,6.62 6.14,7.29 5.83,8H4Z"},"status.chip_override","status.window_overridden"],deactivated:[{kind:"waiting",icon:"M13,16V8H15V16H13M9,16V8H11V16H9M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22A10,10 0 0,1 2,12A10,10 0 0,1 12,2M12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20A8,8 0 0,0 20,12A8,8 0 0,0 12,4Z"},"status.deactivated","status.deactivated"]};function Rr(e){return e.endsWith(":00")?e.slice(0,-3):e}const Br={kind:"on"},Ur={kind:"off"};let qr=class extends fe{constructor(){super(...arguments),this.narrow=!1,this.phoneQuery=new At(this,600),this.narrowerQuery=new At(this,1e3),this.hasPower=!1}get phone(){return this.phoneQuery.matches}get wide(){return!this.narrowerQuery.matches}render(){const e=function(e){return e.priority.map(e=>"appliance"===e.type?{kind:"appliance",appliance:e,on:e.on}:{kind:"charger_group",group:e,on:e.chargers.some(e=>e.activated&&!e.bypassed)})}(this.status),t=function(e){const t=e.map(e=>e.on).lastIndexOf(!0),i=e.slice(t+1).some(e=>"charger_group"===e.kind||!e.appliance.excluded);return t>=0&&i?t:-1}(e);return this.hasPower=function(e){return e.priority.flatMap(e=>"appliance"===e.type?[e]:e.chargers).some(e=>null!==e.power_w)}(this.status),X`
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
    `}columns(){return`grid-template-columns: ${["minmax(24px, max-content)","minmax(0, 1fr)","max-content",...this.hasPower?["max-content"]:[],"var(--waiting-width)",...this.wide?["max-content"]:[],"max-content"].join(" ")}`}renderRow(e,t,i){if(!t)return X`<div class="row ${e}">${i}</div>`;const r=e=>{e.preventDefault(),ct(e,t)};return X`
      <div
        class="row ${e} clickable"
        role="button"
        tabindex="0"
        @click=${r}
        @keydown=${e=>"Enter"===e.key||" "===e.key?r(e):void 0}
      >
        ${i}
      </div>
    `}renderApplianceRow(e,t){const i=null!==e.temperature&&!this.phone;return this.renderRow(`appliance ${e.on?"":"off"} ${e.excluded?"excluded":""} ${e.essential?"essential":""} ${i?"with-temperature":""}`,Rt(this.hass,this.applianceEntity(e)),X`
        ${this.renderRank(t)}
        <div class="row-title">
          ${this.renderApplianceIcon(e)}${this.renderName(e.name)}
          ${e.variant&&!this.phone?X`<span class="variant" title=${e.variant}>${e.variant}</span>`:te}
        </div>
        ${this.renderTemperature(e)} ${this.renderPower(e.power_w)} ${this.renderApplianceWaiting(e)} ${this.renderApplianceChip(e)}
      `)}renderRank(e){return this.renderWideOnly(X`<span class="rank">${e??te}</span>`)}renderWideOnly(e){return this.phone?te:e}renderName(e){return X`<span class="name" title=${e}>${e}</span>`}renderApplianceChip(e){return e.excluded?this.renderChip(jr,"status.chip_excluded","status.excluded"):e.on?this.renderChip(Br,"status.on","status.on"):this.renderChip(Ur,"status.off","status.off")}renderApplianceIcon(e){const t=this.applianceEntity(e),i=t?this.hass.states[t]:void 0;return X`
      <span class="device-icon ${e.on?"on":""}">
        ${i?X`<ha-state-icon .hass=${this.hass} .stateObj=${i}></ha-state-icon>`:te}
        <ha-svg-icon .path=${"M7,2V13H10V22L17,10H13L17,2H7Z"}></ha-svg-icon>
      </span>
    `}renderChargerGroup(e,i){const r=e.chargers;if(1===r.length)return this.renderChargerRow(r[0],i);const a=r.filter(e=>e.charging).length;return X`
      <div class="row group">
        ${this.renderRank(i)}
        <div class="row-title">
          <ha-svg-icon class="ev-icon" .path=${t}></ha-svg-icon>
          ${this.renderName(e.name)} ${0!==r.length||this.phone?te:X`<span class="row-sub">${this.localize("status.no_chargers")}</span>`}
        </div>
        ${this.renderWideOnly(0===r.length?X`<span></span>`:X`<span class="charging-count" title=${this.localize("status.chargers_charging",{charging:a,total:r.length})}>
                <ha-svg-icon .path=${n}></ha-svg-icon>${a} / ${r.length}
              </span>`)}
      </div>
      ${r.map(e=>this.renderChargerRow(e,null))}
    `}renderChargerRow(e,t){return this.renderRow(`charger ${null===t?"":"alone"} ${e.activated?"":"off"}`,Rt(this.hass,this.chargerEntity(e)),X`
        ${this.renderRank(t)}
        <div class="row-title">
          <ha-svg-icon class="device-icon ev ${e.activated?"on":""}" .path=${r}></ha-svg-icon>
          ${this.renderName(e.name)}
        </div>
        ${this.phone?this.renderPhoneCurrent(e):this.renderAmperes(e)} ${this.renderPower(e.power_w)} ${this.renderChargerWaiting(e)}
        ${this.renderChargerChip(e)}
      `)}renderApplianceWaiting(e){return this.renderWaiting(e,e=>`${this.localize("status.delayed_turn_on")}: ${this.localize("status.waiting_ends_at",{time:e})}`,()=>this.renderPowerToFree(e.power_to_free_w,"status.power_to_free_turn_on"))}renderChargerWaiting(e){return this.renderWaiting(e,t=>{switch(e.waiting_reason){case"damping":return`${this.localize("status.damping")}: ${this.localize("status.damping_ampere_at",{time:t})}`;case"start_delay":return`${this.localize("status.start_delay")}: ${this.localize("status.start_delay_ends_at",{time:t})}`;default:return`${this.localize("status.delayed_activation")}: ${this.localize("status.activated_at",{time:t})}`}},()=>this.renderPowerToFree(e.power_to_free_w,e.activated?"status.power_to_free_ampere":"status.power_to_free_activate"))}renderWaiting(e,t,i){if(!e.waiting_since||!e.waiting_ends_at)return X`${i()}${this.wide?X`<span></span>`:te}`;const r=ft(mt(this.hass),e.waiting_ends_at);return X`
      <span class="waiting" title=${t(r)}>
        <ha-svg-icon .path=${"M12,20A7,7 0 0,1 5,13A7,7 0 0,1 12,6A7,7 0 0,1 19,13A7,7 0 0,1 12,20M19.03,7.39L20.45,5.97C20,5.46 19.55,5 19.04,4.56L17.62,6C16.07,4.74 14.12,4 12,4A9,9 0 0,0 3,13A9,9 0 0,0 12,22C17,22 21,17.97 21,13C21,10.88 20.26,8.93 19.03,7.39M11,14H13V8H11M15,1H9V3H15V1Z"}></ha-svg-icon>
        ${this.renderWideOnly(X`<kraftvakt-countdown-bar .start=${Date.parse(e.waiting_since)} .end=${Date.parse(e.waiting_ends_at)}></kraftvakt-countdown-bar>`)}
      </span>
      ${this.wide?X`<span class="waiting-ends-at" title=${t(r)}>${r}</span>`:te}
    `}renderPowerToFree(e,t){if(null===e)return this.phone?te:X`<span></span>`;const i=pt(this.hass.language,e);return X`
      <span class="waiting" title=${this.localize(t,{power:i})}>
        <ha-svg-icon .path=${"M19.92,12.08L12,20L4.08,12.08L5.5,10.67L11,16.17V2H13V16.17L18.5,10.66L19.92,12.08M12,20H2V22H22V20H12Z"}></ha-svg-icon>
        ${this.renderWideOnly(X`<span class="power-to-free">${i} kW</span>`)}
      </span>
    `}renderPower(e){return this.hasPower?this.renderWideOnly(X`<span class="measured" title=${this.localize("status.power")}>${null===e?te:`${pt(this.hass.language,e)} kW`}</span>`):te}renderTemperature(e){const t=e.temperature;return null===t||this.phone?te:X`<span class="measured" title=${this.localize("status.temperature")}>${ht(this.hass.language,t.value,1)} ${t.unit}</span>`}renderAmperes(e){const t=this.chargerConfig(e);if(!t)return X`<span></span>`;const i=t.max_current_a-t.min_current_a+1,r=null===e.current_a?0:e.current_a-t.min_current_a+1,a=e.bypassed?"on bypassed":"on";return X`
      <span class="amperes">
        <span class="current ${null===e.current_a?"none":""}"
          >${null===e.current_a?"–":this.localize("status.amperes",{current:e.current_a})}</span
        >
        <span class="ampere-steps ${i>16?"small":""}">
          ${Array.from({length:i},(e,t)=>X`<span class="ampere ${t<r?a:""}"></span>`)}
        </span>
      </span>
    `}renderPhoneCurrent(e){return null===e.current_a?te:X`<span class="current">${this.localize("status.amperes",{current:e.current_a})}</span>`}renderChargerChip(e){const{chip:t,word:i,sentence:r,wordParams:a,sentenceParams:n}=function(e,t,i,r){const[a,n,s]=Ir[e.state];return"outside_window"===e.state&&i?{chip:a,word:n,sentence:s,wordParams:{start:Rr(i.start),end:Rr(i.end)},sentenceParams:{...i}}:"starting"===e.state&&e.starting_until?{chip:a,word:n,sentence:s,wordParams:{},sentenceParams:{time:ft(t,e.starting_until)}}:"queued"===e.state&&"waiting_time"===e.waiting_reason?{chip:a,word:n,sentence:"status.queued_waiting_time",wordParams:{},sentenceParams:{}}:"queued"===e.state&&r?{chip:a,word:n,sentence:"status.queued_for_room",wordParams:{},sentenceParams:{}}:{chip:a,word:n,sentence:s,wordParams:{},sentenceParams:{current:e.current_a??0}}}(e,mt(this.hass),this.chargerConfig(e)?.charging_window,this.sharesByChargingPower(e));return this.renderChip(t,i,r,a,n)}renderChip(e,t,i,r={},a=r){return X`
      <span class="state chip ${e.kind}" title=${this.localize(i,a)}>
        ${e.icon?X`<ha-svg-icon .path=${e.icon}></ha-svg-icon>`:X`<span class="dot"></span>`} ${this.localize(t,r)}
      </span>
    `}renderCutOff(){const e=this.status,t=this.hass.language,i=e.regulation_average_w,r=null===i?0:e.power_limit_w-i;return X`
      <div class="cut-off" title=${this.localize("status.power_runs_out")}>
        <ha-svg-icon .path=${"M11,4H13V16L18.5,10.5L19.92,11.92L12,19.84L4.08,11.92L5.5,10.5L11,16V4Z"}></ha-svg-icon>
        ${r>0?this.localize("status.free_power",{power:pt(t,r),share:gt(t,r/e.power_limit_w)}):te}
      </div>
    `}applianceEntity(e){return this.config?.config.appliances.find(t=>t.id===e.id)?.entity_id}chargerConfig(e){return this.config&&rt(this.config.config).find(t=>t.id===e.id)}chargerEntity(e){const t=this.chargerConfig(e);return t?jt(t):null}sharesByChargingPower(e){const t=this.config?.config.charger_groups.find(t=>t.chargers.some(t=>t.id===e.id)),i=this.status.priority.find(e=>"charger_group"===e.type&&e.id===t?.id);return!!t&&!!i&&t.dynamic_order&&!i.one_at_a_time}static{this.styles=[Sr,Vr,g`
      :host {
        display: block;
        container-type: inline-size;
      }
      /*
       * The spacing grows with the list's width, from tight just above the phone layout (600 px)
       * to a list 1040 px wide, where the columns after the name take its right half.
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
      .row.charger:not(.alone) {
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
      .row.charger:not(.alone) .row-title {
        padding-inline-start: 24px;
      }
      :host([narrow]) .row.charger:not(.alone) .row-title {
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
      .waiting-ends-at {
        color: var(--secondary-text-color);
        font-size: var(--ha-font-size-s, 12px);
        font-variant-numeric: tabular-nums;
        white-space: nowrap;
      }
      .power-to-free {
        color: var(--secondary-text-color);
        font-size: var(--ha-font-size-s, 12px);
        font-variant-numeric: tabular-nums;
        white-space: nowrap;
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
        background: repeating-linear-gradient(45deg, var(--secondary-text-color) 0 2px, rgba(127, 127, 127, 0.16) 2px 4px);
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
    `]}};e([$e({attribute:!1})],qr.prototype,"hass",void 0),e([$e({attribute:!1})],qr.prototype,"localize",void 0),e([$e({type:Boolean,reflect:!0})],qr.prototype,"narrow",void 0),e([$e({attribute:!1})],qr.prototype,"status",void 0),e([$e({attribute:!1})],qr.prototype,"config",void 0),qr=e([we("kraftvakt-priority-list")],qr);let Gr=class extends fe{constructor(){super(...arguments),this.narrow=!1}render(){if(!this.status)return te;const e=this.status;return X`
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
    `}renderRunning(e){const t=this.config?.config.general.power_sensor??null,i=qt(this.hass,t??"");return X`
      ${e.safe_state?this.renderSafeState(null!==i):te} ${e.penalty.active?this.renderPenalty(e):te}
      <kraftvakt-power-overview
        .hass=${this.hass}
        .localize=${this.localize}
        .narrow=${this.narrow}
        .status=${e}
        .powerNowW=${i}
        .powerSensor=${t}
      ></kraftvakt-power-overview>
    `}renderNextDecision(e,t){const i=Date.parse(t),r=1e3*e.regulation_window_s,a=ft(mt(this.hass),t);return X`
      <span class="next-decision" title=${this.localize("status.next_decision_at",{time:a})}>
        ${this.narrow?te:this.localize("status.next_decision")}
        <kraftvakt-countdown-ring .start=${i-r} .end=${i}></kraftvakt-countdown-ring>
      </span>
    `}renderSafeState(e){const t=this.config?.config.general.power_sensor??"",i=this.hass.states[t]?.attributes.friendly_name??t;return X`
      <ha-alert alert-type=${e?"info":"error"} .title=${this.localize("status.safe_state_title")}>
        ${this.localize(e?"status.safe_state_back_text":"status.safe_state_text",{sensor:i})}
      </ha-alert>
    `}renderPenalty(e){const t=(i=this.hass.language,r=Math.max(0,e.penalty.overconsumption_wh),ht(i,r/1e3,2));var i,r;const a=e.penalty.recovery_started?"status.recovery_started":"status.recovery_not_started";return X`
      <ha-alert alert-type="warning" .title=${this.localize("status.penalty_title")}>
        ${this.localize("status.penalty_text")}
        <div class="penalty-details">${this.localize("status.overconsumption_left",{energy:t})} · ${this.localize(a)}</div>
      </ha-alert>
    `}renderStopped(e){return 0===e.missing.length?X`<ha-alert alert-type="info">${this.localize("status.stopped_info")}</ha-alert>`:X`
      <ha-alert alert-type="warning" .title=${this.localize("status.incomplete_title")}>
        <ul class="missing">
          ${e.missing.map(e=>{const t=function(e){return"general"===e.section&&e.field&&Jt.has(e.field)?"advanced":Zt[e.section]}(e);return X`
              <li>
                ${function(e,t,i,r){const a={item:Xt(e,t,i,r),action:Qt(e.field,i),code:e.code};return i(Gt[e.code]??"missing.unknown",a)}(e,this.config,this.localize,this.hass)}
                <a href="${lt}/${t}" @click=${e=>this.openPage(e,t)}> ${this.localize(`tabs.${t}`)} </a>
              </li>
            `})}
        </ul>
      </ha-alert>
    `}openPage(e,t){e.preventDefault(),dt(t)}static{this.styles=[Sr,Vr,g`
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
    `]}};e([$e({attribute:!1})],Gr.prototype,"hass",void 0),e([$e({attribute:!1})],Gr.prototype,"localize",void 0),e([$e({type:Boolean,reflect:!0})],Gr.prototype,"narrow",void 0),e([$e({attribute:!1})],Gr.prototype,"status",void 0),e([$e({attribute:!1})],Gr.prototype,"config",void 0),e([ke()],Gr.prototype,"runningError",void 0),Gr=e([we("kraftvakt-status-page")],Gr);const Kr={status:"M3,13H5.79L10.1,4.79L11.28,13.75L14.5,9.66L17.83,13H21V15H17L14.67,12.67L9.92,18.73L8.94,11.31L7,15H3V13Z",general:"M12,15.5A3.5,3.5 0 0,1 8.5,12A3.5,3.5 0 0,1 12,8.5A3.5,3.5 0 0,1 15.5,12A3.5,3.5 0 0,1 12,15.5M19.43,12.97C19.47,12.65 19.5,12.33 19.5,12C19.5,11.67 19.47,11.34 19.43,11L21.54,9.37C21.73,9.22 21.78,8.95 21.66,8.73L19.66,5.27C19.54,5.05 19.27,4.96 19.05,5.05L16.56,6.05C16.04,5.66 15.5,5.32 14.87,5.07L14.5,2.42C14.46,2.18 14.25,2 14,2H10C9.75,2 9.54,2.18 9.5,2.42L9.13,5.07C8.5,5.32 7.96,5.66 7.44,6.05L4.95,5.05C4.73,4.96 4.46,5.05 4.34,5.27L2.34,8.73C2.21,8.95 2.27,9.22 2.46,9.37L4.57,11C4.53,11.34 4.5,11.67 4.5,12C4.5,12.33 4.53,12.65 4.57,12.97L2.46,14.63C2.27,14.78 2.21,15.05 2.34,15.27L4.34,18.73C4.46,18.95 4.73,19.03 4.95,18.95L7.44,17.94C7.96,18.34 8.5,18.68 9.13,18.93L9.5,21.58C9.54,21.82 9.75,22 10,22H14C14.25,22 14.46,21.82 14.5,21.58L14.87,18.93C15.5,18.67 16.04,18.34 16.56,17.94L19.05,18.95C19.27,19.03 19.54,18.95 19.66,18.73L21.66,15.27C21.78,15.05 21.73,14.78 21.54,14.63L19.43,12.97Z",appliances:"M7,13V11H21V13H7M7,19V17H21V19H7M7,7V5H21V7H7M3,8V5H2V4H4V8H3M2,17V16H5V20H2V19H4V18.5H3V17.5H4V17H2M4.25,10A0.75,0.75 0 0,1 5,10.75C5,10.95 4.92,11.14 4.79,11.27L3.12,13H5V14H2V13.08L4,11H2V10H4.25Z",charging:t,advanced:"M3,17V19H9V17H3M3,5V7H13V5H3M13,21V19H21V17H13V15H11V21H13M7,9V11H3V13H7V15H9V9H7M21,13V11H11V13H21M15,9H17V7H21V5H17V3H15V9Z",diagnostics:"M19,8C19.56,8 20,8.43 20,9A1,1 0 0,1 19,10C18.43,10 18,9.55 18,9C18,8.43 18.43,8 19,8M2,2V11C2,13.96 4.19,16.5 7.14,16.91C7.76,19.92 10.42,22 13.5,22A6.5,6.5 0 0,0 20,15.5V11.81C21.16,11.39 22,10.29 22,9A3,3 0 0,0 19,6A3,3 0 0,0 16,9C16,10.29 16.84,11.4 18,11.81V15.41C18,17.91 16,19.91 13.5,19.91C11.5,19.91 9.82,18.7 9.22,16.9C12,16.3 14,13.8 14,11V2H10V5H12V11A4,4 0 0,1 8,15A4,4 0 0,1 4,11V5H6V2H2Z"},Zr=["status","diagnostics"],Jr={general:je`kraftvakt-general-page`,appliances:je`kraftvakt-appliances-page`,charging:je`kraftvakt-charging-page`,advanced:je`kraftvakt-advanced-page`};let Qr=class extends fe{constructor(){super(...arguments),this.narrow=!1,this.haElementsReady=!1,this.saveErrors=[],this.saving=!1,this.localize=nt("en"),this.warnBeforeUnload=e=>{this.dirty&&e.preventDefault()}}connectedCallback(){super.connectedCallback(),window.addEventListener("beforeunload",this.warnBeforeUnload),customElements.whenDefined("ha-form").then(()=>{this.haElementsReady=!0}),this.hass&&this.subscribe()}disconnectedCallback(){super.disconnectedCallback(),window.removeEventListener("beforeunload",this.warnBeforeUnload),this.unsubscribe()}willUpdate(e){e.has("hass")&&this.hass?.language!==e.get("hass")?.language&&(this.localize=nt(this.hass?.language??"en"),this.hass?.loadFragmentTranslation("config")),e.has("hass")&&this.hass&&!this.unsubscribeStatus&&this.subscribe()}updated(e){e.has("route")&&this.openAppliancesFromConfigureButton()}render(){if(!this.hass||!this.haElementsReady)return X``;const e=this.currentPage;return X`
      <div class="toolbar">
        <ha-menu-button .hass=${this.hass} .narrow=${this.narrow}></ha-menu-button>
        <div class="title">${this.localize("panel.title")}</div>
        <ha-tab-group @wa-tab-show=${this.tabShown}>
          ${Object.entries(Kr).map(([t,i])=>X`
              <ha-tab-group-tab slot="nav" panel=${t} .active=${Oe(t===e)} title=${this.tabLabel(t)}>
                <ha-svg-icon .path=${i}></ha-svg-icon>
                <span class="tab-label">${this.tabLabel(t)}</span>
              </ha-tab-group-tab>
            `)}
        </ha-tab-group>
      </div>
      <div class="content ${Zr.includes(e)?"":"config"}" @draft-changed=${this.draftChanged}>
        ${this.renderLoadError()} ${this.renderPage(e)}
      </div>
      <kraftvakt-confirm-dialog
        .open=${void 0!==this.leavingTo}
        .heading=${this.localize("config.leave_title")}
        .text=${this.localize("config.leave_text")}
        .confirmText=${this.localize("config.leave")}
        .cancelText=${this.localize("config.stay")}
        @confirm=${this.leaveConfirmed}
        @cancel=${this.leaveCancelled}
      ></kraftvakt-confirm-dialog>
    `}renderLoadError(){if(void 0===this.loadError)return"";const e=qe(this.loadError)&&"not_loaded"===this.loadError.code?this.localize("panel.not_loaded"):this.localize("panel.error",{message:Ge(this.loadError)});return X`<ha-alert alert-type="error">${e}</ha-alert>`}renderPage(e){switch(e){case"status":return X`
          <kraftvakt-status-page .hass=${this.hass} .localize=${this.localize} .narrow=${this.narrow} .status=${this.status} .config=${this.config}></kraftvakt-status-page>
        `;case"diagnostics":return X`
          <kraftvakt-diagnostics-page
            .hass=${this.hass}
            .localize=${this.localize}
            .narrow=${this.narrow}
            .status=${this.status}
            .config=${this.config}
          ></kraftvakt-diagnostics-page>
        `;case"general":case"appliances":case"charging":case"advanced":return this.renderConfigPage(e)}}renderConfigPage(e){if(!(this.hass&&this.status&&this.config&&this.draft&&this.capabilities))return"";const t=this.status.running,i=t?[]:mi(this.draft,this.capabilities,this.hass),r=!t&&(this.dirty||this.saveErrors.length>0),a=t?[]:this.pageIssues(i);return X`
      ${t?X`<kraftvakt-locked-banner .hass=${this.hass} .localize=${this.localize} .narrow=${this.narrow}></kraftvakt-locked-banner>`:""}
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
    `}renderConfigPageContent(e,t,i,r){const a=Jr[e];return Re`
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
    `}pageIssues(e){return this.draft?[...e,...this.saveErrors,...fi(this.draft)]:[]}get dirty(){return void 0!==this.draft&&(e=this.draft,t=this.savedConfig,!(JSON.stringify(e)===JSON.stringify(t)));var e,t}get savedConfig(){return this.config&&it(this.config.config)}draftChanged(e){e.type!==Xe||this.status?.running||(this.draft=it(e.detail))}async save(){if(this.hass&&this.draft){this.saving=!0,this.saveMessage=void 0;try{const e=await((e,t)=>e.callWS({type:"kraftvakt/config/save",config:t}))(this.hass,this.draft);e.saved?(this.saveErrors=[],await this.loadConfig({resetDraft:!0})):(this.saveErrors=e.errors,this.saveMessage=this.localize("config.not_saved"))}catch(e){this.saveMessage=qe(e)&&"regulation_running"===e.code?this.localize("config.save_refused_running"):this.localize("panel.error",{message:Ge(e)})}finally{this.saving=!1}}}discard(){this.resetDraft()}resetDraft(){this.draft=this.savedConfig,this.saveErrors=[],this.saveMessage=void 0}leaveConfirmed(){const e=this.leavingTo;this.leavingTo=void 0,this.resetDraft(),e&&dt(e)}leaveCancelled(){this.leavingTo=void 0}get currentPage(){return function(e){const t=e.split("/")[1]??"";return ot.includes(t)?t:"status"}(this.route?.path??"")}tabLabel(e){return this.localize(`tabs.${e}`)}tabShown(e){const t=e.detail.name;t!==this.currentPage&&(Zr.includes(t)&&this.dirty?this.leavingTo=t:dt(t))}subscribe(){var e,t;this.hass&&(this.unsubscribeStatus=(e=this.hass,t=e=>this.statusReceived(e),e.connection.subscribeMessage(t,{type:"kraftvakt/status/subscribe"})),this.unsubscribeStatus.catch(e=>{this.loadError=e,this.unsubscribeStatus=void 0}),(e=>e.callWS({type:"kraftvakt/capabilities"}))(this.hass).then(e=>this.capabilities=e).catch(e=>this.loadError=e))}unsubscribe(){this.unsubscribeStatus?.then(e=>e()).catch(()=>{}),this.unsubscribeStatus=void 0}statusReceived(e){const t=this.status;this.status=e,this.loadError=void 0,void 0!==t&&t.running===e.running&&t.config_version===e.config_version&&JSON.stringify(t.missing)===JSON.stringify(e.missing)||this.loadConfig()}async loadConfig(e={}){var t;if(this.hass)try{const i=this.dirty&&!e.resetDraft&&!this.status?.running;this.config=await(t=this.hass,t.callWS({type:"kraftvakt/config/get"})),i||this.resetDraft()}catch(e){this.loadError=e}}openAppliancesFromConfigureButton(){new URLSearchParams(window.location.search).has("config_entry")&&dt("appliances",{replace:!0})}static{this.styles=g`
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
    /* As wide as Home Assistant's Overview dashboard: three sections of 500 px with 32 px between them. */
    .content {
      max-width: 1564px;
      margin: 0 auto;
      padding: 16px;
    }
    .content.config {
      max-width: 840px;
    }
    :host([narrow]) .content {
      padding: 8px;
    }
  `}};e([$e({attribute:!1})],Qr.prototype,"hass",void 0),e([$e({type:Boolean,reflect:!0})],Qr.prototype,"narrow",void 0),e([$e({attribute:!1})],Qr.prototype,"route",void 0),e([ke()],Qr.prototype,"haElementsReady",void 0),e([ke()],Qr.prototype,"status",void 0),e([ke()],Qr.prototype,"config",void 0),e([ke()],Qr.prototype,"loadError",void 0),e([ke()],Qr.prototype,"capabilities",void 0),e([ke()],Qr.prototype,"draft",void 0),e([ke()],Qr.prototype,"saveErrors",void 0),e([ke()],Qr.prototype,"saveMessage",void 0),e([ke()],Qr.prototype,"saving",void 0),e([ke()],Qr.prototype,"leavingTo",void 0),Qr=e([we("kraftvakt-panel")],Qr);export{Qr as KraftvaktPanel};
