;;; Emacs-plac integration: add the following to your .emacs

(define-generic-mode 'plac-mode
  '("#") ; comment chars
  '(); highlighted commands
  nil
  '(".plac"); file extensions
  nil)
 
(add-hook 'plac-mode-hook (lambda () (local-set-key [f4]  'plac-start)))
(add-hook 'plac-mode-hook (lambda () (local-set-key [f5]  'plac-send)))
(add-hook 'plac-mode-hook (lambda () (local-set-key [f6]  'plac-stop)))

(defvar *plac-process* nil)

(defun plac-start ()
  "Start an inferior plac process by inferring the script to use from the 
  shebang line"
  (interactive)
  (let ((shebang-line 
         (save-excursion
           (goto-line 1) (end-of-line)
           (buffer-substring 3 (point)))))
    (if *plac-process* (princ "plac already started")
      (setq *plac-process*
            (start-process
             "plac" "*plac*" "plac_runner.py" "-m" shebang-line))))
  (display-buffer "*plac*"))

(defun plac-send ()
  "Send the current region to the inferior plac process"
  (interactive)
  (process-send-region *plac-process* (region-beginning) (region-end)))

(defun plac-stop ()
  "Stop the inferior plac process by sending to it an EOF"
  (interactive)
  (process-send-eof *plac-process*)
  (setq *plac-process* nil))
