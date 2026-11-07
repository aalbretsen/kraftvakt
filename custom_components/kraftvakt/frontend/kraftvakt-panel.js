function t(t,e,s,i){var r,a=arguments.length,n=a<3?e:null===i?i=Object.getOwnPropertyDescriptor(e,s):i;if("object"==typeof Reflect&&"function"==typeof Reflect.decorate)n=Reflect.decorate(t,e,s,i);else for(var o=t.length-1;o>=0;o--)(r=t[o])&&(n=(a<3?r(n):a>3?r(e,s,n):r(e,s))||n);return a>3&&n&&Object.defineProperty(e,s,n),n}"function"==typeof SuppressedError&&SuppressedError;const e=globalThis,s=e.ShadowRoot&&(void 0===e.ShadyCSS||e.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,i=Symbol(),r=new WeakMap;let a=class{constructor(t,e,s){if(this._$cssResult$=!0,s!==i)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=e}get styleSheet(){let t=this.o;const e=this.t;if(s&&void 0===t){const s=void 0!==e&&1===e.length;s&&(t=r.get(e)),void 0===t&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),s&&r.set(e,t))}return t}toString(){return this.cssText}};const n=(t,...e)=>{const s=1===t.length?t[0]:e.reduce((e,s,i)=>e+(t=>{if(!0===t._$cssResult$)return t.cssText;if("number"==typeof t)return t;throw Error("Value passed to 'css' function must be a 'css' function result: "+t+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(s)+t[i+1],t[0]);return new a(s,t,i)},o=s?t=>t:t=>t instanceof CSSStyleSheet?(t=>{let e="";for(const s of t.cssRules)e+=s.cssText;return(t=>new a("string"==typeof t?t:t+"",void 0,i))(e)})(t):t,{is:l,defineProperty:c,getOwnPropertyDescriptor:h,getOwnPropertyNames:p,getOwnPropertySymbols:d,getPrototypeOf:u}=Object,g=globalThis,f=g.trustedTypes,v=f?f.emptyScript:"",_=g.reactiveElementPolyfillSupport,m=(t,e)=>t,$={toAttribute(t,e){switch(e){case Boolean:t=t?v:null;break;case Object:case Array:t=null==t?t:JSON.stringify(t)}return t},fromAttribute(t,e){let s=t;switch(e){case Boolean:s=null!==t;break;case Number:s=null===t?null:Number(t);break;case Object:case Array:try{s=JSON.parse(t)}catch(t){s=null}}return s}},y=(t,e)=>!l(t,e),b={attribute:!0,type:String,converter:$,reflect:!1,useDefault:!1,hasChanged:y};Symbol.metadata??=Symbol("metadata"),g.litPropertyMetadata??=new WeakMap;let w=class extends HTMLElement{static addInitializer(t){this._$Ei(),(this.l??=[]).push(t)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(t,e=b){if(e.state&&(e.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(t)&&((e=Object.create(e)).wrapped=!0),this.elementProperties.set(t,e),!e.noAccessor){const s=Symbol(),i=this.getPropertyDescriptor(t,s,e);void 0!==i&&c(this.prototype,t,i)}}static getPropertyDescriptor(t,e,s){const{get:i,set:r}=h(this.prototype,t)??{get(){return this[e]},set(t){this[e]=t}};return{get:i,set(e){const a=i?.call(this);r?.call(this,e),this.requestUpdate(t,a,s)},configurable:!0,enumerable:!0}}static getPropertyOptions(t){return this.elementProperties.get(t)??b}static _$Ei(){if(this.hasOwnProperty(m("elementProperties")))return;const t=u(this);t.finalize(),void 0!==t.l&&(this.l=[...t.l]),this.elementProperties=new Map(t.elementProperties)}static finalize(){if(this.hasOwnProperty(m("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(m("properties"))){const t=this.properties,e=[...p(t),...d(t)];for(const s of e)this.createProperty(s,t[s])}const t=this[Symbol.metadata];if(null!==t){const e=litPropertyMetadata.get(t);if(void 0!==e)for(const[t,s]of e)this.elementProperties.set(t,s)}this._$Eh=new Map;for(const[t,e]of this.elementProperties){const s=this._$Eu(t,e);void 0!==s&&this._$Eh.set(s,t)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(t){const e=[];if(Array.isArray(t)){const s=new Set(t.flat(1/0).reverse());for(const t of s)e.unshift(o(t))}else void 0!==t&&e.push(o(t));return e}static _$Eu(t,e){const s=e.attribute;return!1===s?void 0:"string"==typeof s?s:"string"==typeof t?t.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(t=>this.enableUpdating=t),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(t=>t(this))}addController(t){(this._$EO??=new Set).add(t),void 0!==this.renderRoot&&this.isConnected&&t.hostConnected?.()}removeController(t){this._$EO?.delete(t)}_$E_(){const t=new Map,e=this.constructor.elementProperties;for(const s of e.keys())this.hasOwnProperty(s)&&(t.set(s,this[s]),delete this[s]);t.size>0&&(this._$Ep=t)}createRenderRoot(){const t=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return((t,i)=>{if(s)t.adoptedStyleSheets=i.map(t=>t instanceof CSSStyleSheet?t:t.styleSheet);else for(const s of i){const i=document.createElement("style"),r=e.litNonce;void 0!==r&&i.setAttribute("nonce",r),i.textContent=s.cssText,t.appendChild(i)}})(t,this.constructor.elementStyles),t}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(t=>t.hostConnected?.())}enableUpdating(t){}disconnectedCallback(){this._$EO?.forEach(t=>t.hostDisconnected?.())}attributeChangedCallback(t,e,s){this._$AK(t,s)}_$ET(t,e){const s=this.constructor.elementProperties.get(t),i=this.constructor._$Eu(t,s);if(void 0!==i&&!0===s.reflect){const r=(void 0!==s.converter?.toAttribute?s.converter:$).toAttribute(e,s.type);this._$Em=t,null==r?this.removeAttribute(i):this.setAttribute(i,r),this._$Em=null}}_$AK(t,e){const s=this.constructor,i=s._$Eh.get(t);if(void 0!==i&&this._$Em!==i){const t=s.getPropertyOptions(i),r="function"==typeof t.converter?{fromAttribute:t.converter}:void 0!==t.converter?.fromAttribute?t.converter:$;this._$Em=i;const a=r.fromAttribute(e,t.type);this[i]=a??this._$Ej?.get(i)??a,this._$Em=null}}requestUpdate(t,e,s,i=!1,r){if(void 0!==t){const a=this.constructor;if(!1===i&&(r=this[t]),s??=a.getPropertyOptions(t),!((s.hasChanged??y)(r,e)||s.useDefault&&s.reflect&&r===this._$Ej?.get(t)&&!this.hasAttribute(a._$Eu(t,s))))return;this.C(t,e,s)}!1===this.isUpdatePending&&(this._$ES=this._$EP())}C(t,e,{useDefault:s,reflect:i,wrapped:r},a){s&&!(this._$Ej??=new Map).has(t)&&(this._$Ej.set(t,a??e??this[t]),!0!==r||void 0!==a)||(this._$AL.has(t)||(this.hasUpdated||s||(e=void 0),this._$AL.set(t,e)),!0===i&&this._$Em!==t&&(this._$Eq??=new Set).add(t))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(t){Promise.reject(t)}const t=this.scheduleUpdate();return null!=t&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(const[t,e]of this._$Ep)this[t]=e;this._$Ep=void 0}const t=this.constructor.elementProperties;if(t.size>0)for(const[e,s]of t){const{wrapped:t}=s,i=this[e];!0!==t||this._$AL.has(e)||void 0===i||this.C(e,void 0,s,i)}}let t=!1;const e=this._$AL;try{t=this.shouldUpdate(e),t?(this.willUpdate(e),this._$EO?.forEach(t=>t.hostUpdate?.()),this.update(e)):this._$EM()}catch(e){throw t=!1,this._$EM(),e}t&&this._$AE(e)}willUpdate(t){}_$AE(t){this._$EO?.forEach(t=>t.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(t)),this.updated(t)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(t){return!0}update(t){this._$Eq&&=this._$Eq.forEach(t=>this._$ET(t,this[t])),this._$EM()}updated(t){}firstUpdated(t){}};w.elementStyles=[],w.shadowRootOptions={mode:"open"},w[m("elementProperties")]=new Map,w[m("finalized")]=new Map,_?.({ReactiveElement:w}),(g.reactiveElementVersions??=[]).push("2.1.2");const x=globalThis,A=t=>t,k=x.trustedTypes,S=k?k.createPolicy("lit-html",{createHTML:t=>t}):void 0,E="$lit$",C=`lit$${Math.random().toFixed(9).slice(2)}$`,z="?"+C,H=`<${z}>`,P=document,M=()=>P.createComment(""),L=t=>null===t||"object"!=typeof t&&"function"!=typeof t,R=Array.isArray,O="[ \t\n\f\r]",V=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,U=/-->/g,T=/>/g,N=RegExp(`>|${O}(?:([^\\s"'>=/]+)(${O}*=${O}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`,"g"),j=/'/g,D=/"/g,W=/^(?:script|style|textarea|title)$/i,I=(t=>(e,...s)=>({_$litType$:t,strings:e,values:s}))(1),B=Symbol.for("lit-noChange"),K=Symbol.for("lit-nothing"),q=new WeakMap,Z=P.createTreeWalker(P,129);function F(t,e){if(!R(t)||!t.hasOwnProperty("raw"))throw Error("invalid template strings array");return void 0!==S?S.createHTML(e):e}const J=(t,e)=>{const s=t.length-1,i=[];let r,a=2===e?"<svg>":3===e?"<math>":"",n=V;for(let e=0;e<s;e++){const s=t[e];let o,l,c=-1,h=0;for(;h<s.length&&(n.lastIndex=h,l=n.exec(s),null!==l);)h=n.lastIndex,n===V?"!--"===l[1]?n=U:void 0!==l[1]?n=T:void 0!==l[2]?(W.test(l[2])&&(r=RegExp("</"+l[2],"g")),n=N):void 0!==l[3]&&(n=N):n===N?">"===l[0]?(n=r??V,c=-1):void 0===l[1]?c=-2:(c=n.lastIndex-l[2].length,o=l[1],n=void 0===l[3]?N:'"'===l[3]?D:j):n===D||n===j?n=N:n===U||n===T?n=V:(n=N,r=void 0);const p=n===N&&t[e+1].startsWith("/>")?" ":"";a+=n===V?s+H:c>=0?(i.push(o),s.slice(0,c)+E+s.slice(c)+C+p):s+C+(-2===c?e:p)}return[F(t,a+(t[s]||"<?>")+(2===e?"</svg>":3===e?"</math>":"")),i]};class G{constructor({strings:t,_$litType$:e},s){let i;this.parts=[];let r=0,a=0;const n=t.length-1,o=this.parts,[l,c]=J(t,e);if(this.el=G.createElement(l,s),Z.currentNode=this.el.content,2===e||3===e){const t=this.el.content.firstChild;t.replaceWith(...t.childNodes)}for(;null!==(i=Z.nextNode())&&o.length<n;){if(1===i.nodeType){if(i.hasAttributes())for(const t of i.getAttributeNames())if(t.endsWith(E)){const e=c[a++],s=i.getAttribute(t).split(C),n=/([.?@])?(.*)/.exec(e);o.push({type:1,index:r,name:n[2],strings:s,ctor:"."===n[1]?et:"?"===n[1]?st:"@"===n[1]?it:tt}),i.removeAttribute(t)}else t.startsWith(C)&&(o.push({type:6,index:r}),i.removeAttribute(t));if(W.test(i.tagName)){const t=i.textContent.split(C),e=t.length-1;if(e>0){i.textContent=k?k.emptyScript:"";for(let s=0;s<e;s++)i.append(t[s],M()),Z.nextNode(),o.push({type:2,index:++r});i.append(t[e],M())}}}else if(8===i.nodeType)if(i.data===z)o.push({type:2,index:r});else{let t=-1;for(;-1!==(t=i.data.indexOf(C,t+1));)o.push({type:7,index:r}),t+=C.length-1}r++}}static createElement(t,e){const s=P.createElement("template");return s.innerHTML=t,s}}function X(t,e,s=t,i){if(e===B)return e;let r=void 0!==i?s._$Co?.[i]:s._$Cl;const a=L(e)?void 0:e._$litDirective$;return r?.constructor!==a&&(r?._$AO?.(!1),void 0===a?r=void 0:(r=new a(t),r._$AT(t,s,i)),void 0!==i?(s._$Co??=[])[i]=r:s._$Cl=r),void 0!==r&&(e=X(t,r._$AS(t,e.values),r,i)),e}class Q{constructor(t,e){this._$AV=[],this._$AN=void 0,this._$AD=t,this._$AM=e}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(t){const{el:{content:e},parts:s}=this._$AD,i=(t?.creationScope??P).importNode(e,!0);Z.currentNode=i;let r=Z.nextNode(),a=0,n=0,o=s[0];for(;void 0!==o;){if(a===o.index){let e;2===o.type?e=new Y(r,r.nextSibling,this,t):1===o.type?e=new o.ctor(r,o.name,o.strings,this,t):6===o.type&&(e=new rt(r,this,t)),this._$AV.push(e),o=s[++n]}a!==o?.index&&(r=Z.nextNode(),a++)}return Z.currentNode=P,i}p(t){let e=0;for(const s of this._$AV)void 0!==s&&(void 0!==s.strings?(s._$AI(t,s,e),e+=s.strings.length-2):s._$AI(t[e])),e++}}class Y{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(t,e,s,i){this.type=2,this._$AH=K,this._$AN=void 0,this._$AA=t,this._$AB=e,this._$AM=s,this.options=i,this._$Cv=i?.isConnected??!0}get parentNode(){let t=this._$AA.parentNode;const e=this._$AM;return void 0!==e&&11===t?.nodeType&&(t=e.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,e=this){t=X(this,t,e),L(t)?t===K||null==t||""===t?(this._$AH!==K&&this._$AR(),this._$AH=K):t!==this._$AH&&t!==B&&this._(t):void 0!==t._$litType$?this.$(t):void 0!==t.nodeType?this.T(t):(t=>R(t)||"function"==typeof t?.[Symbol.iterator])(t)?this.k(t):this._(t)}O(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t))}_(t){this._$AH!==K&&L(this._$AH)?this._$AA.nextSibling.data=t:this.T(P.createTextNode(t)),this._$AH=t}$(t){const{values:e,_$litType$:s}=t,i="number"==typeof s?this._$AC(t):(void 0===s.el&&(s.el=G.createElement(F(s.h,s.h[0]),this.options)),s);if(this._$AH?._$AD===i)this._$AH.p(e);else{const t=new Q(i,this),s=t.u(this.options);t.p(e),this.T(s),this._$AH=t}}_$AC(t){let e=q.get(t.strings);return void 0===e&&q.set(t.strings,e=new G(t)),e}k(t){R(this._$AH)||(this._$AH=[],this._$AR());const e=this._$AH;let s,i=0;for(const r of t)i===e.length?e.push(s=new Y(this.O(M()),this.O(M()),this,this.options)):s=e[i],s._$AI(r),i++;i<e.length&&(this._$AR(s&&s._$AB.nextSibling,i),e.length=i)}_$AR(t=this._$AA.nextSibling,e){for(this._$AP?.(!1,!0,e);t!==this._$AB;){const e=A(t).nextSibling;A(t).remove(),t=e}}setConnected(t){void 0===this._$AM&&(this._$Cv=t,this._$AP?.(t))}}class tt{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(t,e,s,i,r){this.type=1,this._$AH=K,this._$AN=void 0,this.element=t,this.name=e,this._$AM=i,this.options=r,s.length>2||""!==s[0]||""!==s[1]?(this._$AH=Array(s.length-1).fill(new String),this.strings=s):this._$AH=K}_$AI(t,e=this,s,i){const r=this.strings;let a=!1;if(void 0===r)t=X(this,t,e,0),a=!L(t)||t!==this._$AH&&t!==B,a&&(this._$AH=t);else{const i=t;let n,o;for(t=r[0],n=0;n<r.length-1;n++)o=X(this,i[s+n],e,n),o===B&&(o=this._$AH[n]),a||=!L(o)||o!==this._$AH[n],o===K?t=K:t!==K&&(t+=(o??"")+r[n+1]),this._$AH[n]=o}a&&!i&&this.j(t)}j(t){t===K?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,t??"")}}class et extends tt{constructor(){super(...arguments),this.type=3}j(t){this.element[this.name]=t===K?void 0:t}}class st extends tt{constructor(){super(...arguments),this.type=4}j(t){this.element.toggleAttribute(this.name,!!t&&t!==K)}}class it extends tt{constructor(t,e,s,i,r){super(t,e,s,i,r),this.type=5}_$AI(t,e=this){if((t=X(this,t,e,0)??K)===B)return;const s=this._$AH,i=t===K&&s!==K||t.capture!==s.capture||t.once!==s.once||t.passive!==s.passive,r=t!==K&&(s===K||i);i&&this.element.removeEventListener(this.name,this,s),r&&this.element.addEventListener(this.name,this,t),this._$AH=t}handleEvent(t){"function"==typeof this._$AH?this._$AH.call(this.options?.host??this.element,t):this._$AH.handleEvent(t)}}class rt{constructor(t,e,s){this.element=t,this.type=6,this._$AN=void 0,this._$AM=e,this.options=s}get _$AU(){return this._$AM._$AU}_$AI(t){X(this,t)}}const at=x.litHtmlPolyfillSupport;at?.(G,Y),(x.litHtmlVersions??=[]).push("3.3.3");const nt=globalThis;class ot extends w{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){const t=super.createRenderRoot();return this.renderOptions.renderBefore??=t.firstChild,t}update(t){const e=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this._$Do=((t,e,s)=>{const i=s?.renderBefore??e;let r=i._$litPart$;if(void 0===r){const t=s?.renderBefore??null;i._$litPart$=r=new Y(e.insertBefore(M(),t),t,void 0,s??{})}return r._$AI(t),r})(e,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return B}}ot._$litElement$=!0,ot.finalized=!0,nt.litElementHydrateSupport?.({LitElement:ot});const lt=nt.litElementPolyfillSupport;lt?.({LitElement:ot}),(nt.litElementVersions??=[]).push("4.2.2");const ct=t=>(e,s)=>{void 0!==s?s.addInitializer(()=>{customElements.define(t,e)}):customElements.define(t,e)},ht={attribute:!0,type:String,converter:$,reflect:!1,hasChanged:y},pt=(t=ht,e,s)=>{const{kind:i,metadata:r}=s;let a=globalThis.litPropertyMetadata.get(r);if(void 0===a&&globalThis.litPropertyMetadata.set(r,a=new Map),"setter"===i&&((t=Object.create(t)).wrapped=!0),a.set(s.name,t),"accessor"===i){const{name:i}=s;return{set(s){const r=e.get.call(this);e.set.call(this,s),this.requestUpdate(i,r,t,!0,s)},init(e){return void 0!==e&&this.C(i,void 0,t,e),e}}}if("setter"===i){const{name:i}=s;return function(s){const r=this[i];e.call(this,s),this.requestUpdate(i,r,t,!0,s)}}throw Error("Unsupported decorator location: "+i)};function dt(t){return(e,s)=>"object"==typeof s?pt(t,e,s):((t,e,s)=>{const i=e.hasOwnProperty(s);return e.constructor.createProperty(s,t),i?Object.getOwnPropertyDescriptor(e,s):void 0})(t,e,s)}function ut(t){return dt({...t,state:!0,attribute:!1})}function gt(t){return"object"==typeof t&&null!==t&&"code"in t&&"message"in t}const ft={en:{panel:{title:"Kraftvakt",not_loaded:"Kraftvakt is not loaded. Check the integration under Settings → Devices & services.",error:"Something went wrong: {message}"},tabs:{status:"Status",general:"General",appliances:"Appliances",charging:"EV charging"},placeholder:{not_ready:"This page is not ready yet. It comes in a later version of Kraftvakt."},status:{regulation:"Regulation",running:"Running",stopped:"Stopped",start:"Start regulation",stop:"Stop regulation",stopped_info:"The regulation is stopped, and all regulated appliances and EV chargers are turned off. The configuration can be changed. When the regulation starts, the appliances are turned on again one by one.",incomplete_title:"The configuration is not complete",start_refused:"The regulation cannot start before the configuration is complete.",safe_state_title:"Safe state",safe_state_text:"The power sensor {sensor} gives no valid measurement. All regulated appliances and EV chargers are turned off. The regulation starts again by itself when the sensor gives a valid value again.",penalty_title:"Penalty period",penalty_text:"The average consumption has been above the power limit. All regulated appliances and EV chargers are kept off until the overconsumption is recovered.",overconsumption_left:"Overconsumption left: {energy} kWh",recovery_started:"recovery has started",recovery_not_started:"recovery has not started",regulation_average:"Regulation average",capacity_average:"Average consumption last hour",power_limit:"Power limit",scale_limit:"Limit {power} kW",safe_state_chip:"Safe state: {value}",penalty_chip:"Penalty period: {value}",yes:"yes",no:"no",next_decision:"Next decision in {time}",appliances:"Appliances",appliances_order:"in order of priority",no_appliances:"No appliances are configured.",chargers:"EV chargers",chargers_order:"current charging priority",on:"On",off:"Off",activated:"Activated",deactivated:"Deactivated",waiting_to_turn_on:"Waiting, turns on in about {time}",waiting_to_activate:"Waiting, is activated in about {time}",waiting_to_increase:"Waiting, the current is increased in about {time}",charging_current:"{current} A of {min}–{max} A",bypassed:"Bypassed: draws no power",waiting_charger:"Waiting: another EV charger is charging",excluded:"Excluded from the regulation",outside_window:"Outside the charging window ({start}–{end})"},missing:{missing_power_sensor:"The power sensor is not chosen.",missing_entity:"{item}: the entity is not chosen.",missing_action:"{item}: the action to {action} is missing.",missing_charge_power_sensor:"{item}: the sensor for charging power is missing.",unknown:"{item}: {code}",appliance_without_entity:"An appliance without an entity",charger_without_entity:"An EV charger without an entity",actions:{turn_on:"turn it on",turn_off:"turn it off",activate:"activate it",deactivate:"deactivate it",set_current:"set the charging current"}}},nb:{panel:{title:"Kraftvakt",not_loaded:"Kraftvakt er ikke lastet. Sjekk integrasjonen under Innstillinger → Enheter og tjenester.",error:"Noe gikk galt: {message}"},tabs:{status:"Status",general:"Generelt",appliances:"Apparater",charging:"Billading"},placeholder:{not_ready:"Denne siden er ikke klar ennå. Den kommer i en senere versjon av Kraftvakt."},status:{regulation:"Regulering",running:"Kjører",stopped:"Stoppet",start:"Start regulering",stop:"Stopp regulering",stopped_info:"Reguleringen er stoppet, og alle regulerte apparater og elbilladere er slått av. Konfigurasjonen kan endres. Når reguleringen startes, slås apparatene på igjen ett og ett.",incomplete_title:"Konfigurasjonen er ikke fullstendig",start_refused:"Reguleringen kan ikke startes før konfigurasjonen er fullstendig.",safe_state_title:"Sikker tilstand",safe_state_text:"Effektsensoren {sensor} gir ingen gyldig måling. Alle regulerte apparater og elbilladere er slått av. Reguleringen starter på nytt av seg selv når sensoren gir en gyldig verdi igjen.",penalty_title:"Straffeperiode pågår",penalty_text:"Snittforbruket har vært over effektgrensen. Alle regulerte apparater og elbilladere holdes av til overforbruket er hentet inn.",overconsumption_left:"Overforbruk igjen: {energy} kWh",recovery_started:"innhenting har startet",recovery_not_started:"innhenting har ikke startet",regulation_average:"Reguleringssnitt",capacity_average:"Snittforbruk siste time",power_limit:"Effektgrense",scale_limit:"Grense {power} kW",safe_state_chip:"Sikker tilstand: {value}",penalty_chip:"Straffeperiode: {value}",yes:"ja",no:"nei",next_decision:"Neste avgjørelse om {time}",appliances:"Apparater",appliances_order:"i prioritert rekkefølge",no_appliances:"Ingen apparater er konfigurert.",chargers:"Elbilladere",chargers_order:"gjeldende ladeprioritering",on:"På",off:"Av",activated:"Aktivert",deactivated:"Deaktivert",waiting_to_turn_on:"Venter, slås på om ca. {time}",waiting_to_activate:"Venter, aktiveres om ca. {time}",waiting_to_increase:"Venter, ladestrømmen økes om ca. {time}",charging_current:"{current} A av {min}–{max} A",bypassed:"Forbigått: trekker ikke strøm",waiting_charger:"Ventende: en annen elbillader lader",excluded:"Utenfor regulering",outside_window:"Utenfor ladetidsrom ({start}–{end})"},missing:{missing_power_sensor:"Effektsensor er ikke valgt.",missing_entity:"{item}: entitet er ikke valgt.",missing_action:"{item}: handling for å {action} mangler.",missing_charge_power_sensor:"{item}: sensor for ladeeffekt mangler.",unknown:"{item}: {code}",appliance_without_entity:"Et apparat uten entitet",charger_without_entity:"En elbillader uten entitet",actions:{turn_on:"slå på",turn_off:"slå av",activate:"aktivere",deactivate:"deaktivere",set_current:"sette ladestrøm"}}}};function vt(t){const e=ft[t]??ft[t.split("-")[0]]??ft.en;return(t,s={})=>(_t(e,t)??_t(ft.en,t)??t).replace(/\{(\w+)\}/g,(t,e)=>e in s?String(s[e]):t)}function _t(t,e){let s=t;for(const t of e.split("."))s=s?.[t];return"string"==typeof s?s:void 0}const mt=["status","general","appliances","charging"],$t="/kraftvakt";function yt(t,e={}){const s=`${$t}/${t}`;e.replace?history.replaceState(null,"",s):history.pushState(null,"",s),window.dispatchEvent(new CustomEvent("location-changed",{detail:{replace:e.replace??!1}}))}let bt=class extends ot{render(){return I`<ha-card><div class="content">${this.localize("placeholder.not_ready")}</div></ha-card>`}static{this.styles=n`
    .content {
      padding: 16px;
    }
  `}};t([dt({attribute:!1})],bt.prototype,"localize",void 0),bt=t([ct("kraftvakt-placeholder-page")],bt);class wt{constructor(t){this.host=t,this.now=Date.now(),t.addController(this)}hostConnected(){this.timer=window.setInterval(()=>{this.now=Date.now(),this.host.requestUpdate()},1e3)}hostDisconnected(){window.clearInterval(this.timer)}}function xt(t,e,s){return new Intl.NumberFormat(t,{minimumFractionDigits:s,maximumFractionDigits:s}).format(e)}function At(t,e){return null===e?"–":xt(t,e,2)}function kt(t,e){const s=Math.max(0,Math.ceil((Date.parse(t)-e)/1e3)),i=Math.floor(s/3600),r=Math.floor(s%3600/60),a=String(s%60).padStart(2,"0");return i>0?`${i}:${String(r).padStart(2,"0")}:${a}`:`${r}:${a}`}const St={missing_power_sensor:"missing.missing_power_sensor",missing_entity:"missing.missing_entity",missing_action:"missing.missing_action",missing_charge_power_sensor:"missing.missing_charge_power_sensor"},Et={turn_on:"missing.actions.turn_on",turn_off:"missing.actions.turn_off",activate:"missing.actions.activate",deactivate:"missing.actions.deactivate",set_current:"missing.actions.set_current"},Ct={general:"general",appliances:"appliances",priority:"appliances",charging:"charging",chargers:"charging"};function zt(t,e,s){const i="chargers"===t.section?e?.config.charging.chargers:e?.config.appliances,r=i?.find(e=>e.id===t.target)?.entity_id;return r?e?.entity_names[r]??r:s("chargers"===t.section?"missing.charger_without_entity":"missing.appliance_without_entity")}let Ht=class extends ot{constructor(){super(...arguments),this.narrow=!1,this.changingRunning=!1,this.clock=new wt(this)}render(){if(!this.status)return K;const t=this.status;return I`
      <div class="cards">
        ${this.renderRegulationCard(t)} ${t.running?this.renderAppliancesCard(t.appliances):K}
        ${t.running&&t.chargers.length>0?this.renderChargersCard(t.chargers):K}
      </div>
    `}renderRegulationCard(t){return I`
      <ha-card class="regulation">
        <div class="card-header">
          <span>${this.localize("status.regulation")}</span>
          <span class="chip ${t.running?"running":"off"}">
            <span class="dot"></span>
            ${this.localize(t.running?"status.running":"status.stopped")}
          </span>
          <span class="spacer"></span>
          ${this.narrow?K:this.renderStartStop(t)}
        </div>
        <div class="card-content">
          ${this.runningError?I`<ha-alert alert-type="error">${this.runningError}</ha-alert>`:K}
          ${t.running?this.renderRunning(t):this.renderStopped(t)}
        </div>
        ${this.narrow?I`<div class="card-actions">${this.renderStartStop(t)}</div>`:K}
      </ha-card>
    `}renderStartStop(t){return t.running?I`
        <ha-button
          variant="danger"
          appearance="outlined"
          .disabled=${this.changingRunning}
          @click=${()=>this.changeRunning(!1)}
        >
          <ha-svg-icon slot="start" .path=${"M18,18H6V6H18V18Z"}></ha-svg-icon>
          ${this.localize("status.stop")}
        </ha-button>
      `:I`
      <ha-button
        .disabled=${this.changingRunning||t.missing.length>0}
        @click=${()=>this.changeRunning(!0)}
      >
        <ha-svg-icon slot="start" .path=${"M8,5.14V19.14L19,12.14L8,5.14Z"}></ha-svg-icon>
        ${this.localize("status.start")}
      </ha-button>
    `}renderRunning(t){const e=this.hass.language;return I`
      ${t.safe_state?this.renderSafeState():K} ${t.penalty.active?this.renderPenalty(t):K}
      <div class="stats">
        ${this.renderStat("regulation-average","status.regulation_average",At(e,t.regulation_average_kw))}
        ${this.renderStat("capacity-average","status.capacity_average",At(e,t.capacity_average_kw),(s=t.capacity_average_kw,null!==s&&s>t.power_limit_kw))}
        ${this.renderStat("","status.power_limit",At(e,t.power_limit_kw))}
      </div>
      ${this.renderMeter(t)}
      <div class="facts">
        <span class="chip ${t.safe_state?"alarm":"off"}">
          ${this.localize("status.safe_state_chip",{value:this.yesNo(t.safe_state)})}
        </span>
        <span class="chip ${t.penalty.active?"alarm":"off"}">
          ${this.localize("status.penalty_chip",{value:this.yesNo(t.penalty.active)})}
        </span>
        ${t.next_decision_at?I`<span>
              ${this.localize("status.next_decision",{time:kt(t.next_decision_at,this.clock.now)})}
            </span>`:K}
      </div>
    `;var s}renderSafeState(){const t=this.config?.config.general.power_sensor??"",e=this.hass.states[t]?.attributes.friendly_name??t;return I`
      <ha-alert alert-type="error" .title=${this.localize("status.safe_state_title")}>
        ${this.localize("status.safe_state_text",{sensor:e})}
      </ha-alert>
    `}renderPenalty(t){const e=xt(this.hass.language,Math.max(0,t.penalty.overconsumption_kwh),2),s=t.penalty.recovery_started?"status.recovery_started":"status.recovery_not_started";return I`
      <ha-alert alert-type="warning" .title=${this.localize("status.penalty_title")}>
        ${this.localize("status.penalty_text")}
        <div class="penalty-details">${this.localize("status.overconsumption_left",{energy:e})} · ${this.localize(s)}</div>
      </ha-alert>
    `}renderStat(t,e,s,i=!1){return I`
      <div class="stat">
        <div class="stat-label">${t?I`<span class="swatch ${t}"></span>`:K}${this.localize(e)}</div>
        <div class="stat-value ${i?"alarm":""}">${s} <small>kW</small></div>
      </div>
    `}renderMeter(t){const e=t.regulation_average_kw,s=t.capacity_average_kw;if(null===e||null===s)return K;const i=Math.max(1.2*t.power_limit_kw,e,s),r=t=>100*t/i+"%",a=this.hass.language;return I`
      <div class="meter">
        <div class="limit-label">
          <span style="left: ${r(t.power_limit_kw)}">
            ${this.localize("status.scale_limit",{power:xt(a,t.power_limit_kw,1)})}
          </span>
        </div>
        <div class="bar">
          <div class="fill regulation-average" style="width: ${r(e)}"></div>
          <div class="fill capacity-average" style="width: ${r(s)}"></div>
          <div class="limit" style="left: ${r(t.power_limit_kw)}"></div>
        </div>
        <div class="scale">
          <span>0 kW</span>
          <span>${xt(a,i,1)} kW</span>
        </div>
      </div>
    `}renderAppliancesCard(t){return I`
      <ha-card>
        <div class="card-header">
          <span>${this.localize("status.appliances")}</span>
          <span class="sub">${this.localize("status.appliances_order")}</span>
        </div>
        ${0===t.length?I`<div class="card-content empty">${this.localize("status.no_appliances")}</div>`:I`<div class="list">
              ${t.map((t,e)=>I`
                  <div class="row">
                    <span class="rank">${e+1}</span>
                    <div class="row-main">
                      <div class="row-title">
                        ${t.name}
                        ${t.variant?I`<span class="variant">${t.variant}</span>`:K}
                      </div>
                      ${t.waiting_until?I`<div class="row-sub">
                            ${this.localize("status.waiting_to_turn_on",{time:kt(t.waiting_until,this.clock.now)})}
                          </div>`:K}
                    </div>
                    ${this.renderOnOff(t.on,"status.on","status.off")}
                  </div>
                `)}
            </div>`}
      </ha-card>
    `}renderChargersCard(t){return I`
      <ha-card>
        <div class="card-header">
          <span>${this.localize("status.chargers")}</span>
          <span class="sub">${this.localize("status.chargers_order")}</span>
        </div>
        <div class="list">
          ${t.map(t=>{const e=this.chargerDetails(t);return I`
              <div class="row">
                <ha-svg-icon class="rank" .path=${"M19.77,7.23L19.78,7.22L16.06,3.5L15,4.56L17.11,6.67C16.17,7.03 15.5,7.93 15.5,9A2.5,2.5 0 0,0 18,11.5C18.36,11.5 18.69,11.42 19,11.29V18.5A1,1 0 0,1 18,19.5A1,1 0 0,1 17,18.5V14A2,2 0 0,0 15,12H14V5A2,2 0 0,0 12,3H6A2,2 0 0,0 4,5V21H14V13.5H15.5V18.5A2.5,2.5 0 0,0 18,21A2.5,2.5 0 0,0 20.5,18.5V9C20.5,8.31 20.22,7.68 19.77,7.23M18,10A1,1 0 0,1 17,9A1,1 0 0,1 18,8A1,1 0 0,1 19,9A1,1 0 0,1 18,10M8,18V13.5H6L10,6V11H12L8,18Z"}></ha-svg-icon>
                <div class="row-main">
                  <div class="row-title">${t.name}</div>
                  ${e.length>0?I`<div class="row-sub">${e.join(" · ")}</div>`:K}
                </div>
                ${this.renderOnOff(t.activated,"status.activated","status.deactivated")}
              </div>
            `})}
        </div>
      </ha-card>
    `}chargerDetails(t){const e=this.config?.config.charging.chargers.find(e=>e.id===t.id),s=[];if(null!==t.current_a&&e&&s.push(this.localize("status.charging_current",{current:t.current_a,min:e.min_current_a,max:e.max_current_a})),t.bypassed&&s.push(this.localize("status.bypassed")),t.waiting&&s.push(this.localize("status.waiting_charger")),!t.allowed&&t.excluded?s.push(this.localize("status.excluded")):!t.allowed&&!1===t.excluded&&e?.charging_window&&s.push(this.localize("status.outside_window",{...e.charging_window})),t.waiting_until){const e=kt(t.waiting_until,this.clock.now);s.push(this.localize(t.activated?"status.waiting_to_increase":"status.waiting_to_activate",{time:e}))}return s}renderOnOff(t,e,s){return I`<span class="chip ${t?"on":"off"}"><span class="dot"></span>${this.localize(t?e:s)}</span>`}yesNo(t){return this.localize(t?"status.yes":"status.no")}renderStopped(t){return 0===t.missing.length?I`<ha-alert alert-type="info">${this.localize("status.stopped_info")}</ha-alert>`:I`
      <ha-alert alert-type="warning" .title=${this.localize("status.incomplete_title")}>
        <ul class="missing">
          ${t.missing.map(t=>{const e=function(t){return Ct[t.section]}(t);return I`
              <li>
                ${function(t,e,s){const i={item:zt(t,e,s),action:t.field&&Et[t.field]?s(Et[t.field]):t.field??"",code:t.code};return s(St[t.code]??"missing.unknown",i)}(t,this.config,this.localize)}
                <a href="${$t}/${e}" @click=${t=>this.openPage(t,e)}>
                  ${this.localize(`tabs.${e}`)}
                </a>
              </li>
            `})}
        </ul>
      </ha-alert>
    `}async changeRunning(t){this.changingRunning=!0,this.runningError=void 0;try{await((t,e)=>t.callWS({type:"kraftvakt/regulation/set_running",running:e}))(this.hass,t)}catch(t){this.runningError=gt(t)&&"config_incomplete"===t.code?this.localize("status.start_refused"):this.localize("panel.error",{message:gt(t)?t.message:String(t)})}finally{this.changingRunning=!1}}openPage(t,e){t.preventDefault(),yt(e)}static{this.styles=n`
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
  `}};t([dt({attribute:!1})],Ht.prototype,"hass",void 0),t([dt({attribute:!1})],Ht.prototype,"localize",void 0),t([dt({type:Boolean,reflect:!0})],Ht.prototype,"narrow",void 0),t([dt({attribute:!1})],Ht.prototype,"status",void 0),t([dt({attribute:!1})],Ht.prototype,"config",void 0),t([ut()],Ht.prototype,"changingRunning",void 0),t([ut()],Ht.prototype,"runningError",void 0),Ht=t([ct("kraftvakt-status-page")],Ht);const Pt={status:"M3,13H5.79L10.1,4.79L11.28,13.75L14.5,9.66L17.83,13H21V15H17L14.67,12.67L9.92,18.73L8.94,11.31L7,15H3V13Z",general:"M12,15.5A3.5,3.5 0 0,1 8.5,12A3.5,3.5 0 0,1 12,8.5A3.5,3.5 0 0,1 15.5,12A3.5,3.5 0 0,1 12,15.5M19.43,12.97C19.47,12.65 19.5,12.33 19.5,12C19.5,11.67 19.47,11.34 19.43,11L21.54,9.37C21.73,9.22 21.78,8.95 21.66,8.73L19.66,5.27C19.54,5.05 19.27,4.96 19.05,5.05L16.56,6.05C16.04,5.66 15.5,5.32 14.87,5.07L14.5,2.42C14.46,2.18 14.25,2 14,2H10C9.75,2 9.54,2.18 9.5,2.42L9.13,5.07C8.5,5.32 7.96,5.66 7.44,6.05L4.95,5.05C4.73,4.96 4.46,5.05 4.34,5.27L2.34,8.73C2.21,8.95 2.27,9.22 2.46,9.37L4.57,11C4.53,11.34 4.5,11.67 4.5,12C4.5,12.33 4.53,12.65 4.57,12.97L2.46,14.63C2.27,14.78 2.21,15.05 2.34,15.27L4.34,18.73C4.46,18.95 4.73,19.03 4.95,18.95L7.44,17.94C7.96,18.34 8.5,18.68 9.13,18.93L9.5,21.58C9.54,21.82 9.75,22 10,22H14C14.25,22 14.46,21.82 14.5,21.58L14.87,18.93C15.5,18.67 16.04,18.34 16.56,17.94L19.05,18.95C19.27,19.03 19.54,18.95 19.66,18.73L21.66,15.27C21.78,15.05 21.73,14.78 21.54,14.63L19.43,12.97Z",appliances:"M7,13V11H21V13H7M7,19V17H21V19H7M7,7V5H21V7H7M3,8V5H2V4H4V8H3M2,17V16H5V20H2V19H4V18.5H3V17.5H4V17H2M4.25,10A0.75,0.75 0 0,1 5,10.75C5,10.95 4.92,11.14 4.79,11.27L3.12,13H5V14H2V13.08L4,11H2V10H4.25Z",charging:"M18.92 2C18.72 1.42 18.16 1 17.5 1H6.5C5.84 1 5.29 1.42 5.08 2L3 8V16C3 16.55 3.45 17 4 17H5C5.55 17 6 16.55 6 16V15H18V16C18 16.55 18.45 17 19 17H20C20.55 17 21 16.55 21 16V8L18.92 2M6.5 12C5.67 12 5 11.33 5 10.5S5.67 9 6.5 9 8 9.67 8 10.5 7.33 12 6.5 12M17.5 12C16.67 12 16 11.33 16 10.5S16.67 9 17.5 9 19 9.67 19 10.5 18.33 12 17.5 12M5 7L6.5 2.5H17.5L19 7H5M7 20H11V18L17 21H13V23L7 20Z"};let Mt=class extends ot{constructor(){super(...arguments),this.narrow=!1,this.haElementsReady=!1,this.localize=vt("en")}connectedCallback(){super.connectedCallback(),customElements.whenDefined("ha-form").then(()=>{this.haElementsReady=!0}),this.hass&&this.subscribe()}disconnectedCallback(){super.disconnectedCallback(),this.unsubscribe()}willUpdate(t){t.has("hass")&&this.hass?.language!==t.get("hass")?.language&&(this.localize=vt(this.hass?.language??"en")),t.has("hass")&&this.hass&&!this.unsubscribeStatus&&this.subscribe()}updated(t){t.has("route")&&this.openAppliancesFromConfigureButton()}render(){if(!this.hass||!this.haElementsReady)return I``;const t=this.currentPage;return I`
      <div class="toolbar">
        <ha-menu-button .hass=${this.hass} .narrow=${this.narrow}></ha-menu-button>
        <div class="title">${this.localize("panel.title")}</div>
        <ha-tab-group @wa-tab-show=${this.tabShown}>
          ${Object.entries(Pt).map(([e,s])=>I`
              <ha-tab-group-tab slot="nav" panel=${e} .active=${e===t} title=${this.tabLabel(e)}>
                <ha-svg-icon .path=${s}></ha-svg-icon>
                <span class="tab-label">${this.tabLabel(e)}</span>
              </ha-tab-group-tab>
            `)}
        </ha-tab-group>
      </div>
      <div class="content">${this.renderLoadError()} ${this.renderPage(t)}</div>
    `}renderLoadError(){if(void 0===this.loadError)return"";const t=gt(this.loadError)&&"not_loaded"===this.loadError.code?this.localize("panel.not_loaded"):this.localize("panel.error",{message:(e=this.loadError,gt(e)?e.message:String(e))});var e;return I`<ha-alert alert-type="error">${t}</ha-alert>`}renderPage(t){switch(t){case"status":return I`
          <kraftvakt-status-page
            .hass=${this.hass}
            .localize=${this.localize}
            .narrow=${this.narrow}
            .status=${this.status}
            .config=${this.config}
          ></kraftvakt-status-page>
        `;case"general":case"appliances":case"charging":return I`<kraftvakt-placeholder-page .localize=${this.localize}></kraftvakt-placeholder-page>`}}get currentPage(){return function(t){const e=t.split("/")[1]??"";return mt.includes(e)?e:"status"}(this.route?.path??"")}tabLabel(t){return this.localize(`tabs.${t}`)}tabShown(t){t.detail.name!==this.currentPage&&yt(t.detail.name)}subscribe(){var t,e;this.hass&&(this.unsubscribeStatus=(t=this.hass,e=t=>this.statusReceived(t),t.connection.subscribeMessage(e,{type:"kraftvakt/status/subscribe"})),this.unsubscribeStatus.catch(t=>{this.loadError=t,this.unsubscribeStatus=void 0}))}unsubscribe(){this.unsubscribeStatus?.then(t=>t()).catch(()=>{}),this.unsubscribeStatus=void 0}statusReceived(t){const e=this.status;this.status=t,this.loadError=void 0,void 0!==e&&e.running===t.running&&JSON.stringify(e.missing)===JSON.stringify(t.missing)||this.loadConfig()}async loadConfig(){var t;if(this.hass)try{this.config=await(t=this.hass,t.callWS({type:"kraftvakt/config/get"}))}catch(t){this.loadError=t}}openAppliancesFromConfigureButton(){new URLSearchParams(window.location.search).has("config_entry")&&yt("appliances",{replace:!0})}static{this.styles=n`
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
  `}};t([dt({attribute:!1})],Mt.prototype,"hass",void 0),t([dt({type:Boolean,reflect:!0})],Mt.prototype,"narrow",void 0),t([dt({attribute:!1})],Mt.prototype,"route",void 0),t([ut()],Mt.prototype,"haElementsReady",void 0),t([ut()],Mt.prototype,"status",void 0),t([ut()],Mt.prototype,"config",void 0),t([ut()],Mt.prototype,"loadError",void 0),Mt=t([ct("kraftvakt-panel")],Mt);export{Mt as KraftvaktPanel};
