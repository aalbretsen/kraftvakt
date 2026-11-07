function e(e,t,a,i){var r,n=arguments.length,s=n<3?t:null===i?i=Object.getOwnPropertyDescriptor(t,a):i;if("object"==typeof Reflect&&"function"==typeof Reflect.decorate)s=Reflect.decorate(e,t,a,i);else for(var o=e.length-1;o>=0;o--)(r=e[o])&&(s=(n<3?r(s):n>3?r(t,a,s):r(t,a))||s);return n>3&&s&&Object.defineProperty(t,a,s),s}"function"==typeof SuppressedError&&SuppressedError;const t=globalThis,a=t.ShadowRoot&&(void 0===t.ShadyCSS||t.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,i=Symbol(),r=new WeakMap;let n=class{constructor(e,t,a){if(this._$cssResult$=!0,a!==i)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=e,this.t=t}get styleSheet(){let e=this.o;const t=this.t;if(a&&void 0===e){const a=void 0!==t&&1===t.length;a&&(e=r.get(t)),void 0===e&&((this.o=e=new CSSStyleSheet).replaceSync(this.cssText),a&&r.set(t,e))}return e}toString(){return this.cssText}};const s=(e,...t)=>{const a=1===e.length?e[0]:t.reduce((t,a,i)=>t+(e=>{if(!0===e._$cssResult$)return e.cssText;if("number"==typeof e)return e;throw Error("Value passed to 'css' function must be a 'css' function result: "+e+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(a)+e[i+1],e[0]);return new n(a,e,i)},o=a?e=>e:e=>e instanceof CSSStyleSheet?(e=>{let t="";for(const a of e.cssRules)t+=a.cssText;return(e=>new n("string"==typeof e?e:e+"",void 0,i))(t)})(e):e,{is:l,defineProperty:c,getOwnPropertyDescriptor:d,getOwnPropertyNames:h,getOwnPropertySymbols:p,getPrototypeOf:g}=Object,u=globalThis,v=u.trustedTypes,f=v?v.emptyScript:"",m=u.reactiveElementPolyfillSupport,_=(e,t)=>e,b={toAttribute(e,t){switch(t){case Boolean:e=e?f:null;break;case Object:case Array:e=null==e?e:JSON.stringify(e)}return e},fromAttribute(e,t){let a=e;switch(t){case Boolean:a=null!==e;break;case Number:a=null===e?null:Number(e);break;case Object:case Array:try{a=JSON.parse(e)}catch(e){a=null}}return a}},y=(e,t)=>!l(e,t),w={attribute:!0,type:String,converter:b,reflect:!1,useDefault:!1,hasChanged:y};Symbol.metadata??=Symbol("metadata"),u.litPropertyMetadata??=new WeakMap;let $=class extends HTMLElement{static addInitializer(e){this._$Ei(),(this.l??=[]).push(e)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(e,t=w){if(t.state&&(t.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(e)&&((t=Object.create(t)).wrapped=!0),this.elementProperties.set(e,t),!t.noAccessor){const a=Symbol(),i=this.getPropertyDescriptor(e,a,t);void 0!==i&&c(this.prototype,e,i)}}static getPropertyDescriptor(e,t,a){const{get:i,set:r}=d(this.prototype,e)??{get(){return this[t]},set(e){this[t]=e}};return{get:i,set(t){const n=i?.call(this);r?.call(this,t),this.requestUpdate(e,n,a)},configurable:!0,enumerable:!0}}static getPropertyOptions(e){return this.elementProperties.get(e)??w}static _$Ei(){if(this.hasOwnProperty(_("elementProperties")))return;const e=g(this);e.finalize(),void 0!==e.l&&(this.l=[...e.l]),this.elementProperties=new Map(e.elementProperties)}static finalize(){if(this.hasOwnProperty(_("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(_("properties"))){const e=this.properties,t=[...h(e),...p(e)];for(const a of t)this.createProperty(a,e[a])}const e=this[Symbol.metadata];if(null!==e){const t=litPropertyMetadata.get(e);if(void 0!==t)for(const[e,a]of t)this.elementProperties.set(e,a)}this._$Eh=new Map;for(const[e,t]of this.elementProperties){const a=this._$Eu(e,t);void 0!==a&&this._$Eh.set(a,e)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(e){const t=[];if(Array.isArray(e)){const a=new Set(e.flat(1/0).reverse());for(const e of a)t.unshift(o(e))}else void 0!==e&&t.push(o(e));return t}static _$Eu(e,t){const a=t.attribute;return!1===a?void 0:"string"==typeof a?a:"string"==typeof e?e.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(e=>this.enableUpdating=e),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(e=>e(this))}addController(e){(this._$EO??=new Set).add(e),void 0!==this.renderRoot&&this.isConnected&&e.hostConnected?.()}removeController(e){this._$EO?.delete(e)}_$E_(){const e=new Map,t=this.constructor.elementProperties;for(const a of t.keys())this.hasOwnProperty(a)&&(e.set(a,this[a]),delete this[a]);e.size>0&&(this._$Ep=e)}createRenderRoot(){const e=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return((e,i)=>{if(a)e.adoptedStyleSheets=i.map(e=>e instanceof CSSStyleSheet?e:e.styleSheet);else for(const a of i){const i=document.createElement("style"),r=t.litNonce;void 0!==r&&i.setAttribute("nonce",r),i.textContent=a.cssText,e.appendChild(i)}})(e,this.constructor.elementStyles),e}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(e=>e.hostConnected?.())}enableUpdating(e){}disconnectedCallback(){this._$EO?.forEach(e=>e.hostDisconnected?.())}attributeChangedCallback(e,t,a){this._$AK(e,a)}_$ET(e,t){const a=this.constructor.elementProperties.get(e),i=this.constructor._$Eu(e,a);if(void 0!==i&&!0===a.reflect){const r=(void 0!==a.converter?.toAttribute?a.converter:b).toAttribute(t,a.type);this._$Em=e,null==r?this.removeAttribute(i):this.setAttribute(i,r),this._$Em=null}}_$AK(e,t){const a=this.constructor,i=a._$Eh.get(e);if(void 0!==i&&this._$Em!==i){const e=a.getPropertyOptions(i),r="function"==typeof e.converter?{fromAttribute:e.converter}:void 0!==e.converter?.fromAttribute?e.converter:b;this._$Em=i;const n=r.fromAttribute(t,e.type);this[i]=n??this._$Ej?.get(i)??n,this._$Em=null}}requestUpdate(e,t,a,i=!1,r){if(void 0!==e){const n=this.constructor;if(!1===i&&(r=this[e]),a??=n.getPropertyOptions(e),!((a.hasChanged??y)(r,t)||a.useDefault&&a.reflect&&r===this._$Ej?.get(e)&&!this.hasAttribute(n._$Eu(e,a))))return;this.C(e,t,a)}!1===this.isUpdatePending&&(this._$ES=this._$EP())}C(e,t,{useDefault:a,reflect:i,wrapped:r},n){a&&!(this._$Ej??=new Map).has(e)&&(this._$Ej.set(e,n??t??this[e]),!0!==r||void 0!==n)||(this._$AL.has(e)||(this.hasUpdated||a||(t=void 0),this._$AL.set(e,t)),!0===i&&this._$Em!==e&&(this._$Eq??=new Set).add(e))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(e){Promise.reject(e)}const e=this.scheduleUpdate();return null!=e&&await e,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(const[e,t]of this._$Ep)this[e]=t;this._$Ep=void 0}const e=this.constructor.elementProperties;if(e.size>0)for(const[t,a]of e){const{wrapped:e}=a,i=this[t];!0!==e||this._$AL.has(t)||void 0===i||this.C(t,void 0,a,i)}}let e=!1;const t=this._$AL;try{e=this.shouldUpdate(t),e?(this.willUpdate(t),this._$EO?.forEach(e=>e.hostUpdate?.()),this.update(t)):this._$EM()}catch(t){throw e=!1,this._$EM(),t}e&&this._$AE(t)}willUpdate(e){}_$AE(e){this._$EO?.forEach(e=>e.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(e)),this.updated(e)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(e){return!0}update(e){this._$Eq&&=this._$Eq.forEach(e=>this._$ET(e,this[e])),this._$EM()}updated(e){}firstUpdated(e){}};$.elementStyles=[],$.shadowRootOptions={mode:"open"},$[_("elementProperties")]=new Map,$[_("finalized")]=new Map,m?.({ReactiveElement:$}),(u.reactiveElementVersions??=[]).push("2.1.2");const k=globalThis,x=e=>e,A=k.trustedTypes,E=A?A.createPolicy("lit-html",{createHTML:e=>e}):void 0,S="$lit$",C=`lit$${Math.random().toFixed(9).slice(2)}$`,M="?"+C,z=`<${M}>`,V=document,T=()=>V.createComment(""),H=e=>null===e||"object"!=typeof e&&"function"!=typeof e,P=Array.isArray,L="[ \t\n\f\r]",R=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,U=/-->/g,O=/>/g,j=RegExp(`>|${L}(?:([^\\s"'>=/]+)(${L}*=${L}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`,"g"),N=/'/g,D=/"/g,W=/^(?:script|style|textarea|title)$/i,K=(e=>(t,...a)=>({_$litType$:e,strings:t,values:a}))(1),B=Symbol.for("lit-noChange"),I=Symbol.for("lit-nothing"),F=new WeakMap,q=V.createTreeWalker(V,129);function Z(e,t){if(!P(e)||!e.hasOwnProperty("raw"))throw Error("invalid template strings array");return void 0!==E?E.createHTML(t):t}const J=(e,t)=>{const a=e.length-1,i=[];let r,n=2===t?"<svg>":3===t?"<math>":"",s=R;for(let t=0;t<a;t++){const a=e[t];let o,l,c=-1,d=0;for(;d<a.length&&(s.lastIndex=d,l=s.exec(a),null!==l);)d=s.lastIndex,s===R?"!--"===l[1]?s=U:void 0!==l[1]?s=O:void 0!==l[2]?(W.test(l[2])&&(r=RegExp("</"+l[2],"g")),s=j):void 0!==l[3]&&(s=j):s===j?">"===l[0]?(s=r??R,c=-1):void 0===l[1]?c=-2:(c=s.lastIndex-l[2].length,o=l[1],s=void 0===l[3]?j:'"'===l[3]?D:N):s===D||s===N?s=j:s===U||s===O?s=R:(s=j,r=void 0);const h=s===j&&e[t+1].startsWith("/>")?" ":"";n+=s===R?a+z:c>=0?(i.push(o),a.slice(0,c)+S+a.slice(c)+C+h):a+C+(-2===c?t:h)}return[Z(e,n+(e[a]||"<?>")+(2===t?"</svg>":3===t?"</math>":"")),i]};class G{constructor({strings:e,_$litType$:t},a){let i;this.parts=[];let r=0,n=0;const s=e.length-1,o=this.parts,[l,c]=J(e,t);if(this.el=G.createElement(l,a),q.currentNode=this.el.content,2===t||3===t){const e=this.el.content.firstChild;e.replaceWith(...e.childNodes)}for(;null!==(i=q.nextNode())&&o.length<s;){if(1===i.nodeType){if(i.hasAttributes())for(const e of i.getAttributeNames())if(e.endsWith(S)){const t=c[n++],a=i.getAttribute(e).split(C),s=/([.?@])?(.*)/.exec(t);o.push({type:1,index:r,name:s[2],strings:a,ctor:"."===s[1]?te:"?"===s[1]?ae:"@"===s[1]?ie:ee}),i.removeAttribute(e)}else e.startsWith(C)&&(o.push({type:6,index:r}),i.removeAttribute(e));if(W.test(i.tagName)){const e=i.textContent.split(C),t=e.length-1;if(t>0){i.textContent=A?A.emptyScript:"";for(let a=0;a<t;a++)i.append(e[a],T()),q.nextNode(),o.push({type:2,index:++r});i.append(e[t],T())}}}else if(8===i.nodeType)if(i.data===M)o.push({type:2,index:r});else{let e=-1;for(;-1!==(e=i.data.indexOf(C,e+1));)o.push({type:7,index:r}),e+=C.length-1}r++}}static createElement(e,t){const a=V.createElement("template");return a.innerHTML=e,a}}function X(e,t,a=e,i){if(t===B)return t;let r=void 0!==i?a._$Co?.[i]:a._$Cl;const n=H(t)?void 0:t._$litDirective$;return r?.constructor!==n&&(r?._$AO?.(!1),void 0===n?r=void 0:(r=new n(e),r._$AT(e,a,i)),void 0!==i?(a._$Co??=[])[i]=r:a._$Cl=r),void 0!==r&&(t=X(e,r._$AS(e,t.values),r,i)),t}class Q{constructor(e,t){this._$AV=[],this._$AN=void 0,this._$AD=e,this._$AM=t}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(e){const{el:{content:t},parts:a}=this._$AD,i=(e?.creationScope??V).importNode(t,!0);q.currentNode=i;let r=q.nextNode(),n=0,s=0,o=a[0];for(;void 0!==o;){if(n===o.index){let t;2===o.type?t=new Y(r,r.nextSibling,this,e):1===o.type?t=new o.ctor(r,o.name,o.strings,this,e):6===o.type&&(t=new re(r,this,e)),this._$AV.push(t),o=a[++s]}n!==o?.index&&(r=q.nextNode(),n++)}return q.currentNode=V,i}p(e){let t=0;for(const a of this._$AV)void 0!==a&&(void 0!==a.strings?(a._$AI(e,a,t),t+=a.strings.length-2):a._$AI(e[t])),t++}}class Y{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(e,t,a,i){this.type=2,this._$AH=I,this._$AN=void 0,this._$AA=e,this._$AB=t,this._$AM=a,this.options=i,this._$Cv=i?.isConnected??!0}get parentNode(){let e=this._$AA.parentNode;const t=this._$AM;return void 0!==t&&11===e?.nodeType&&(e=t.parentNode),e}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(e,t=this){e=X(this,e,t),H(e)?e===I||null==e||""===e?(this._$AH!==I&&this._$AR(),this._$AH=I):e!==this._$AH&&e!==B&&this._(e):void 0!==e._$litType$?this.$(e):void 0!==e.nodeType?this.T(e):(e=>P(e)||"function"==typeof e?.[Symbol.iterator])(e)?this.k(e):this._(e)}O(e){return this._$AA.parentNode.insertBefore(e,this._$AB)}T(e){this._$AH!==e&&(this._$AR(),this._$AH=this.O(e))}_(e){this._$AH!==I&&H(this._$AH)?this._$AA.nextSibling.data=e:this.T(V.createTextNode(e)),this._$AH=e}$(e){const{values:t,_$litType$:a}=e,i="number"==typeof a?this._$AC(e):(void 0===a.el&&(a.el=G.createElement(Z(a.h,a.h[0]),this.options)),a);if(this._$AH?._$AD===i)this._$AH.p(t);else{const e=new Q(i,this),a=e.u(this.options);e.p(t),this.T(a),this._$AH=e}}_$AC(e){let t=F.get(e.strings);return void 0===t&&F.set(e.strings,t=new G(e)),t}k(e){P(this._$AH)||(this._$AH=[],this._$AR());const t=this._$AH;let a,i=0;for(const r of e)i===t.length?t.push(a=new Y(this.O(T()),this.O(T()),this,this.options)):a=t[i],a._$AI(r),i++;i<t.length&&(this._$AR(a&&a._$AB.nextSibling,i),t.length=i)}_$AR(e=this._$AA.nextSibling,t){for(this._$AP?.(!1,!0,t);e!==this._$AB;){const t=x(e).nextSibling;x(e).remove(),e=t}}setConnected(e){void 0===this._$AM&&(this._$Cv=e,this._$AP?.(e))}}class ee{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(e,t,a,i,r){this.type=1,this._$AH=I,this._$AN=void 0,this.element=e,this.name=t,this._$AM=i,this.options=r,a.length>2||""!==a[0]||""!==a[1]?(this._$AH=Array(a.length-1).fill(new String),this.strings=a):this._$AH=I}_$AI(e,t=this,a,i){const r=this.strings;let n=!1;if(void 0===r)e=X(this,e,t,0),n=!H(e)||e!==this._$AH&&e!==B,n&&(this._$AH=e);else{const i=e;let s,o;for(e=r[0],s=0;s<r.length-1;s++)o=X(this,i[a+s],t,s),o===B&&(o=this._$AH[s]),n||=!H(o)||o!==this._$AH[s],o===I?e=I:e!==I&&(e+=(o??"")+r[s+1]),this._$AH[s]=o}n&&!i&&this.j(e)}j(e){e===I?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,e??"")}}class te extends ee{constructor(){super(...arguments),this.type=3}j(e){this.element[this.name]=e===I?void 0:e}}class ae extends ee{constructor(){super(...arguments),this.type=4}j(e){this.element.toggleAttribute(this.name,!!e&&e!==I)}}class ie extends ee{constructor(e,t,a,i,r){super(e,t,a,i,r),this.type=5}_$AI(e,t=this){if((e=X(this,e,t,0)??I)===B)return;const a=this._$AH,i=e===I&&a!==I||e.capture!==a.capture||e.once!==a.once||e.passive!==a.passive,r=e!==I&&(a===I||i);i&&this.element.removeEventListener(this.name,this,a),r&&this.element.addEventListener(this.name,this,e),this._$AH=e}handleEvent(e){"function"==typeof this._$AH?this._$AH.call(this.options?.host??this.element,e):this._$AH.handleEvent(e)}}class re{constructor(e,t,a){this.element=e,this.type=6,this._$AN=void 0,this._$AM=t,this.options=a}get _$AU(){return this._$AM._$AU}_$AI(e){X(this,e)}}const ne=k.litHtmlPolyfillSupport;ne?.(G,Y),(k.litHtmlVersions??=[]).push("3.3.3");const se=globalThis;let oe=class extends ${constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){const e=super.createRenderRoot();return this.renderOptions.renderBefore??=e.firstChild,e}update(e){const t=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(e),this._$Do=((e,t,a)=>{const i=a?.renderBefore??t;let r=i._$litPart$;if(void 0===r){const e=a?.renderBefore??null;i._$litPart$=r=new Y(t.insertBefore(T(),e),e,void 0,a??{})}return r._$AI(e),r})(t,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return B}};oe._$litElement$=!0,oe.finalized=!0,se.litElementHydrateSupport?.({LitElement:oe});const le=se.litElementPolyfillSupport;le?.({LitElement:oe}),(se.litElementVersions??=[]).push("4.2.2");const ce=e=>(t,a)=>{void 0!==a?a.addInitializer(()=>{customElements.define(e,t)}):customElements.define(e,t)},de={attribute:!0,type:String,converter:b,reflect:!1,hasChanged:y},he=(e=de,t,a)=>{const{kind:i,metadata:r}=a;let n=globalThis.litPropertyMetadata.get(r);if(void 0===n&&globalThis.litPropertyMetadata.set(r,n=new Map),"setter"===i&&((e=Object.create(e)).wrapped=!0),n.set(a.name,e),"accessor"===i){const{name:i}=a;return{set(a){const r=t.get.call(this);t.set.call(this,a),this.requestUpdate(i,r,e,!0,a)},init(t){return void 0!==t&&this.C(i,void 0,e,t),t}}}if("setter"===i){const{name:i}=a;return function(a){const r=this[i];t.call(this,a),this.requestUpdate(i,r,e,!0,a)}}throw Error("Unsupported decorator location: "+i)};function pe(e){return(t,a)=>"object"==typeof a?he(e,t,a):((e,t,a)=>{const i=t.hasOwnProperty(a);return t.constructor.createProperty(a,e),i?Object.getOwnPropertyDescriptor(t,a):void 0})(e,t,a)}function ge(e){return pe({...e,state:!0,attribute:!1})}const ue=1,ve=3,fe=4;class me{constructor(e){}get _$AU(){return this._$AM._$AU}_$AT(e,t,a){this._$Ct=e,this._$AM=t,this._$Ci=a}_$AS(e,t){return this.update(e,t)}update(e,t){return this.render(...t)}}const _e={},be=(e=>(...t)=>({_$litDirective$:e,values:t}))(class extends me{constructor(e){if(super(e),e.type!==ve&&e.type!==ue&&e.type!==fe)throw Error("The `live` directive is not allowed on child or event bindings");if(!(e=>void 0===e.strings)(e))throw Error("`live` bindings can only contain a single expression")}render(e){return e}update(e,[t]){if(t===B||t===I)return t;const a=e.element,i=e.name;if(e.type===ve){if(t===a[i])return B}else if(e.type===fe){if(!!t===a.hasAttribute(i))return B}else if(e.type===ue&&a.getAttribute(i)===t+"")return B;return((e,t=_e)=>{e._$AH=t})(e),t}});function ye(e){return"object"==typeof e&&null!==e&&"code"in e&&"message"in e}let we=class extends oe{constructor(){super(...arguments),this.open=!1,this.heading="",this.text="",this.confirmText="",this.cancelText="",this.confirmed=!1}render(){return K`
      <ha-dialog .open=${this.open} .headerTitle=${this.heading} width="small" @closed=${this.closed}>
        <p>${this.text}</p>
        <div slot="footer">
          <ha-button appearance="plain" @click=${this.cancel}>${this.cancelText}</ha-button>
          <ha-button variant="danger" @click=${this.confirm}>${this.confirmText}</ha-button>
        </div>
      </ha-dialog>
    `}confirm(){this.confirmed=!0,this.open=!1}cancel(){this.open=!1}closed(){const e=this.confirmed?"confirm":"cancel";this.confirmed=!1,this.open=!1,this.dispatchEvent(new CustomEvent(e))}};e([pe({type:Boolean})],we.prototype,"open",void 0),e([pe()],we.prototype,"heading",void 0),e([pe()],we.prototype,"text",void 0),e([pe()],we.prototype,"confirmText",void 0),e([pe()],we.prototype,"cancelText",void 0),we=e([ce("kraftvakt-confirm-dialog")],we);let $e=class extends oe{constructor(){super(...arguments),this.errorCount=0,this.saving=!1}render(){const e=this.errorCount>0?this.localize("config.fix_before_saving",{count:this.errorCount}):this.message;return K`
      <div class="bar" role="region" aria-label=${this.localize("config.unsaved")}>
        <div class="text">
          <div class="title">${this.localize("config.unsaved")}</div>
          ${e?K`<div class="error">${e}</div>`:I}
        </div>
        <ha-button appearance="plain" .disabled=${this.saving} @click=${()=>this.fire("discard")}>
          ${this.localize("config.discard")}
        </ha-button>
        <ha-button .disabled=${this.saving||this.errorCount>0} @click=${()=>this.fire("save")}>
          <ha-svg-icon slot="start" .path=${"M15,9H5V5H15M12,19A3,3 0 0,1 9,16A3,3 0 0,1 12,13A3,3 0 0,1 15,16A3,3 0 0,1 12,19M17,3H5C3.89,3 3,3.9 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V7L17,3Z"}></ha-svg-icon>
          ${this.localize("config.save")}
        </ha-button>
      </div>
    `}fire(e){this.dispatchEvent(new CustomEvent(e))}static{this.styles=s`
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
  `}};e([pe({attribute:!1})],$e.prototype,"localize",void 0),e([pe({type:Number})],$e.prototype,"errorCount",void 0),e([pe({type:Boolean})],$e.prototype,"saving",void 0),e([pe()],$e.prototype,"message",void 0),$e=e([ce("kraftvakt-save-bar")],$e);function ke(e){return"ev_charging"===e.type?"ev_charging":`${e.appliance_id}/${e.variant_id??""}`}function xe(e){const t=function(e){const t=e.appliances.flatMap(e=>[{type:"appliance",appliance_id:e.id,variant_id:null},...e.variants.map(t=>({type:"appliance",appliance_id:e.id,variant_id:t.id}))]);e.charging.enabled&&t.push({type:"ev_charging"});return t}(e),a=new Set(t.map(ke)),i=new Set,r=e.priority.filter(e=>{const t=ke(e);return!(!a.has(t)||i.has(t))&&(i.add(t),!0)}),n=t.filter(e=>!i.has(ke(e)));return{...e,priority:[...r,...n]}}const Ae={en:{panel:{title:"Kraftvakt",not_loaded:"Kraftvakt is not loaded. Check the integration under Settings → Devices & services.",error:"Something went wrong: {message}"},tabs:{status:"Status",general:"General",appliances:"Appliances",charging:"EV charging"},placeholder:{not_ready:"This page is not ready yet. It comes in a later version of Kraftvakt."},status:{regulation:"Regulation",running:"Running",stopped:"Stopped",start:"Start regulation",stop:"Stop regulation",stopped_info:"The regulation is stopped, and all regulated appliances and EV chargers are turned off. The configuration can be changed. When the regulation starts, the appliances are turned on again one by one.",incomplete_title:"The configuration is not complete",start_refused:"The regulation cannot start before the configuration is complete.",safe_state_title:"Safe state",safe_state_text:"The power sensor {sensor} gives no valid measurement. All regulated appliances and EV chargers are turned off. The regulation starts again by itself when the sensor gives a valid value again.",penalty_title:"Penalty period",penalty_text:"The average consumption has been above the power limit. All regulated appliances and EV chargers are kept off until the overconsumption is recovered.",overconsumption_left:"Overconsumption left: {energy} kWh",recovery_started:"recovery has started",recovery_not_started:"recovery has not started",regulation_average:"Regulation average",capacity_average:"Average consumption last hour",power_limit:"Power limit",scale_limit:"Limit {power} kW",safe_state_chip:"Safe state: {value}",penalty_chip:"Penalty period: {value}",yes:"yes",no:"no",next_decision:"Next decision in {time}",appliances:"Appliances",appliances_order:"in order of priority",no_appliances:"No appliances are configured.",chargers:"EV chargers",chargers_order:"current charging priority",on:"On",off:"Off",activated:"Activated",deactivated:"Deactivated",waiting_to_turn_on:"Waiting, turns on in about {time}",waiting_to_activate:"Waiting, is activated in about {time}",waiting_to_increase:"Waiting, the current is increased in about {time}",charging_current:"{current} A of {min}–{max} A",bypassed:"Bypassed: draws no power",waiting_charger:"Waiting: another EV charger is charging",excluded:"Excluded from the regulation",outside_window:"Outside the charging window ({start}–{end})"},missing:{missing_power_sensor:"The power sensor is not chosen.",missing_entity:"{item}: the entity is not chosen.",missing_action:"{item}: the action to {action} is missing.",missing_charge_power_sensor:"{item}: the sensor for charging power is missing.",unknown:"{item}: {code}",appliance_without_entity:"An appliance without an entity",charger_without_entity:"An EV charger without an entity",actions:{turn_on:"turn it on",turn_off:"turn it off",activate:"activate it",deactivate:"deactivate it",set_current:"set the charging current"}},config:{save:"Save",discard:"Discard",unsaved:"Unsaved changes",fix_before_saving:"Fix {count} marked settings before saving.",not_saved:"The configuration was not saved. Fix the marked settings.",save_refused_running:"The configuration cannot be saved while the regulation runs.",leave_title:"Discard unsaved changes?",leave_text:"The changes on the configuration pages are not saved. They are lost if you leave.",stay:"Keep editing",leave:"Discard changes"},locked:{title:"The configuration is locked",text:"The regulation runs. Stop the regulation to change the configuration. When the regulation stops, all regulated appliances and EV chargers are turned off.",stop:"Stop regulation"},warning:{appliances_title:"Do not turn regulated appliances on or off outside Kraftvakt",chargers_title:"Do not turn EV chargers on or off outside Kraftvakt",text:"Manual control and automations can disturb the regulation, affect appliances with higher priority and trigger a penalty."},errors:{required:"Required.",out_of_range:"Must be between {min} and {max}.",at_least:"Must be at least {min}.",invalid_resolution:"Must be in steps of {step}.",not_integer:"Must be a whole number.",invalid_entity_id:"Not a valid entity ID.",empty_label:"The label cannot be empty.",duplicate_label:"The label must be unique for the appliance.",min_current_above_max:"The minimum current cannot be above the maximum current.",invalid_time:"Give both start and end.",window_start_equals_end:"Start and end cannot be the same.",duplicate_entity:"The entity is already used by another appliance or EV charger.",invalid_action:"Home Assistant cannot read the action.",invalid_template:"The template has a syntax error.",default_action_unavailable:"The entity has no standard action. Choose a custom action.",unknown:"Invalid value ({code})."},dialog:{ok:"OK",cancel:"Cancel",close:"Close"},general:{measurement:"Measurement",regulation:"Regulation",penalty:"Penalty",capacity_window_info:"The capacity window is fixed at one hour and cannot be changed.",interval_option:"{count} × the regulation window",fields:{power_sensor:{label:"Power sensor",helper:"The sensor that measures the total power of the house, in W or kW."},regulation_window_s:{label:"Regulation window",helper:"The period the regulation average is calculated over. {min}–{max} s, default {default} s."},power_limit_kw:{label:"Power limit",helper:"The highest allowed average consumption per hour. {min}–{max} kW, default {default} kW."},regulation_interval:{label:"Regulation interval",helper:"A decision every {seconds} seconds. Default {default} ×."},wait_at_limit_min:{label:"Waiting time at the power limit",helper:"How long an appliance waits before it is turned on when the regulation average is at the power limit. Shorter when the average is lower. {min}–{max} min, default {default} min."},penalty_threshold_kw:{label:"Penalty threshold",helper:"How much the average consumption may exceed the power limit before a penalty starts. {min}–{max} kW, default {default} kW."}}},list:{drag:"Drag to change the order",edit:"Edit",view:"Show"},appliances:{priority_title:"Priority list",priority_sub:"Top = highest priority, turned off last",add:"Add appliance",empty:"No appliances yet. Add the appliances Kraftvakt may turn off when the consumption is too high.",ev_charging:"EV charging",ev_charging_sub:"{count} EV chargers · configured under",power_reserve:"power reserve {power} kW",variant_count:"{count} variants",variant_entity:"Variant · entity {entity}",variant_template:"Variant · template"},appliance:{add_title:"Add appliance",edit_title:"Edit appliance",view_title:"Appliance",actions:"Actions",variants:"Variants",variants_info:"A variant gives the appliance another place in the priority list while its expression is true. The top true expression applies. A new variant is put at the bottom of the priority list.",add_variant:"Add variant",remove_variant:"Remove variant",variant:"Variant {label}",delete:"Delete appliance",fields:{entity_id:{label:"Entity",helper:"The name in Home Assistant becomes the name of the appliance. The entity is available as entity_id and entity (the state object) in templates and actions."},turn_on:{label:"Turn on"},turn_off:{label:"Turn off"},power_reserve_kw:{label:"Power reserve (optional)",helper:"Free power that must be available before the appliance is turned on. Use it for appliances that draw a lot as soon as they are turned on."},label:{label:"Label"},condition:{label:"Expression"}}},action:{default:"Standard",custom:"Custom",default_runs:"Runs {service} for the entity.",no_default:"The entity type has no standard action, so the action must be custom.",choose_entity:"Choose the entity to use the standard action.",variables:"Variables: {variables}."},condition:{none:"Not set",entity:"Entity",template:"Template",entity_label:"Boolean entity",template_label:"Template",entity_helper:"True only when the entity is on. Unavailable counts as false.",template_helper:"True only when the template gives the boolean value true. Variables: entity_id, entity.",now:"Now: {value}",true:"true",false:"false",error:"Error: {message}"},charging:{shared:"Shared settings",enabled:"EV charging control",enabled_sub:"When it is off, the EV chargers are left to themselves and «EV charging» is removed from the priority list.",one_at_a_time:"One EV charger at a time",one_at_a_time_sub:"An EV charger that charges may continue until the car is full or disconnected. The others wait.",disabled_info:"EV charging control is off. The EV chargers below are kept, but Kraftvakt sends no commands to them.",chargers:"EV chargers",chargers_sub:"Charging priority, highest at the top",add:"Add EV charger",empty:"No EV chargers yet.",switches_info:"For each EV charger Kraftvakt makes two switches that can also be used while the regulation runs: «‹charger› excluded from regulation» and «‹charger› override charging window».",currents:"{min}–{max} A",reserve:"reserve {power} kW",window:"charging window {start}–{end}",always_allowed:"always allowed to charge",car_from:"car connected from {source}",car_template:"car connected from a template"},charger:{add_title:"Add EV charger",edit_title:"Edit EV charger",view_title:"EV charger",allowed_charging:"Allowed charging",charging_current:"Charging current",measurement:"Measurement",minimum_first:"The charging current is always set to the minimum before the EV charger is activated or deactivated.",delete:"Delete EV charger",fields:{entity_id:{label:"Entity for allowed charging",helper:"Normally the charger's switch for allowing charging. The name in Home Assistant becomes the name of the EV charger. The entity is available as entity_id and entity in templates and actions."},activate:{label:"Activate"},deactivate:{label:"Deactivate"},min_current_a:{label:"Minimum charging current"},max_current_a:{label:"Maximum charging current",helper:"Whole amperes. The minimum cannot be above the maximum."},set_current:{label:"Set charging current"},charge_power_sensor:{label:"Sensor for charging power",helper:"Above 100 W counts as charging. Unavailable counts as charging."},power_reserve_kw:{label:"Power reserve",helper:"The power the EV charger draws when charging starts at the minimum current. {min}–{max} kW, default {default} kW (about 6 A on three phases, 400 V)."},car_connected:{label:"Car connected (optional)",helper:"The car counts as connected only when the value is true. Unavailable counts as not connected."},charging_window:{label:"Charging window (optional)",helper:"Can span midnight. Start and end cannot be the same. Without a charging window, the EV charger is always allowed to charge."},start:{label:"Start"},end:{label:"End"}}}},nb:{panel:{title:"Kraftvakt",not_loaded:"Kraftvakt er ikke lastet. Sjekk integrasjonen under Innstillinger → Enheter og tjenester.",error:"Noe gikk galt: {message}"},tabs:{status:"Status",general:"Generelt",appliances:"Apparater",charging:"Billading"},placeholder:{not_ready:"Denne siden er ikke klar ennå. Den kommer i en senere versjon av Kraftvakt."},status:{regulation:"Regulering",running:"Kjører",stopped:"Stoppet",start:"Start regulering",stop:"Stopp regulering",stopped_info:"Reguleringen er stoppet, og alle regulerte apparater og elbilladere er slått av. Konfigurasjonen kan endres. Når reguleringen startes, slås apparatene på igjen ett og ett.",incomplete_title:"Konfigurasjonen er ikke fullstendig",start_refused:"Reguleringen kan ikke startes før konfigurasjonen er fullstendig.",safe_state_title:"Sikker tilstand",safe_state_text:"Effektsensoren {sensor} gir ingen gyldig måling. Alle regulerte apparater og elbilladere er slått av. Reguleringen starter på nytt av seg selv når sensoren gir en gyldig verdi igjen.",penalty_title:"Straffeperiode pågår",penalty_text:"Snittforbruket har vært over effektgrensen. Alle regulerte apparater og elbilladere holdes av til overforbruket er hentet inn.",overconsumption_left:"Overforbruk igjen: {energy} kWh",recovery_started:"innhenting har startet",recovery_not_started:"innhenting har ikke startet",regulation_average:"Reguleringssnitt",capacity_average:"Snittforbruk siste time",power_limit:"Effektgrense",scale_limit:"Grense {power} kW",safe_state_chip:"Sikker tilstand: {value}",penalty_chip:"Straffeperiode: {value}",yes:"ja",no:"nei",next_decision:"Neste avgjørelse om {time}",appliances:"Apparater",appliances_order:"i prioritert rekkefølge",no_appliances:"Ingen apparater er konfigurert.",chargers:"Elbilladere",chargers_order:"gjeldende ladeprioritering",on:"På",off:"Av",activated:"Aktivert",deactivated:"Deaktivert",waiting_to_turn_on:"Venter, slås på om ca. {time}",waiting_to_activate:"Venter, aktiveres om ca. {time}",waiting_to_increase:"Venter, ladestrømmen økes om ca. {time}",charging_current:"{current} A av {min}–{max} A",bypassed:"Forbigått: trekker ikke strøm",waiting_charger:"Ventende: en annen elbillader lader",excluded:"Utenfor regulering",outside_window:"Utenfor ladetidsrom ({start}–{end})"},missing:{missing_power_sensor:"Effektsensor er ikke valgt.",missing_entity:"{item}: entitet er ikke valgt.",missing_action:"{item}: handling for å {action} mangler.",missing_charge_power_sensor:"{item}: sensor for ladeeffekt mangler.",unknown:"{item}: {code}",appliance_without_entity:"Et apparat uten entitet",charger_without_entity:"En elbillader uten entitet",actions:{turn_on:"slå på",turn_off:"slå av",activate:"aktivere",deactivate:"deaktivere",set_current:"sette ladestrøm"}},config:{save:"Lagre",discard:"Forkast",unsaved:"Ulagrede endringer",fix_before_saving:"Rett {count} merkede innstillinger før du lagrer.",not_saved:"Konfigurasjonen ble ikke lagret. Rett de merkede innstillingene.",save_refused_running:"Konfigurasjonen kan ikke lagres mens reguleringen kjører.",leave_title:"Forkaste ulagrede endringer?",leave_text:"Endringene på konfigurasjonssidene er ikke lagret. De går tapt hvis du går videre.",stay:"Fortsett å redigere",leave:"Forkast endringer"},locked:{title:"Konfigurasjonen er låst",text:"Reguleringen kjører. Stopp reguleringen for å endre konfigurasjonen. Når reguleringen stoppes, slås alle regulerte apparater og elbilladere av.",stop:"Stopp regulering"},warning:{appliances_title:"Ikke slå regulerte apparater av eller på utenom Kraftvakt",chargers_title:"Ikke slå elbilladere av eller på utenom Kraftvakt",text:"Manuell styring og automasjoner kan forstyrre reguleringen, gå ut over apparater med høyere prioritet og utløse straff."},errors:{required:"Påkrevd.",out_of_range:"Må være mellom {min} og {max}.",at_least:"Må være minst {min}.",invalid_resolution:"Må være i steg på {step}.",not_integer:"Må være et helt tall.",invalid_entity_id:"Ikke en gyldig entitets-ID.",empty_label:"Merkelappen kan ikke være tom.",duplicate_label:"Merkelappen må være unik for apparatet.",min_current_above_max:"Minste ladestrøm kan ikke være større enn største.",invalid_time:"Angi både start og slutt.",window_start_equals_end:"Start og slutt kan ikke være like.",duplicate_entity:"Entiteten brukes allerede av et annet apparat eller en elbillader.",invalid_action:"Home Assistant kan ikke lese handlingen.",invalid_template:"Malen har en syntaksfeil.",default_action_unavailable:"Entiteten har ingen standardhandling. Velg egendefinert handling.",unknown:"Ugyldig verdi ({code})."},dialog:{ok:"OK",cancel:"Avbryt",close:"Lukk"},general:{measurement:"Måling",regulation:"Regulering",penalty:"Straff",capacity_window_info:"Kapasitetsvinduet er fast én time og kan ikke endres.",interval_option:"{count} × reguleringsvinduet",fields:{power_sensor:{label:"Effektsensor",helper:"Sensoren som måler husets totale momentane effekt, i W eller kW."},regulation_window_s:{label:"Reguleringsvindu",helper:"Tidsrommet reguleringssnittet beregnes over. {min}–{max} s, standard {default} s."},power_limit_kw:{label:"Effektgrense",helper:"Høyeste tillatte snittforbruk per time. {min}–{max} kW, standard {default} kW."},regulation_interval:{label:"Reguleringsintervall",helper:"Avgjørelse hvert {seconds}. sekund. Standard {default} ×."},wait_at_limit_min:{label:"Ventetid ved effektgrensen",helper:"Hvor lenge et apparat venter før det slås på når reguleringssnittet er ved effektgrensen. Kortere når snittet er lavere. {min}–{max} min, standard {default} min."},penalty_threshold_kw:{label:"Straffeterskel",helper:"Hvor mye snittforbruket kan overstige effektgrensen før straff starter. {min}–{max} kW, standard {default} kW."}}},list:{drag:"Dra for å endre rekkefølgen",edit:"Rediger",view:"Vis"},appliances:{priority_title:"Prioritetsliste",priority_sub:"Øverst = høyest prioritet, slås av sist",add:"Legg til apparat",empty:"Ingen apparater ennå. Legg til apparatene Kraftvakt kan slå av når forbruket blir for høyt.",ev_charging:"Elbillading",ev_charging_sub:"{count} elbilladere · konfigureres under",power_reserve:"effektreserve {power} kW",variant_count:"{count} varianter",variant_entity:"Variant · entitet {entity}",variant_template:"Variant · mal"},appliance:{add_title:"Legg til apparat",edit_title:"Rediger apparat",view_title:"Apparat",actions:"Handlinger",variants:"Varianter",variants_info:"En variant gir apparatet en annen plass i prioritetslisten mens uttrykket er sant. Det øverste sanne uttrykket gjelder. En ny variant legges nederst i prioritetslisten.",add_variant:"Legg til variant",remove_variant:"Fjern variant",variant:"Variant {label}",delete:"Slett apparat",fields:{entity_id:{label:"Entitet",helper:"Navnet i Home Assistant blir apparatets navn. Entiteten er tilgjengelig som entity_id og entity (tilstandsobjektet) i maler og handlinger."},turn_on:{label:"Slå på"},turn_off:{label:"Slå av"},power_reserve_kw:{label:"Effektreserve (valgfri)",helper:"Ledig effekt som må finnes før apparatet slås på. Bruk den for apparater som trekker mye straks de slås på."},label:{label:"Merkelapp"},condition:{label:"Uttrykk"}}},action:{default:"Standard",custom:"Egendefinert",default_runs:"Kjører {service} for entiteten.",no_default:"Entitetstypen har ingen standardhandling, så handlingen må være egendefinert.",choose_entity:"Velg entitet for å bruke standardhandlingen.",variables:"Variabler: {variables}."},condition:{none:"Ikke angitt",entity:"Entitet",template:"Mal",entity_label:"Boolsk entitet",template_label:"Mal",entity_helper:"Sann bare når entiteten er på. Utilgjengelig regnes som usann.",template_helper:"Sann bare når malen gir den boolske verdien sann. Variabler: entity_id, entity.",now:"Nå: {value}",true:"sann",false:"usann",error:"Feil: {message}"},charging:{shared:"Felles innstillinger",enabled:"Billadestyring",enabled_sub:"Når den er av, overlates elbilladerne til seg selv og «Elbillading» fjernes fra prioritetslisten.",one_at_a_time:"Én elbillader om gangen",one_at_a_time_sub:"En elbillader som lader, får fortsette til bilen er fulladet eller koblet fra. Andre venter.",disabled_info:"Billadestyring er av. Elbilladerne nedenfor beholdes, men Kraftvakt sender ingen kommandoer til dem.",chargers:"Elbilladere",chargers_sub:"Ladeprioritering, høyest øverst",add:"Legg til elbillader",empty:"Ingen elbilladere ennå.",switches_info:"For hver elbillader lager Kraftvakt to brytere som kan brukes også mens reguleringen kjører: «‹lader› utenfor regulering» og «‹lader› overstyr ladetidsrom».",currents:"{min}–{max} A",reserve:"reserve {power} kW",window:"ladetidsrom {start}–{end}",always_allowed:"alltid lov til å lade",car_from:"bil tilkoblet fra {source}",car_template:"bil tilkoblet fra mal"},charger:{add_title:"Legg til elbillader",edit_title:"Rediger elbillader",view_title:"Elbillader",allowed_charging:"Tillatt lading",charging_current:"Ladestrøm",measurement:"Måling",minimum_first:"Ladestrømmen settes alltid til minste ladestrøm før elbilladeren aktiveres eller deaktiveres.",delete:"Slett elbillader",fields:{entity_id:{label:"Entitet for tillatt lading",helper:"Normalt laderens bryter for å tillate lading. Navnet i Home Assistant blir elbilladerens navn. Entiteten er tilgjengelig som entity_id og entity i maler og handlinger."},activate:{label:"Aktiver"},deactivate:{label:"Deaktiver"},min_current_a:{label:"Minste ladestrøm"},max_current_a:{label:"Største ladestrøm",helper:"Hele ampere. Minste kan ikke være større enn største."},set_current:{label:"Sett ladestrøm"},charge_power_sensor:{label:"Sensor for ladeeffekt",helper:"Over 100 W regnes som lading. Utilgjengelig regnes som lading."},power_reserve_kw:{label:"Effektreserve",helper:"Effekten elbilladeren trekker når lading starter på minste ladestrøm. {min}–{max} kW, standard {default} kW (ca. 6 A på tre faser, 400 V)."},car_connected:{label:"Bil tilkoblet (valgfri)",helper:"Bilen regnes som tilkoblet bare når verdien er sann. Utilgjengelig regnes som ikke tilkoblet."},charging_window:{label:"Ladetidsrom (valgfritt)",helper:"Kan gå over midnatt. Start og slutt kan ikke være like. Uten ladetidsrom har elbilladeren alltid lov til å lade."},start:{label:"Start"},end:{label:"Slutt"}}}}};function Ee(e){const t=Ae[e]??Ae[e.split("-")[0]]??Ae.en;return(e,a={})=>(Se(t,e)??Se(Ae.en,e)??e).replace(/\{(\w+)\}/g,(e,t)=>t in a?String(a[t]):e)}function Se(e,t){let a=e;for(const e of t.split("."))a=a?.[e];return"string"==typeof a?a:void 0}const Ce=["status","general","appliances","charging"],Me="/kraftvakt";function ze(e,t={}){const a=`${Me}/${e}`;t.replace?history.replaceState(null,"",a):history.pushState(null,"",a),window.dispatchEvent(new CustomEvent("location-changed",{detail:{replace:t.replace??!1}}))}let Ve=class extends oe{render(){return K`<ha-card><div class="content">${this.localize("placeholder.not_ready")}</div></ha-card>`}static{this.styles=s`
    .content {
      padding: 16px;
    }
  `}};e([pe({attribute:!1})],Ve.prototype,"localize",void 0),Ve=e([ce("kraftvakt-placeholder-page")],Ve);class Te{constructor(e){this.host=e,this.now=Date.now(),e.addController(this)}hostConnected(){this.timer=window.setInterval(()=>{this.now=Date.now(),this.host.requestUpdate()},1e3)}hostDisconnected(){window.clearInterval(this.timer)}}function He(e,t,a){return new Intl.NumberFormat(e,{minimumFractionDigits:a,maximumFractionDigits:a}).format(t)}function Pe(e,t){return null===t?"–":He(e,t,2)}function Le(e,t){const a=Math.max(0,Math.ceil((Date.parse(e)-t)/1e3)),i=Math.floor(a/3600),r=Math.floor(a%3600/60),n=String(a%60).padStart(2,"0");return i>0?`${i}:${String(r).padStart(2,"0")}:${n}`:`${r}:${n}`}const Re={missing_power_sensor:"missing.missing_power_sensor",missing_entity:"missing.missing_entity",missing_action:"missing.missing_action",missing_charge_power_sensor:"missing.missing_charge_power_sensor"},Ue={turn_on:"missing.actions.turn_on",turn_off:"missing.actions.turn_off",activate:"missing.actions.activate",deactivate:"missing.actions.deactivate",set_current:"missing.actions.set_current"},Oe={general:"general",appliances:"appliances",priority:"appliances",charging:"charging",chargers:"charging"};function je(e,t,a){const i="chargers"===e.section?t?.config.charging.chargers:t?.config.appliances,r=i?.find(t=>t.id===e.target)?.entity_id;return r?t?.entity_names[r]??r:a("chargers"===e.section?"missing.charger_without_entity":"missing.appliance_without_entity")}let Ne=class extends oe{constructor(){super(...arguments),this.narrow=!1,this.changingRunning=!1,this.clock=new Te(this)}render(){if(!this.status)return I;const e=this.status;return K`
      <div class="cards">
        ${this.renderRegulationCard(e)} ${e.running?this.renderAppliancesCard(e.appliances):I}
        ${e.running&&e.chargers.length>0?this.renderChargersCard(e.chargers):I}
      </div>
    `}renderRegulationCard(e){return K`
      <ha-card class="regulation">
        <div class="card-header">
          <span>${this.localize("status.regulation")}</span>
          <span class="chip ${e.running?"running":"off"}">
            <span class="dot"></span>
            ${this.localize(e.running?"status.running":"status.stopped")}
          </span>
          <span class="spacer"></span>
          ${this.narrow?I:this.renderStartStop(e)}
        </div>
        <div class="card-content">
          ${this.runningError?K`<ha-alert alert-type="error">${this.runningError}</ha-alert>`:I}
          ${e.running?this.renderRunning(e):this.renderStopped(e)}
        </div>
        ${this.narrow?K`<div class="card-actions">${this.renderStartStop(e)}</div>`:I}
      </ha-card>
    `}renderStartStop(e){return e.running?K`
        <ha-button
          variant="danger"
          appearance="outlined"
          .disabled=${this.changingRunning}
          @click=${()=>this.changeRunning(!1)}
        >
          <ha-svg-icon slot="start" .path=${"M18,18H6V6H18V18Z"}></ha-svg-icon>
          ${this.localize("status.stop")}
        </ha-button>
      `:K`
      <ha-button
        .disabled=${this.changingRunning||e.missing.length>0}
        @click=${()=>this.changeRunning(!0)}
      >
        <ha-svg-icon slot="start" .path=${"M8,5.14V19.14L19,12.14L8,5.14Z"}></ha-svg-icon>
        ${this.localize("status.start")}
      </ha-button>
    `}renderRunning(e){const t=this.hass.language;return K`
      ${e.safe_state?this.renderSafeState():I} ${e.penalty.active?this.renderPenalty(e):I}
      <div class="stats">
        ${this.renderStat("regulation-average","status.regulation_average",Pe(t,e.regulation_average_kw))}
        ${this.renderStat("capacity-average","status.capacity_average",Pe(t,e.capacity_average_kw),(a=e.capacity_average_kw,null!==a&&a>e.power_limit_kw))}
        ${this.renderStat("","status.power_limit",Pe(t,e.power_limit_kw))}
      </div>
      ${this.renderMeter(e)}
      <div class="facts">
        <span class="chip ${e.safe_state?"alarm":"off"}">
          ${this.localize("status.safe_state_chip",{value:this.yesNo(e.safe_state)})}
        </span>
        <span class="chip ${e.penalty.active?"alarm":"off"}">
          ${this.localize("status.penalty_chip",{value:this.yesNo(e.penalty.active)})}
        </span>
        ${e.next_decision_at?K`<span>
              ${this.localize("status.next_decision",{time:Le(e.next_decision_at,this.clock.now)})}
            </span>`:I}
      </div>
    `;var a}renderSafeState(){const e=this.config?.config.general.power_sensor??"",t=this.hass.states[e]?.attributes.friendly_name??e;return K`
      <ha-alert alert-type="error" .title=${this.localize("status.safe_state_title")}>
        ${this.localize("status.safe_state_text",{sensor:t})}
      </ha-alert>
    `}renderPenalty(e){const t=He(this.hass.language,Math.max(0,e.penalty.overconsumption_kwh),2),a=e.penalty.recovery_started?"status.recovery_started":"status.recovery_not_started";return K`
      <ha-alert alert-type="warning" .title=${this.localize("status.penalty_title")}>
        ${this.localize("status.penalty_text")}
        <div class="penalty-details">${this.localize("status.overconsumption_left",{energy:t})} · ${this.localize(a)}</div>
      </ha-alert>
    `}renderStat(e,t,a,i=!1){return K`
      <div class="stat">
        <div class="stat-label">${e?K`<span class="swatch ${e}"></span>`:I}${this.localize(t)}</div>
        <div class="stat-value ${i?"alarm":""}">${a} <small>kW</small></div>
      </div>
    `}renderMeter(e){const t=e.regulation_average_kw,a=e.capacity_average_kw;if(null===t||null===a)return I;const i=Math.max(1.2*e.power_limit_kw,t,a),r=e=>100*e/i+"%",n=this.hass.language;return K`
      <div class="meter">
        <div class="limit-label">
          <span style="left: ${r(e.power_limit_kw)}">
            ${this.localize("status.scale_limit",{power:He(n,e.power_limit_kw,1)})}
          </span>
        </div>
        <div class="bar">
          <div class="fill regulation-average" style="width: ${r(t)}"></div>
          <div class="fill capacity-average" style="width: ${r(a)}"></div>
          <div class="limit" style="left: ${r(e.power_limit_kw)}"></div>
        </div>
        <div class="scale">
          <span>0 kW</span>
          <span>${He(n,i,1)} kW</span>
        </div>
      </div>
    `}renderAppliancesCard(e){return K`
      <ha-card>
        <div class="card-header">
          <span>${this.localize("status.appliances")}</span>
          <span class="sub">${this.localize("status.appliances_order")}</span>
        </div>
        ${0===e.length?K`<div class="card-content empty">${this.localize("status.no_appliances")}</div>`:K`<div class="list">
              ${e.map((e,t)=>K`
                  <div class="row">
                    <span class="rank">${t+1}</span>
                    <div class="row-main">
                      <div class="row-title">
                        ${e.name}
                        ${e.variant?K`<span class="variant">${e.variant}</span>`:I}
                      </div>
                      ${e.waiting_until?K`<div class="row-sub">
                            ${this.localize("status.waiting_to_turn_on",{time:Le(e.waiting_until,this.clock.now)})}
                          </div>`:I}
                    </div>
                    ${this.renderOnOff(e.on,"status.on","status.off")}
                  </div>
                `)}
            </div>`}
      </ha-card>
    `}renderChargersCard(e){return K`
      <ha-card>
        <div class="card-header">
          <span>${this.localize("status.chargers")}</span>
          <span class="sub">${this.localize("status.chargers_order")}</span>
        </div>
        <div class="list">
          ${e.map(e=>{const t=this.chargerDetails(e);return K`
              <div class="row">
                <ha-svg-icon class="rank" .path=${"M19.77,7.23L19.78,7.22L16.06,3.5L15,4.56L17.11,6.67C16.17,7.03 15.5,7.93 15.5,9A2.5,2.5 0 0,0 18,11.5C18.36,11.5 18.69,11.42 19,11.29V18.5A1,1 0 0,1 18,19.5A1,1 0 0,1 17,18.5V14A2,2 0 0,0 15,12H14V5A2,2 0 0,0 12,3H6A2,2 0 0,0 4,5V21H14V13.5H15.5V18.5A2.5,2.5 0 0,0 18,21A2.5,2.5 0 0,0 20.5,18.5V9C20.5,8.31 20.22,7.68 19.77,7.23M18,10A1,1 0 0,1 17,9A1,1 0 0,1 18,8A1,1 0 0,1 19,9A1,1 0 0,1 18,10M8,18V13.5H6L10,6V11H12L8,18Z"}></ha-svg-icon>
                <div class="row-main">
                  <div class="row-title">${e.name}</div>
                  ${t.length>0?K`<div class="row-sub">${t.join(" · ")}</div>`:I}
                </div>
                ${this.renderOnOff(e.activated,"status.activated","status.deactivated")}
              </div>
            `})}
        </div>
      </ha-card>
    `}chargerDetails(e){const t=this.config?.config.charging.chargers.find(t=>t.id===e.id),a=[];if(null!==e.current_a&&t&&a.push(this.localize("status.charging_current",{current:e.current_a,min:t.min_current_a,max:t.max_current_a})),e.bypassed&&a.push(this.localize("status.bypassed")),e.waiting&&a.push(this.localize("status.waiting_charger")),!e.allowed&&e.excluded?a.push(this.localize("status.excluded")):!e.allowed&&!1===e.excluded&&t?.charging_window&&a.push(this.localize("status.outside_window",{...t.charging_window})),e.waiting_until){const t=Le(e.waiting_until,this.clock.now);a.push(this.localize(e.activated?"status.waiting_to_increase":"status.waiting_to_activate",{time:t}))}return a}renderOnOff(e,t,a){return K`<span class="chip ${e?"on":"off"}"><span class="dot"></span>${this.localize(e?t:a)}</span>`}yesNo(e){return this.localize(e?"status.yes":"status.no")}renderStopped(e){return 0===e.missing.length?K`<ha-alert alert-type="info">${this.localize("status.stopped_info")}</ha-alert>`:K`
      <ha-alert alert-type="warning" .title=${this.localize("status.incomplete_title")}>
        <ul class="missing">
          ${e.missing.map(e=>{const t=function(e){return Oe[e.section]}(e);return K`
              <li>
                ${function(e,t,a){const i={item:je(e,t,a),action:e.field&&Ue[e.field]?a(Ue[e.field]):e.field??"",code:e.code};return a(Re[e.code]??"missing.unknown",i)}(e,this.config,this.localize)}
                <a href="${Me}/${t}" @click=${e=>this.openPage(e,t)}>
                  ${this.localize(`tabs.${t}`)}
                </a>
              </li>
            `})}
        </ul>
      </ha-alert>
    `}async changeRunning(e){this.changingRunning=!0,this.runningError=void 0;try{await((e,t)=>e.callWS({type:"kraftvakt/regulation/set_running",running:t}))(this.hass,e)}catch(e){this.runningError=ye(e)&&"config_incomplete"===e.code?this.localize("status.start_refused"):this.localize("panel.error",{message:ye(e)?e.message:String(e)})}finally{this.changingRunning=!1}}openPage(e,t){e.preventDefault(),ze(t)}static{this.styles=s`
    :host {
      display: block;
    }
    .cards {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
      align-items: start;
    }
    :host([narrow]) .cards {
      grid-template-columns: minmax(0, 1fr);
      gap: 8px;
    }
    .regulation {
      grid-column: 1 / -1;
    }
    .card-header {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
      padding: 12px 16px;
      font-size: var(--ha-font-size-xl, 20px);
    }
    .spacer {
      flex: 1;
    }
    .card-content {
      display: grid;
      gap: 12px;
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
    .stat-value small {
      font-size: var(--ha-font-size-m, 14px);
      color: var(--secondary-text-color);
    }
    :host([narrow]) .stats {
      grid-template-columns: repeat(3, minmax(0, 1fr));
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
      width: 12px;
      height: 8px;
      border-radius: 4px;
    }
    .regulation-average {
      background: var(--primary-color);
    }
    .capacity-average {
      background: color-mix(in srgb, var(--primary-text-color) 55%, transparent);
    }
    .meter .bar {
      position: relative;
      height: 12px;
      border-radius: 6px;
      background: var(--secondary-background-color);
    }
    .meter .fill {
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      border-radius: 6px;
    }
    .meter .fill.capacity-average {
      top: 4px;
      bottom: 4px;
    }
    .meter .limit {
      position: absolute;
      top: -4px;
      bottom: -4px;
      width: 2px;
      margin-left: -1px;
      background: var(--error-color);
    }
    .meter .scale {
      display: flex;
      justify-content: space-between;
      margin-top: 4px;
      font-size: var(--ha-font-size-s, 12px);
      color: var(--secondary-text-color);
    }
    .meter .limit-label {
      position: relative;
      height: 18px;
      margin-bottom: 4px;
      font-size: var(--ha-font-size-s, 12px);
      color: var(--secondary-text-color);
    }
    .meter .limit-label span {
      position: absolute;
      transform: translateX(-100%);
      padding-inline-end: 6px;
      white-space: nowrap;
    }
    .facts {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px;
      color: var(--secondary-text-color);
    }
    .penalty-details {
      margin-top: 8px;
    }
    .card-header .sub {
      font-size: var(--ha-font-size-m, 14px);
      color: var(--secondary-text-color);
    }
    .empty {
      color: var(--secondary-text-color);
    }
    .row {
      display: flex;
      align-items: center;
      gap: 12px;
      min-height: 56px;
      padding: 6px 16px;
      border-top: 1px solid var(--divider-color);
      box-sizing: border-box;
    }
    .rank {
      flex: none;
      width: 24px;
      text-align: center;
      color: var(--secondary-text-color);
    }
    .row-main {
      flex: 1;
      min-width: 0;
    }
    .row-title {
      overflow-wrap: anywhere;
    }
    .row-sub {
      color: var(--secondary-text-color);
      font-size: var(--ha-font-size-s, 12px);
    }
    .variant {
      display: inline-block;
      margin-inline-start: 6px;
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
  `}};e([pe({attribute:!1})],Ne.prototype,"hass",void 0),e([pe({attribute:!1})],Ne.prototype,"localize",void 0),e([pe({type:Boolean,reflect:!0})],Ne.prototype,"narrow",void 0),e([pe({attribute:!1})],Ne.prototype,"status",void 0),e([pe({attribute:!1})],Ne.prototype,"config",void 0),e([ge()],Ne.prototype,"changingRunning",void 0),e([ge()],Ne.prototype,"runningError",void 0),Ne=e([ce("kraftvakt-status-page")],Ne);const De=["turn_on","turn_off"],We=["activate","deactivate","set_current"];function Ke(e,t){return[...Fe("general",void 0,e.general,t.limits.general,!0),...e.appliances.flatMap(e=>function(e,t){const a=e.variants.map(e=>e.label.trim());return[...Fe("appliances",e.id,e,t.limits.appliances,!1),...qe("appliances",e,De,t),...e.variants.flatMap((t,i)=>{const r=`variants.${t.id}.`,n=[];return""===a[i]?n.push(Be(e,"empty_label",`${r}label`)):a.filter(e=>e===a[i]).length>1&&n.push(Be(e,"duplicate_label",`${r}label`)),[...n,...Ie("appliances",e.id,`${r}condition`,t.condition)]})]}(e,t)),...e.charging.chargers.flatMap(e=>function(e,t){const a=(t,a)=>({code:t,section:"chargers",target:e.id,field:a}),i=[...Fe("chargers",e.id,e,t.limits.chargers,!0),...qe("chargers",e,We,t)];e.min_current_a>e.max_current_a&&i.push(a("min_current_above_max","min_current_a"));e.car_connected&&i.push(...Ie("chargers",e.id,"car_connected",e.car_connected));const r=e.charging_window;!r||r.start&&r.end?r&&r.start===r.end&&i.push(a("window_start_equals_end","charging_window")):i.push(a("invalid_time","charging_window"));return i}(e,t))]}function Be(e,t,a){return{code:t,section:"appliances",target:e.id,field:a}}function Ie(e,t,a,i){return""===i.value.trim()?[{code:"required",section:e,target:t,field:a}]:[]}function Fe(e,t,a,i,r){const n=a;return Object.entries(i).flatMap(([a,i])=>{const s=n[a],o="number"!=typeof s||Number.isNaN(s)?r?"required":void 0:function(e,t){if(null!==t.min&&e<t.min||null!==t.max&&e>t.max)return"out_of_range";const a=e/t.step;return Math.abs(a-Math.round(a))<1e-6?void 0:"invalid_resolution"}(s,i);return o?[{code:o,section:e,target:t,field:a}]:[]})}function qe(e,t,a,i){const r=t;return a.filter(a=>"default"===r[a]?.mode&&null!==t.entity_id&&!function(e,t,a,i){const r=e.default_actions[t][a]??[];return null!==i&&r.includes(i.split(".")[0])}(i,e,a,t.entity_id)).map(a=>({code:"default_action_unavailable",section:e,target:t.id,field:a}))}const Ze={status:"M3,13H5.79L10.1,4.79L11.28,13.75L14.5,9.66L17.83,13H21V15H17L14.67,12.67L9.92,18.73L8.94,11.31L7,15H3V13Z",general:"M12,15.5A3.5,3.5 0 0,1 8.5,12A3.5,3.5 0 0,1 12,8.5A3.5,3.5 0 0,1 15.5,12A3.5,3.5 0 0,1 12,15.5M19.43,12.97C19.47,12.65 19.5,12.33 19.5,12C19.5,11.67 19.47,11.34 19.43,11L21.54,9.37C21.73,9.22 21.78,8.95 21.66,8.73L19.66,5.27C19.54,5.05 19.27,4.96 19.05,5.05L16.56,6.05C16.04,5.66 15.5,5.32 14.87,5.07L14.5,2.42C14.46,2.18 14.25,2 14,2H10C9.75,2 9.54,2.18 9.5,2.42L9.13,5.07C8.5,5.32 7.96,5.66 7.44,6.05L4.95,5.05C4.73,4.96 4.46,5.05 4.34,5.27L2.34,8.73C2.21,8.95 2.27,9.22 2.46,9.37L4.57,11C4.53,11.34 4.5,11.67 4.5,12C4.5,12.33 4.53,12.65 4.57,12.97L2.46,14.63C2.27,14.78 2.21,15.05 2.34,15.27L4.34,18.73C4.46,18.95 4.73,19.03 4.95,18.95L7.44,17.94C7.96,18.34 8.5,18.68 9.13,18.93L9.5,21.58C9.54,21.82 9.75,22 10,22H14C14.25,22 14.46,21.82 14.5,21.58L14.87,18.93C15.5,18.67 16.04,18.34 16.56,17.94L19.05,18.95C19.27,19.03 19.54,18.95 19.66,18.73L21.66,15.27C21.78,15.05 21.73,14.78 21.54,14.63L19.43,12.97Z",appliances:"M7,13V11H21V13H7M7,19V17H21V19H7M7,7V5H21V7H7M3,8V5H2V4H4V8H3M2,17V16H5V20H2V19H4V18.5H3V17.5H4V17H2M4.25,10A0.75,0.75 0 0,1 5,10.75C5,10.95 4.92,11.14 4.79,11.27L3.12,13H5V14H2V13.08L4,11H2V10H4.25Z",charging:"M18.92 2C18.72 1.42 18.16 1 17.5 1H6.5C5.84 1 5.29 1.42 5.08 2L3 8V16C3 16.55 3.45 17 4 17H5C5.55 17 6 16.55 6 16V15H18V16C18 16.55 18.45 17 19 17H20C20.55 17 21 16.55 21 16V8L18.92 2M6.5 12C5.67 12 5 11.33 5 10.5S5.67 9 6.5 9 8 9.67 8 10.5 7.33 12 6.5 12M17.5 12C16.67 12 16 11.33 16 10.5S16.67 9 17.5 9 19 9.67 19 10.5 18.33 12 17.5 12M5 7L6.5 2.5H17.5L19 7H5M7 20H11V18L17 21H13V23L7 20Z"};let Je=class extends oe{constructor(){super(...arguments),this.narrow=!1,this.haElementsReady=!1,this.saveErrors=[],this.saving=!1,this.localize=Ee("en"),this.warnBeforeUnload=e=>{this.dirty&&e.preventDefault()}}connectedCallback(){super.connectedCallback(),window.addEventListener("beforeunload",this.warnBeforeUnload),customElements.whenDefined("ha-form").then(()=>{this.haElementsReady=!0}),this.hass&&this.subscribe()}disconnectedCallback(){super.disconnectedCallback(),window.removeEventListener("beforeunload",this.warnBeforeUnload),this.unsubscribe()}willUpdate(e){e.has("hass")&&this.hass?.language!==e.get("hass")?.language&&(this.localize=Ee(this.hass?.language??"en")),e.has("hass")&&this.hass&&!this.unsubscribeStatus&&this.subscribe()}updated(e){e.has("route")&&this.openAppliancesFromConfigureButton()}render(){if(!this.hass||!this.haElementsReady)return K``;const e=this.currentPage;return K`
      <div class="toolbar">
        <ha-menu-button .hass=${this.hass} .narrow=${this.narrow}></ha-menu-button>
        <div class="title">${this.localize("panel.title")}</div>
        <ha-tab-group @wa-tab-show=${this.tabShown}>
          ${Object.entries(Ze).map(([t,a])=>K`
              <ha-tab-group-tab
                slot="nav"
                panel=${t}
                .active=${be(t===e)}
                title=${this.tabLabel(t)}
              >
                <ha-svg-icon .path=${a}></ha-svg-icon>
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
    `}renderLoadError(){if(void 0===this.loadError)return"";const e=ye(this.loadError)&&"not_loaded"===this.loadError.code?this.localize("panel.not_loaded"):this.localize("panel.error",{message:Ge(this.loadError)});return K`<ha-alert alert-type="error">${e}</ha-alert>`}renderPage(e){switch(e){case"status":return K`
          <kraftvakt-status-page
            .hass=${this.hass}
            .localize=${this.localize}
            .narrow=${this.narrow}
            .status=${this.status}
            .config=${this.config}
          ></kraftvakt-status-page>
        `;case"general":case"appliances":case"charging":return this.renderConfigPage()}}renderConfigPage(){if(!(this.status&&this.config&&this.draft&&this.capabilities))return"";const e=this.status.running,t=e?[]:Ke(this.draft,this.capabilities),a=!e&&(this.dirty||this.saveErrors.length>0);return K`
      <kraftvakt-placeholder-page .localize=${this.localize}></kraftvakt-placeholder-page>
      ${a?K`
            <kraftvakt-save-bar
              .localize=${this.localize}
              .errorCount=${t.length}
              .saving=${this.saving}
              .message=${this.saveMessage}
              @save=${this.save}
              @discard=${this.discard}
            ></kraftvakt-save-bar>
          `:""}
    `}get dirty(){return void 0!==this.draft&&(e=this.draft,t=this.savedConfig,!(JSON.stringify(e)===JSON.stringify(t)));var e,t}get savedConfig(){return this.config&&xe(this.config.config)}draftChanged(e){"draft-changed"!==e.type||this.status?.running||(this.draft=xe(e.detail))}async save(){if(this.hass&&this.draft){this.saving=!0,this.saveMessage=void 0;try{const e=await((e,t)=>e.callWS({type:"kraftvakt/config/save",config:t}))(this.hass,this.draft);e.saved?(this.saveErrors=[],await this.loadConfig({resetDraft:!0})):(this.saveErrors=e.errors,this.saveMessage=this.localize("config.not_saved"))}catch(e){this.saveMessage=ye(e)&&"regulation_running"===e.code?this.localize("config.save_refused_running"):this.localize("panel.error",{message:Ge(e)})}finally{this.saving=!1}}}discard(){this.resetDraft()}resetDraft(){this.draft=this.savedConfig,this.saveErrors=[],this.saveMessage=void 0}leaveConfirmed(){const e=this.leavingTo;this.leavingTo=void 0,this.resetDraft(),e&&ze(e)}leaveCancelled(){this.leavingTo=void 0}get currentPage(){return function(e){const t=e.split("/")[1]??"";return Ce.includes(t)?t:"status"}(this.route?.path??"")}tabLabel(e){return this.localize(`tabs.${e}`)}tabShown(e){const t=e.detail.name;t!==this.currentPage&&("status"===t&&this.dirty?this.leavingTo=t:ze(t))}subscribe(){var e,t;this.hass&&(this.unsubscribeStatus=(e=this.hass,t=e=>this.statusReceived(e),e.connection.subscribeMessage(t,{type:"kraftvakt/status/subscribe"})),this.unsubscribeStatus.catch(e=>{this.loadError=e,this.unsubscribeStatus=void 0}),(e=>e.callWS({type:"kraftvakt/capabilities"}))(this.hass).then(e=>this.capabilities=e).catch(e=>this.loadError=e))}unsubscribe(){this.unsubscribeStatus?.then(e=>e()).catch(()=>{}),this.unsubscribeStatus=void 0}statusReceived(e){const t=this.status;this.status=e,this.loadError=void 0,void 0!==t&&t.running===e.running&&JSON.stringify(t.missing)===JSON.stringify(e.missing)||this.loadConfig()}async loadConfig(e={}){var t;if(this.hass)try{const a=this.dirty&&!e.resetDraft&&!this.status?.running;this.config=await(t=this.hass,t.callWS({type:"kraftvakt/config/get"})),a||this.resetDraft()}catch(e){this.loadError=e}}openAppliancesFromConfigureButton(){new URLSearchParams(window.location.search).has("config_entry")&&ze("appliances",{replace:!0})}static{this.styles=s`
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
  `}};function Ge(e){return ye(e)?e.message:String(e)}e([pe({attribute:!1})],Je.prototype,"hass",void 0),e([pe({type:Boolean,reflect:!0})],Je.prototype,"narrow",void 0),e([pe({attribute:!1})],Je.prototype,"route",void 0),e([ge()],Je.prototype,"haElementsReady",void 0),e([ge()],Je.prototype,"status",void 0),e([ge()],Je.prototype,"config",void 0),e([ge()],Je.prototype,"loadError",void 0),e([ge()],Je.prototype,"capabilities",void 0),e([ge()],Je.prototype,"draft",void 0),e([ge()],Je.prototype,"saveErrors",void 0),e([ge()],Je.prototype,"saveMessage",void 0),e([ge()],Je.prototype,"saving",void 0),e([ge()],Je.prototype,"leavingTo",void 0),Je=e([ce("kraftvakt-panel")],Je);export{Je as KraftvaktPanel};
