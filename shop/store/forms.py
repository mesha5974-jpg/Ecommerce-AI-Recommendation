from django import forms

from .models import ContactMessage, NewsletterSubscriber, Review


class NewsletterForm(forms.ModelForm):
    class Meta:
        model = NewsletterSubscriber
        fields = ["email"]

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def validate_unique(self):
        # Re-subscribing is not an error from the visitor's point of view.
        pass


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "subject", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Your name", "autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"placeholder": "you@example.com", "autocomplete": "email"}),
            "subject": forms.TextInput(attrs={"placeholder": "How can we help?"}),
            "message": forms.Textarea(attrs={"rows": 6, "placeholder": "Your message"}),
        }

    def clean_message(self):
        message = self.cleaned_data["message"].strip()
        if len(message) < 10:
            raise forms.ValidationError("Please write at least a short sentence.")
        return message


class ReviewForm(forms.ModelForm):
    rating = forms.IntegerField(min_value=1, max_value=5, widget=forms.HiddenInput)

    class Meta:
        model = Review
        fields = ["rating", "title", "body"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Summarise your experience"}),
            "body": forms.Textarea(attrs={"rows": 4, "placeholder": "What did you love? Anything to improve?"}),
        }
