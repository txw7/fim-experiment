(in-package #:lsip)

;;; Bounded native construction capabilities. These are checked primitive
;;; attachments, not synthesized new laws or an executable VM admission.

(defun shg-growth-snapshot-v1 (closure)
  (semantic-bundle-snapshot-ref-v1-snapshot-identity
   (semantic-bundle-closure-v1-bundle-snapshot-ref closure)))

(defvar *shg-growth-stages-v1* nil)

(defun shg-growth-stage-ref-v1 (state)
  ;; Only native identities cross the JSON execution boundary. The dynamic
  ;; table is an invocation-local staging context, not graph storage/authority.
  (realization-v1-digest
   (list :shg-growth-stage-v1
         (getf state :transaction) (getf state :expected-snapshot)
         (getf state :symbolic-route-profile)
         (getf state :construction-law) (getf state :budget)
         (when (getf state :step-subject-address)
           (semantic-bundle-row-address-v1-address-identity (getf state :step-subject-address)))
         (when (getf state :subject-address)
           (semantic-bundle-row-address-v1-address-identity (getf state :subject-address)))
         (mapcar #'semantic-bundle-delta-op-form-v1 (getf state :operations))
         (getf state :selected-member-refs)
         (semantic-scope-path-v1-segment-tokens (getf state :source-path))
         (semantic-decomposition-policy-v1-policy-identity (getf state :policy))
         (getf state :provides)
         (shg-growth-snapshot-v1 (getf state :closure))
         (when (getf state :child-closure)
           (shg-growth-snapshot-v1 (getf state :child-closure)))
         (when (getf state :parent-closure)
           (shg-growth-snapshot-v1 (getf state :parent-closure)))
         (when (getf state :view)
           (semantic-contracted-region-view-v1-view-identity (getf state :view))))))

(defun shg-growth-input-v1 (node environment prior)
  (let* ((required (first (getf node :requires)))
         (ref (if (eq (getf node :primitive) :shg-growth-append-v1)
                  (getf environment :request-ref)
                  (loop for entry in prior
                        for payload = (semantic-constructor-value-v1-payload (cdr entry))
                        when (eq (getf payload :provides) required)
                          return (getf payload :stage-ref))))
         (state (and *shg-growth-stages-v1* (gethash ref *shg-growth-stages-v1*))))
    (unless (and state (equal ref (shg-growth-stage-ref-v1 state)))
      (error "Growth stage is missing or its native identity has changed."))
    (copy-list state)))

(defun shg-growth-value-v1 (node state)
  (setf (getf state :provides) (getf node :provides))
  (let ((ref (shg-growth-stage-ref-v1 state)))
    (setf (gethash ref *shg-growth-stages-v1*) state)
    (make-semantic-constructor-value-v1
     :kind :shg-growth-stage :contract "shg-growth-stage-v1"
     :payload (list :stage-ref ref :provides (getf node :provides))
     :producer-node (getf node :node))))

(defun execute-shg-growth-request-v1 (program description request)
  (let* ((*shg-growth-stages-v1* (make-hash-table :test #'equal))
         (ref (shg-growth-stage-ref-v1 request)))
    (setf (gethash ref *shg-growth-stages-v1*) request)
    (let* ((execution (execute-semantic-constructor-program-v1
                       program description (list :request-ref ref)))
           (payload (semantic-constructor-value-v1-payload (getf execution :result)))
           (result (gethash (getf payload :stage-ref) *shg-growth-stages-v1*)))
      (unless (and result
                   (equal (getf payload :stage-ref) (shg-growth-stage-ref-v1 result)))
        (error "Growth result identity does not resolve in this transaction."))
      (values result execution))))

(defun shg-growth-symbolic-route-rows-v1 (bundle profile)
  ;; This bounded profile navigates binary source/target relations only.
  ;; It grants neither executable authority nor general hyperedge traversal.
  (unless (eq profile :source-target-v1)
    (error "Unsupported symbolic routing profile: ~S." profile))
  (let ((generator (semantic-bundle-generator-v1
                    :route-registry-v1
                    '(:relation-registry-v1 :incidence-registry-v1)))
        (incidences (recursive-semantic-bundle-base-rows-v1
                     bundle :incidence-registry-v1)))
    (loop for relation in (recursive-semantic-bundle-base-rows-v1
                          bundle :relation-registry-v1)
          when (member (semantic-relation-row-v1-relation-kind relation)
                       '(:control :dataflow))
          collect
          (let* ((ref (semantic-relation-row-v1-relation-row-identity relation))
                 (ends (remove ref incidences :test-not #'equal
                               :key #'semantic-incidence-row-v1-relation-ref))
                 (source (find :source ends :key #'semantic-incidence-row-v1-role))
                 (target (find :target ends :key #'semantic-incidence-row-v1-role)))
            (unless (and (= 2 (length ends)) source target)
              (error "Symbolic routing requires exactly one source and target: ~S." ref))
            (flet ((endpoint (incidence)
                     (let* ((kind (semantic-incidence-row-v1-participant-kind incidence))
                            (row-ref (semantic-incidence-row-v1-participant-ref incidence))
                            (registry (ecase kind
                                        (:member :member-registry-v1)
                                        (:port :port-registry-v1))))
                       (unless (find row-ref
                                     (recursive-semantic-bundle-base-rows-v1 bundle registry)
                                     :test #'equal :key #'semantic-registry-row-identity-v1)
                         (error "Symbolic route has a dangling endpoint: ~S." row-ref))
                       (list :registry registry :row-ref row-ref))))
              (semantic-bundle-generated-row-v1
               generator
               (list :profile profile :relation-ref ref
                     :source (endpoint source) :target (endpoint target)
                     :execution :unbound :authority :symbolic-only)
               (list ref
                     (semantic-incidence-row-v1-incidence-row-identity source)
                     (semantic-incidence-row-v1-incidence-row-identity target))
               (list (recursive-semantic-bundle-v1-bundle-identity bundle))))))))

(defun shg-growth-incidence-route-rows-v1 (bundle)
  ;; N-ary navigation preserves roles and ordinals. It does not infer an
  ;; execution order or grant provider/executable authority.
  (let ((generator (semantic-bundle-generator-v1
                    :route-registry-v1 '(:relation-registry-v1 :incidence-registry-v1)))
        (incidences (recursive-semantic-bundle-base-rows-v1 bundle :incidence-registry-v1)))
    (loop for relation in (recursive-semantic-bundle-base-rows-v1 bundle :relation-registry-v1)
          for ref = (semantic-relation-row-v1-relation-row-identity relation)
          for ends = (remove ref incidences :test-not #'equal
                             :key #'semantic-incidence-row-v1-relation-ref)
          collect
          (semantic-bundle-generated-row-v1
           generator
           (list :profile :relation-incidences-v1 :relation-ref ref
                 :constitution (semantic-relation-row-v1-constitution-ref relation)
                 :endpoints
                 (mapcar (lambda (end)
                           (let* ((kind (semantic-incidence-row-v1-participant-kind end))
                                  (registry (ecase kind
                                              ((:member :child-bundle) :member-registry-v1)
                                              (:port :port-registry-v1)
                                              (:relation :relation-registry-v1)))
                                  (participant (semantic-incidence-row-v1-participant-ref end)))
                             (unless (find participant
                                           (recursive-semantic-bundle-base-rows-v1 bundle registry)
                                           :test #'equal :key #'semantic-registry-row-identity-v1)
                               (error "Dangling native navigation endpoint."))
                             (list :role (semantic-incidence-row-v1-role end)
                                   :ordinal (semantic-incidence-row-v1-ordinal end)
                                   :registry registry :row-ref participant))) ends)
                 :execution :unbound :authority :symbolic-only)
           (cons ref (mapcar #'semantic-incidence-row-v1-incidence-row-identity ends))
           (list (recursive-semantic-bundle-v1-bundle-identity bundle))))))

(defun shg-growth-source-target-route-rows-v1 (bundle)
  (shg-growth-symbolic-route-rows-v1 bundle :source-target-v1))

(defun shg-growth-append-v1 (node environment prior)
  (let* ((state (shg-growth-input-v1 node environment prior))
         (bundle (getf state :bundle)) (closure (getf state :closure))
         (transaction (getf state :transaction)))
    (validate-semantic-bundle-persistence-components-v1
     bundle (getf state :generated) closure)
    (unless (and (realization-v1-reference-p transaction)
                 (equal (getf state :expected-snapshot)
                        (shg-growth-snapshot-v1 closure)))
      (error "Growth request has missing transaction or stale source."))
    (when (getf state :construction-law)
      (ecase (getf state :construction-law)
        (:shg-vm-run-growth-v1 (setf state (shg-vm-run-growth-v1 state)))
        (:shg-vm-joint-growth-v1 (setf state (shg-vm-joint-growth-v1 state)))))
    (let* ((operations (getf state :operations))
           (_shape
             (dolist (op operations)
               (unless (and (realization-v1-proper-list-p op)
                            (= 2 (length op))
                            (case (first op)
                              (:add-member (typep (second op) 'semantic-member-row-v1))
                              (:add-port (typep (second op) 'semantic-port-row-v1))
                              (:add-relation (typep (second op) 'semantic-relation-row-v1))
                              (:add-incidence (typep (second op) 'semantic-incidence-row-v1))
                              (:add-hole (typep (second op) 'semantic-hole-row-v1))))
                 (error "Growth append requires an exact typed addition."))))
           (delta (make-semantic-bundle-delta-v1
                   :expected-predecessor-snapshot
                   (semantic-bundle-closure-v1-bundle-snapshot-ref closure)
                   :operations operations
                   :provenance-ref (list :shg-growth-append-v1 transaction)))
           (candidate (apply-semantic-bundle-delta-v1 bundle closure delta)))
      (declare (ignore _shape))
      (multiple-value-bind (closed generated)
          (close-recursive-semantic-bundle-v1
           candidate :route-rows
           (when (getf state :symbolic-route-profile)
             (ecase (getf state :symbolic-route-profile)
               (:source-target-v1 (shg-growth-source-target-route-rows-v1 candidate))
               (:relation-incidences-v1 (shg-growth-incidence-route-rows-v1 candidate)))))
        (setf (getf state :bundle) candidate
              (getf state :closure) closed
              (getf state :generated) generated
              (getf state :append-delta) delta)
        (shg-growth-value-v1 node state)))))

(defun shg-growth-nest-v1 (node environment prior)
  (let* ((state (shg-growth-input-v1 node environment prior))
         (bundle (getf state :bundle)) (closure (getf state :closure))
         (generated (getf state :generated))
         (policy (getf state :policy))
         (selection (make-semantic-region-selection-v1
                     :source-bundle bundle :source-closure closure
                     :selected-member-refs (getf state :selected-member-refs)
                     :selection-policy-ref policy
                     :source-occurrence-path
                     (make-semantic-scope-path-v1
                      :segment-tokens
                      (append (semantic-scope-path-v1-segment-tokens
                               (getf state :source-path))
                              (list (getf state :transaction))))))
         (saturation (semantic-bundle-saturate-v1 bundle closure generated))
         (cut (derive-semantic-boundary-cut-v1
               bundle closure selection :policy policy
               :saturation-closure saturation)))
    (multiple-value-bind
          (fragment child child-closure child-generated parent parent-closure
           parent-generated delta extraction address-map)
        (extract-semantic-fragment-v1
         bundle closure generated selection cut
         :fragment-kind :function-fragment :policy policy
         :route-row-producer
         (when (getf state :symbolic-route-profile)
           (ecase (getf state :symbolic-route-profile)
             (:source-target-v1 'shg-growth-source-target-route-rows-v1)
             (:relation-incidences-v1 'shg-growth-incidence-route-rows-v1)))
         :saturation-closure saturation)
      (setf (getf state :fragment) fragment
            (getf state :child) child
            (getf state :child-closure) child-closure
            (getf state :child-generated) child-generated
            (getf state :parent) parent
            (getf state :parent-closure) parent-closure
            (getf state :parent-generated) parent-generated
            (getf state :nest-delta) delta
            (getf state :extraction) extraction
            (getf state :address-map) address-map)
      (shg-growth-value-v1 node state))))

(defun shg-growth-enclose-v1 (node environment prior)
  (let ((state (shg-growth-input-v1 node environment prior)))
    ;; Boundary maps are derived by H006 cut/extraction, not parameter lists.
    (multiple-value-bind (view witness contracted)
        (contract-semantic-region-v1
         (getf state :fragment) (getf state :child)
         (getf state :child-closure) (getf state :child-generated)
         :embedding-occurrence-ref
         (semantic-extraction-witness-v1-child-member-ref
          (getf state :extraction)))
      (let* ((child (getf state :child))
             (closure (getf state :child-closure))
             (path (make-semantic-scope-path-v1
                    :segment-tokens
                    (append
                     (semantic-scope-path-v1-segment-tokens (getf state :source-path))
                     (list (semantic-contracted-region-view-v1-embedding-occurrence-ref view)))))
             (addresses
               (loop for kind in *semantic-bundle-base-registry-kinds-v1*
                     append
                     (loop for row in (recursive-semantic-bundle-base-rows-v1 child kind)
                           collect (make-semantic-bundle-row-address-v1
                                    :bundle-occurrence-path path
                                    :bundle-snapshot-ref
                                    (semantic-bundle-closure-v1-bundle-snapshot-ref closure)
                                    :registry-kind kind
                                    :row-ref (semantic-registry-row-identity-v1 row)
                                    :lineage-ref (semantic-bundle-row-lineage-v1 path kind row))))))
        (dolist (address addresses)
          (resolve-semantic-bundle-row-address-v1
           address child closure (getf state :child-generated)))
        (setf (getf state :child-addresses) addresses))
      (setf (getf state :view) view
            (getf state :boundary-witness) witness
            (getf state :contracted) contracted
            (getf state :admission) :structural-candidate
            (getf state :behavioral-proof) :open)
      (shg-growth-value-v1 node state))))

(defun install-shg-growth-constructor-capabilities-v1 ()
  (install-semantic-constructor-capabilities-v1)
  (loop for (primitive provides requires evaluator) in
        '((:shg-growth-append-v1 :shg-growth-appended (:shg-growth-source)
           shg-growth-append-v1)
          (:shg-growth-nest-v1 :shg-growth-nested (:shg-growth-appended)
           shg-growth-nest-v1)
          (:shg-growth-enclose-v1 :shg-growth-enclosed (:shg-growth-nested)
           shg-growth-enclose-v1))
        do (register-semantic-constructor-primitive-description-v1
            (make-semantic-constructor-primitive-description-v1
             :primitive-id primitive :input-contract "shg-growth-stage-v1"
             :output-contract "shg-growth-stage-v1" :effect-class :staged-native-construction)
            (symbol-function evaluator))
           (register-semantic-constructor-capability-v1
            (make-semantic-constructor-capability-v1
             :capability-id primitive :primitive-id primitive
             :provides provides :requires requires :effect-class :staged-native-construction)))
  t)

(defun shg-growth-constructor-description-v1 ()
  (make-semantic-constructor-description-v1
   :constructor-id "shg-growth-constructor-v1"
   :input-contract "shg-growth-stage-v1"
   :output-contract "shg-growth-stage-v1"
   :primitive-set-id (semantic-constructor-capability-set-identity-v1)
   :invariants '(:capability-resolved-primitives-only)))
