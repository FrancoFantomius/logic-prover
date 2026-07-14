namespace Analysis1

set_option linter.unusedVariables false

-- Assiomi standard della logica proposizionale
axiom ax1 (A B : Prop) : A → (B → A)
axiom ax2 (A B C : Prop) : (A → (B → C)) → ((A → B) → (A → C))
axiom ax3 (A B : Prop) : (¬A → ¬B) → (B → A)

-- Assiomi specifici di Analisi 1
axiom an_ax1 (Complete MonotoneConvergence OrderedField : Prop) : (OrderedField → (Complete → MonotoneConvergence))
axiom an_ax2 (MonotoneConvergence NestedIntervals OrderedField : Prop) : (OrderedField → (MonotoneConvergence → NestedIntervals))
axiom an_ax3 (Archimedean CauchyComplete NestedIntervals OrderedField : Prop) : (OrderedField → (NestedIntervals → (Archimedean → CauchyComplete)))
axiom an_ax4 (Archimedean BolzanoWeierstrass CauchyComplete OrderedField : Prop) : (OrderedField → (CauchyComplete → (Archimedean → BolzanoWeierstrass)))
axiom an_ax5 (BolzanoWeierstrass HeineBorel OrderedField : Prop) : (OrderedField → (BolzanoWeierstrass → HeineBorel))
axiom an_ax6 (HeineBorel IntermediateValue OrderedField : Prop) : (OrderedField → (HeineBorel → IntermediateValue))
axiom an_hyp_arch (Archimedean : Prop) : Archimedean
axiom an_hyp_complete (Complete : Prop) : Complete
axiom an_hyp_field (OrderedField : Prop) : OrderedField

theorem thm_1 (A Archimedean B BolzanoWeierstrass C CauchyComplete Complete HeineBorel IntermediateValue MonotoneConvergence NestedIntervals OrderedField : Prop) : MonotoneConvergence :=
  let step0 : Complete := an_hyp_complete (Complete)
  let step1 : OrderedField := an_hyp_field (OrderedField)
  let step2 : (OrderedField → (Complete → MonotoneConvergence)) := an_ax1 (Complete) (MonotoneConvergence) (OrderedField)
  let step3 : (Complete → MonotoneConvergence) := step2 step1
  let step4 : MonotoneConvergence := step3 step0
  step4

theorem thm_2 (A Archimedean B BolzanoWeierstrass C CauchyComplete Complete HeineBorel IntermediateValue MonotoneConvergence NestedIntervals OrderedField : Prop) : NestedIntervals :=
  let step0 : MonotoneConvergence := thm_1 (A) (Archimedean) (B) (BolzanoWeierstrass) (C) (CauchyComplete) (Complete) (HeineBorel) (IntermediateValue) (MonotoneConvergence) (NestedIntervals) (OrderedField)
  let step1 : OrderedField := an_hyp_field (OrderedField)
  let step2 : (OrderedField → (MonotoneConvergence → NestedIntervals)) := an_ax2 (MonotoneConvergence) (NestedIntervals) (OrderedField)
  let step3 : (MonotoneConvergence → NestedIntervals) := step2 step1
  let step4 : NestedIntervals := step3 step0
  step4

theorem thm_3 (A Archimedean B BolzanoWeierstrass C CauchyComplete Complete HeineBorel IntermediateValue MonotoneConvergence NestedIntervals OrderedField : Prop) : CauchyComplete :=
  let step0 : Archimedean := an_hyp_arch (Archimedean)
  let step1 : NestedIntervals := thm_2 (A) (Archimedean) (B) (BolzanoWeierstrass) (C) (CauchyComplete) (Complete) (HeineBorel) (IntermediateValue) (MonotoneConvergence) (NestedIntervals) (OrderedField)
  let step2 : OrderedField := an_hyp_field (OrderedField)
  let step3 : (OrderedField → (NestedIntervals → (Archimedean → CauchyComplete))) := an_ax3 (Archimedean) (CauchyComplete) (NestedIntervals) (OrderedField)
  let step4 : (NestedIntervals → (Archimedean → CauchyComplete)) := step3 step2
  let step5 : (Archimedean → CauchyComplete) := step4 step1
  let step6 : CauchyComplete := step5 step0
  step6

theorem thm_4 (A Archimedean B BolzanoWeierstrass C CauchyComplete Complete HeineBorel IntermediateValue MonotoneConvergence NestedIntervals OrderedField : Prop) : BolzanoWeierstrass :=
  let step0 : Archimedean := an_hyp_arch (Archimedean)
  let step1 : CauchyComplete := thm_3 (A) (Archimedean) (B) (BolzanoWeierstrass) (C) (CauchyComplete) (Complete) (HeineBorel) (IntermediateValue) (MonotoneConvergence) (NestedIntervals) (OrderedField)
  let step2 : OrderedField := an_hyp_field (OrderedField)
  let step3 : (OrderedField → (CauchyComplete → (Archimedean → BolzanoWeierstrass))) := an_ax4 (Archimedean) (BolzanoWeierstrass) (CauchyComplete) (OrderedField)
  let step4 : (CauchyComplete → (Archimedean → BolzanoWeierstrass)) := step3 step2
  let step5 : (Archimedean → BolzanoWeierstrass) := step4 step1
  let step6 : BolzanoWeierstrass := step5 step0
  step6

theorem thm_5 (A Archimedean B BolzanoWeierstrass C CauchyComplete Complete HeineBorel IntermediateValue MonotoneConvergence NestedIntervals OrderedField : Prop) : HeineBorel :=
  let step0 : BolzanoWeierstrass := thm_4 (A) (Archimedean) (B) (BolzanoWeierstrass) (C) (CauchyComplete) (Complete) (HeineBorel) (IntermediateValue) (MonotoneConvergence) (NestedIntervals) (OrderedField)
  let step1 : OrderedField := an_hyp_field (OrderedField)
  let step2 : (OrderedField → (BolzanoWeierstrass → HeineBorel)) := an_ax5 (BolzanoWeierstrass) (HeineBorel) (OrderedField)
  let step3 : (BolzanoWeierstrass → HeineBorel) := step2 step1
  let step4 : HeineBorel := step3 step0
  step4

theorem thm_6 (A Archimedean B BolzanoWeierstrass C CauchyComplete Complete HeineBorel IntermediateValue MonotoneConvergence NestedIntervals OrderedField : Prop) : IntermediateValue :=
  let step0 : HeineBorel := thm_5 (A) (Archimedean) (B) (BolzanoWeierstrass) (C) (CauchyComplete) (Complete) (HeineBorel) (IntermediateValue) (MonotoneConvergence) (NestedIntervals) (OrderedField)
  let step1 : OrderedField := an_hyp_field (OrderedField)
  let step2 : (OrderedField → (HeineBorel → IntermediateValue)) := an_ax6 (HeineBorel) (IntermediateValue) (OrderedField)
  let step3 : (HeineBorel → IntermediateValue) := step2 step1
  let step4 : IntermediateValue := step3 step0
  step4

theorem thm_7 (A Archimedean B BolzanoWeierstrass C CauchyComplete Complete HeineBorel IntermediateValue MonotoneConvergence NestedIntervals OrderedField : Prop) : (Archimedean → CauchyComplete) :=
  let step0 : NestedIntervals := thm_2 (A) (Archimedean) (B) (BolzanoWeierstrass) (C) (CauchyComplete) (Complete) (HeineBorel) (IntermediateValue) (MonotoneConvergence) (NestedIntervals) (OrderedField)
  let step1 : OrderedField := an_hyp_field (OrderedField)
  let step2 : (OrderedField → (NestedIntervals → (Archimedean → CauchyComplete))) := an_ax3 (Archimedean) (CauchyComplete) (NestedIntervals) (OrderedField)
  let step3 : (NestedIntervals → (Archimedean → CauchyComplete)) := step2 step1
  let step4 : (Archimedean → CauchyComplete) := step3 step0
  step4

theorem thm_8 (A Archimedean B BolzanoWeierstrass C CauchyComplete Complete HeineBorel IntermediateValue MonotoneConvergence NestedIntervals OrderedField : Prop) : (Archimedean → BolzanoWeierstrass) :=
  let step0 : CauchyComplete := thm_3 (A) (Archimedean) (B) (BolzanoWeierstrass) (C) (CauchyComplete) (Complete) (HeineBorel) (IntermediateValue) (MonotoneConvergence) (NestedIntervals) (OrderedField)
  let step1 : OrderedField := an_hyp_field (OrderedField)
  let step2 : (OrderedField → (CauchyComplete → (Archimedean → BolzanoWeierstrass))) := an_ax4 (Archimedean) (BolzanoWeierstrass) (CauchyComplete) (OrderedField)
  let step3 : (CauchyComplete → (Archimedean → BolzanoWeierstrass)) := step2 step1
  let step4 : (Archimedean → BolzanoWeierstrass) := step3 step0
  step4

end Analysis1