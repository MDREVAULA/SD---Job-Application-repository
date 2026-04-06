function copyPassword() {

    const passwordField = document.getElementById("tempPassword");

    if (!passwordField) return;

    navigator.clipboard.writeText(passwordField.value)
        .then(() => {
            alert("Temporary password copied!");
        })
        .catch(() => {
            alert("Failed to copy password.");
        });

}