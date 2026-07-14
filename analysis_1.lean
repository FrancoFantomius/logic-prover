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

theorem thm_1 (Complete MonotoneConvergence OrderedField : Prop) : MonotoneConvergence :=
  let step0 : Complete := an_hyp_complete (Complete)
  let step1 : OrderedField := an_hyp_field (OrderedField)
  let step2 : (OrderedField → (Complete → MonotoneConvergence)) := an_ax1 (Complete) (MonotoneConvergence) (OrderedField)
  let step3 : (Complete → MonotoneConvergence) := step2 step1
  let step4 : MonotoneConvergence := step3 step0
  step4

theorem thm_2 (Complete MonotoneConvergence NestedIntervals OrderedField : Prop) : NestedIntervals :=
  let step0 : Complete := an_hyp_complete (Complete)
  let step1 : OrderedField := an_hyp_field (OrderedField)
  let step2 : (OrderedField → (Complete → MonotoneConvergence)) := an_ax1 (Complete) (MonotoneConvergence) (OrderedField)
  let step3 : (Complete → MonotoneConvergence) := step2 step1
  let step4 : MonotoneConvergence := step3 step0
  let step5 : (OrderedField → (MonotoneConvergence → NestedIntervals)) := an_ax2 (MonotoneConvergence) (NestedIntervals) (OrderedField)
  let step6 : (MonotoneConvergence → NestedIntervals) := step5 step1
  let step7 : NestedIntervals := step6 step4
  step7

theorem thm_3 (Archimedean CauchyComplete Complete MonotoneConvergence NestedIntervals OrderedField : Prop) : CauchyComplete :=
  let step0 : Archimedean := an_hyp_arch (Archimedean)
  let step1 : Complete := an_hyp_complete (Complete)
  let step2 : OrderedField := an_hyp_field (OrderedField)
  let step3 : (OrderedField → (Complete → MonotoneConvergence)) := an_ax1 (Complete) (MonotoneConvergence) (OrderedField)
  let step4 : (Complete → MonotoneConvergence) := step3 step2
  let step5 : MonotoneConvergence := step4 step1
  let step6 : (OrderedField → (MonotoneConvergence → NestedIntervals)) := an_ax2 (MonotoneConvergence) (NestedIntervals) (OrderedField)
  let step7 : (MonotoneConvergence → NestedIntervals) := step6 step2
  let step8 : NestedIntervals := step7 step5
  let step9 : (OrderedField → (NestedIntervals → (Archimedean → CauchyComplete))) := an_ax3 (Archimedean) (CauchyComplete) (NestedIntervals) (OrderedField)
  let step10 : (NestedIntervals → (Archimedean → CauchyComplete)) := step9 step2
  let step11 : (Archimedean → CauchyComplete) := step10 step8
  let step12 : CauchyComplete := step11 step0
  step12

theorem thm_4 (Archimedean BolzanoWeierstrass CauchyComplete Complete MonotoneConvergence NestedIntervals OrderedField : Prop) : BolzanoWeierstrass :=
  let step0 : Archimedean := an_hyp_arch (Archimedean)
  let step1 : Complete := an_hyp_complete (Complete)
  let step2 : OrderedField := an_hyp_field (OrderedField)
  let step3 : (OrderedField → (Complete → MonotoneConvergence)) := an_ax1 (Complete) (MonotoneConvergence) (OrderedField)
  let step4 : (Complete → MonotoneConvergence) := step3 step2
  let step5 : MonotoneConvergence := step4 step1
  let step6 : (OrderedField → (MonotoneConvergence → NestedIntervals)) := an_ax2 (MonotoneConvergence) (NestedIntervals) (OrderedField)
  let step7 : (MonotoneConvergence → NestedIntervals) := step6 step2
  let step8 : NestedIntervals := step7 step5
  let step9 : (OrderedField → (NestedIntervals → (Archimedean → CauchyComplete))) := an_ax3 (Archimedean) (CauchyComplete) (NestedIntervals) (OrderedField)
  let step10 : (NestedIntervals → (Archimedean → CauchyComplete)) := step9 step2
  let step11 : (Archimedean → CauchyComplete) := step10 step8
  let step12 : CauchyComplete := step11 step0
  let step13 : (OrderedField → (CauchyComplete → (Archimedean → BolzanoWeierstrass))) := an_ax4 (Archimedean) (BolzanoWeierstrass) (CauchyComplete) (OrderedField)
  let step14 : (CauchyComplete → (Archimedean → BolzanoWeierstrass)) := step13 step2
  let step15 : (Archimedean → BolzanoWeierstrass) := step14 step12
  let step16 : BolzanoWeierstrass := step15 step0
  step16

theorem thm_5 (Archimedean BolzanoWeierstrass CauchyComplete Complete HeineBorel MonotoneConvergence NestedIntervals OrderedField : Prop) : HeineBorel :=
  let step0 : Archimedean := an_hyp_arch (Archimedean)
  let step1 : Complete := an_hyp_complete (Complete)
  let step2 : OrderedField := an_hyp_field (OrderedField)
  let step3 : (OrderedField → (Complete → MonotoneConvergence)) := an_ax1 (Complete) (MonotoneConvergence) (OrderedField)
  let step4 : (Complete → MonotoneConvergence) := step3 step2
  let step5 : MonotoneConvergence := step4 step1
  let step6 : (OrderedField → (MonotoneConvergence → NestedIntervals)) := an_ax2 (MonotoneConvergence) (NestedIntervals) (OrderedField)
  let step7 : (MonotoneConvergence → NestedIntervals) := step6 step2
  let step8 : NestedIntervals := step7 step5
  let step9 : (OrderedField → (NestedIntervals → (Archimedean → CauchyComplete))) := an_ax3 (Archimedean) (CauchyComplete) (NestedIntervals) (OrderedField)
  let step10 : (NestedIntervals → (Archimedean → CauchyComplete)) := step9 step2
  let step11 : (Archimedean → CauchyComplete) := step10 step8
  let step12 : CauchyComplete := step11 step0
  let step13 : (OrderedField → (CauchyComplete → (Archimedean → BolzanoWeierstrass))) := an_ax4 (Archimedean) (BolzanoWeierstrass) (CauchyComplete) (OrderedField)
  let step14 : (CauchyComplete → (Archimedean → BolzanoWeierstrass)) := step13 step2
  let step15 : (Archimedean → BolzanoWeierstrass) := step14 step12
  let step16 : BolzanoWeierstrass := step15 step0
  let step17 : (OrderedField → (BolzanoWeierstrass → HeineBorel)) := an_ax5 (BolzanoWeierstrass) (HeineBorel) (OrderedField)
  let step18 : (BolzanoWeierstrass → HeineBorel) := step17 step2
  let step19 : HeineBorel := step18 step16
  step19

theorem thm_6 (Archimedean BolzanoWeierstrass CauchyComplete Complete HeineBorel IntermediateValue MonotoneConvergence NestedIntervals OrderedField : Prop) : IntermediateValue :=
  let step0 : Archimedean := an_hyp_arch (Archimedean)
  let step1 : Complete := an_hyp_complete (Complete)
  let step2 : OrderedField := an_hyp_field (OrderedField)
  let step3 : (OrderedField → (Complete → MonotoneConvergence)) := an_ax1 (Complete) (MonotoneConvergence) (OrderedField)
  let step4 : (Complete → MonotoneConvergence) := step3 step2
  let step5 : MonotoneConvergence := step4 step1
  let step6 : (OrderedField → (MonotoneConvergence → NestedIntervals)) := an_ax2 (MonotoneConvergence) (NestedIntervals) (OrderedField)
  let step7 : (MonotoneConvergence → NestedIntervals) := step6 step2
  let step8 : NestedIntervals := step7 step5
  let step9 : (OrderedField → (NestedIntervals → (Archimedean → CauchyComplete))) := an_ax3 (Archimedean) (CauchyComplete) (NestedIntervals) (OrderedField)
  let step10 : (NestedIntervals → (Archimedean → CauchyComplete)) := step9 step2
  let step11 : (Archimedean → CauchyComplete) := step10 step8
  let step12 : CauchyComplete := step11 step0
  let step13 : (OrderedField → (CauchyComplete → (Archimedean → BolzanoWeierstrass))) := an_ax4 (Archimedean) (BolzanoWeierstrass) (CauchyComplete) (OrderedField)
  let step14 : (CauchyComplete → (Archimedean → BolzanoWeierstrass)) := step13 step2
  let step15 : (Archimedean → BolzanoWeierstrass) := step14 step12
  let step16 : BolzanoWeierstrass := step15 step0
  let step17 : (OrderedField → (BolzanoWeierstrass → HeineBorel)) := an_ax5 (BolzanoWeierstrass) (HeineBorel) (OrderedField)
  let step18 : (BolzanoWeierstrass → HeineBorel) := step17 step2
  let step19 : HeineBorel := step18 step16
  let step20 : (OrderedField → (HeineBorel → IntermediateValue)) := an_ax6 (HeineBorel) (IntermediateValue) (OrderedField)
  let step21 : (HeineBorel → IntermediateValue) := step20 step2
  let step22 : IntermediateValue := step21 step19
  step22

theorem thm_7 (Archimedean CauchyComplete Complete MonotoneConvergence NestedIntervals OrderedField : Prop) : (Archimedean → CauchyComplete) :=
  let step0 : Complete := an_hyp_complete (Complete)
  let step1 : OrderedField := an_hyp_field (OrderedField)
  let step2 : (OrderedField → (Complete → MonotoneConvergence)) := an_ax1 (Complete) (MonotoneConvergence) (OrderedField)
  let step3 : (Complete → MonotoneConvergence) := step2 step1
  let step4 : MonotoneConvergence := step3 step0
  let step5 : (OrderedField → (MonotoneConvergence → NestedIntervals)) := an_ax2 (MonotoneConvergence) (NestedIntervals) (OrderedField)
  let step6 : (MonotoneConvergence → NestedIntervals) := step5 step1
  let step7 : NestedIntervals := step6 step4
  let step8 : (OrderedField → (NestedIntervals → (Archimedean → CauchyComplete))) := an_ax3 (Archimedean) (CauchyComplete) (NestedIntervals) (OrderedField)
  let step9 : (NestedIntervals → (Archimedean → CauchyComplete)) := step8 step1
  let step10 : (Archimedean → CauchyComplete) := step9 step7
  step10

theorem thm_8 (Archimedean BolzanoWeierstrass CauchyComplete Complete MonotoneConvergence NestedIntervals OrderedField : Prop) : (Archimedean → BolzanoWeierstrass) :=
  let step0 : Archimedean := an_hyp_arch (Archimedean)
  let step1 : Complete := an_hyp_complete (Complete)
  let step2 : OrderedField := an_hyp_field (OrderedField)
  let step3 : (OrderedField → (Complete → MonotoneConvergence)) := an_ax1 (Complete) (MonotoneConvergence) (OrderedField)
  let step4 : (Complete → MonotoneConvergence) := step3 step2
  let step5 : MonotoneConvergence := step4 step1
  let step6 : (OrderedField → (MonotoneConvergence → NestedIntervals)) := an_ax2 (MonotoneConvergence) (NestedIntervals) (OrderedField)
  let step7 : (MonotoneConvergence → NestedIntervals) := step6 step2
  let step8 : NestedIntervals := step7 step5
  let step9 : (OrderedField → (NestedIntervals → (Archimedean → CauchyComplete))) := an_ax3 (Archimedean) (CauchyComplete) (NestedIntervals) (OrderedField)
  let step10 : (NestedIntervals → (Archimedean → CauchyComplete)) := step9 step2
  let step11 : (Archimedean → CauchyComplete) := step10 step8
  let step12 : CauchyComplete := step11 step0
  let step13 : (OrderedField → (CauchyComplete → (Archimedean → BolzanoWeierstrass))) := an_ax4 (Archimedean) (BolzanoWeierstrass) (CauchyComplete) (OrderedField)
  let step14 : (CauchyComplete → (Archimedean → BolzanoWeierstrass)) := step13 step2
  let step15 : (Archimedean → BolzanoWeierstrass) := step14 step12
  step15
