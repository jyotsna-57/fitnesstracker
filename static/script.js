document.addEventListener('DOMContentLoaded', function() {
    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const inputs = this.querySelectorAll('input[required]');
            let valid = true;
            
            inputs.forEach(input => {
                if (!input.value.trim()) {
                    valid = false;
                    input.style.borderColor = 'red';
                } else {
                    input.style.borderColor = '';
                }
            });
            
            if (!valid) {
                e.preventDefault();
                alert('Please fill in all required fields');
            }
        });
    });
    
    // Date inputs default to today
    const dateInputs = document.querySelectorAll('input[type="date"]');
    const today = new Date().toISOString().split('T')[0];
    dateInputs.forEach(input => {
        if (!input.value) {
            input.value = today;
        }
    });
    
    // Confirm before deleting
    const deleteLinks = document.querySelectorAll('a.delete');
    deleteLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item?')) {
                e.preventDefault();
            }
        });
    });
    
    // Auto-calculate calories based on exercise type and duration
    const exerciseTypeSelect = document.querySelector('select[name="exercise_type"]');
    const durationInput = document.querySelector('input[name="duration"]');
    
    if (exerciseTypeSelect && durationInput) {
        const calorieRates = {
            'Running': 10,
            'Cycling': 8,
            'Swimming': 9,
            'Weight Training': 5,
            'Yoga': 3,
            'Walking': 4
        };
        
        function calculateCalories() {
            const exerciseType = exerciseTypeSelect.value;
            const duration = parseInt(durationInput.value) || 0;
            const rate = calorieRates[exerciseType] || 7; // Default rate
            
            // You could display this somewhere, though the server will calculate it too
            console.log(`Estimated calories: ${duration * rate}`);
        }
        
        exerciseTypeSelect.addEventListener('change', calculateCalories);
        durationInput.addEventListener('input', calculateCalories);
    }
});