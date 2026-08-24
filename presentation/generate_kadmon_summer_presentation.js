const pptxgen = require('pptxgenjs');
const path = require('path');

const pptx = new pptxgen();
pptx.defineLayout({ name:'KADMON_WIDE', width:13.333, height:7.5 });
pptx.layout = 'KADMON_WIDE';
pptx.author = 'Projet KADMON';
pptx.company = 'Université du Québec en Outaouais';
pptx.subject = 'Progression scientifique du projet KADMON — été 2026';
pptx.title = 'KADMON — De la découverte de la tractographie à la cartographie de déviations';
pptx.lang = 'fr-CA';
pptx.theme = { headFontFace:'Aptos Display', bodyFontFace:'Aptos', lang:'fr-CA' };

const C={bg:'06151B',panel:'102831',panel2:'173640',ink:'F4FAFC',muted:'A8C1C9',teal:'22D3C5',cyan:'55BFFF',orange:'FF9B55',red:'FF6271',green:'7EE081',yellow:'F4D35E',grid:'31545E',white:'FFFFFF',black:'000000'};
const SH=pptx.ShapeType;
const root=path.resolve(__dirname,'..');
const asset=rel=>path.join(root,rel);
const noLine={color:C.bg,transparency:100};

function base(s,section,n){
  s.background={color:C.bg};
  s.addShape(SH.rect,{x:0,y:0,w:0.11,h:7.5,fill:{color:C.teal},line:noLine});
  s.addText(section.toUpperCase(),{x:0.38,y:0.18,w:5.4,h:0.2,fontSize:9.5,bold:true,charSpacing:1.5,color:C.teal,margin:0});
  s.addShape(SH.line,{x:0.38,y:7.05,w:12.1,h:0,line:{color:C.grid,pt:0.55}});
  s.addText(String(n).padStart(2,'0'),{x:12.35,y:7.09,w:0.42,h:0.16,fontSize:8.5,color:C.muted,align:'right',margin:0});
}
function title(s,t,sub){
  s.addText(t,{x:0.38,y:0.54,w:12.25,h:0.54,fontSize:27,bold:true,color:C.ink,margin:0,fit:'shrink'});
  if(sub)s.addText(sub,{x:0.4,y:1.12,w:11.95,h:0.32,fontSize:13.5,color:C.muted,margin:0,fit:'shrink'});
}
function notes(s,t){s.addNotes(t)}
function card(s,x,y,w,h,head,body,accent=C.teal,big=null){
  s.addShape(SH.roundRect,{x,y,w,h,rectRadius:0.07,fill:{color:C.panel},line:{color:C.grid,pt:0.8}});
  s.addShape(SH.rect,{x,y,w:0.055,h,fill:{color:accent},line:noLine});
  if(big)s.addText(big,{x:x+0.24,y:y+0.22,w:w-0.45,h:0.55,fontSize:27,bold:true,color:accent,margin:0,fit:'shrink'});
  s.addText(head,{x:x+0.24,y:y+(big?0.88:0.24),w:w-0.45,h:0.36,fontSize:15.5,bold:true,color:C.ink,margin:0,fit:'shrink'});
  s.addText(body,{x:x+0.24,y:y+(big?1.33:0.76),w:w-0.45,h:h-(big?1.55:1.0),fontSize:12.7,color:C.muted,margin:0,fit:'shrink',valign:'top'});
}
function pill(s,text,x,y,w,color=C.teal){
  s.addShape(SH.roundRect,{x,y,w,h:0.34,rectRadius:0.06,fill:{color,transparency:85},line:{color,pt:0.9}});
  s.addText(text,{x:x+0.07,y:y+0.08,w:w-0.14,h:0.15,fontSize:9.5,bold:true,color,align:'center',margin:0,fit:'shrink'});
}
function placeholder(s,x,y,w,h,label,sub='À insérer'){ 
  s.addShape(SH.roundRect,{x,y,w,h,rectRadius:0.06,fill:{color:C.panel,transparency:15},line:{color:C.cyan,pt:1.4,dash:'dash'}});
  s.addText(label,{x:x+0.25,y:y+h/2-0.3,w:w-0.5,h:0.3,fontSize:17,bold:true,color:C.cyan,align:'center',margin:0,fit:'shrink'});
  s.addText(sub,{x:x+0.25,y:y+h/2+0.12,w:w-0.5,h:0.22,fontSize:11,color:C.muted,align:'center',margin:0,fit:'shrink'});
}
function chevron(s,x,y,color=C.grid){s.addShape(SH.chevron,{x,y,w:0.32,h:0.58,fill:{color},line:noLine});}
function metric(s,x,y,w,label,value,color=C.teal){
  s.addShape(SH.roundRect,{x,y,w,h:0.95,fill:{color:C.panel2},line:{color:C.grid,pt:0.7},rectRadius:0.05});
  s.addText(value,{x:x+0.14,y:y+0.16,w:w-0.28,h:0.32,fontSize:21,bold:true,color,align:'center',margin:0,fit:'shrink'});
  s.addText(label,{x:x+0.14,y:y+0.59,w:w-0.28,h:0.16,fontSize:9.5,color:C.muted,align:'center',margin:0,fit:'shrink'});
}
function transition(s,n,before,but,after){
  base(s,'Transition',n);
  s.addText(before,{x:0.7,y:1.35,w:4.2,h:1.0,fontSize:28,bold:true,color:C.ink,align:'center',valign:'mid',margin:0,fit:'shrink'});
  s.addText('MAIS',{x:5.25,y:2.95,w:2.8,h:0.65,fontSize:38,bold:true,color:C.orange,align:'center',margin:0});
  s.addText(but,{x:4.08,y:3.75,w:5.15,h:0.85,fontSize:20,color:C.muted,align:'center',margin:0,fit:'shrink'});
  s.addShape(SH.downArrow,{x:6.22,y:4.75,w:0.85,h:0.85,fill:{color:C.teal},line:noLine});
  s.addText(after,{x:2.0,y:5.88,w:9.35,h:0.55,fontSize:25,bold:true,color:C.teal,align:'center',margin:0,fit:'shrink'});
}

// 1
{
 const s=pptx.addSlide();s.background={color:C.bg};
 s.addShape(SH.arc,{x:8.35,y:-1.1,w:5.9,h:5.9,adjustPoint:0.22,rotate:18,fill:{color:C.teal,transparency:83},line:{color:C.teal,pt:1.5,transparency:35}});
 s.addShape(SH.arc,{x:9.25,y:0.65,w:4.2,h:4.2,adjustPoint:0.22,rotate:205,fill:{color:C.orange,transparency:89},line:{color:C.orange,pt:1.2,transparency:45}});
 s.addText('KADMON',{x:0.7,y:1.35,w:7.2,h:0.82,fontSize:47,bold:true,color:C.ink,charSpacing:1.8,margin:0});
 s.addText('De la découverte de la tractographie\nà la cartographie de déviations',{x:0.72,y:2.45,w:7.35,h:1.18,fontSize:27,bold:true,color:C.ink,breakLine:false,margin:0,fit:'shrink'});
 s.addText('Une enquête scientifique en quatre mois',{x:0.72,y:3.95,w:5.5,h:0.4,fontSize:18,color:C.teal,margin:0});
 pill(s,'COMPRESSION',0.72,4.78,1.45,C.cyan);pill(s,'OPTIMAL TRANSPORT',2.35,4.78,2.0,C.orange);pill(s,'RE-ID',4.53,4.78,0.92,C.teal);pill(s,'DÉPLACEMENTS',5.63,4.78,1.52,C.green);
 s.addText('Projet d’été · UQO · supervision : Étienne St-Onge',{x:0.72,y:6.55,w:6.8,h:0.28,fontSize:11.5,color:C.muted,margin:0});
 notes(s,'30 secondes. Présenter le projet comme une progression : apprendre le domaine, choisir une question faisable, construire plusieurs pipelines et terminer avec une cartographie exploratoire des déplacements.');
}

// 2
{
 const s=pptx.addSlide();base(s,'Compréhension',2);title(s,'Au départ : deux mondes à apprendre en parallèle');
 card(s,0.6,1.55,3.55,4.75,'Représentation tractographique','streamline\nbundle\ntractogramme\nnorme L2\nMDF',C.cyan,'GÉOMÉTRIE');
 card(s,4.43,1.55,3.55,4.75,'Interprétation biologique','neurones et axones\nmatière blanche / grise\ncellules gliales\nlimites du signal indirect',C.green,'BIOLOGIE');
 placeholder(s,8.28,1.55,4.4,4.75,'IMAGE À AJOUTER','tractogramme + schéma matière blanche');
 s.addText('Comprendre ce que l’on calcule — et ce que les données représentent réellement.',{x:1.25,y:6.55,w:10.8,h:0.28,fontSize:13,bold:true,color:C.teal,align:'center',margin:0});
 notes(s,'35 secondes. Dire que la difficulté initiale était double : apprendre les objets mathématiques manipulés et comprendre leur relation avec la biologie. L’emplacement de droite peut recevoir une capture personnelle de tractogramme ou un schéma pédagogique.');
}

// 3
{
 const s=pptx.addSlide();base(s,'Compréhension',3);title(s,'Chaque réponse ouvrait trois nouvelles questions','État de l’art initial : Handbook of Diffusion MR Tractography · DIPY Workshop 2022');
 const nodes=[['diffusion MRI',1.0,1.85,C.teal],['DTI / DKI',4.05,1.65,C.cyan],['mouvement brownien',7.2,1.9,C.green],['acquisition',10.25,1.62,C.orange],['denoising',1.5,4.48,C.orange],['reconstruction',4.65,4.65,C.teal],['registration',7.8,4.42,C.cyan],['mathématiques',10.35,4.72,C.green]];
 nodes.forEach((d,i)=>{s.addShape(SH.ellipse,{x:d[1],y:d[2],w:2.0,h:0.86,fill:{color:C.panel2},line:{color:d[3],pt:1.2}});s.addText(d[0],{x:d[1]+0.14,y:d[2]+0.29,w:1.72,h:0.22,fontSize:13,bold:true,color:C.ink,align:'center',margin:0,fit:'shrink'});});
 [[2.9,2.25,1.1,0],[6.0,2.15,1.1,0],[9.15,2.18,1.0,0],[2.95,4.65,1.6,0],[6.65,4.67,1.1,0],[9.85,4.73,0.55,0]].forEach(l=>s.addShape(SH.line,{x:l[0],y:l[1],w:l[2],h:l[3],line:{color:C.grid,pt:1.2,dash:'dash',beginArrowType:'none',endArrowType:'triangle'}}));
 s.addShape(SH.line,{x:6.6,y:2.7,w:0,h:1.55,line:{color:C.grid,pt:1.2,dash:'dash',endArrowType:'triangle'}});
 s.addText('L’espace conceptuel grandissait plus vite que le temps disponible.',{x:2.1,y:6.25,w:9.2,h:0.46,fontSize:20,bold:true,color:C.orange,align:'center',margin:0});
 notes(s,'35 secondes. Montrer la croissance du périmètre : la tractographie entraîne vers l’acquisition, la reconstruction, les modèles de diffusion et la registration. Le message n’est pas de détailler chaque terme, mais de montrer pourquoi un choix de direction devenait nécessaire.');
}

// 4
{
 const s=pptx.addSlide();base(s,'Décision',4);
 s.addText('Curiosité scientifique',{x:0.9,y:1.1,w:4.5,h:0.55,fontSize:31,bold:true,color:C.cyan,align:'center',margin:0});
 s.addText('Temps expérimental',{x:7.85,y:1.1,w:4.5,h:0.55,fontSize:31,bold:true,color:C.orange,align:'center',margin:0});
 s.addShape(SH.line,{x:2.1,y:3.18,w:9.2,h:0,line:{color:C.ink,pt:3}});
 s.addShape(SH.triangle,{x:6.17,y:2.98,w:0.95,h:0.65,rotate:180,fill:{color:C.teal},line:noLine});
 s.addShape(SH.ellipse,{x:1.12,y:2.52,w:2.25,h:1.22,fill:{color:C.panel2},line:{color:C.cyan,pt:1.4}});s.addText('tout comprendre\nen profondeur',{x:1.37,y:2.82,w:1.75,h:0.48,fontSize:15,bold:true,color:C.ink,align:'center',margin:0});
 s.addShape(SH.ellipse,{x:9.95,y:2.52,w:2.25,h:1.22,fill:{color:C.panel2},line:{color:C.orange,pt:1.4}});s.addText('produire des\nrésultats vérifiables',{x:10.18,y:2.82,w:1.78,h:0.48,fontSize:15,bold:true,color:C.ink,align:'center',margin:0});
 s.addText('4 mois',{x:5.55,y:4.2,w:2.25,h:0.75,fontSize:39,bold:true,color:C.teal,align:'center',margin:0});
 s.addText('Choisir une question suffisamment fondamentale pour avancer — sans perdre la finalité biologique.',{x:1.35,y:5.65,w:10.65,h:0.7,fontSize:23,bold:true,color:C.ink,align:'center',margin:0,fit:'shrink'});
 notes(s,'30 secondes. C’est le pivot narratif : il était impossible de tout maîtriser et d’avancer expérimentalement en quatre mois. Il fallait réduire le problème sans abandonner l’objectif à long terme.');
}

// 5
{
 const s=pptx.addSlide();base(s,'Question initiale',5);title(s,'KADMON devait d’abord chercher la déviation pathologique');
 s.addText('Knowledge-driven Atlas for Deviation Mapping of Neural Organization',{x:0.65,y:1.35,w:12.0,h:0.35,fontSize:15,color:C.muted,align:'center',margin:0});
 card(s,0.7,2.0,3.4,3.5,'Référence saine','Human Connectome Project\nDonnées saines disponibles',C.green,'HCP');
 chevron(s,4.34,3.25,C.grid);
 card(s,4.85,2.0,3.55,3.5,'Question envisagée','Comparer normal et pathologique\nLocaliser les différences de matière blanche',C.teal,'Δ');
 chevron(s,8.64,3.25,C.grid);
 card(s,9.15,2.0,3.45,3.5,'Cohorte pathologique','Parkinson’s Progression Markers Initiative\nAccès soumis à démarches',C.orange,'PPMI');
 s.addShape(SH.roundRect,{x:3.05,y:5.95,w:7.2,h:0.58,fill:{color:C.red,transparency:84},line:{color:C.red,pt:1}});
 s.addText('Dataset public ≠ accès immédiat · irréaliste dans le calendrier disponible',{x:3.25,y:6.13,w:6.8,h:0.2,fontSize:12.5,bold:true,color:C.red,align:'center',margin:0});
 notes(s,'40 secondes. Expliquer le nom initial et l’ambition HCP contre PPMI. Le blocage n’était pas scientifique seulement : l’accès aux données PPMI exige des démarches incompatibles avec le calendrier.');
}

// 6
{
 const s=pptx.addSlide();base(s,'Reformulation',6);title(s,'Avant la pathologie, vérifier l’identité géométrique');
 s.addText('Question trop tôt',{x:0.75,y:1.65,w:3.15,h:0.35,fontSize:16,bold:true,color:C.orange,align:'center',margin:0});
 s.addShape(SH.roundRect,{x:0.65,y:2.15,w:3.35,h:2.45,fill:{color:C.panel},line:{color:C.orange,pt:1.2}});s.addText('Sain\nvs\npathologique',{x:1.02,y:2.72,w:2.62,h:1.12,fontSize:23,bold:true,color:C.ink,align:'center',margin:0,fit:'shrink'});
 s.addShape(SH.rightArrow,{x:4.35,y:2.88,w:1.3,h:0.65,fill:{color:C.teal},line:noLine});
 s.addText('Question de validation',{x:5.85,y:1.65,w:6.2,h:0.35,fontSize:16,bold:true,color:C.teal,align:'center',margin:0});
 s.addShape(SH.roundRect,{x:5.75,y:2.15,w:6.45,h:2.45,fill:{color:C.panel2},line:{color:C.teal,pt:1.2}});
 s.addText('Même individu',{x:6.12,y:2.68,w:2.35,h:0.35,fontSize:22,bold:true,color:C.green,align:'center',margin:0});s.addText('≠',{x:8.55,y:2.64,w:0.75,h:0.45,fontSize:31,bold:true,color:C.ink,align:'center',margin:0});s.addText('Individus différents',{x:9.25,y:2.68,w:2.55,h:0.35,fontSize:22,bold:true,color:C.orange,align:'center',margin:0});
 s.addText('intra-sujet : retest reconnu',{x:6.15,y:3.65,w:2.4,h:0.26,fontSize:13,color:C.muted,align:'center',margin:0});s.addText('inter-sujet : séparé',{x:9.35,y:3.65,w:2.25,h:0.26,fontSize:13,color:C.muted,align:'center',margin:0});
 s.addText('RE-ID = test de cohérence du pipeline, pas nouvelle finalité du projet.',{x:2.0,y:5.45,w:9.35,h:0.5,fontSize:22,bold:true,color:C.ink,align:'center',margin:0});
 s.addText('Question centrale : comparer deux bundles tout en conservant une cohérence anatomique.',{x:1.2,y:6.25,w:10.9,h:0.35,fontSize:15,color:C.teal,align:'center',margin:0});
 notes(s,'45 secondes. Présenter la reformulation proposée avec Étienne comme une étape logique de validation : avant de chercher une différence pathologique, le pipeline doit reconnaître la répétition d’un individu et séparer les individus différents.');
}

// 7
{
 const s=pptx.addSlide();base(s,'Optimal Transport',7);title(s,'Comparer des distributions de représentants');
 card(s,0.55,1.7,2.5,3.8,'Source','Représentants xᵢ\nMasses aᵢ',C.cyan,'A');
 s.addShape(SH.rightArrow,{x:3.25,y:3.0,w:0.75,h:0.5,fill:{color:C.grid},line:noLine});
 card(s,4.15,1.7,2.5,3.8,'Coût','Matrice Cᵢⱼ\nDistance MDF entre streamlines',C.orange,'C');
 s.addShape(SH.rightArrow,{x:6.85,y:3.0,w:0.75,h:0.5,fill:{color:C.grid},line:noLine});
 card(s,7.75,1.7,2.5,3.8,'Transport','Plan Pᵢⱼ\nQuelle masse va où ?',C.teal,'P');
 s.addShape(SH.rightArrow,{x:10.45,y:3.0,w:0.75,h:0.5,fill:{color:C.grid},line:noLine});
 card(s,11.35,1.7,1.42,3.8,'Cible','yⱼ\nbⱼ',C.green,'B');
 s.addText('minimiser  Σ Pᵢⱼ · Cᵢⱼ',{x:3.9,y:5.95,w:5.55,h:0.52,fontSize:23,bold:true,color:C.ink,align:'center',margin:0});
 s.addText('L’OT cherche un transport peu coûteux — pas nécessairement un appariement 1 à 1.',{x:2.0,y:6.55,w:9.35,h:0.28,fontSize:12.5,color:C.teal,align:'center',margin:0});
 notes(s,'50 secondes. Introduire uniquement les objets nécessaires : représentants, masses, coût MDF et plan de transport. Insister sur le fait qu’un plan répartit de la masse et n’est pas un matching strict.');
}

// 8
{
 const s=pptx.addSlide();base(s,'Première solution',8);title(s,'QuickBundles + Partial OT','Compresser d’abord; comparer seulement la fraction de masse la plus cohérente.');
 card(s,0.65,1.65,3.45,4.6,'QuickBundles','Regrouper les streamlines proches\n→ centroïdes\n→ poids proportionnels aux clusters',C.cyan,'COMPRESSION');
 chevron(s,4.3,3.45);
 card(s,4.85,1.65,3.45,4.6,'Masses empiriques','aᵢ = nᵢ / N\n\nnᵢ : taille du cluster\nN : streamlines du bundle',C.green,'POIDS');
 chevron(s,8.5,3.45);
 card(s,9.05,1.65,3.45,4.6,'Partial OT','Transporter une masse m < 1\nIgnorer les correspondances les plus coûteuses',C.orange,'m');
 s.addText('Hypothèse : la portion commune du bundle suffit pour reconnaître l’identité.',{x:1.2,y:6.55,w:10.9,h:0.3,fontSize:13,bold:true,color:C.ink,align:'center',margin:0});
 notes(s,'45 secondes. Montrer pourquoi les poids doivent refléter les tailles de clusters. Partial OT peut laisser de côté une partie de la masse, ce qui rend la comparaison robuste aux portions mal expliquées.');
}

// 9
{
 const s=pptx.addSlide();base(s,'Optuna · QB + Partial OT',9);title(s,'Premier pipeline fonctionnel — mais un compromis apparaît');
 metric(s,0.65,1.55,2.3,'RE-ID Top-1','93,55 %',C.teal);metric(s,3.15,1.55,2.3,'rang intra moyen','1,097',C.cyan);metric(s,5.65,1.55,2.3,'masse transportée','0,99',C.orange);metric(s,8.15,1.55,2.3,'représentants moyens','296',C.green);metric(s,10.65,1.55,2.05,'trial anatomique','75',C.yellow);
 s.addShape(SH.roundRect,{x:0.65,y:2.85,w:7.7,h:2.85,fill:{color:C.panel},line:{color:C.grid,pt:0.8}});
 s.addText('Pourquoi trial 75 ?', {x:0.95,y:3.15,w:2.6,h:0.35,fontSize:18,bold:true,color:C.ink,margin:0});
 s.addText('seuil = 7 mm',{x:1.0,y:3.9,w:1.7,h:0.35,fontSize:18,bold:true,color:C.cyan,margin:0});s.addText('masse = 0,99',{x:3.0,y:3.9,w:1.8,h:0.35,fontSize:18,bold:true,color:C.orange,margin:0});
 s.addText('Résolution anatomique substantielle + couverture presque complète, tout en conservant une RE-ID forte.',{x:1.0,y:4.65,w:6.75,h:0.55,fontSize:15,color:C.muted,margin:0,fit:'shrink'});
 s.addShape(SH.roundRect,{x:8.65,y:2.85,w:4.05,h:2.85,fill:{color:C.panel2},line:{color:C.orange,pt:1}});
 s.addText('Bundles non ré-identifiés',{x:8.95,y:3.22,w:3.45,h:0.35,fontSize:17,bold:true,color:C.orange,align:'center',margin:0});
 s.addText('CST_L  ·  IFOF_R',{x:9.08,y:4.12,w:3.2,h:0.48,fontSize:25,bold:true,color:C.ink,align:'center',margin:0});
 s.addText('Aucune cause anatomique démontrée.',{x:9.15,y:4.92,w:3.05,h:0.24,fontSize:11,color:C.muted,align:'center',margin:0});
 s.addText('La petite taille de certains bundles est une hypothèse à tester, pas une conclusion.',{x:1.35,y:6.42,w:10.65,h:0.36,fontSize:12,color:C.orange,align:'center',margin:0});
 notes(s,'45 secondes. Chiffres extraits du trial Optuna 75. Mentionner CST_L et IFOF_R sans proposer d’explication causale. La taille du bundle peut être une hypothèse, mais elle n’est pas démontrée ici.');
}

// 10
{
 const s=pptx.addSlide();transition(s,10,'QuickBundles fonctionne','cardinalité variable · seuil à ajuster · centroïdes artificiels','Il faut mieux contrôler les représentants');
 s.addText('Le nombre de représentants dépend du threshold et de la géométrie propre à chaque sujet.',{x:2.0,y:1.95,w:9.3,h:0.44,fontSize:15,color:C.muted,align:'center',margin:0});
 notes(s,'25 secondes. Transition nette : le pipeline fonctionne, mais le budget de représentants varie entre sujets et les centroïdes ne sont pas forcément de vraies streamlines.');
}

// 11
{
 const s=pptx.addSlide();base(s,'Piste abandonnée',11);title(s,'K-Médoïdes : anatomiquement séduisant, computationnellement prohibitif');
 card(s,0.75,1.65,4.9,4.65,'L’idée','Choisir les représentants parmi les observations existantes.\n\n✓ vraies streamlines\n✓ interprétation directe',C.green,'MÉDOÏDES');
 s.addShape(SH.rightArrow,{x:5.95,y:3.2,w:1.35,h:0.72,fill:{color:C.red},line:noLine});
 card(s,7.65,1.65,4.9,4.65,'Le coût','Matrice de distances et optimisation trop coûteuses à l’échelle des tractogrammes.\n\nPiste arrêtée avant expérimentation complète.',C.red,'COÛT');
 s.addText('Bonne propriété des représentants ≠ méthode exploitable à l’échelle.',{x:2.0,y:6.55,w:9.35,h:0.3,fontSize:14,bold:true,color:C.ink,align:'center',margin:0});
 notes(s,'30 secondes. Ne pas afficher de temps précis : les notebooks historiques ne fournissent pas un benchmark K-médoïdes propre et comparable. Présenter uniquement la raison computationnelle de l’abandon.');
}

// 12
{
 const s=pptx.addSlide();base(s,'Amélioration',12);title(s,'K-Means + Partial OT : imposer exactement K');
 card(s,0.65,1.65,3.45,4.6,'Ce qui change','K est fixé à l’avance.\nLe budget de représentants devient contrôlable entre sujets.',C.cyan,'K = 40');
 chevron(s,4.28,3.45);
 card(s,4.82,1.65,3.45,4.6,'Optuna trial 44','masse = 0,63\n40 représentants\nratio intra/inter = 0,346',C.orange,'TRIAL 44');
 chevron(s,8.45,3.45);
 card(s,9.0,1.65,3.6,4.6,'Résultat RE-ID','31 bundles correctement ré-identifiés dans cette expérience.\n\nPas une preuve de généralisation.',C.green,'100 %');
 s.addText('CST_L est correctement identifié dans ce protocole.',{x:3.5,y:6.52,w:6.35,h:0.3,fontSize:13,bold:true,color:C.teal,align:'center',margin:0});
 notes(s,'50 secondes. Résultat extrait du trial Optuna 44 : K=40, masse 0,63, Top-1 100 %. Souligner que cela démontre que la représentation compressée conserve suffisamment d’information dans cette expérience, pas que la méthode généralisera.');
}

// 13
{
 const s=pptx.addSlide();transition(s,13,'La cardinalité est maintenant contrôlée','le centroïde moyen peut ne correspondre à aucune streamline réelle','Le score global ne suffit plus');
 notes(s,'25 secondes. Même avec 100 % de RE-ID, la question anatomique reste ouverte : QuickBundles et K-Means produisent des représentants artificiels.');
}

// 14
{
 const s=pptx.addSlide();base(s,'Nouvelle piste',14);title(s,'Sinkhorn guide; LDDMM déforme');
 card(s,0.65,1.6,3.65,4.75,'Sinkhorn','Optimal Transport régularisé entropiquement.\n\nTransport « soft » : une source peut distribuer sa masse vers plusieurs cibles.\n\nCalculs MDF et OT accélérables sur GPU.',C.teal,'GUIDAGE');
 s.addText('≠',{x:4.52,y:2.88,w:1.05,h:0.8,fontSize:42,bold:true,color:C.red,align:'center',margin:0});
 card(s,5.78,1.6,3.05,4.75,'Plan OT','Correspondances pondérées.\n\nIl ne constitue pas à lui seul un champ de déformation anatomiquement valide.',C.orange,'P');
 s.addShape(SH.rightArrow,{x:9.05,y:3.12,w:0.75,h:0.62,fill:{color:C.grid},line:noLine});
 card(s,10.02,1.6,2.65,4.75,'LDDMM','Transformation continue et diffeomorphe.\n\nChemin géodésique dans l’espace des transformations.',C.green,'φ');
 s.addText('Piste inspirée par « Optimal Transport for Diffeomorphic Registration »',{x:2.1,y:6.52,w:9.1,h:0.3,fontSize:12.5,color:C.muted,align:'center',margin:0});
 notes(s,'55 secondes. Formulation importante : Sinkhorn n’est pas un matching presque un-à-un. La régularisation entropique diffuse le transport. Le plan peut guider LDDMM, mais plan OT et champ diffeomorphe sont des objets différents.');
}

// 15
{
 const s=pptx.addSlide();base(s,'Expériences Sinkhorn',15);title(s,'Une piste prometteuse — mais hors scope pour une validation complète');
 card(s,0.65,1.55,3.75,3.05,'QuickBundles + Sinkhorn','trial 114\nseuil = 6 mm\nε = 0,087448\n≈ 538 représentants',C.cyan,'90,32 %');
 card(s,4.8,1.55,3.75,3.05,'K-Means + Sinkhorn','trial 130\nK = 155\nε = 0,017737\n≈ 154 représentants',C.teal,'93,55 %');
 card(s,8.95,1.55,3.75,3.05,'Échecs observés','Selon le profil ou le budget :\nCST_L · ICP_L\nIFOF_L · IFOF_R',C.orange,'BUNDLES');
 s.addShape(SH.roundRect,{x:1.05,y:5.08,w:11.15,h:1.03,fill:{color:C.panel2},line:{color:C.red,pt:1}});
 s.addText('LDDMM : exploré dans des notebooks diagnostiques, mais non validé ni intégré au KADMON final.',{x:1.45,y:5.4,w:10.35,h:0.35,fontSize:17,bold:true,color:C.red,align:'center',margin:0,fit:'shrink'});
 s.addText('Le coût scientifique de cette direction dépassait le temps restant.',{x:2.2,y:6.45,w:8.9,h:0.28,fontSize:13,color:C.muted,align:'center',margin:0});
 notes(s,'45 secondes. Les valeurs viennent des trials anatomiques Optuna. La liste agrège les échecs observés dans les profils Sinkhorn et l’analyse à budget comparable. Dire clairement que LDDMM n’est pas une réussite du projet final.');
}

// 16
{
 const s=pptx.addSlide();base(s,'Nouvelle représentation',16);title(s,'TractoSearch Binning : chercher un compromis');
 const xs=[0.65,4.78,8.91];
 card(s,xs[0],1.55,3.75,4.8,'QuickBundles','Cardinalité dépendante du seuil et du bundle.\n\nCompression paire exemple :\n0,12 s Partial · 0,19 s Sinkhorn',C.cyan,'RAPIDE');
 card(s,xs[1],1.55,3.75,4.8,'K-Means','Cardinalité K contrôlée.\n\nCompression paire exemple :\n2,24 s Partial · 3,21 s Sinkhorn',C.orange,'CONTRÔLE');
 card(s,xs[2],1.55,3.75,4.8,'Binning','Cardinalité issue d’une discrétisation spatiale.\n\nCompression paire exemple :\n1,18 s Partial · 1,21 s Sinkhorn',C.teal,'COMPROMIS');
 s.addText('Profils Optuna Binning : Partial OT 96,77 % · Sinkhorn 96,77 %',{x:2.1,y:6.52,w:9.1,h:0.3,fontSize:14,bold:true,color:C.ink,align:'center',margin:0});
 notes(s,'45 secondes. Le qualificatif « intermédiaire » s’applique au temps de compression observé sur la paire 103818→135528 du notebook de comparaison : environ 1,2 s, contre 0,1–0,2 s pour QuickBundles et 2,2–3,2 s pour K-Means. Ne pas le généraliser comme benchmark universel.');
}

// 17
{
 const s=pptx.addSlide();base(s,'Comparaison finale',17);title(s,'Six profils anatomiques Optuna','La performance ne se résume ni au transport, ni au nombre de représentants.');
 const labels=['QB +\nPartial','QB +\nSinkhorn','KM +\nPartial','KM +\nSinkhorn','Bin +\nPartial','Bin +\nSinkhorn'];
 const vals=[93.55,90.32,100,93.55,96.77,96.77];
 s.addChart(pptx.ChartType.bar,[{name:'RE-ID',labels,values:vals}],{x:0.55,y:1.5,w:7.35,h:4.85,catAxisLabelColor:C.muted,catAxisLabelFontSize:11,valAxisLabelColor:C.muted,valAxisLabelFontSize:9,valAxisMinVal:80,valAxisMaxVal:100,valAxisMajorUnit:5,showLegend:false,chartColors:[C.teal],showValue:true,dataLabelColor:C.ink,dataLabelPosition:'outEnd',dataLabelFormatCode:'0.00" %"',showGridLines:true,gridLine:{color:C.grid,pt:0.6},chartArea:{fill:{color:C.bg,transparency:100},line:{color:C.bg,transparency:100}},plotArea:{fill:{color:C.bg,transparency:100},line:{color:C.bg,transparency:100}}});
 const rows=[['Profil','Représ. moy.','m / ε'],['QB + Partial','296','0,99'],['QB + Sinkhorn','538','0,0874'],['KM + Partial','40','0,63'],['KM + Sinkhorn','154','0,0177'],['Bin + Partial','147','0,68'],['Bin + Sinkhorn','986','0,0252']];
 s.addTable(rows,{x:8.15,y:1.65,w:4.55,h:4.55,colW:[1.75,1.35,1.15],rowH:0.54,border:{color:C.grid,pt:0.7},fill:C.panel,color:C.muted,fontSize:11.5,margin:[0.07,0.09,0.05,0.09],valign:'mid'});
 s.addText('Les profils privilégient la couverture et la résolution anatomique tout en conservant une RE-ID forte.',{x:1.25,y:6.48,w:10.8,h:0.3,fontSize:12.5,color:C.teal,align:'center',margin:0});
 notes(s,'50 secondes. Valeurs extraites des six trials documentés dans le README et la base Optuna. Les nombres de représentants sont des moyennes sur l’étude, tandis que les paramètres sont ceux des profils anatomiques.');
}

// 18
{
 const s=pptx.addSlide();base(s,'Limites scientifiques',18);title(s,'Que mesure réellement le pipeline ?');
 const items=[['Acquisition','séquences et résolution',C.cyan],['Reconstruction','algorithme et paramètres',C.orange],['Datasets','protocoles non harmonisés',C.red],['Coordonnées','RASMM et transformations',C.teal],['Registration','alignement des streamlines',C.green],['Variabilité','inter-sujet / intra-sujet',C.yellow],['Distance','MDF et alternatives',C.cyan],['Compression + OT','représentants, m et ε',C.orange]];
 items.forEach((d,i)=>{const col=i%4,row=Math.floor(i/4),x=0.55+col*3.15,y=1.55+row*1.55;s.addShape(SH.roundRect,{x,y,w:2.75,h:1.15,fill:{color:C.panel},line:{color:d[2],pt:1},rectRadius:0.06});s.addText(d[0],{x:x+0.18,y:y+0.18,w:2.39,h:0.25,fontSize:15,bold:true,color:d[2],align:'center',margin:0});s.addText(d[1],{x:x+0.18,y:y+0.64,w:2.39,h:0.2,fontSize:10.5,color:C.muted,align:'center',margin:0,fit:'shrink'});});
 s.addShape(SH.roundRect,{x:1.0,y:5.0,w:11.25,h:1.18,fill:{color:C.red,transparency:86},line:{color:C.red,pt:1.1}});
 s.addText('Risque majeur',{x:1.35,y:5.3,w:1.8,h:0.32,fontSize:17,bold:true,color:C.red,margin:0});
 s.addText('mesurer une différence de pipeline ou d’acquisition plutôt que la différence biologique recherchée',{x:3.0,y:5.26,w:8.75,h:0.42,fontSize:18,bold:true,color:C.ink,margin:0,fit:'shrink'});
 s.addText('Une comparaison pathologique exigera une harmonisation et des contrôles beaucoup plus stricts.',{x:1.65,y:6.55,w:10.0,h:0.28,fontSize:12.5,color:C.muted,align:'center',margin:0});
 notes(s,'45 secondes. Slide d’honnêteté scientifique. Le principal risque est le confounding : si les datasets sont acquis ou reconstruits différemment, la métrique peut détecter le pipeline plutôt que la biologie.');
}

// 19
{
 const s=pptx.addSlide();base(s,'Projection barycentrique',19);title(s,'Le plan de transport suggère une position cible','Une estimation locale simple — pas une déformation anatomique validée.');
 card(s,0.7,1.75,3.45,4.4,'1 · Lire une ligne du plan','Pour la source xᵢ, la ligne Pᵢⱼ indique quelle masse est envoyée vers chaque cible yⱼ.',C.cyan,'Pᵢ·');
 chevron(s,4.35,3.55);
 card(s,4.9,1.75,3.55,4.4,'2 · Faire le barycentre','x̂ᵢ = Σⱼ Pᵢⱼ yᵢⱼ* / Σⱼ Pᵢⱼ\n\nLes cibles sont orientées relativement à la source avant la moyenne.',C.teal,'x̂ᵢ');
 chevron(s,8.65,3.55);
 card(s,9.2,1.75,3.45,4.4,'3 · Calculer le déplacement','dᵢ = x̂ᵢ − xᵢ\n\nLa norme de dᵢ donne une magnitude locale en millimètres.',C.orange,'dᵢ');
 s.addText('RASMM commun requis   ·   projection suggérée par OT   ·   aucune garantie diffeomorphique',{x:1.05,y:6.52,w:11.25,h:0.3,fontSize:12.5,bold:true,color:C.muted,align:'center',margin:0});
 notes(s,'45 secondes. Pour chaque représentant source, on prend la ligne correspondante du plan OT. Les masses de cette ligne servent de poids pour calculer le barycentre des cibles orientées. La différence entre cette projection et la source donne le déplacement estimé. Le calcul exige un espace physique commun RASMM et ne garantit ni continuité ni inversibilité.');
}

// 20
{
 const s=pptx.addSlide();base(s,'Animation',20);title(s,'De la source à la projection barycentrique');
 placeholder(s,0.65,1.45,12.0,4.95,'VIDÉO FURY À INSÉRER','source → déplacement → projection barycentrique');
 s.addText('P(t) = (1 − t) P_source + t P_projection',{x:3.15,y:5.8,w:7.0,h:0.44,fontSize:21,bold:true,color:C.ink,align:'center',margin:0});
 s.addText('Interpolation linéaire pour la visualisation — pas trajectoire LDDMM.',{x:2.25,y:6.5,w:8.85,h:0.28,fontSize:12.5,color:C.orange,align:'center',margin:0});
 notes(s,'30 à 45 secondes selon la vidéo. Remplacer le cadre par la vidéo FURY existante. L’animation interpole linéairement les positions; elle ne représente pas un chemin géodésique ni une déformation anatomiquement contrainte.');
}

// 21
{
 const s=pptx.addSlide();base(s,'Conclusion',21);title(s,'Ce que quatre mois ont permis d’établir');
 const points=[['Pipeline RE-ID','fonctionnel',C.green],['3 compressions','QB · K-Means · Binning',C.cyan],['2 transports','Partial OT · Sinkhorn',C.orange],['Meilleur essai','K-Means + Partial : 100 %',C.teal],['Cardinalité','importante, mais non suffisante',C.yellow],['Projection OT','visualisation barycentrique',C.cyan],['Limite centrale','plan OT ≠ déformation valide',C.red],['Finalité','préparer la comparaison pathologique',C.green]];
 points.forEach((d,i)=>{const col=i%4,row=Math.floor(i/4),x=0.55+col*3.15,y=1.55+row*1.55;s.addShape(SH.roundRect,{x,y,w:2.75,h:1.15,fill:{color:C.panel},line:{color:d[2],pt:1},rectRadius:0.06});s.addText(d[0],{x:x+0.16,y:y+0.18,w:2.43,h:0.25,fontSize:14.5,bold:true,color:d[2],align:'center',margin:0});s.addText(d[1],{x:x+0.16,y:y+0.62,w:2.43,h:0.24,fontSize:10.5,color:C.muted,align:'center',margin:0,fit:'shrink'});});
 s.addText('Plusieurs pipelines de compression + OT contiennent suffisamment d’information pour distinguer les sujets dans le protocole étudié.',{x:1.0,y:5.0,w:11.25,h:0.58,fontSize:20,bold:true,color:C.ink,align:'center',margin:0,fit:'shrink'});
 s.addText('Suite : données pathologiques · harmonisation · registration · vraies streamlines · Sinkhorn + LDDMM · validation anatomique',{x:0.8,y:6.25,w:11.7,h:0.38,fontSize:12.5,color:C.teal,align:'center',margin:0,fit:'shrink'});
 notes(s,'50 secondes. La conclusion globale est la construction et la comparaison des pipelines, pas seulement le score maximal. Le projet établit une première validation d’identité géométrique et ouvre la voie vers la comparaison pathologique, sous réserve d’harmonisation et de validation anatomique.');
}

// 22
{
 const s=pptx.addSlide();s.background={color:C.bg};
 s.addShape(SH.arc,{x:8.55,y:-0.8,w:5.4,h:5.4,adjustPoint:0.2,rotate:22,fill:{color:C.teal,transparency:84},line:{color:C.teal,pt:1.4,transparency:40}});
 s.addText('Questions ?',{x:0.85,y:2.45,w:7.2,h:0.95,fontSize:50,bold:true,color:C.ink,margin:0});
 s.addText('KADMON',{x:0.9,y:3.62,w:3.0,h:0.4,fontSize:19,bold:true,color:C.teal,charSpacing:1.5,margin:0});
 s.addText('Compression · Optimal Transport · RE-ID · cartographie locale',{x:0.9,y:4.28,w:6.6,h:0.3,fontSize:13,color:C.muted,margin:0});
 notes(s,'Questions.');
}

pptx.writeFile({fileName:path.join(__dirname,'KADMON_ete_progression_scientifique.pptx'),compression:true});
