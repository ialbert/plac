;;; Emacs-plac integration: add the following to your .emacs

(define-generic-mode 'plac-mode
  '("#") ; comment chars
  '(); highlighted commands
  nil
  '(".plac\\'"); file extensions
  nil)
 
(add-hook 'plac-mode-hook (lambda () (local-set-key [f4]  'plac-start)))
(add-hook 'plac-mode-hook (lambda () (local-set-key [f5]  'plac-send)))
(add-hook 'plac-mode-hook (lambda () (local-set-key [f6]  'plac-stop)))

(defconst terminator 59); ASCII code for the semicolon
(defvar *plac-process* nil)

(defun plac-start ()
  "Start an inferior plac process by inferring the script to use from the 
  shebang line"
  (interactive)
  (let ((shebang-line 
         (save-excursion
           (goto-line 1) (end-of-line)
           (buffer-substring-no-properties 3 (point)))))
    (if *plac-process* (princ "plac already started")
      (setq *plac-process*
            (start-process
             "plac" "*plac*" "plac_runner.py" "-m" shebang-line))))
  (display-buffer "*plac*"))

;(defun plac-send ()
;  "Send the current region to the inferior plac process"
;  (interactive)
;  (save-excursion (set-buffer "*plac*") (erase-buffer))
;  (process-send-region *plac-process* (region-beginning) (region-end)))

(defun current-paragraph-beg-end ()
  "Returns the extrema of the current paragraph, delimited by semicolons"
  (interactive)
  (save-excursion
    (let ((beg (save-excursion (goto-line 2) (point))); skip the shebang
          (end (point-max)))
      ;; go backward
      (while (> (point) beg)
        (goto-char (1- (point)))
        (if (= terminator (following-char))
            (setq beg (point))))
      (if (= terminator (following-char))
          (setq beg (1+ beg)))
      ;; go forward
      (while (< (point) end)
        (goto-char (1+ (point)))
        (if (= 59 (following-char))
            (setq end (point))))
      (if (= 59 (following-char))
          (setq end (1+ end)))
      (list beg end))))
 
(defun plac-send ()
  "Send the current region to the inferior plac process"
  (interactive)
  (save-excursion (set-buffer "*plac*") (erase-buffer))
  (let ((p (apply 'buffer-substring-no-properties (current-paragraph-beg-end))))
    (message p)
    (process-send-string *plac-process* (concat p "\n"))))
    ;(switch-to-buffer-other-window "*plac*")))
    ;(save-excursion (set-buffer "*plac*") 
    ;  (set-window-start (selected-window) 1 nil))))

(defun plac-stop ()
  "Stop the inferior plac process by sending to it an EOF"
  (interactive)
  (process-send-eof *plac-process*)
  (setq *plac-process* nil)
  "killed *plac-process*")

(provide 'plac)
