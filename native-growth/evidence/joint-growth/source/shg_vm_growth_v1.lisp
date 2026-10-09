(in-package #:lsip)

;;; Bounded authored VM declarations, lowered by native H001/A002 owners.
;;; The open interface is deliberate: no concrete VM encoding or ABI is inferred.
(defparameter *shg-vm-functions-v1*
  '(:run :step :fetch :decode :execute :alu :memory-exec :control
    :register-read :register-write :flags :memory-read :memory-write))
(defparameter *shg-vm-calls-v1*
  '((:run :step) (:step :fetch) (:step :decode) (:step :execute)
    (:execute :alu) (:execute :memory-exec) (:execute :control)
    (:fetch :memory-read) (:alu :register-read) (:alu :register-write) (:alu :flags)
    (:memory-exec :register-read) (:memory-exec :register-write)
    (:memory-exec :memory-read) (:memory-exec :memory-write)
    (:control :register-read) (:control :register-write)
    (:control :memory-read) (:control :memory-write)))

(defun shg-vm-close-v1 (bundle)
  (close-recursive-semantic-bundle-v1
   bundle :route-rows (shg-growth-incidence-route-rows-v1 bundle)))

(defun shg-vm-member-v1 (bundle name)
  (or (find name (recursive-semantic-bundle-base-rows-v1 bundle :member-registry-v1)
            :test #'equal :key #'semantic-member-row-v1-local-member-key)
      (error "Unknown VM member ~S." name)))

(defun shg-vm-add-relation-v1 (bundle closure constitution roles parameters &optional surfaces)
  (when (eq constitution :state-access-v2)
    (let* ((actor (third (assoc :actor roles)))
           (domain (third (assoc :state roles)))
           (incidences (recursive-semantic-bundle-base-rows-v1 bundle :incidence-registry-v1))
           (owned
             (loop for relation in (recursive-semantic-bundle-base-rows-v1 bundle :relation-registry-v1)
                   thereis (and (eq :state-ownership (semantic-relation-row-v1-relation-kind relation))
                   (let ((ends (remove (semantic-relation-row-v1-relation-row-identity relation)
                                       incidences :test-not #'equal
                                       :key #'semantic-incidence-row-v1-relation-ref)))
                     (and (find-if (lambda (i) (and (eq :owner (semantic-incidence-row-v1-role i))
                                                    (equal actor (semantic-incidence-row-v1-participant-ref i)))) ends)
                          (find-if (lambda (i) (and (eq :state (semantic-incidence-row-v1-role i))
                                                    (equal domain (semantic-incidence-row-v1-participant-ref i)))) ends)))))))
      (setf parameters (append parameters (list :owned-state-refs (when owned (list domain)))))))
  (when (eq constitution :state-ownership-v2)
    (setf parameters
          (append parameters
                  (list :linearity-law
                        (make-semantic-linearity-law-v1
                         :law-id :vm-private-state-single-owner-v1
                         :semantic-class :vm-private-state :linearity-class :linear)
                        :use-count (length (remove-duplicates
                                            (mapcar #'third (remove :owner roles :test-not #'eq :key #'first))
                                            :test #'equal))
                        :operation :own))))
  (let* ((application
           (make-semantic-relation-application-v1
            :constitution-ref constitution :role-bindings roles
            :parameter-bindings parameters :input-surface-refs surfaces
            :applicability-domain-ref :shg-vm-structural-open-v1))
         (delta (handler-case
                    (materialize-semantic-relation-v1
                     application (semantic-bundle-closure-v1-bundle-snapshot-ref closure))
                  (error (e) (error "Native VM relation ~S rejected: ~A" constitution e))))
         (next (apply-semantic-bundle-delta-v1 bundle closure delta)))
    (multiple-value-bind (closed generated) (shg-vm-close-v1 next)
      (values next closed generated delta application))))

(defun make-shg-vm-call-seed-v1 ()
  (let* ((effects (make-semantic-effect-profile-v1
                   :effect-kinds '(:vm-state-access) :externality-class :local))
         (surface (make-semantic-boundary-surface-v1 :effect-profile effects))
         (members nil) (ports nil) (holes nil))
    (dolist (name *shg-vm-functions-v1*)
      (let* ((member (make-semantic-member-row-v1
                      :local-member-key name :member-kind :operation
                      :semantic-ref (list :vm-function name :interface :open)
                      :surface-ref (semantic-boundary-surface-v1-surface-identity surface)
                      :effect-profile-ref (semantic-effect-profile-v1-profile-identity effects)))
             (ref (semantic-member-row-v1-member-row-identity member)))
        (push member members)
        (push (make-semantic-hole-row-v1
               :local-hole-key (list name :body) :hole-kind :refinement :owner-ref ref
               :required-contract-refs '(:vm-interface-open-v1)
               :required-formal-refs '(:vm-body-semantics-open-v1)) holes)
        (dolist (direction '(:in :out))
          (push (make-semantic-port-row-v1
                 :local-port-key (list name direction) :owner-kind :member :owner-ref ref
                 :port-kind (if (eq direction :in) :input :output) :direction direction
                 :contract-ref :vm-interface-open-v1
                 :effect-profile-ref (semantic-effect-profile-v1-profile-identity effects)
                 :visibility :bundle-export) ports))))
    (let* ((base (l7-make-base-registry-set-v1
                  :member-rows (nreverse members) :port-rows (nreverse ports)
                  :hole-rows (nreverse holes) :relation-rows nil :incidence-rows nil))
           (bundle (make-recursive-semantic-bundle-v1
                    :bundle-kind :function :subject-semantic-ref :vm-declared-call-network-v1
                    :surface-ref (semantic-boundary-surface-v1-surface-identity surface)
                    :base-registry-set-ref base
                    :closure-law-set-ref :shg-vm-open-structural-v1))
           (closure nil) (generated nil) (applications nil))
      (multiple-value-setq (closure generated) (shg-vm-close-v1 bundle))
      (dolist (call *shg-vm-calls-v1*)
        (multiple-value-bind (next closed registries delta application)
            (shg-vm-add-relation-v1
             bundle closure :call-v2
             (list (list :caller :member
                         (semantic-member-row-v1-member-row-identity
                          (shg-vm-member-v1 bundle (first call))))
                   (list :callee :member
                         (semantic-member-row-v1-member-row-identity
                          (shg-vm-member-v1 bundle (second call)))))
             (list :call-site-ref (list :vm-callsite (first call) (second call)))
             (list surface surface))
          (declare (ignore delta))
          (setf bundle next closure closed generated registries)
          (push application applications)))
      (list :bundle bundle :closure closure :generated generated :surface surface
            :call-applications (nreverse applications)))))

(defun shg-vm-run-body-address-v1 (seed path)
  (let* ((bundle (getf seed :bundle))
         (run (shg-vm-member-v1 bundle :run))
         (hole (or (find (semantic-member-row-v1-member-row-identity run)
                         (recursive-semantic-bundle-base-rows-v1 bundle :hole-registry-v1)
                         :test #'equal :key #'semantic-hole-row-v1-owner-ref)
                   (error "Run has no open body."))))
    (make-semantic-bundle-row-address-v1
     :bundle-occurrence-path path
     :bundle-snapshot-ref (semantic-bundle-closure-v1-bundle-snapshot-ref (getf seed :closure))
     :registry-kind :hole-registry-v1 :row-ref (semantic-hole-row-v1-hole-row-identity hole)
     :lineage-ref (semantic-bundle-row-lineage-v1 path :hole-registry-v1 hole))))

(defun shg-vm-run-growth-v1 (state)
  (let* ((source (getf state :bundle)) (closure (getf state :closure))
         (address (getf state :subject-address))
         (hole (getf (resolve-semantic-bundle-row-address-v1
                address source closure (getf state :generated)) :row))
         (run (shg-vm-member-v1 source :run)) (step (shg-vm-member-v1 source :step))
         (run-ref (semantic-member-row-v1-member-row-identity run))
         (step-ref (semantic-member-row-v1-member-row-identity step))
         (canonical (shg-vm-run-body-address-v1 state (getf state :source-path)))
         (source-call nil) (namespace nil) (members nil) (ports nil) (holes nil)
         (operations nil) (relation-receipts nil))
    (unless (and (typep hole 'semantic-hole-row-v1)
                 (equal run-ref (semantic-hole-row-v1-owner-ref hole))
                 (equalp address canonical)
                 (typep (getf state :budget) '(integer 0 *)))
      (error "VM growth requires the exact run body address and a natural budget."))
    (let ((incidences (recursive-semantic-bundle-base-rows-v1 source :incidence-registry-v1)))
      (dolist (relation (recursive-semantic-bundle-base-rows-v1 source :relation-registry-v1))
        (when (and (eq :call (semantic-relation-row-v1-relation-kind relation))
                   (let ((ends (remove (semantic-relation-row-v1-relation-row-identity relation)
                                       incidences :test-not #'equal
                                       :key #'semantic-incidence-row-v1-relation-ref)))
                     (and (find-if (lambda (i) (and (eq :caller (semantic-incidence-row-v1-role i))
                                                    (equal run-ref (semantic-incidence-row-v1-participant-ref i)))) ends)
                          (find-if (lambda (i) (and (eq :callee (semantic-incidence-row-v1-role i))
                                                    (equal step-ref (semantic-incidence-row-v1-participant-ref i)))) ends))))
          (when source-call (error "Ambiguous source run/step call."))
          (setf source-call (semantic-relation-row-v1-relation-row-identity relation)))))
    (unless source-call (error "No native run/step CALL to grow."))
    (setf namespace (realization-v1-digest
                     (list :shg-vm-run-growth-v1 (getf state :transaction) (getf state :budget)
                           (getf state :expected-snapshot)
                           (semantic-bundle-row-address-v1-address-identity address))))
    (labels ((member-row (name kind semantic &optional state-profile effect-profile)
               (let ((row (make-semantic-member-row-v1
                           :local-member-key (list namespace name) :member-kind kind
                           :semantic-ref semantic :state-profile-ref state-profile :effect-profile-ref effect-profile
                           :provenance-ref (list :rule :shg-vm-run-growth-v1 :source-call source-call))))
                 (push row members) row))
             (port-row (name owner direction kind contract)
               (let ((row (make-semantic-port-row-v1
                           :local-port-key (list namespace name) :owner-kind :member
                           :owner-ref (semantic-member-row-v1-member-row-identity owner)
                           :direction direction :port-kind kind :contract-ref contract :visibility :internal)))
                 (push row ports) row))
             (open-hole (name owner contract)
               (push (make-semantic-hole-row-v1
                      :local-hole-key (list namespace name) :hole-kind :parameter
                      :owner-ref (semantic-member-row-v1-member-row-identity owner)
                      :required-contract-refs (list contract)
                      :required-formal-refs (list name)) holes)))
      (let* ((kernel (afsm-kernel-validate
                      (afsm-kernel-normalize
                       '(:states (:ready :waiting :halted :trapped :exhausted)
                         :events ((dispatch) (continue) (halt) (trap) (exhaust) (reject))
                         :transitions ((:ready (dispatch) :waiting)
                                       (:ready (exhaust) :exhausted)
                                       (:waiting (continue) :ready)
                                       (:waiting (halt) :halted)
                                       (:waiting (trap) :trapped)
                                       (:waiting (reject) :waiting))))))
             (family-id :vm-run-phase)
             (family (make-typed-afsm-family-v1
                      :id family-id :identity (typed-afsm-family-computed-identity-v1
                                               family-id kernel :vm-loop-event-v1 :vm-loop-phase-v1)
                      :kernel kernel :initial-state :ready
                      :input-contract :vm-loop-event-v1 :output-contract :vm-loop-phase-v1))
             (descriptor (recursive-afsm-family-descriptor-v1 family))
             (machine (member-row :machine :semantic-object (list :native-afsm-definition descriptor)))
             (carried (member-row :carried :state-domain '(:type :vm-state :schema :open)))
             (budget (member-row :budget :state-domain (list :type :natural :initial (getf state :budget))))
             (pending (member-row :pending :state-domain
                                  '(:type (:option :activation-key) :fields (:incarnation :invocation :graph-generation :input-generation :iteration :attempt))))
             (state-profile (make-semantic-state-profile-v1
                             :state-domain-refs (mapcar #'semantic-member-row-v1-member-row-identity
                                                      (list carried budget pending))
                             :read-set (mapcar #'semantic-member-row-v1-member-row-identity
                                               (list carried budget pending))
                             :write-set (mapcar #'semantic-member-row-v1-member-row-identity
                                                (list carried budget pending))))
             (state-surface (make-semantic-boundary-surface-v1 :state-profile state-profile))
             (controller (member-row :controller :operation
                                     (list :controls source-call :machine-definition-ref (getf descriptor :family-identity))
                                     (semantic-state-profile-v1-profile-identity state-profile)))
             (worker (member-row :worker :operation (list :callee step-ref :source-call source-call)))
             (request (port-row :request controller :out :protocol :vm-step-request-v1))
             (input (port-row :work-input worker :in :protocol :vm-step-request-v1))
             (result (port-row :work-result worker :out :protocol :vm-step-completion-v1))
             (completion (port-row :completion controller :in :protocol :vm-step-completion-v1))
             (again (port-row :continue controller :out :control :vm-loop-continue-v1))
             (halt (port-row :halt controller :out :failure :vm-halt-outcome-v1))
             (trap (port-row :trap controller :out :failure :vm-trap-outcome-v1))
             (phase-rows
               (loop for phase in (getf kernel :states)
                     collect (member-row (list :phase phase) :protocol-state
                                         (list :phase-definition-ref (getf descriptor :family-identity)
                                               :state phase))))
             (transition-rows
               (loop for transition in (getf kernel :transitions) for ordinal from 0
                     collect (member-row (list :transition ordinal) :semantic-object
                                         (list :phase-definition-ref (getf descriptor :family-identity)
                                               :transition transition :guard-status :open))))
             (effects (make-semantic-effect-profile-v1 :effect-kinds '(:vm-state-access) :externality-class :local))
             (surface (make-semantic-boundary-surface-v1 :effect-profile effects))
             (policy (make-semantic-decomposition-policy-v1)))
        (validate-recursive-afsm-family-descriptor-v1 descriptor)
        (dolist (claim '(:positive-budget :correlated-completion :at-most-once-commit
                         :loop-carried-state :continue-or-terminal :dispatch-budget-consumption
                         :declared-effects-only :parent-boundary-preservation :eventual-progress))
          (open-hole claim controller :vm-loop-contract-v1))
        (open-hole :argument-result-mapping worker :vm-interface-open-v1)
        (setf operations (append (mapcar (lambda (m) (list :add-member m)) (nreverse members))
                                 (mapcar (lambda (p) (list :add-port p)) (nreverse ports))
                                 (mapcar (lambda (h) (list :add-hole h)) (nreverse holes))))
        (let* ((delta (make-semantic-bundle-delta-v1
                       :expected-predecessor-snapshot (semantic-bundle-closure-v1-bundle-snapshot-ref closure)
                       :operations operations :provenance-ref (list :shg-vm-run-growth-v1 namespace)))
               (candidate (apply-semantic-bundle-delta-v1 source closure delta))
               (closed nil) (generated nil)
               (coordination (or (gethash :shg-vm-coordination-open-v1 *semantic-relation-constitutions-v2*)
                                 (semantic-v2-register
                              (current-semantic-algebra-registry-v2)
                              :shg-vm-coordination-open-v1 :protocol :protocol
                              (append (mapcar (lambda (role) (semantic-v2-role role 1 1 '(:member)))
                                              '(:controller :worker :machine :carried :budget :pending))
                                      (mapcar (lambda (role) (semantic-v2-role role 1 1 '(:port)))
                                              '(:request :work-input :work-result :completion :continue :halt :trap)))
                              :parameters '(:source-call-ref :source-body-ref :phase-definition-ref :contract-status)))))
          (unless (gethash :shg-vm-machine-members-v1 *semantic-relation-constitutions-v2*)
            (semantic-v2-register
             (current-semantic-algebra-registry-v2) :shg-vm-machine-members-v1 :protocol :protocol
             (list (semantic-v2-role :machine 1 1 '(:member))
                   (semantic-v2-role :phase 5 5 '(:member) :ordered t)
                   (semantic-v2-role :transition 6 6 '(:member) :ordered t))))
          (unless (gethash :shg-vm-body-candidate-v1 *semantic-relation-constitutions-v2*)
            (semantic-v2-register
             (current-semantic-algebra-registry-v2) :shg-vm-body-candidate-v1 :refinement :refinement
             (list (semantic-v2-role :abstract 1 1 '(:member :port))
                   (semantic-v2-role :refinement 1 1 '(:member :port)))
             :parameters '(:source-body-ref :preservation-status)))
          (multiple-value-setq (closed generated) (shg-vm-close-v1 candidate))
          (dolist (production
                    (append
                     (list
                     (list :shg-vm-body-candidate-v1
                           (list (list :abstract :member run-ref)
                                 (list :refinement :member (semantic-member-row-v1-member-row-identity controller)))
                           (list :source-body-ref (semantic-bundle-row-address-v1-address-identity address)
                                 :preservation-status :open) nil)
                     (list :shg-vm-machine-members-v1
                           (append (list (list :machine :member (semantic-member-row-v1-member-row-identity machine)))
                                   (loop for row in phase-rows for ordinal from 0
                                         collect (list :phase :member (semantic-member-row-v1-member-row-identity row) ordinal))
                                   (loop for row in transition-rows for ordinal from 0
                                         collect (list :transition :member (semantic-member-row-v1-member-row-identity row) ordinal)))
                           nil nil)
                     (list :call-v2
                           (list (list :caller :member (semantic-member-row-v1-member-row-identity worker))
                                 (list :callee :member step-ref))
                           (list :call-site-ref (list namespace :worker-step)) (list surface surface))
                     (list (semantic-relation-constitution-v2-constitution-id coordination)
                           (append
                            (loop for role in '(:controller :worker :machine :carried :budget :pending)
                                  for row in (list controller worker machine carried budget pending)
                                  collect (list role :member (semantic-member-row-v1-member-row-identity row)))
                            (loop for role in '(:request :work-input :work-result :completion :continue :halt :trap)
                                  for row in (list request input result completion again halt trap)
                                  collect (list role :port (semantic-port-row-v1-port-row-identity row))))
                           (list :source-call-ref source-call
                                 :source-body-ref (semantic-bundle-row-address-v1-address-identity address)
                                 :phase-definition-ref (getf descriptor :family-identity)
                                 :contract-status :open) nil))
                     (loop for pair in (list (list request input :vm-step-request-v1)
                                             (list result completion :vm-step-completion-v1))
                           for channel-surface = (make-semantic-boundary-surface-v1
                                                  :input-port-classes (list (third pair))
                                                  :output-port-classes (list (third pair)))
                           collect (list :dataflow-v2
                                         (list (list :source :port (semantic-port-row-v1-port-row-identity (first pair)))
                                               (list :target :port (semantic-port-row-v1-port-row-identity (second pair))))
                                         nil (list channel-surface channel-surface)))
                     (loop for domain in (list carried budget pending)
                           collect (list :state-ownership-v2
                                         (list (list :owner :member (semantic-member-row-v1-member-row-identity controller))
                                               (list :state :member (semantic-member-row-v1-member-row-identity domain)))
                                         (list :state-ref (semantic-member-row-v1-member-row-identity domain))
                                         (list state-surface)))
                     (loop for domain in (list carried budget pending) append
                           (loop for mode in '(:read :write)
                                 collect (list :state-access-v2
                                               (list (list :actor :member (semantic-member-row-v1-member-row-identity controller))
                                                     (list :state :member (semantic-member-row-v1-member-row-identity domain)))
                                               (list :state-ref (semantic-member-row-v1-member-row-identity domain)
                                                     :access-mode mode)
                                               (list state-surface))))))
            (multiple-value-bind (next new-closure registries relation-delta application)
                (apply #'shg-vm-add-relation-v1 candidate closed production)
              (setf candidate next closed new-closure generated registries
                    operations (append operations (semantic-bundle-delta-v1-operations relation-delta)))
              (push (list :application application :delta relation-delta) relation-receipts)))
          ;; One aggregate delta must reproduce the staged native construction.
          (let* ((aggregate (make-semantic-bundle-delta-v1
                             :expected-predecessor-snapshot (semantic-bundle-closure-v1-bundle-snapshot-ref closure)
                             :operations operations :provenance-ref (list :shg-vm-run-growth-v1 namespace)))
                 (replayed (apply-semantic-bundle-delta-v1 source closure aggregate)))
            (dolist (kind *semantic-bundle-base-registry-kinds-v1*)
              (unless (equal (mapcar #'semantic-registry-row-identity-v1
                                    (recursive-semantic-bundle-base-rows-v1 replayed kind))
                             (mapcar #'semantic-registry-row-identity-v1
                                     (recursive-semantic-bundle-base-rows-v1 candidate kind)))
                (error "VM aggregate delta disagrees with staged native rows: ~S." kind)))
            ;; Staged validation has intermediate predecessors; the transaction
            ;; successor has the one original predecessor and the same rows.
            (setf candidate replayed)
            (multiple-value-setq (closed generated) (shg-vm-close-v1 candidate)))
          (setf (getf state :operations) operations
                (getf state :selected-member-refs)
                (mapcar #'semantic-member-row-v1-member-row-identity
                        (append (list controller worker machine carried budget pending) phase-rows transition-rows))
                (getf state :policy) policy
                (getf state :vm-growth-receipt)
                (list :namespace namespace :source-body address :source-call source-call
                      :machine descriptor :relations (nreverse relation-receipts)
                      :structural-status :candidate :behavioral-proof :open
                      :liveness-proof :open :execution :unbound)))))
    state))

(defun shg-vm-boundary-links-v1 (state)
  "Resolve the retained H006 correspondence; these links are not CALL edges."
  (let* ((map (getf state :address-map))
         (witness (semantic-extraction-address-map-v1-address-map-identity map))
         (embedding (semantic-contracted-region-view-v1-embedding-occurrence-ref (getf state :view)))
         (links nil))
    (unless (equal witness (realization-v1-digest (list :semantic-extraction-address-map-v1 (semantic-extraction-address-map-form-v1 map))))
      (error "H006 correspondence identity mismatch."))
    (labels ((coordinate (scope kind ref)
               (let* ((bundle (getf state scope))
                      (closure (getf state (if (eq scope :parent) :parent-closure :child-closure)))
                      (generated (getf state (if (eq scope :parent) :parent-generated :child-generated)))
                      (path (make-semantic-scope-path-v1
                             :segment-tokens
                             (append (semantic-scope-path-v1-segment-tokens (getf state :source-path))
                                     (when (eq scope :child) (list embedding)))))
                      (row (or (find ref (recursive-semantic-bundle-base-rows-v1 bundle kind)
                                     :test #'equal :key #'semantic-registry-row-identity-v1)
                               (error "Dangling H006 correspondence endpoint: ~S." ref)))
                      (address (make-semantic-bundle-row-address-v1
                                :bundle-occurrence-path path
                                :bundle-snapshot-ref (semantic-bundle-closure-v1-bundle-snapshot-ref closure)
                                :registry-kind kind :row-ref ref
                                :lineage-ref (semantic-bundle-row-lineage-v1 path kind row))))
                 (resolve-semantic-bundle-row-address-v1 address bundle closure generated)
                 (values address row)))
             (link (type from to from-address to-address rewrite port)
               (push (list (cons "type" type) (cons "source" from) (cons "target" to)
                           (cons "role" type) (cons "correspondence" witness)
                           (cons "source_address" (semantic-bundle-row-address-v1-address-identity from-address))
                           (cons "target_address" (semantic-bundle-row-address-v1-address-identity to-address))
                           (cons "direction" (string-downcase (symbol-name (semantic-port-row-v1-direction port))))
                           (cons "contract" (prin1-to-string (semantic-port-row-v1-contract-ref port)))
                           (cons "details" (with-standard-io-syntax
                                             (prin1-to-string (list :h006-address-map-ref witness :rewrite rewrite
                                                                    :source-address from-address :target-address to-address))))) links)))
      (multiple-value-bind (embedding-address member) (coordinate :parent :member-registry-v1 embedding)
        (unless (equal (semantic-member-row-v1-child-bundle-ref member)
                       (semantic-bundle-closure-v1-closure-identity (getf state :child-closure)))
          (error "H006 embedding refers to another child closure."))
        (dolist (rewrite (semantic-extraction-address-map-v1-parent-boundary-rewrites map))
          (let* ((parent-ref (getf rewrite :parent-port-ref))
                 (original (or (find (getf rewrite :source-incidence-ref)
                                     (recursive-semantic-bundle-base-rows-v1 (getf state :bundle) :incidence-registry-v1)
                                     :test #'equal :key #'semantic-registry-row-identity-v1)
                               (error "Missing H006 source incidence.")))
                 (successor (find (getf rewrite :successor-incidence-ref)
                                  (recursive-semantic-bundle-base-rows-v1 (getf state :parent) :incidence-registry-v1)
                                  :test #'equal :key #'semantic-registry-row-identity-v1)))
            (unless (and (equal (getf rewrite :source-incidence-form) (semantic-incidence-row-v1-form original))
                         successor (equal parent-ref (semantic-incidence-row-v1-participant-ref successor))
                         (equal (semantic-incidence-row-v1-relation-ref original) (semantic-incidence-row-v1-relation-ref successor))
                         (eq (semantic-incidence-row-v1-role original) (semantic-incidence-row-v1-role successor)))
              (error "H006 incidence correspondence mismatch."))
            (multiple-value-bind (parent-address parent-port) (coordinate :parent :port-registry-v1 parent-ref)
              (unless (equal embedding (semantic-port-row-v1-owner-ref parent-port))
                (error "H006 parent boundary has the wrong owner."))
              (link "embedding-boundary" embedding parent-ref embedding-address parent-address rewrite parent-port)
              (dolist (child-ref (getf rewrite :child-port-refs))
                (multiple-value-bind (child-address child-port) (coordinate :child :port-registry-v1 child-ref)
                  (unless (and (eq (semantic-port-row-v1-direction parent-port) (semantic-port-row-v1-direction child-port))
                               (equal (semantic-port-row-v1-contract-ref parent-port) (semantic-port-row-v1-contract-ref child-port)))
                    (error "H006 boundary contract mismatch."))
                  (link "boundary-correspondence" parent-ref child-ref parent-address child-address rewrite child-port)
                  (let* ((participant (semantic-incidence-row-v1-participant-ref original))
                         (kind (ecase (semantic-incidence-row-v1-participant-kind original)
                                 (:member :member-registry-v1) (:port :port-registry-v1) (:relation :relation-registry-v1))))
                    (link "boundary-projection" child-ref participant child-address
                          (coordinate :child kind participant) rewrite child-port)))))))))
    (nreverse links)))

(defun shg-vm-growth-view-v1 (state)
  "Export resolved native rows, not a second editable semantic authority."
  (let ((nodes nil) (edges nil) (headers nil) (resolved 0))
    (loop for label in '("parent" "child")
          for bundle in (list (getf state :parent) (getf state :child))
          for closure in (list (getf state :parent-closure) (getf state :child-closure))
          for generated in (list (getf state :parent-generated) (getf state :child-generated))
          for path = (make-semantic-scope-path-v1
                      :segment-tokens
                      (append (semantic-scope-path-v1-segment-tokens (getf state :source-path))
                              (when (equal label "child")
                                (list (semantic-contracted-region-view-v1-embedding-occurrence-ref
                                       (getf state :view))))))
          do
          (push (list (cons "scope" label)
                      (cons "bundle" (recursive-semantic-bundle-v1-bundle-identity bundle))
                      (cons "snapshot" (shg-growth-snapshot-v1 closure))) headers)
          (dolist (kind (append *semantic-bundle-base-registry-kinds-v1*
                               *semantic-bundle-generated-registry-kinds-v1*))
            (let ((root (semantic-bundle-row-address-root-v1 bundle generated kind)))
              (dolist (row (semantic-registry-root-v1-rows root))
                (let* ((ref (semantic-registry-row-identity-v1 row))
                       (address (make-semantic-bundle-row-address-v1
                                 :bundle-occurrence-path path
                                 :bundle-snapshot-ref (semantic-bundle-closure-v1-bundle-snapshot-ref closure)
                                 :registry-kind kind :row-ref ref
                                 :lineage-ref (semantic-bundle-row-lineage-v1 path kind row)))
                       (resolution (resolve-semantic-bundle-row-address-v1 address bundle closure generated)))
                  (assert (equal ref (getf resolution :row-ref)))
                  (incf resolved)
                  (cond
                    ((typep row 'semantic-incidence-row-v1)
                     (push (list (cons "source" (semantic-incidence-row-v1-participant-ref row))
                                 (cons "target" (semantic-incidence-row-v1-relation-ref row))
                                 (cons "role" (string-downcase (symbol-name (semantic-incidence-row-v1-role row))))
                                 (cons "ordinal" (semantic-incidence-row-v1-ordinal row))
                                 (cons "incidence" ref)) edges))
                    (t
                     (push (list (cons "id" ref) (cons "scope" label)
                                 (cons "registry" (string-downcase (symbol-name kind)))
                                 (cons "address" (semantic-bundle-row-address-v1-address-identity address))
                                 (cons "label"
                                       (typecase row
                                         (semantic-member-row-v1
                                          (let ((key (semantic-member-row-v1-local-member-key row)))
                                            (format nil "~S" (if (consp key) (second key) key))))
                                         (semantic-port-row-v1
                                          (format nil "~S" (semantic-port-row-v1-local-port-key row)))
                                         (semantic-relation-row-v1
                                          (string-downcase (symbol-name (semantic-relation-row-v1-relation-kind row))))
                                         (semantic-hole-row-v1 "open obligation")
                                         (t (string-downcase (symbol-name kind)))))
                                 (cons "details" (with-standard-io-syntax (prin1-to-string row)))) nodes))))))))
    (list (cons "schema" "native-vm-growth-view-v1")
          (cons "status" "structural candidate; behavioral and liveness proof OPEN")
          (cons "resolved_addresses" resolved)
          (cons "headers" (nreverse headers))
          (cons "embedding" (semantic-contracted-region-view-v1-embedding-occurrence-ref (getf state :view)))
          (cons "nodes" (nreverse nodes))
          (cons "edges" (append (nreverse edges) (shg-vm-boundary-links-v1 state))))))

(defun shg-vm-call-ref-v1 (bundle caller callee)
  (let ((matches nil)
        (incidences (recursive-semantic-bundle-base-rows-v1 bundle :incidence-registry-v1)))
    (dolist (relation (recursive-semantic-bundle-base-rows-v1 bundle :relation-registry-v1))
      (when (eq :call (semantic-relation-row-v1-relation-kind relation))
        (let ((ends (remove (semantic-relation-row-v1-relation-row-identity relation) incidences
                            :test-not #'equal :key #'semantic-incidence-row-v1-relation-ref)))
          (when (and (find-if (lambda (i) (and (eq :caller (semantic-incidence-row-v1-role i))
                                               (equal caller (semantic-incidence-row-v1-participant-ref i)))) ends)
                     (find-if (lambda (i) (and (eq :callee (semantic-incidence-row-v1-role i))
                                               (equal callee (semantic-incidence-row-v1-participant-ref i)))) ends))
            (push (semantic-relation-row-v1-relation-row-identity relation) matches)))))
    (unless (= 1 (length matches)) (error "Expected one source CALL: ~S -> ~S." caller callee))
    (first matches)))

(defun shg-vm-step-body-address-v1 (state)
  (let* ((bundle (getf state :bundle)) (path (getf state :source-path))
         (owner (semantic-member-row-v1-member-row-identity (shg-vm-member-v1 bundle :step)))
         (hole (or (find owner (recursive-semantic-bundle-base-rows-v1 bundle :hole-registry-v1)
                         :test #'equal :key #'semantic-hole-row-v1-owner-ref)
                   (error "Step has no open body."))))
    (make-semantic-bundle-row-address-v1
     :bundle-occurrence-path path
     :bundle-snapshot-ref (semantic-bundle-closure-v1-bundle-snapshot-ref (getf state :closure))
     :registry-kind :hole-registry-v1 :row-ref (semantic-hole-row-v1-hole-row-identity hole)
     :lineage-ref (semantic-bundle-row-lineage-v1 path :hole-registry-v1 hole))))

(defun shg-vm-joint-growth-v1 (input)
  "One fixed law stages run and step; only one aggregate successor is returned."
  (let* ((state (shg-vm-run-growth-v1 input))
         (source (getf state :bundle)) (closure (getf state :closure))
         (address (getf state :step-subject-address))
         (canonical (shg-vm-step-body-address-v1 state))
         (step-ref (semantic-member-row-v1-member-row-identity (shg-vm-member-v1 source :step)))
         (namespace (realization-v1-digest
                     (list :shg-vm-joint-step-v1 (getf state :transaction) (getf state :expected-snapshot)
                           (semantic-bundle-row-address-v1-address-identity canonical))))
         (members nil) (ports nil) (holes nil) (productions nil) (applications nil)
         (operations (copy-list (getf state :operations)))
         (effects (make-semantic-effect-profile-v1 :effect-kinds '(:vm-state-access) :externality-class :local))
         (surface (make-semantic-boundary-surface-v1 :effect-profile effects)))
    (unless (and (typep address 'semantic-bundle-row-address-v1) (equalp canonical address))
      (error "Joint growth requires the exact source step body coordinate."))
    (resolve-semantic-bundle-row-address-v1 address source closure (getf state :generated))
    (labels ((member-row (name kind semantic &optional profile)
               (let ((row (make-semantic-member-row-v1
                           :local-member-key (list namespace name) :member-kind kind :semantic-ref semantic
                           :state-profile-ref profile
                           :provenance-ref (list :rule :shg-vm-joint-growth-v1 :source-body (semantic-bundle-row-address-v1-address-identity canonical)))))
                 (push row members) row))
             (port-row (name owner direction contract)
               (let ((row (make-semantic-port-row-v1
                           :local-port-key (list namespace name) :owner-kind :member
                           :owner-ref (semantic-member-row-v1-member-row-identity owner)
                           :port-kind :protocol :direction direction :contract-ref contract :visibility :internal)))
                 (push row ports) row))
             (hole (name owner contract)
               (push (make-semantic-hole-row-v1
                      :local-hole-key (list namespace name) :hole-kind :parameter
                      :owner-ref (semantic-member-row-v1-member-row-identity owner)
                      :required-contract-refs (list contract) :required-formal-refs (list name)) holes))
             (ref (row) (semantic-registry-row-identity-v1 row))
             (production (constitution roles parameters &optional surfaces)
               (push (list constitution roles parameters surfaces) productions)))
      (let* ((kernel (afsm-kernel-validate
                      (afsm-kernel-normalize
                       '(:states (:fetch :decode :execute :done)
                         :events ((fetch-ok) (decode-ok) (execute-ok) (trap) (new-request))
                         :transitions ((:fetch (fetch-ok) :decode) (:decode (decode-ok) :execute)
                                       (:execute (execute-ok) :done) (:fetch (trap) :done)
                                       (:decode (trap) :done) (:execute (trap) :done)
                                       (:done (new-request) :fetch))))))
             (family (make-typed-afsm-family-v1
                      :id :vm-step-phase :identity (typed-afsm-family-computed-identity-v1
                                                   :vm-step-phase kernel :vm-step-event-open-v1 :vm-step-phase-v1)
                      :kernel kernel :initial-state :fetch
                      :input-contract :vm-step-event-open-v1 :output-contract :vm-step-phase-v1))
             (descriptor (recursive-afsm-family-descriptor-v1 family))
             (machine (member-row :step-machine :semantic-object (list :native-afsm-definition descriptor)))
             (carried (member-row :step-carried :state-domain '(:type :vm-state :schema :open)))
             (pending (member-row :step-pending :state-domain '(:type (:option :activation-key) :schema :open)))
             (outcome (member-row :step-outcome :state-domain '(:type (:result :step-outcome :trap) :schema :open)))
             (domains (list carried pending outcome))
             (profile (make-semantic-state-profile-v1
                       :state-domain-refs (mapcar #'ref domains) :read-set (mapcar #'ref domains)
                       :write-set (mapcar #'ref domains)))
             (state-surface (make-semantic-boundary-surface-v1 :state-profile profile))
             (controller (member-row :step-controller :operation
                                     (list :controls step-ref :machine-definition-ref (getf descriptor :family-identity)
                                           :activation-mode :open)
                                     (semantic-state-profile-v1-profile-identity profile)))
             (phases (loop for phase in (getf kernel :states)
                           collect (member-row (list :step-phase phase) :protocol-state
                                               (list :machine-ref (ref machine) :state phase))))
             (transitions (loop for transition in (getf kernel :transitions) for ordinal from 0
                                collect (member-row (list :step-transition ordinal) :semantic-object
                                                    (list :machine-ref (ref machine) :transition transition :guard-status :open))))
             (workers nil) (source-calls nil))
        (validate-recursive-afsm-family-descriptor-v1 descriptor)
        (unless (gethash :shg-vm-step-machine-members-v1 *semantic-relation-constitutions-v2*)
          (semantic-v2-register (current-semantic-algebra-registry-v2)
                               :shg-vm-step-machine-members-v1 :protocol :protocol
                               (list (semantic-v2-role :machine 1 1 '(:member))
                                     (semantic-v2-role :phase 4 4 '(:member) :ordered t)
                                     (semantic-v2-role :transition 7 7 '(:member) :ordered t))))
        (unless (gethash :shg-vm-call-coordination-open-v1 *semantic-relation-constitutions-v2*)
          (semantic-v2-register
           (current-semantic-algebra-registry-v2) :shg-vm-call-coordination-open-v1 :protocol :protocol
           (append (mapcar (lambda (r) (semantic-v2-role r 1 1 '(:member))) '(:controller :worker :machine :pending))
                   (mapcar (lambda (r) (semantic-v2-role r 1 1 '(:port))) '(:request :work-input :work-result :completion)))
           :parameters '(:source-call-ref :contract-status :activation-mode)))
        (production :shg-vm-body-candidate-v1
                    (list (list :abstract :member step-ref) (list :refinement :member (ref controller)))
                    (list :source-body-ref (semantic-bundle-row-address-v1-address-identity address) :preservation-status :open))
        (production :shg-vm-step-machine-members-v1
                    (append (list (list :machine :member (ref machine)))
                            (loop for row in phases for n from 0 collect (list :phase :member (ref row) n))
                            (loop for row in transitions for n from 0 collect (list :transition :member (ref row) n))) nil)
        (dolist (name '(:fetch :decode :execute))
          (let* ((callee (semantic-member-row-v1-member-row-identity (shg-vm-member-v1 source name)))
                 (call (shg-vm-call-ref-v1 source step-ref callee))
                 (worker (member-row (list :step-use name) :operation (list :callee callee :source-call call)))
                 (request-type (list :step-request-open-v1 name))
                 (result-type (list :step-result-open-v1 name))
                 (request (port-row (list name :request) controller :out request-type))
                 (input-port (port-row (list name :input) worker :in request-type))
                 (result (port-row (list name :result) worker :out result-type))
                 (completion (port-row (list name :completion) controller :in result-type)))
            (push worker workers) (push call source-calls)
            (hole (list name :argument-result-mapping) worker :vm-interface-open-v1)
            (production :call-v2 (list (list :caller :member (ref worker)) (list :callee :member callee))
                        (list :call-site-ref (list namespace name)) (list surface surface))
            (production :shg-vm-call-coordination-open-v1
                        (list (list :controller :member (ref controller)) (list :worker :member (ref worker))
                              (list :machine :member (ref machine)) (list :pending :member (ref pending))
                              (list :request :port (ref request)) (list :work-input :port (ref input-port))
                              (list :work-result :port (ref result)) (list :completion :port (ref completion)))
                        (list :source-call-ref call :contract-status :open :activation-mode :open))
            (dolist (pair (list (list request input-port request-type) (list result completion result-type)))
              (let ((channel (make-semantic-boundary-surface-v1 :input-port-classes (list (third pair))
                                                                 :output-port-classes (list (third pair)))))
                (production :dataflow-v2 (list (list :source :port (ref (first pair)))
                                               (list :target :port (ref (second pair)))) nil (list channel channel))))))
        ;; The fixed law supplies ordering; CALL topology alone does not.
        (production :serial-v2 (loop for worker in (reverse workers) for n from 0
                                    collect (list :operand :member (ref worker) n)) nil
                    (list surface surface surface))
        (dolist (domain domains)
          (production :state-ownership-v2 (list (list :owner :member (ref controller)) (list :state :member (ref domain)))
                      (list :state-ref (ref domain)) (list state-surface))
          (dolist (mode '(:read :write))
            (production :state-access-v2 (list (list :actor :member (ref controller)) (list :state :member (ref domain)))
                        (list :state-ref (ref domain) :access-mode mode) (list state-surface))))
        (dolist (claim '(:fetch-decode-mapping :decode-execute-mapping :trap-propagation :state-effect-frame
                         :new-invocation-reset :matching-completion :at-most-once-commit :activation-mode :boundary-preservation))
          (hole claim controller :vm-step-contract-open-v1))
        (setf operations (append operations
                                 (mapcar (lambda (r) (list :add-member r)) (reverse members))
                                 (mapcar (lambda (r) (list :add-port r)) (reverse ports))
                                 (mapcar (lambda (r) (list :add-hole r)) (reverse holes))))
        (let* ((delta (make-semantic-bundle-delta-v1
                       :expected-predecessor-snapshot (semantic-bundle-closure-v1-bundle-snapshot-ref closure)
                       :operations operations :provenance-ref (list :shg-vm-joint-growth-v1 namespace)))
               (candidate (apply-semantic-bundle-delta-v1 source closure delta))
               (closed nil) (generated nil))
          (multiple-value-setq (closed generated) (shg-vm-close-v1 candidate))
          (dolist (p (reverse productions))
            (multiple-value-bind (next next-closure registries relation-delta application)
                (apply #'shg-vm-add-relation-v1 candidate closed p)
              (setf candidate next closed next-closure generated registries
                    operations (append operations (semantic-bundle-delta-v1-operations relation-delta)))
              (push (list :application application :delta relation-delta) applications)))
          (let* ((aggregate (make-semantic-bundle-delta-v1
                             :expected-predecessor-snapshot (semantic-bundle-closure-v1-bundle-snapshot-ref closure)
                             :operations operations :provenance-ref (list :shg-vm-joint-growth-v1 namespace)))
                 (replayed (apply-semantic-bundle-delta-v1 source closure aggregate)))
            (dolist (kind *semantic-bundle-base-registry-kinds-v1*)
              (unless (equal (mapcar #'semantic-registry-row-identity-v1 (recursive-semantic-bundle-base-rows-v1 replayed kind))
                             (mapcar #'semantic-registry-row-identity-v1 (recursive-semantic-bundle-base-rows-v1 candidate kind)))
                (error "Joint aggregate disagrees with staged native rows: ~S." kind))))
          (setf (getf state :operations) operations
                (getf state :selected-member-refs) (append (getf state :selected-member-refs) (mapcar #'ref members))
                (getf state :step-growth-receipt)
                (list :namespace namespace :source-body address :source-calls (reverse source-calls)
                      :controller (ref controller) :machine descriptor :relations (reverse applications)
                      :semantic-status :open :activation-mode :open :behavioral-proof :open)))))
    state))
