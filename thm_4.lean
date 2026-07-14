-- Assiomi standard della logica proposizionale
axiom ax1 (A B : Prop) : A → (B → A)
axiom ax2 (A B C : Prop) : (A → (B → C)) → ((A → B) → (A → C))
axiom ax3 (A B : Prop) : (¬A → ¬B) → (B → A)

-- Assiomi specifici del dominio
axiom gp_ax1 (Hom Ker : Prop) : (Hom → Ker)
axiom gp_ax2 (Ker Normal : Prop) : (Ker → Normal)
axiom gp_ax3 (Normal QuotientGroup : Prop) : (Normal → QuotientGroup)
axiom gp_ax4 (Hom InducedHom QuotientGroup : Prop) : (QuotientGroup → (Hom → InducedHom))
axiom gp_ax5 (Bijective Hom : Prop) : (Hom → Bijective)
axiom gp_ax6 (Bijective InducedHom Isomorphism : Prop) : (InducedHom → (Bijective → Isomorphism))
axiom gp_hyp_hom (Hom : Prop) : Hom

theorem thm_4 (Bijective Hom InducedHom Isomorphism Ker Normal QuotientGroup : Prop) : Isomorphism :=
  let step0 : Hom := gp_hyp_hom (Hom)
  let step1 : (Hom → Bijective) := gp_ax5 (Bijective) (Hom)
  let step2 : Bijective := step1 step0
  let step3 : (Hom → Ker) := gp_ax1 (Hom) (Ker)
  let step4 : Ker := step3 step0
  let step5 : (Ker → Normal) := gp_ax2 (Ker) (Normal)
  let step6 : Normal := step5 step4
  let step7 : (Normal → QuotientGroup) := gp_ax3 (Normal) (QuotientGroup)
  let step8 : QuotientGroup := step7 step6
  let step9 : (QuotientGroup → (Hom → InducedHom)) := gp_ax4 (Hom) (InducedHom) (QuotientGroup)
  let step10 : (Hom → InducedHom) := step9 step8
  let step11 : InducedHom := step10 step0
  let step12 : (InducedHom → (Bijective → Isomorphism)) := gp_ax6 (Bijective) (InducedHom) (Isomorphism)
  let step13 : (Bijective → Isomorphism) := step12 step11
  let step14 : Isomorphism := step13 step2
  step14