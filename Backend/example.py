import resend

resend.api_key = "re_S8UxUxRv_Nhvi8FJo4ypSfNY93nyoRKLo"

r = resend.Emails.send({
  "from": "onboarding@resend.dev",
  "to": "b23197@students.iitmandi.ac.in",
  "subject": "Hello World",
  "html": "<p>Congrats on sending your <strong>first email</strong>!</p>"
})
